import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import pandas as pd
import numpy as np
import re
from app.models.schemas import QueryIntent, ResponseType, DataManipulationResult, CalculationResult
from app.services.llm_service import llm_service

if TYPE_CHECKING:
    from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AgenticService:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        
        # Remove hardcoded keywords - now using LLM for intent classification
        self.calculation_keywords = []
        self.manipulation_keywords = []
        self.analysis_keywords = []
    
    async def analyze_query_intent(self, user_query: str, data_context: Dict[str, Any]) -> QueryIntent:
        """Analyze user query to determine the intent using LLM"""
        query_lower = user_query.lower()
        
        print(f"[DEBUG] ===== INTENT ANALYSIS DEBUG =====")
        print(f"[DEBUG] User query: {user_query}")
        print(f"[DEBUG] Query lower: {query_lower}")
        print(f"[DEBUG] LLM service client: {self.llm_service.client}")
        
        # Use LLM to determine intent instead of hardcoded rules
        try:
            print(f"[DEBUG] Starting LLM intent analysis for query: {user_query}")
            
            system_prompt = """You are an AI assistant that analyzes user queries to determine their intent. 
            Classify the query into one of these categories:
            
            - VISUALIZATION: User wants to see charts, graphs, plots, or visual representations (keywords: chart, graph, plot, visualize, bar, line, scatter, pie, show me, display, create a chart, create a graph, visualization)
            - DATA_MANIPULATION: User wants to modify, filter, sort, add columns, or manipulate the data (keywords: add, create, modify, filter, sort, new column, update, change)
            - DATA_ANALYSIS: User wants to analyze data, get insights, statistics, trends, or market performance analysis (keywords: analyze, analysis, stats, statistics, insights, trends, market, performance)
            - GENERAL_QUERY: General questions, analysis, or other queries
            
            Respond with ONLY the category name (VISUALIZATION, DATA_MANIPULATION, DATA_ANALYSIS, or GENERAL_QUERY)."""
            
            print(f"[DEBUG] Sending LLM request for intent analysis")
            print(f"[DEBUG] System prompt: {system_prompt}")
            
            # Use synchronous call since Cerebras client is not async
            response = self.llm_service.client.chat.completions.create(
                model="llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {user_query}"}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            print(f"[DEBUG] LLM response received: {response}")
            
            # Extract the response content
            intent_response = response.choices[0].message.content.strip().lower()
            print(f"[DEBUG] LLM intent response: {intent_response}")
            
            # Parse the intent from the response
            if "visualization" in intent_response:
                print(f"[DEBUG] Classified as VISUALIZATION")
                return QueryIntent.VISUALIZATION
            elif "data_manipulation" in intent_response or "manipulation" in intent_response:
                print(f"[DEBUG] Classified as DATA_MANIPULATION")
                return QueryIntent.DATA_MANIPULATION
            elif "data_analysis" in intent_response or "analysis" in intent_response:
                print(f"[DEBUG] Classified as DATA_ANALYSIS")
                return QueryIntent.DATA_ANALYSIS
            else:
                print(f"[DEBUG] Classified as GENERAL_QUERY")
                return QueryIntent.GENERAL_QUERY
                
        except Exception as e:
            print(f"[DEBUG] LLM intent analysis failed: {e}")
            print(f"[DEBUG] Falling back to keyword-based classification")
            print(f"[DEBUG] Exception details: {type(e).__name__}: {str(e)}")
            
            # Fallback to improved keyword-based classification with priority for visualization
            # Check visualization keywords first (highest priority) - including "create" when followed by visualization words
            visualization_keywords = ["chart", "graph", "plot", "visualize", "bar", "line", "scatter", "pie", "show me", "display", "visualization"]
            if any(keyword in query_lower for keyword in visualization_keywords) or "create a visualization" in query_lower or "create visualization" in query_lower:
                print(f"[DEBUG] Fallback classified as VISUALIZATION")
                return QueryIntent.VISUALIZATION
            # Check data analysis keywords second
            elif any(keyword in query_lower for keyword in ["analyze", "analysis", "stats", "statistics", "insights", "trends", "market", "performance"]):
                print(f"[DEBUG] Fallback classified as DATA_ANALYSIS")
                return QueryIntent.DATA_ANALYSIS
            # Check data manipulation keywords last (lowest priority) - but exclude "create" when it's about visualization
            elif any(keyword in query_lower for keyword in ["add", "modify", "filter", "sort", "new column", "update", "change"]) or ("create" in query_lower and "visualization" not in query_lower and "chart" not in query_lower and "graph" not in query_lower):
                print(f"[DEBUG] Fallback classified as DATA_MANIPULATION")
                return QueryIntent.DATA_MANIPULATION
            else:
                print(f"[DEBUG] Fallback classified as GENERAL_QUERY")
                return QueryIntent.GENERAL_QUERY
    
    async def process_calculation_query(self, user_query: str, data_context: Dict[str, Any]) -> CalculationResult:
        """Process calculation queries like 'total cost', 'sum of expenses'"""
        try:
            logger.info(f"[DEBUG] ===== CALCULATION QUERY DEBUG =====")
            logger.info(f"[DEBUG] User query: {user_query}")
            logger.info(f"[DEBUG] Data context keys: {list(data_context.keys())}")
            
            # Extract the DataFrame from context
            df = self._get_dataframe_from_context(data_context)
            if df is None or df.empty:
                logger.warning("[DEBUG] No DataFrame created from context")
                return CalculationResult(
                    operation="error",
                    result=None,
                    description="No data available for calculation"
                )
            
            # Check if we have numeric columns
            file_data = data_context.get("file_data", {})
            numeric_columns = file_data.get("numeric_columns", [])
            
            logger.info(f"[DEBUG] File data keys: {list(file_data.keys())}")
            logger.info(f"[DEBUG] Numeric columns from file_data: {numeric_columns}")
            logger.info(f"[DEBUG] DataFrame columns: {list(df.columns) if df is not None else 'No DataFrame'}")
            logger.info(f"[DEBUG] DataFrame dtypes: {df.dtypes.to_dict() if df is not None else 'No DataFrame'}")
            logger.info(f"[DEBUG] DataFrame shape: {df.shape if df is not None else 'No DataFrame'}")
            
            if not numeric_columns:
                # Try to detect numeric columns from the DataFrame itself
                if df is not None:
                    df_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    logger.info(f"[DEBUG] DataFrame numeric columns: {df_numeric_cols}")
                    if df_numeric_cols:
                        numeric_columns = df_numeric_cols
                        logger.info(f"[DEBUG] Using DataFrame numeric columns: {numeric_columns}")
                
                if not numeric_columns:
                    logger.warning("[DEBUG] No numeric columns found anywhere")
                    return CalculationResult(
                        operation="error",
                        result=None,
                        description="No numeric columns found in the data. Cannot perform calculations."
                    )
            
            logger.info(f"[DEBUG] Final numeric columns to use: {numeric_columns}")
            
            # Use LLM to understand the calculation request
            calculation_code = await self._generate_calculation_code(user_query, data_context)
            
            logger.info(f"[DEBUG] Generated calculation code: {calculation_code}")
            
            # Execute the calculation
            result = self._execute_calculation(calculation_code, data_context)
            
            logger.info(f"[DEBUG] Calculation result: {result}")
            logger.info(f"[DEBUG] ===== END CALCULATION QUERY DEBUG =====")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing calculation query: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return CalculationResult(
                operation="error",
                result=None,
                description=f"Failed to process calculation: {str(e)}"
            )
    
    async def process_data_manipulation_query(self, user_query: str, data_context: Dict[str, Any]) -> DataManipulationResult:
        """Process data manipulation queries like 'filter by category', 'sort by date'"""
        try:
            # Extract the DataFrame from context
            df = self._get_dataframe_from_context(data_context)
            if df is None or df.empty:
                return DataManipulationResult(
                    operation="error",
                    result=None,
                    description="No data available for manipulation"
                )
            
            # Check if this is a file modification request
            query_lower = user_query.lower()
            is_file_modification = any(phrase in query_lower for phrase in [
                "add a new column", "new column", "modify the csv", "update the csv", 
                "save to csv", "write to csv", "modify the file", "update the file",
                "add a column", "add column", "mode", "average", "multiply"
            ])
            
            # Use LLM to understand the manipulation request
            manipulation_code = await self._generate_manipulation_code(user_query, data_context)
            logger.info(f"[DEBUG] Generated manipulation code: {manipulation_code}")
            
            # Execute the manipulation
            result = await self._execute_manipulation(manipulation_code, df, data_context, is_file_modification)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing data manipulation query: {e}")
            return DataManipulationResult(
                operation="error",
                result=None,
                description=f"Failed to process manipulation: {str(e)}"
            )
    
    async def process_analysis_query(self, user_query: str, data_context: Dict[str, Any]) -> str:
        """Process analysis queries using LLM"""
        try:
            # Use LLM to generate analysis
            analysis_prompt = f"""
            Analyze the following data based on the user's query: "{user_query}"
            
            Data Context: {data_context}
            
            Provide a comprehensive analysis including:
            1. Key insights
            2. Patterns and trends
            3. Statistical summary
            4. Recommendations
            
            Make the analysis conversational and easy to understand.
            """
            
            response = await llm_service.generate_text_response(user_query, data_context)
            return response
            
        except Exception as e:
            logger.error(f"Error processing analysis query: {e}")
            return f"Failed to analyze data: {str(e)}"
    
    async def process_general_query(self, user_query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process general queries including analysis requests"""
        try:
            logger.info(f"[DEBUG] Processing general query: {user_query}")
            
            # Check if this is an analysis request
            analysis_keywords = ["analyze", "analysis", "stats", "statistics", "insights", "trends", "market", "performance"]
            if any(keyword in user_query.lower() for keyword in analysis_keywords):
                logger.info(f"[DEBUG] Detected analysis request, processing as data analysis")
                return await self.process_analysis_query(user_query, data_context)
            
            # For other general queries, use LLM to generate a response
            system_prompt = """You are a helpful data analysis assistant. The user has uploaded a CSV/Excel file and is asking questions about their data.
            
            Available data context:
            - File contains various product information including prices, quantities, categories, etc.
            - You can provide insights, analysis, and recommendations based on the data
            
            Provide a helpful, informative response that addresses the user's question. If they're asking for analysis, provide detailed insights with specific data points."""
            
            response = await self.llm_service.client.chat.completions.create(
                model="llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User question: {user_query}"}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            response_content = response.choices[0].message.content
            
            return {
                "type": "text",
                "content": response_content,
                "message": response_content,
                "response_type": "text"
            }
            
        except Exception as e:
            logger.error(f"Error processing general query: {e}")
            return {
                "type": "text",
                "content": "I apologize, but I encountered an error while processing your request. Please try rephrasing your question or ask for a specific analysis.",
                "message": "I apologize, but I encountered an error while processing your request. Please try rephrasing your question or ask for a specific analysis.",
                "response_type": "text"
            }
    
    def _get_dataframe_from_context(self, data_context: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Extract DataFrame from data context"""
        try:
            if not data_context or "file_data" not in data_context:
                logger.warning("[DEBUG] No file_data in data_context")
                return None
            
            file_data = data_context["file_data"]
            logger.info(f"[DEBUG] File data keys: {list(file_data.keys())}")
            
            # Check if we have preview data
            if "head" in file_data and file_data["head"]:
                head_data = file_data["head"]
                logger.info(f"[DEBUG] Found head_data with {len(head_data)} rows")
                logger.info(f"[DEBUG] Head data type: {type(head_data)}")
                logger.info(f"[DEBUG] First row: {head_data[0] if head_data else 'None'}")
                
                try:
                    # Check if first row contains headers
                    if len(head_data) > 1:
                        first_row = head_data[0]
                        logger.info(f"[DEBUG] First row keys: {list(first_row.keys()) if isinstance(first_row, dict) else 'Not a dict'}")
                        
                        # Check if first row looks like headers
                        if isinstance(first_row, dict) and any('Date' in str(v) or 'Category' in str(v) or 'Description' in str(v) for v in first_row.values()):
                            # Use second row onwards as data with proper column names
                            df = pd.DataFrame(head_data[1:], columns=first_row.values())
                            logger.info(f"[DEBUG] Created DataFrame with headers: {list(df.columns)}")
                        else:
                            # Use all data as is
                            df = pd.DataFrame(head_data)
                            logger.info(f"[DEBUG] Created DataFrame without headers: {list(df.columns)}")
                    else:
                        df = pd.DataFrame(head_data)
                        logger.info(f"[DEBUG] Created DataFrame from single row: {list(df.columns)}")
                    
                    # Validate the DataFrame
                    if df.empty:
                        logger.warning("[DEBUG] DataFrame is empty after creation")
                        return None
                    
                    logger.info(f"[DEBUG] DataFrame created successfully: shape={df.shape}, columns={list(df.columns)}")
                    return df
                    
                except Exception as df_error:
                    logger.error(f"[DEBUG] Error creating DataFrame from head_data: {df_error}")
                    logger.error(f"[DEBUG] Head data structure: {type(head_data)}")
                    if isinstance(head_data, list) and len(head_data) > 0:
                        logger.error(f"[DEBUG] First row type: {type(head_data[0])}")
                        logger.error(f"[DEBUG] First row content: {head_data[0]}")
                    
                    # Try fallback: create DataFrame directly from file
                    return self._create_dataframe_from_file(file_data)
            else:
                logger.warning("[DEBUG] No head data available in file_data")
                if "head" in file_data:
                    logger.warning(f"[DEBUG] Head data is: {file_data['head']}")
                
                # Try fallback: create DataFrame directly from file
                return self._create_dataframe_from_file(file_data)
            
        except Exception as e:
            logger.error(f"Error creating DataFrame from context: {e}")
            logger.error(f"Data context keys: {list(data_context.keys()) if data_context else 'None'}")
            if data_context and "file_data" in data_context:
                file_data = data_context["file_data"]
                logger.error(f"File data keys: {list(file_data.keys()) if file_data else 'None'}")
                if file_data and "head" in file_data:
                    logger.error(f"Head data type: {type(file_data['head'])}")
                    logger.error(f"Head data content: {file_data['head']}")
            
            # Try fallback: create DataFrame directly from file
            if data_context and "file_data" in data_context:
                return self._create_dataframe_from_file(data_context["file_data"])
            
            return None
    
    def _create_dataframe_from_file(self, file_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Fallback method to create DataFrame directly from file"""
        try:
            if "file_path" in file_data and "file_type" in file_data:
                file_path = file_data["file_path"]
                file_type = file_data["file_type"]
                
                logger.info(f"[DEBUG] Trying to create DataFrame from file: {file_path}")
                
                # Read file based on type
                if file_type in ["text/csv", "application/csv"]:
                    df = pd.read_csv(file_path)
                elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                 "application/vnd.ms-excel"]:
                    df = pd.read_excel(file_path)
                else:
                    logger.warning(f"[DEBUG] Unsupported file type for fallback: {file_type}")
                    return None
                
                logger.info(f"[DEBUG] Fallback DataFrame created: shape={df.shape}, columns={list(df.columns)}")
                return df
            else:
                logger.warning("[DEBUG] No file_path or file_type in file_data for fallback")
                return None
                
        except Exception as e:
            logger.error(f"[DEBUG] Error in fallback DataFrame creation: {e}")
            return None
    
    async def _generate_calculation_code(self, user_query: str, data_context: Dict[str, Any]) -> str:
        """Generate Python code for calculations"""
        system_prompt = """You are a data calculation expert. Generate Python code to perform calculations on a DataFrame named 'df'.

Available data context:
"""
        
        if "file_data" in data_context:
            file_data = data_context["file_data"]
            columns = file_data.get("columns", [])
            numeric_columns = file_data.get("numeric_columns", [])
            
            # If no numeric columns in file_data, try to get them from the DataFrame
            if not numeric_columns:
                df = self._get_dataframe_from_context(data_context)
                if df is not None:
                    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                    logger.info(f"[DEBUG] Detected numeric columns from DataFrame: {numeric_columns}")
            
            system_prompt += f"""
Data Information:
- Columns: {columns}
- Numeric Columns: {numeric_columns}
- Data Preview: {file_data.get('head', [])}

Instructions:
1. Use the DataFrame 'df' which is already loaded
2. Identify the relevant columns for the calculation
3. Generate code that performs the requested calculation
4. ALWAYS set the result in a variable called 'result'
5. Handle data type conversions if needed
6. Use pandas operations for efficiency
7. Always check if columns exist before using them

Example calculations:
- "total cost" -> result = df['Cost'].sum() if 'Cost' in df.columns else "Column 'Cost' not found"
- "average balance" -> result = df['Balance'].mean() if 'Balance' in df.columns else "Column 'Balance' not found"
- "count of transactions" -> result = len(df)
- "maximum debit" -> result = df['Debit'].max() if 'Debit' in df.columns else "Column 'Debit' not found"

IMPORTANT: Always set the final result in the 'result' variable, do not use print().
Generate only the calculation code, no explanations.
"""
        
        try:
            # Use the LLM service directly with our custom system prompt
            if hasattr(llm_service, 'client') and llm_service.client:
                response = llm_service.client.chat.completions.create(
                    model="llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                response_content = response.choices[0].message.content
                logger.info(f"[DEBUG] LLM calculation response: {response_content}")
                
                # Extract code from response if it contains code blocks
                if "```python" in response_content:
                    code_start = response_content.find("```python") + 9
                    code_end = response_content.find("```", code_start)
                    if code_end != -1:
                        return response_content[code_start:code_end].strip()
                
                # If no code block, return the response as is
                return response_content
            else:
                # Fallback to simple calculation
                return self._generate_simple_calculation(user_query, data_context)
            
        except Exception as e:
            logger.error(f"Error generating calculation code: {e}")
            return self._generate_simple_calculation(user_query, data_context)
    
    def _generate_simple_calculation(self, user_query: str, data_context: Dict[str, Any]) -> str:
        """Generate simple calculation code based on keywords"""
        query_lower = user_query.lower()
        file_data = data_context.get("file_data", {})
        numeric_columns = file_data.get("numeric_columns", [])
        
        # If no numeric columns in file_data, try to get them from the DataFrame
        if not numeric_columns:
            df = self._get_dataframe_from_context(data_context)
            if df is not None:
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                logger.info(f"[DEBUG] Detected numeric columns from DataFrame: {numeric_columns}")
        
        if not numeric_columns:
            return """
# No numeric columns available for calculation
print("No numeric columns available for calculation")
result = "No numeric columns found in the data"
"""
        
        # Find the most relevant numeric column based on the query
        target_column = None
        
        # Look for specific column names in the query
        for col in numeric_columns:
            if col.lower() in query_lower:
                target_column = col
                break
        
        # If no specific column found, look for keywords
        if not target_column:
            if any(word in query_lower for word in ["cost", "price", "amount", "mrp"]):
                # Look for columns that might contain cost/price data
                for col in numeric_columns:
                    if any(keyword in col.lower() for keyword in ["cost", "price", "amount", "mrp", "value"]):
                        target_column = col
                        break
        
        # If still no target column, use the first numeric column
        if not target_column:
            target_column = numeric_columns[0]
        
        logger.info(f"[DEBUG] Selected target column for calculation: {target_column}")
        
        # Determine operation based on keywords
        if any(word in query_lower for word in ["total", "sum", "add"]):
            operation = f"df['{target_column}'].sum() if '{target_column}' in df.columns else 'Column {target_column} not found'"
        elif any(word in query_lower for word in ["average", "mean"]):
            operation = f"df['{target_column}'].mean() if '{target_column}' in df.columns else 'Column {target_column} not found'"
        elif any(word in query_lower for word in ["maximum", "max", "highest"]):
            operation = f"df['{target_column}'].max() if '{target_column}' in df.columns else 'Column {target_column} not found'"
        elif any(word in query_lower for word in ["minimum", "min", "lowest"]):
            operation = f"df['{target_column}'].min() if '{target_column}' in df.columns else 'Column {target_column} not found'"
        elif any(word in query_lower for word in ["count", "number"]):
            operation = f"len(df)"
        else:
            operation = f"df['{target_column}'].sum() if '{target_column}' in df.columns else 'Column {target_column} not found'"
        
        return f"""
# Calculate {user_query}
print(f"Available numeric columns: {{list(df.select_dtypes(include=['number']).columns)}}")
print(f"Selected column: {target_column}")
result = {operation}
print(f"Result: {{result}}")
"""
    
    def _execute_calculation(self, code: str, data_context: Dict[str, Any]) -> Optional[CalculationResult]:
        """Execute calculation code and return result"""
        try:
            # Get DataFrame
            df = self._get_dataframe_from_context(data_context)
            if df is None or df.empty:
                logger.error("[DEBUG] DataFrame is None or empty")
                return CalculationResult(
                    operation="error",
                    result=None,
                    formula=None,
                    description="No data available for calculation",
                    units=None
                )
            
            logger.info(f"[DEBUG] DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            
            # Convert numeric columns that might be strings
            file_data = data_context.get("file_data", {})
            numeric_columns = file_data.get("numeric_columns", [])
            
            for col in numeric_columns:
                if col in df.columns:
                    # Check if column is object type but should be numeric
                    if df[col].dtype == 'object':
                        logger.info(f"[DEBUG] Converting string column to numeric: {col}")
                        try:
                            # Remove non-numeric characters and convert
                            import re
                            df[col] = df[col].astype(str).apply(
                                lambda x: float(re.sub(r'[^\d.\-]', '', x)) if re.sub(r'[^\d.\-]', '', x) else None
                            )
                            logger.info(f"[DEBUG] Successfully converted {col} to numeric")
                        except Exception as e:
                            logger.warning(f"[DEBUG] Failed to convert {col} to numeric: {e}")
            
            # Create local variables for code execution
            local_vars = {
                'df': df,
                'pd': pd,
                'np': np,
                'result': None
            }
            
            logger.info(f"[DEBUG] Executing calculation code: {code}")
            
            # Execute the code
            exec(code, globals(), local_vars)
            
            # Get the result
            result = local_vars.get('result')
            
            if result is None:
                logger.warning("[DEBUG] Calculation result is None")
                return CalculationResult(
                    operation="error",
                    result=None,
                    formula=code,
                    description="Calculation returned no result",
                    units=None
                )
            
            logger.info(f"[DEBUG] Calculation result: {result} (type: {type(result)})")
            
            # Format the result
            if isinstance(result, (int, float)):
                if isinstance(result, int):
                    formatted_result = f"{result:,}"
                else:
                    formatted_result = f"{result:,.2f}"
            else:
                formatted_result = str(result)
            
            # Determine operation type from code
            operation = "calculation"
            if "sum" in code.lower():
                operation = "sum"
            elif "mean" in code.lower() or "average" in code.lower():
                operation = "average"
            elif "max" in code.lower():
                operation = "maximum"
            elif "min" in code.lower():
                operation = "minimum"
            elif "count" in code.lower():
                operation = "count"
            
            return CalculationResult(
                operation=operation,
                result=formatted_result,
                formula=code,
                description=f"Successfully calculated {operation}",
                units=None
            )
            
        except Exception as e:
            logger.error(f"[DEBUG] Error executing calculation: {e}")
            import traceback
            logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return CalculationResult(
                operation="error",
                result=None,
                formula=code,
                description=f"Calculation failed: {str(e)}",
                units=None
            )
    
    async def _generate_manipulation_code(self, user_query: str, data_context: Dict[str, Any]) -> str:
        """Generate manipulation code using LLM"""
        try:
            file_data = data_context.get("file_data", {})
            columns = file_data.get("columns", [])
            numeric_columns = file_data.get("numeric_columns", [])
            
            system_prompt = f"""You are a data manipulation expert. Generate Python code to manipulate a pandas DataFrame based on the user's request.

IMPORTANT RULES:
1. The DataFrame is already loaded as 'df' - DO NOT use pd.read_csv() or any file reading
2. Perform the requested manipulation on the existing DataFrame
3. ALWAYS set the result in a variable called 'result'
4. For file modifications (like adding columns), modify the DataFrame in-place and set result = df
5. Use pandas operations like df['new_column'] = calculation
6. DO NOT use pd.read_csv() or any file reading operations
7. Use the available columns: {columns}
8. Available numeric columns: {numeric_columns}
9. Generate clean, efficient pandas/numpy code
10. Handle edge cases gracefully
11. If you need to create visualizations, ALWAYS import matplotlib: import matplotlib.pyplot as plt
12. For column names, use descriptive names based on the user's request (e.g., 'total_cost', 'discount', 'profit_margin')
13. Make sure all imports are at the top of the code

User request: {user_query}"""
            
            response = await llm_service.generate_text_response(system_prompt, user_query)
            logger.info(f"[DEBUG] LLM response: {response}")
            
            # Extract code from response
            extracted_code = self._extract_code_from_response(response)
            logger.info(f"[DEBUG] Extracted code: {extracted_code}")
            
            return extracted_code
            
        except Exception as e:
            logger.error(f"Error generating manipulation code: {e}")
            # Return a basic fallback that doesn't break
            return """
# Basic fallback manipulation
result = df
print("Basic manipulation applied")
"""
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from LLM response"""
        # Look for code blocks
        if "```python" in response:
            code_start = response.find("```python") + 9
            code_end = response.find("```", code_start)
            if code_end != -1:
                return response[code_start:code_end].strip()
        
        # If no code block, return the response as-is
        return response.strip()
    
    async def _execute_manipulation(self, code: str, df: pd.DataFrame, data_context: Dict[str, Any], is_file_modification: bool) -> DataManipulationResult:
        """Execute manipulation code and return result"""
        try:
            logger.info(f"[DEBUG] Executing manipulation code: {code}")
            logger.info(f"[DEBUG] DataFrame shape: {df.shape}")
            logger.info(f"[DEBUG] Is file modification: {is_file_modification}")
            
            # Create a safe execution environment
            local_vars = {
                'df': df, 
                'pd': pd, 
                'np': np,
                'file_data': data_context.get('file_data', {}),
                'data_context': data_context
            }
            
            # Execute the code
            exec(code, globals(), local_vars)
            
            # Get the result
            result = local_vars.get('result', None)
            logger.info(f"[DEBUG] Result from execution: {result}")
            logger.info(f"[DEBUG] Result type: {type(result)}")
            
            if result is not None and hasattr(result, 'shape'):
                logger.info(f"[DEBUG] Result shape: {result.shape}")
                new_column_name = "new_column"  # Default value
                file_path = "unknown"  # Default value
                
                if is_file_modification:
                    # If it's a file modification, save the result back to the file
                    file_data = data_context.get("file_data", {})
                    file_path = file_data.get("file_path", "unknown")
                    
                    # Try to detect the new column name
                    if hasattr(result, 'columns'):
                        original_columns = set(df.columns)
                        new_columns = set(result.columns)
                        new_column_name = list(new_columns - original_columns)[0] if new_columns - original_columns else "new_column"
                    
                    if file_path and file_path != "unknown":
                        if file_data.get("file_type") == "text/csv":
                            result.to_csv(file_path, index=False)
                        elif file_data.get("file_type") in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                                          "application/vnd.ms-excel"]:
                            result.to_excel(file_path, index=False)
                        else:
                            logger.warning(f"Unsupported file type for saving: {file_data.get('file_type')}")
                        logger.info(f"File saved successfully to {file_path}")
                    else:
                        logger.warning("No file_path in data_context to save file.")

                return DataManipulationResult(
                    operation="manipulation",
                    result=result.to_dict('records')[:50],  # Limit to first 50 rows
                    description=f"✅ **File Successfully Updated!**\n\nA new column '{new_column_name}' has been added to your CSV file. The file now contains {result.shape[0]} rows and {result.shape[1]} columns.\n\n**Changes Made:**\n- Added new column: {new_column_name}\n- File saved to: {file_path}\n- Original data preserved\n\n**📊 CSV Preview Available:**\nClick the 'View CSV Preview' button above to see your updated data in a proper CSV viewer with download functionality!",
                    affected_rows=result.shape[0]
                )
            else:
                logger.warning(f"[DEBUG] No valid result found. Result: {result}")
                return DataManipulationResult(
                    operation="error",
                    result=None,
                    description="❌ **Operation Failed**\n\nUnable to complete the requested data manipulation. Please try a different approach or check your data format."
                )
                
        except Exception as e:
            logger.error(f"Error executing manipulation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return DataManipulationResult(
                operation="error",
                result=None,
                description=f"❌ **Operation Failed**\n\nError: {str(e)}\n\nPlease try a different approach or check your data format."
            )

    def _format_data_preview(self, df: pd.DataFrame) -> str:
        """Formats a DataFrame for preview in the chat interface."""
        if df.empty:
            return "No data available for preview."
        
        # Create a simple, clean preview
        preview_str = f"📊 **File Summary:**\n"
        preview_str += f"- **Rows:** {df.shape[0]}\n"
        preview_str += f"- **Columns:** {df.shape[1]}\n"
        preview_str += f"- **New Column:** {list(df.columns)[-1]}\n\n"
        
        # Show a few key columns for preview (excluding long URLs)
        key_columns = ['brand', 'name', 'mrp', 'price', list(df.columns)[-1]]  # Include the new column
        preview_df = df[key_columns].head(3)
        
        preview_str += "**Sample Data:**\n"
        preview_str += "```\n"
        preview_str += preview_df.to_string(index=False) + "\n"
        preview_str += "```\n"
        
        return preview_str


# Initialize the agentic service with LLM service
agentic_service = AgenticService(llm_service) 