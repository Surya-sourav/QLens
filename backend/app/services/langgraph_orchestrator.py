from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from app.services.llm_service import llm_service
from app.services.code_executor import code_executor
from app.services.agentic_service import agentic_service
from app.models.schemas import CodeExecutionRequest, QueryIntent, ResponseType


class LangGraphOrchestrator:
    def __init__(self):
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        print("[DEBUG] Creating LangGraph workflow")
        
        # Define the state structure
        workflow = StateGraph(Dict[str, Any])
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("execute_code", self._execute_code)
        workflow.add_node("process_calculation", self._process_calculation)
        workflow.add_node("process_manipulation", self._process_manipulation)
        workflow.add_node("process_analysis", self._process_analysis)
        workflow.add_node("process_general", self._process_general)
        workflow.add_node("format_response", self._format_response)
        
        # Define edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "route_query")
        workflow.add_conditional_edges(
            "route_query",
            self._route_decision,
            {
                "visualization": "generate_code",
                "calculation": "process_calculation",
                "manipulation": "process_manipulation",
                "analysis": "process_analysis",
                "general": "process_general"
            }
        )
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_edge("execute_code", "format_response")
        workflow.add_edge("process_calculation", "format_response")
        workflow.add_edge("process_manipulation", "format_response")
        workflow.add_edge("process_analysis", "format_response")
        workflow.add_edge("process_general", "format_response")
        workflow.add_edge("format_response", END)
        
        compiled_workflow = workflow.compile()
        print("[DEBUG] LangGraph workflow created successfully")
        return compiled_workflow
    
    async def _analyze_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _analyze_query")
        """Analyze user query to determine intent and type"""
        user_query = state.get("user_query", "")
        
        # Use agentic service to analyze query intent
        query_intent = await agentic_service.analyze_query_intent(user_query, state.get("data_context", {}))
        
        print(f"[DEBUG] User query: {user_query}")
        print(f"[DEBUG] Query intent: {query_intent}")
        
        state["query_intent"] = query_intent
        state["query_analysis"] = {
            "original_query": user_query,
            "intent": query_intent,
            "needs_chart": query_intent == QueryIntent.VISUALIZATION
        }
        
        return state
    
    async def _route_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route query to appropriate handler"""
        print("[DEBUG] Entered _route_query")
        query_intent = state.get("query_intent", QueryIntent.GENERAL_QUERY)
        
        # Handle generic greetings
        user_query = state.get("user_query", "").strip().lower()
        generic_greetings = ["hi", "hello", "hey", "how are you", "good morning", "good afternoon", "good evening"]
        
        if user_query in generic_greetings:
            state["response_type"] = ResponseType.TEXT
            state["text_response"] = (
                "Hello! I'm your data assistant. You can upload a CSV or Excel file and ask me questions about your data, "
                "request visualizations, perform calculations, or get insights. How can I help you with your data today?"
            )
            return state
        
        # Route based on intent
        if query_intent == QueryIntent.VISUALIZATION:
            state["response_type"] = ResponseType.CHART
        elif query_intent == QueryIntent.CALCULATION:
            state["response_type"] = ResponseType.CALCULATION
        elif query_intent == QueryIntent.DATA_MANIPULATION:
            state["response_type"] = ResponseType.DATA_MANIPULATION
        elif query_intent == QueryIntent.DATA_ANALYSIS:
            state["response_type"] = ResponseType.ANALYSIS
        else:
            state["response_type"] = ResponseType.TEXT
        
        return state
    
    def _route_decision(self, state: Dict[str, Any]) -> str:
        """Make routing decision based on query intent"""
        query_intent = state.get("query_intent", QueryIntent.GENERAL_QUERY)
        response_type = state.get("response_type", ResponseType.TEXT)
        
        if response_type == ResponseType.TEXT:
            return "general"
        elif query_intent == QueryIntent.VISUALIZATION:
            return "visualization"
        elif query_intent == QueryIntent.CALCULATION:
            return "calculation"
        elif query_intent == QueryIntent.DATA_MANIPULATION:
            return "manipulation"
        elif query_intent == QueryIntent.DATA_ANALYSIS:
            return "analysis"
        else:
            return "general"
    
    async def _generate_code(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _generate_code")
        """Generate visualization code using LLM"""
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        print("[DEBUG] Using LLM for chart code generation")
        try:
            llm_result = await llm_service.generate_chart_code(
                user_query,
                data_context
            )
            print(f"[DEBUG] LLM result: {llm_result}")
            state["generated_code"] = llm_result.get("code", "")
            state["chart_type"] = llm_result.get("chart_type", "unknown")
            state["llm_response"] = llm_result.get("raw_response", "")
            state["clarification_needed"] = False
            return state
        except Exception as e:
            print(f"[DEBUG] LLM generation failed: {e}")
            state["generated_code"] = ""
            state["chart_type"] = "unknown"
            state["llm_response"] = f"I encountered an error while generating the chart: {str(e)}. Please try rephrasing your request."
            state["clarification_needed"] = True
            return state
    
    async def _execute_code(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _execute_code")
        """Execute the generated code"""
        generated_code = state.get("generated_code", "")
        print(f"[DEBUG] Generated code length: {len(generated_code)}")
        
        if not generated_code:
            print(f"[DEBUG] No code generated, returning error")
            state["execution_result"] = {
                "success": False,
                "error": "No code generated"
            }
            return state
        
        # Execute the code
        print(f"[DEBUG] Creating CodeExecutionRequest")
        execution_request = CodeExecutionRequest(
            code=generated_code,
            data_context=state.get("data_context", {}),
            timeout=30,
            execution_type="chart"
        )
        
        print(f"[DEBUG] Calling code_executor.execute_code")
        execution_result = await code_executor.execute_code(execution_request)
        print(f"[DEBUG] code_executor.execute_code returned: {execution_result}")
        
        # Convert CodeExecutionResponse to dict for JSON serialization
        if hasattr(execution_result, '__dict__'):
            state["execution_result"] = {
                'success': execution_result.success,
                'error': execution_result.error,
                'chart_data': execution_result.chart_data,
                'execution_time': execution_result.execution_time
            }
        else:
            state["execution_result"] = execution_result
        
        print(f"[DEBUG] Final execution_result: {state['execution_result']}")
        return state
    
    async def _process_calculation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process calculation queries"""
        print("[DEBUG] Entered _process_calculation")
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        try:
            calculation_result = await agentic_service.process_calculation_query(user_query, data_context)
            state["calculation_result"] = calculation_result
            print(f"[DEBUG] Calculation result: {calculation_result}")
        except Exception as e:
            print(f"[DEBUG] Calculation processing failed: {e}")
            state["calculation_result"] = {
                "operation": "error",
                "result": None,
                "description": f"Failed to process calculation: {str(e)}"
            }
        
        return state
    
    async def _process_manipulation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process data manipulation queries"""
        print("[DEBUG] Entered _process_manipulation")
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        try:
            manipulation_result = await agentic_service.process_data_manipulation_query(user_query, data_context)
            state["manipulation_result"] = manipulation_result
            print(f"[DEBUG] Manipulation result: {manipulation_result}")
        except Exception as e:
            print(f"[DEBUG] Manipulation processing failed: {e}")
            state["manipulation_result"] = {
                "operation": "error",
                "result": None,
                "description": f"Failed to process manipulation: {str(e)}"
            }
        
        return state
    
    async def _process_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process analysis queries"""
        print("[DEBUG] Entered _process_analysis")
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        try:
            analysis_result = await agentic_service.process_analysis_query(user_query, data_context)
            state["analysis_result"] = analysis_result
            print(f"[DEBUG] Analysis result: {analysis_result}")
        except Exception as e:
            print(f"[DEBUG] Analysis processing failed: {e}")
            state["analysis_result"] = f"Failed to analyze data: {str(e)}"
        
        return state
    
    async def _process_general(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process general queries including analysis requests"""
        print("[DEBUG] Entered _process_general")
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        try:
            # Use agentic service to process general queries
            result = await agentic_service.process_general_query(user_query, data_context)
            
            state["general_response"] = result
            state["response_type"] = ResponseType.TEXT
            state["text_response"] = result.get("message", "No response generated")
            
            return state
        except Exception as e:
            print(f"[DEBUG] Error processing general query: {e}")
            state["general_response"] = {
                "type": "text",
                "content": f"I encountered an error while processing your request: {str(e)}",
                "message": f"I encountered an error while processing your request: {str(e)}",
                "response_type": "text"
            }
            state["response_type"] = ResponseType.TEXT
            state["text_response"] = f"I encountered an error while processing your request: {str(e)}"
            return state
    
    async def _format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _format_response")
        """Format the final response based on response type"""
        response_type = state.get("response_type", ResponseType.TEXT)
        
        if response_type == ResponseType.CHART:
            # Format chart response
            if state.get("clarification_needed"):
                state["final_response"] = {
                    "type": "clarification",
                    "content": state.get("llm_response", "Please specify which columns and chart type you want."),
                    "message": state.get("llm_response", "Please specify which columns and chart type you want."),
                    "response_type": ResponseType.TEXT
                }
                return state
            
            execution_result = state.get("execution_result", {})
            
            if isinstance(execution_result, dict):
                success = execution_result.get('success', False)
                chart_data = execution_result.get('chart_data')
                error = execution_result.get('error')
            else:
                success = execution_result.success
                chart_data = execution_result.chart_data
                error = execution_result.error
            
            if success and chart_data:
                content = state.get("llm_response", "Chart generated successfully")
                if not content or content == "TEMPLATE":
                    content = "Chart generated successfully"
                
                state["final_response"] = {
                    "type": "chart",
                    "content": content,
                    "chart_data": chart_data,
                    "chart_type": state.get("chart_type", "unknown"),
                    "code": state.get("generated_code", ""),
                    "message": content,
                    "response_type": ResponseType.CHART
                }
            else:
                error_msg = error or 'No chart image was generated. Please check your data and prompt.'
                state["final_response"] = {
                    "type": "error",
                    "content": f"Failed to generate chart: {error_msg}",
                    "message": f"Failed to generate chart: {error_msg}",
                    "code": state.get("generated_code", ""),
                    "response_type": ResponseType.TEXT
                }
        
        elif response_type == ResponseType.CALCULATION:
            # Format calculation response
            calculation_result = state.get("calculation_result", {})
            if calculation_result and calculation_result.operation != "error":
                result = calculation_result.result
                description = calculation_result.description
                units = calculation_result.units
                
                content = f"**Calculation Result:** {result}"
                if units:
                    content += f" {units}"
                content += f"\n\n{description}"
                
                state["final_response"] = {
                    "type": "calculation",
                    "content": content,
                    "message": content,
                    "calculation_result": {
                        "operation": calculation_result.operation,
                        "result": calculation_result.result,
                        "description": calculation_result.description,
                        "units": calculation_result.units
                    },
                    "response_type": ResponseType.CALCULATION
                }
            else:
                error_msg = calculation_result.description if calculation_result else "Failed to perform calculation"
                state["final_response"] = {
                    "type": "error",
                    "content": error_msg,
                    "message": error_msg,
                    "response_type": ResponseType.TEXT
                }
        
        elif response_type == ResponseType.DATA_MANIPULATION:
            # Format manipulation response
            manipulation_result = state.get("manipulation_result", {})
            if manipulation_result and manipulation_result.operation != "error":
                description = manipulation_result.description
                affected_rows = manipulation_result.affected_rows
                result_data = manipulation_result.result
                
                content = f"**Data Manipulation Result:**\n{description}\n\n"
                if result_data:
                    content += f"Showing first {len(result_data)} rows of results:\n"
                    # Format the data as a simple table
                    if result_data and len(result_data) > 0:
                        columns = list(result_data[0].keys())
                        content += "| " + " | ".join(columns) + " |\n"
                        content += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                        for row in result_data[:10]:  # Show first 10 rows
                            content += "| " + " | ".join(str(row.get(col, "")) for col in columns) + " |\n"
                
                state["final_response"] = {
                    "type": "manipulation",
                    "content": content,
                    "message": content,
                    "manipulation_result": {
                        "operation": manipulation_result.operation,
                        "result": manipulation_result.result,
                        "description": manipulation_result.description,
                        "affected_rows": manipulation_result.affected_rows,
                        "summary": manipulation_result.summary
                    },
                    "response_type": ResponseType.DATA_MANIPULATION
                }
            else:
                error_msg = manipulation_result.description if manipulation_result else "Failed to perform data manipulation"
                state["final_response"] = {
                    "type": "error",
                    "content": error_msg,
                    "message": error_msg,
                    "response_type": ResponseType.TEXT
                }
        
        elif response_type == ResponseType.ANALYSIS:
            # Format analysis response
            analysis_result = state.get("analysis_result", "")
            if analysis_result:
                state["final_response"] = {
                    "type": "analysis",
                    "content": analysis_result,
                    "message": analysis_result,
                    "response_type": ResponseType.ANALYSIS
                }
            else:
                state["final_response"] = {
                    "type": "error",
                    "content": "Failed to analyze data",
                    "message": "Failed to analyze data",
                    "response_type": ResponseType.TEXT
                }
        
        else:
            # Format text response
            text_response = state.get("text_response", "No response generated")
            state["final_response"] = {
                "type": "text",
                "content": text_response,
                "message": text_response,
                "response_type": ResponseType.TEXT
            }
        
        # Add query intent and analysis to the final response
        state["final_response"]["query_intent"] = state.get("query_intent")
        state["final_response"]["query_analysis"] = state.get("query_analysis")
        
        return state
    
    async def process_query(self, user_query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered process_query")
        """Process a user query through the workflow"""
        
        # Create initial state
        initial_state = {
            "user_query": user_query,
            "data_context": data_context
        }
        
        try:
            # Run the workflow
            try:
                print(f"[DEBUG] Starting workflow execution")
                result = await self.workflow.ainvoke(initial_state)
                print(f"[DEBUG] Workflow execution completed")
                print(f"[DEBUG] Workflow result: {result}")
                return result
            except Exception as e:
                print(f"[DEBUG] Workflow error: {e}")
                import traceback
                print(f"[DEBUG] Workflow error traceback: {traceback.format_exc()}")
                return {
                    "error": f"Workflow execution failed: {str(e)}",
                    "response": "I encountered an error while processing your request. Please try again."
                }
        except Exception as e:
            print(f"[DEBUG] process_query error: {e}")
            return {
                "error": f"Failed to process query: {str(e)}",
                "response": "I encountered an error while processing your request. Please try again."
            }


orchestrator = LangGraphOrchestrator()
print("[DEBUG] LangGraphOrchestrator instantiated successfully")
