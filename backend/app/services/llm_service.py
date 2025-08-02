import os
import json
import logging
from typing import Dict, Any, Optional, List
from cerebras.cloud.sdk import Cerebras
from app.config import settings
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = settings.cerebras_api_key
        
        # Initialize Cerebras client
        try:
            self.client = Cerebras(api_key=self.api_key)
            logger.info("Cerebras client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cerebras client: {e}")
            self.client = None
    
    async def generate_chart_code(self, user_query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart code using LLM"""
        try:
            # Create system prompt
            system_prompt = self._create_system_prompt(data_context)

            logger.info(f"[DEBUG] System prompt sent to LLM: {system_prompt}")

            # Generate response from LLM (synchronous call)
            response = self.client.chat.completions.create(
                model="llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # Log the response for debugging
            logger.info(f"[DEBUG] Cerebras LLM response: {response}")

            # Extract the response content
            response_content = response.choices[0].message.content
            logger.info(f"[DEBUG] LLM response content: {response_content}")

            # Parse the response
            result = self._parse_llm_response(response_content, data_context)
            logger.info(f"[DEBUG] Parsed LLM result: {result}")

            # Check if this is a "no data" response
            if not data_context or not data_context.get("file_data"):
                # If no data context, return a helpful message instead of trying to generate code
                return {
                    "code": "",
                    "chart_type": "none",
                    "data_context": data_context,
                    "raw_response": "I'd be happy to help you generate a chart! However, I don't see any data file uploaded yet. Please upload a CSV or Excel file first, and then I'll be able to create visualizations based on your data."
                }

            return result
        except Exception as e:
            logger.error(f"Error generating chart code: {e}")
            # Instead of falling back to mock, raise an error
            raise RuntimeError(f"LLM chart code generation failed: {e}")
    
    def _create_system_prompt(self, data_context: Dict[str, Any]) -> str:
        """Create system prompt with data context"""
        
        prompt = """You are an expert data visualization assistant. Your task is to generate Python code that creates charts and visualizations based on user queries.

Available data context:
"""
        
        # Check if we have any data context
        if not data_context or not data_context.get("file_data"):
            prompt += """
NO DATA CONTEXT AVAILABLE:
The user has requested a chart, but no data file has been uploaded or the data context is missing.

Please inform the user that they need to upload a CSV or Excel file first before generating charts.
Do not generate any code - just provide a helpful message asking them to upload data.
"""
            return prompt
        
        if "file_data" in data_context:
            df_info = data_context["file_data"]
            # Build a preview table string
            preview_rows = df_info.get('head', [])
            columns = df_info.get('columns', [])
            dtypes = df_info.get('dtypes', {})
            preview_table = ''
            if preview_rows and columns:
                preview_table += '\n| ' + ' | '.join(columns) + ' |\n'
                preview_table += '| ' + ' | '.join(['---'] * len(columns)) + ' |\n'
                for row in preview_rows:
                    preview_table += '| ' + ' | '.join(str(row.get(col, '')) for col in columns) + ' |\n'
            prompt += f"""
File Data Information:
- Shape: {df_info.get('shape', 'Unknown')}
- Columns: {df_info.get('columns', [])}
- Data Types: {dtypes}
- Numeric Columns: {df_info.get('numeric_columns', [])}
- Categorical Columns: {df_info.get('categorical_columns', [])}
- Data Preview (first rows):
{preview_table}

CRITICAL INSTRUCTIONS:
1. You MUST use ONLY the DataFrame 'df' (already loaded from the uploaded file) and the columns from the data preview above.
2. **ABSOLUTELY NEVER** use pd.DataFrame({{ ... }}), pd.read_csv, pd.read_excel, or any file loading functions.
3. **CRITICAL**: The DataFrame 'df' is already loaded and available in the execution environment. DO NOT try to load any files.
4. **FORBIDDEN CODE PATTERNS** - DO NOT USE:
   - pd.read_csv('filename.csv')
   - pd.read_excel('filename.xlsx')
   - pd.DataFrame({{ ... }})
   - Any file path references like './uploads/...'
   - Any file loading operations
5. **DATA TYPE HANDLING - CRITICAL**:
   - ALWAYS check data types before applying operations: `print(df.dtypes)` or `print(df['column_name'].dtype)`
   - If a column is already numeric (float64, int64), DO NOT use .str accessor
   - Only use .str accessor if the column is object/string type
   - For currency columns that might be mixed types, use: `pd.to_numeric(df['column'], errors='coerce')`
   - Example of safe currency handling:
     ```python
     # Check if column is already numeric
     if df['Balance'].dtype in ['float64', 'int64']:
         balance_values = df['Balance']
     else:
         # Only use string operations if it's actually a string column
         balance_values = pd.to_numeric(df['Balance'].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')
     ```
6. If you need to filter or process data, always use the 'df' variable.
7. **MOST IMPORTANT**: If the user prompt is ambiguous or doesn't specify exact columns, YOU MUST intelligently select the most relevant columns from the data and generate an appropriate chart. DO NOT ask the user to specify columns.
8. **Chart Selection Logic**:
   - For financial data (columns like 'Debit', 'Credit', 'Amount', 'Balance'): Use the first numeric column vs a categorical column or date column
   - For time series data: Use date/time columns with numeric columns
   - For categorical data: Use categorical columns with numeric columns
   - Default: Use the first two columns if unsure
9. **Always explain your column choice** in plain English before the code
10. DO NOT create a new DataFrame or use sample data
11. Make the chart informative and well-labeled
12. **START YOUR CODE WITH**: The DataFrame 'df' is already loaded and contains the data. I will create a chart using the existing data.
13. **SAFE DATA PROCESSING PATTERN**:
    ```python
    # Always start with data type inspection
    print("Data types:", df.dtypes)
    print("Sample data:", df.head())
    
    # Safe numeric conversion
    if 'Balance' in df.columns:
        if df['Balance'].dtype in ['float64', 'int64']:
            balance_data = df['Balance']
        else:
            balance_data = pd.to_numeric(df['Balance'].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')
    ```
"""
        
        if "database_data" in data_context:
            db_info = data_context["database_data"]
            prompt += f"""
Database Data Information:
- Tables: {db_info.get('tables', [])}
- Schema: {db_info.get('schema_info', {})}
"""
        
        if "file_analysis" in data_context:
            prompt += f"\nData Analysis Results (from previous analysis):\n{data_context['file_analysis']}\n"
        
        prompt += """
Code Generation Rules:
1. Always import required libraries (pandas, matplotlib, seaborn, plotly)
2. Use the provided data context to understand the data structure
3. Generate appropriate visualizations based on the user query
4. Include data preprocessing if needed
5. CRITICAL: Create charts that can be captured by the system
6. DO NOT save charts to files - create them in memory only
7. For matplotlib: Use plt.figure() and create charts in memory, DO NOT use plt.savefig()
8. For plotly: Store the figure in a variable named 'fig' (e.g., fig = px.bar(...))
9. Make the code safe and executable
10. Handle potential errors gracefully
11. KEEP THE CODE SIMPLE - avoid complex string formatting or JSON dumps
12. DO NOT include print statements with complex formatting
13. **ALWAYS CHECK DATA TYPES FIRST** before applying any operations

IMPORTANT: The system will capture charts from variables in memory, not from saved files.
DO NOT use plt.savefig(), fig.write_image(), or any file saving functions.
DO NOT include complex print statements or JSON dumps in the code.

Response Format:
First, explain your analysis and column selection in plain English, then provide the code:

```python
# Generated code here
# Make sure to store the chart in a variable that can be captured
# DO NOT save to files
# KEEP IT SIMPLE
# ALWAYS check data types first
```

IMPORTANT: 
- Always start with a clear explanation of what chart you're creating and why you chose specific columns
- If the user's request is vague, make intelligent assumptions based on the data structure
- Focus on creating meaningful visualizations that provide insights
- Use appropriate chart types: bar charts for categorical comparisons, line charts for trends, scatter plots for correlations, etc.
- **ALWAYS check data types before applying string operations**
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response to extract code and metadata"""
        
        # Extract code block
        code_start = response.find("```python")
        code_end = response.find("```", code_start + 9)
        
        if code_start != -1 and code_end != -1:
            code = response[code_start + 9:code_end].strip()
        else:
            # Fallback: try to extract code without markdown
            code = response.strip()
        
        # Determine chart type from code
        chart_type = self._detect_chart_type(code)
        
        # Create result structure
        result = {
            "code": code,
            "chart_type": chart_type,
            "data_context": data_context,
            "raw_response": response
        }
        
        return result
    
    def _detect_chart_type(self, code: str) -> str:
        """Detect chart type from generated code"""
        code_lower = code.lower()
        
        if any(keyword in code_lower for keyword in ["plt.plot", "sns.lineplot", "px.line"]):
            return "line"
        elif any(keyword in code_lower for keyword in ["plt.bar", "sns.barplot", "px.bar"]):
            return "bar"
        elif any(keyword in code_lower for keyword in ["plt.scatter", "sns.scatterplot", "px.scatter"]):
            return "scatter"
        elif any(keyword in code_lower for keyword in ["plt.pie", "px.pie"]):
            return "pie"
        elif any(keyword in code_lower for keyword in ["plt.hist", "sns.histplot", "px.histogram"]):
            return "histogram"
        elif any(keyword in code_lower for keyword in ["sns.heatmap", "px.imshow"]):
            return "heatmap"
        elif any(keyword in code_lower for keyword in ["plt.boxplot", "sns.boxplot", "px.box"]):
            return "box"
        elif any(keyword in code_lower for keyword in ["sns.violinplot", "px.violin"]):
            return "violin"
        else:
            return "unknown"
    
    def _generate_mock_chart_code(self, user_query: str) -> str:
        """Generate mock chart code for development"""
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["bar", "bar chart"]):
            return """
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Sample data
data = {'Category': ['A', 'B', 'C', 'D'], 'Value': [10, 20, 15, 25]}
df = pd.DataFrame(data)

# Create plotly chart (stored in fig variable for capture)
fig = px.bar(df, x='Category', y='Value', title='Bar Chart Example')
fig.update_layout(xaxis_title='Category', yaxis_title='Value')

# Also create matplotlib version as backup (in memory only)
plt.figure(figsize=(10, 6))
plt.bar(df['Category'], df['Value'], color='skyblue')
plt.title('Bar Chart')
plt.xlabel('Category')
plt.ylabel('Value')
plt.grid(True, alpha=0.3)
# Note: DO NOT use plt.savefig() - keep chart in memory for capture
```
"""
        elif any(word in query_lower for word in ["line", "trend", "time"]):
            return """
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np

# Sample time series data
dates = pd.date_range('2023-01-01', periods=30, freq='D')
values = np.random.randn(30).cumsum()
df = pd.DataFrame({'Date': dates, 'Value': values})

# Create plotly chart (stored in fig variable for capture)
fig = px.line(df, x='Date', y='Value', title='Time Series Trend')
fig.update_layout(xaxis_title='Date', yaxis_title='Value')

# Also create matplotlib version as backup (in memory only)
plt.figure(figsize=(12, 6))
plt.plot(df['Date'], df['Value'], marker='o', linewidth=2, markersize=4)
plt.title('Time Series Trend')
plt.xlabel('Date')
plt.ylabel('Value')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
# Note: DO NOT use plt.savefig() - keep chart in memory for capture
```
"""
        elif any(word in query_lower for word in ["scatter", "correlation"]):
            return """
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np

# Sample scatter data
np.random.seed(42)
x = np.random.randn(100)
y = x * 0.5 + np.random.randn(100) * 0.5
df = pd.DataFrame({'X': x, 'Y': y})

# Create plotly chart (stored in fig variable for capture)
fig = px.scatter(df, x='X', y='Y', title='Scatter Plot')
fig.update_layout(xaxis_title='X Values', yaxis_title='Y Values')

# Also create matplotlib version as backup (in memory only)
plt.figure(figsize=(10, 6))
plt.scatter(df['X'], df['Y'], alpha=0.6, color='red')
plt.title('Scatter Plot')
plt.xlabel('X Values')
plt.ylabel('Y Values')
plt.grid(True, alpha=0.3)
# Note: DO NOT use plt.savefig() - keep chart in memory for capture
```
"""
        else:
            return """
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Sample data
data = {'Category': ['A', 'B', 'C'], 'Value': [10, 20, 15]}
df = pd.DataFrame(data)

# Create plotly chart (stored in fig variable for capture)
fig = px.bar(df, x='Category', y='Value', title='Simple Chart')
fig.update_layout(xaxis_title='Category', yaxis_title='Value')

# Also create matplotlib version as backup (in memory only)
plt.figure(figsize=(8, 6))
plt.bar(df['Category'], df['Value'], color='lightblue')
plt.title('Simple Chart')
plt.xlabel('Category')
plt.ylabel('Value')
# Note: DO NOT use plt.savefig() - keep chart in memory for capture
```
"""
    
    def _generate_mock_response(self, user_query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response for development"""
        mock_code = self._generate_mock_chart_code(user_query)
        
        # Extract code from markdown if present
        if "```python" in mock_code:
            code_start = mock_code.find("```python") + 9
            code_end = mock_code.find("```", code_start)
            if code_end != -1:
                mock_code = mock_code[code_start:code_end].strip()
        
        chart_type = self._detect_chart_type(mock_code)
        
        return {
            "code": mock_code,
            "chart_type": chart_type,
            "data_context": data_context,
            "raw_response": mock_code
        }
    
    async def generate_text_response(self, user_query: str, data_context: Dict[str, Any]) -> str:
        """Generate text response for non-chart queries"""
        
        try:
            if not self.client:
                logger.warning("Cerebras client not available, using mock response")
                return f"I understand you're asking about: {user_query}. Based on the available data, I can help you analyze this information. Would you like me to create a visualization or provide specific insights about your data?"
            
            system_prompt = """You are a helpful data analysis assistant. Provide insights and analysis based on the user's query and the available data context."""
            
            user_prompt = f"""
User Query: {user_query}

Data Context: {json.dumps(data_context, indent=2)}

Please provide a helpful response that addresses the user's query using the available data context.
"""
            
            # Get response from Cerebras LLM
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama3.1-8b",
                max_tokens=800,
                temperature=0.7,
                top_p=1
            )
            logger.info(f"[DEBUG] Cerebras LLM text response: {response}")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text response: {e}")
            return f"I understand you're asking about: {user_query}. Based on the available data, I can help you analyze this information. Would you like me to create a visualization or provide specific insights about your data?"

def extract_chart_intent(user_query: str, columns: list) -> dict:
    """Extract chart type and columns from user query using simple heuristics."""
    chart_types = ['bar', 'line', 'pie', 'scatter', 'histogram']
    chart_type = None
    for ct in chart_types:
        if ct in user_query.lower():
            chart_type = ct
            break
    # Find columns mentioned in the prompt that match real columns
    used_columns = []
    for col in columns:
        if re.search(rf"\\b{re.escape(col)}\\b", user_query, re.IGNORECASE):
            used_columns.append(col)
    return {'chart_type': chart_type, 'columns': used_columns}

def generate_chart_code_template(chart_type: str, columns: list) -> str:
    """Generate Python code for a chart using a template and real df."""
    if chart_type == 'bar' and len(columns) >= 2:
        x, y = columns[0], columns[1]
        return f"""
import matplotlib.pyplot as plt
plt.figure(figsize=(10,6))
df['{y}'] = pd.to_numeric(df['{y}'], errors='coerce')
plt.bar(df['{x}'], df['{y}'])
plt.xlabel('{x}')
plt.ylabel('{y}')
plt.title('{y} by {x}')
plt.xticks(rotation=45)
plt.tight_layout()
"""
    if chart_type == 'pie' and len(columns) >= 2:
        labels, values = columns[0], columns[1]
        return f"""
import matplotlib.pyplot as plt
sizes = df['{values}'].astype(float)
labels = df['{labels}']
plt.figure(figsize=(8,8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.title('Pie chart of {values} by {labels}')
plt.tight_layout()
"""
    # Add more templates as needed
    return None


llm_service = LLMService()
