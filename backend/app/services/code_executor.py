import asyncio
import subprocess
import tempfile
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
from app.models.schemas import CodeExecutionRequest, CodeExecutionResponse
import logging
from app.config import settings


class CodeExecutor:
    def __init__(self):
        self.safe_imports = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 
            'sklearn', 'scipy', 'json', 'datetime', 'math'
        }
    
    def _validate_code_uses_real_columns(self, code: str, columns: list) -> bool:
        """Check if the generated code references at least one real column name."""
        import re
        
        # Reject if code creates a new DataFrame from sample data
        if re.search(r"pd\.DataFrame\s*\(\s*\{", code):
            return False
        # Reject if code tries to load a file
        if re.search(r"pd\.read_csv|pd\.read_excel|open\s*\(", code):
            return False
        
        # If no columns are available, allow the code to proceed (LLM will handle it)
        if not columns:
            return True
            
        # Check if code references any real column
        for col in columns:
            # Look for the column name as a string in the code
            if re.search(rf"['\"]{re.escape(col)}['\"]", code):
                return True
        
        # If no columns are referenced but the code looks like it's using 'df', allow it
        # (the LLM might be using column indices or other methods)
        if re.search(r"df\[", code) or re.search(r"df\.", code):
            return True
        
        # Allow code that creates charts with hardcoded data (user explicitly requested it)
        # Check for common patterns of hardcoded chart data
        hardcoded_patterns = [
            r"values\s*=\s*\[",  # values = [1, 2, 3]
            r"labels\s*=\s*\[",  # labels = ["A", "B", "C"]
            r"data\s*=\s*\[",    # data = [1, 2, 3]
            r"plt\.bar\s*\(\s*\[",  # plt.bar([1, 2], [3, 4])
            r"plt\.plot\s*\(\s*\[",  # plt.plot([1, 2], [3, 4])
            r"plt\.scatter\s*\(\s*\[",  # plt.scatter([1, 2], [3, 4])
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, code):
                return True
            
        return False
    
    def _validate_code_does_not_read_files(self, code: str) -> bool:
        """Check if the generated code tries to read files (which is not allowed)."""
        import re
        # Check for file reading operations
        file_reading_patterns = [
            r"pd\.read_csv\s*\(",
            r"pd\.read_excel\s*\(",
            r"open\s*\(",
            r"with\s+open\s*\(",
            r"\.read\s*\(",
            r"\.load\s*\("
        ]
        
        for pattern in file_reading_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        return True

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        """Execute generated code in a safe environment"""
        print(f"[DEBUG] Starting execute_code method")
        start_time = asyncio.get_event_loop().time()
        columns = []
        if request.data_context and "file_data" in request.data_context:
            columns = request.data_context["file_data"].get("columns", [])
            print(f"[DEBUG] Found columns: {columns}")
        
        # Validate that code doesn't try to read files
        print(f"[DEBUG] Validating code doesn't read files")
        if not self._validate_code_does_not_read_files(request.code):
            print(f"[DEBUG] Code validation failed - tries to read files")
            return CodeExecutionResponse(
                success=False,
                error="The generated code tries to read files, which is not allowed. The data should already be loaded in the 'df' variable. Please try rephrasing your request.",
                execution_time=0
            )
        
        # Validate that code uses real columns if available
        print(f"[DEBUG] Validating code uses real columns")
        if columns and not self._validate_code_uses_real_columns(request.code, columns):
            print(f"[DEBUG] Code validation failed - doesn't use real columns")
            return CodeExecutionResponse(
                success=False,
                error=f"The generated code doesn't seem to use your data properly. Available columns: {columns}. Please try rephrasing your request.",
                execution_time=0
            )
        
        print(f"[DEBUG] Code validation passed, creating temp directory")
        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"[DEBUG] Created temp directory: {temp_dir}")
                # Create execution script
                script_path = os.path.join(temp_dir, "execute.py")
                
                # Prepare the execution code
                print(f"[DEBUG] Preparing execution code")
                execution_code = self._prepare_execution_code(request.code, request.data_context)
                
                print(f"[DEBUG] Writing script to file")
                with open(script_path, 'w') as f:
                    f.write(execution_code)
                
                print(f"[DEBUG] Execution code prepared: {len(execution_code)} characters")
                print(f"[DEBUG] Script path: {script_path}")
                print(f"[DEBUG] Script file exists: {os.path.exists(script_path)}")
                print(f"[DEBUG] Script file size: {os.path.getsize(script_path)} bytes")
                print(f"[DEBUG] First 200 chars of script: {execution_code[:200]}")
                print(f"[DEBUG] Last 200 chars of script: {execution_code[-200:]}")
                
                # Execute the code with timeout
                print(f"[DEBUG] Starting code execution")
                result = await asyncio.wait_for(
                    self._run_code(script_path, temp_dir),
                    timeout=request.timeout
                )
                print(f"[DEBUG] Code execution completed, result: {result}")
                
                # If execution failed, surface the error
                if result.get('error'):
                    print(f"[DEBUG] Execution failed with error: {result.get('error')}")
                    return CodeExecutionResponse(
                        success=False,
                        error=result.get('error'),
                        execution_time=asyncio.get_event_loop().time() - start_time
                    )
                
                # If no chart data was generated, return an error
                if not result.get('chart_data'):
                    print(f"[DEBUG] No chart data generated")
                    return CodeExecutionResponse(
                        success=False,
                        error="No chart image was generated. The code executed successfully but no chart was created. Please check your data and prompt.",
                        execution_time=asyncio.get_event_loop().time() - start_time
                    )
                
                print(f"[DEBUG] Execution result: {result}")
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return CodeExecutionResponse(
                    success=True,
                    output=result.get('output'),
                    chart_data=result.get('chart_data'),
                    execution_time=execution_time
                )
                
        except asyncio.TimeoutError:
            print(f"[DEBUG] Execution timed out")
            execution_time = asyncio.get_event_loop().time() - start_time
            return CodeExecutionResponse(
                success=False,
                error="Code execution timed out",
                execution_time=execution_time
            )
        except Exception as e:
            print(f"[DEBUG] Execution failed with exception: {e}")
            execution_time = asyncio.get_event_loop().time() - start_time
            return CodeExecutionResponse(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _prepare_execution_code(self, code: str, data_context: Optional[Dict[str, Any]]) -> str:
        """Prepare the execution code with proper data setup and validation"""
        try:
            # Get file data from context
            file_data = data_context.get("file_data", {})
            
            # Check if we have column mapping information
            column_mapping = file_data.get("column_mapping", {})
            reverse_mapping = {v: k for k, v in column_mapping.items()}
            
            # Replace old column names with proper column names in the generated code
            if column_mapping:
                # Create a mapping of old column names to new column names
                old_to_new_mapping = {}
                for old_name, new_name in column_mapping.items():
                    if old_name != new_name:  # Only map if they're different
                        old_to_new_mapping[old_name] = new_name
                
                # Replace old column names in the generated code
                modified_code = code
                for old_name, new_name in old_to_new_mapping.items():
                    # Replace df['old_name'] with df['new_name']
                    modified_code = modified_code.replace(f"df['{old_name}']", f"df['{new_name}']")
                    # Replace df.iloc[:, index] references if we can identify them
                    # This is a more complex replacement that would need column index mapping
                
                # Log the column mapping replacements
                if modified_code != code:
                    print(f"[DEBUG] Applied column mapping to generated code")
                    print(f"[DEBUG] Column mapping applied: {old_to_new_mapping}")
                    code = modified_code
            
            # Always use preview data instead of trying to read actual files
            # This avoids issues with stale file paths in the database
            print(f"[DEBUG] Using preview data for execution (file system loading is disabled)")
            file_data_for_serialization = self._convert_nulls_to_none(data_context["file_data"])
            serialized_data = self._serialize_data_for_python(file_data_for_serialization)
            
            # Create data setup code
            data_setup = f"""
# Load data from context (preview data)
file_data = {serialized_data}
if isinstance(file_data, dict) and 'head' in file_data:
    # Create DataFrame from head data, but skip the first row if it's a header
    head_data = file_data['head']
    if len(head_data) > 1:
        # Check if first row looks like headers (contains 'Date', 'Category', etc.)
        first_row = head_data[0]
        if any('Date' in str(v) or 'Category' in str(v) or 'Description' in str(v) for v in first_row.values()):
            # Skip header row and use second row onwards as data with proper column names
            df = pd.DataFrame(head_data[1:], columns=first_row.values())
            # Now df has proper column names like 'Date', 'Category', 'Description', etc.
        else:
            # Use all data as is
            df = pd.DataFrame(head_data)
    else:
        df = pd.DataFrame(head_data)
else:
    # If no preview data available, raise an error instead of using mock data
    raise ValueError("No data available. Please ensure a file is uploaded and contains valid data.")

# Print data information for debugging and LLM understanding
print('[DEBUG EXECUTOR] df.shape:', df.shape)
print('[DEBUG EXECUTOR] df.columns:', list(df.columns))
print('[DEBUG EXECUTOR] df.dtypes:')
for col in df.columns:
    print(f'  {{col}}: {{df[col].dtype}}')
print('[DEBUG EXECUTOR] df.head():')
print(df.head())
"""
        
            import re
            # Remove any lines from the LLM-generated code that try to load files
            forbidden_patterns = [
                'read_csv',
                'read_excel',
                './uploads/',
                'open(',
                'with open',
            ]
            code_lines = code.splitlines()
            filtered_lines = [line for line in code_lines if not any(pattern in line for pattern in forbidden_patterns)]
            code = '\n'.join(filtered_lines)

            # Prepare the execution code
            execution_code = f"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
import io
import json
import sys

{data_setup}

# Validate DataFrame
if df.empty:
    raise ValueError("DataFrame is empty. Please check your data source.")

# User's chart generation code
{code}

# Debug: Check if fig exists after LLM code
print('[DEBUG EXECUTOR] fig in locals:', 'fig' in locals(), file=sys.stderr)

# Ensure we have a figure to return
if 'fig' not in locals():
    fig = plt.gcf()

# Capture the figure as base64 image
print('[DEBUG EXECUTOR] Capturing figure...', file=sys.stderr)
img_buffer = io.BytesIO()
fig.savefig(img_buffer, format='png', bbox_inches='tight')
img_buffer.seek(0)
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
print('[DEBUG EXECUTOR] Figure captured, base64 length:', len(img_base64), file=sys.stderr)

# Return the result as JSON
result = {{
    'success': True,
    'chart_data': {{
        'type': 'matplotlib',
        'data': img_base64
    }}
}}

print('RESULT_START')
print(json.dumps(result))
print('RESULT_END')
"""
            print("[DEBUG] FINAL EXECUTION CODE:\n" + execution_code)
            
            print(f"[DEBUG] Prepared execution code with column mapping")
            return execution_code
            
        except Exception as e:
            print(f"Error preparing execution code: {e}")
            raise
    
    def _serialize_data_for_python(self, data: Any) -> str:
        """Serialize data for Python execution, handling null values properly"""
        import json
        
        # Debug logging
        print(f"[DEBUG] _serialize_data_for_python called with type: {type(data)}")
        
        # If data is a JSON string (from database), parse it first
        if isinstance(data, str):
            try:
                print("[DEBUG] Data is a string, parsing as JSON first")
                parsed_data = json.loads(data)
                # Recursively convert null to None
                parsed_data = self._convert_nulls_to_none(parsed_data)
                # Then serialize to Python literal
                return self._serialize_data_for_python(parsed_data)
            except json.JSONDecodeError:
                print("[DEBUG] Failed to parse data as JSON, treating as regular string")
                return f'"{data}"'
        
        # If data is already a dict/list with None values, serialize it directly
        if isinstance(data, dict):
            # Convert the dict to a Python literal string
            print("[DEBUG] Data is dict, converting to Python literal")
            return self._dict_to_python_literal(data)
        elif isinstance(data, list):
            # Convert the list to a Python literal string
            print("[DEBUG] Data is list, converting to Python literal")
            return self._list_to_python_literal(data)
        else:
            # For other types, use JSON with null replacement
            print("[DEBUG] Data is other type, using JSON serialization")
            json_str = json.dumps(data, default=str)
            json_str = json_str.replace('"null"', 'None')
            return json_str
    
    def _convert_nulls_to_none(self, obj):
        """Recursively convert null values to None for Python compatibility"""
        if obj is None:
            return None
        elif isinstance(obj, dict):
            converted = {}
            for k, v in obj.items():
                converted[k] = self._convert_nulls_to_none(v)
            return converted
        elif isinstance(obj, list):
            converted = []
            for item in obj:
                converted.append(self._convert_nulls_to_none(item))
            return converted
        else:
            return obj
    
    def _dict_to_python_literal(self, obj: dict) -> str:
        """Convert dict to Python literal string"""
        items = []
        for k, v in obj.items():
            if isinstance(v, dict):
                items.append(f'"{k}": {self._dict_to_python_literal(v)}')
            elif isinstance(v, list):
                items.append(f'"{k}": {self._list_to_python_literal(v)}')
            elif v is None:
                items.append(f'"{k}": None')
            elif isinstance(v, str):
                items.append(f'"{k}": "{v}"')
            else:
                items.append(f'"{k}": {v}')
        return '{' + ', '.join(items) + '}'
    
    def _list_to_python_literal(self, obj: list) -> str:
        """Convert list to Python literal string"""
        items = []
        for v in obj:
            if isinstance(v, dict):
                items.append(self._dict_to_python_literal(v))
            elif isinstance(v, list):
                items.append(self._list_to_python_literal(v))
            elif v is None:
                items.append('None')
            elif isinstance(v, str):
                items.append(f'"{v}"')
            else:
                items.append(str(v))
        return '[' + ', '.join(items) + ']'
    
    async def _run_code(self, script_path: str, temp_dir: str) -> Dict[str, Any]:
        """Run code in a subprocess"""
        print(f"[DEBUG] _run_code called with script_path: {script_path}")
        print(f"[DEBUG] _run_code called with temp_dir: {temp_dir}")
        print(f"[DEBUG] Script file exists: {os.path.exists(script_path)}")
        print(f"[DEBUG] Script file size: {os.path.getsize(script_path)} bytes")
        
        # Create a Python subprocess
        print(f"[DEBUG] Creating subprocess with python3 and script_path")
        process = await asyncio.create_subprocess_exec(
            'python3', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir
        )
        
        print(f"[DEBUG] Subprocess created, PID: {process.pid}")
        print(f"[DEBUG] Waiting for subprocess to complete...")
        
        stdout, stderr = await process.communicate()
        
        print(f"[DEBUG] Process return code: {process.returncode}")
        print(f"[DEBUG] Stdout: {stdout.decode()}")
        print(f"[DEBUG] Stderr: {stderr.decode()}")
        
        if process.returncode == 0:
            try:
                stdout_str = stdout.decode().strip()
                
                # Look for JSON result between RESULT_START and RESULT_END markers
                if "RESULT_START" in stdout_str and "RESULT_END" in stdout_str:
                    start_idx = stdout_str.find("RESULT_START") + len("RESULT_START")
                    end_idx = stdout_str.find("RESULT_END")
                    result_str = stdout_str[start_idx:end_idx].strip()
                    print(f"[DEBUG] Found result between markers: {result_str}")
                    return json.loads(result_str)
                
                # Fallback: try to parse the entire stdout as JSON
                if stdout_str:
                    # Try to find the last complete JSON object
                    # Look for the last occurrence of a complete JSON object
                    json_start = stdout_str.rfind('{')
                    if json_start != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        json_end = -1
                        for i in range(json_start, len(stdout_str)):
                            if stdout_str[i] == '{':
                                brace_count += 1
                            elif stdout_str[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        if json_end != -1:
                            json_str = stdout_str[json_start:json_end]
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                pass
                    
                    # If we can't find a complete JSON object, try parsing the whole string
                    try:
                        return json.loads(stdout_str)
                    except json.JSONDecodeError:
                        pass
                else:
                    return {'success': True, 'output': '', 'chart_data': None}
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON decode error: {e}")
                # Try to extract chart data from the output even if JSON parsing fails
                stdout_str = stdout.decode()
                if 'chart_data' in stdout_str and 'type' in stdout_str:
                    # Try to extract the chart data manually
                    try:
                        # Find the chart_data section
                        chart_start = stdout_str.find('"chart_data"')
                        if chart_start != -1:
                            # Find the start of the chart_data object
                            obj_start = stdout_str.find('{', chart_start)
                            if obj_start != -1:
                                # Find the matching closing brace
                                brace_count = 0
                                obj_end = -1
                                for i in range(obj_start, len(stdout_str)):
                                    if stdout_str[i] == '{':
                                        brace_count += 1
                                    elif stdout_str[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            obj_end = i + 1
                                            break
                                
                                if obj_end != -1:
                                    chart_json = stdout_str[obj_start:obj_end]
                                    chart_data = json.loads(chart_json)
                                    return {
                                        'success': True,
                                        'output': stdout.decode(),
                                        'chart_data': chart_data
                                    }
                    except Exception as e:
                        print(f"[DEBUG] Failed to extract chart data: {e}")
                
                return {'success': False, 'error': f'JSON decode error: {e}', 'chart_data': None}
        else:
            # Process failed
            stderr_str = stderr.decode()
            return {'success': False, 'error': f'Process failed with return code {process.returncode}: {stderr_str}', 'chart_data': None}


code_executor = CodeExecutor()
