from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from app.services.llm_service import llm_service
from app.services.code_executor import code_executor
from app.models.schemas import CodeExecutionRequest


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
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("execute_code", self._execute_code)
        workflow.add_node("format_response", self._format_response)
        
        # Define edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "generate_code")
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_edge("execute_code", "format_response")
        workflow.add_edge("format_response", END)
        
        compiled_workflow = workflow.compile()
        print("[DEBUG] LangGraph workflow created successfully")
        return compiled_workflow
    
    async def _analyze_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _analyze_query")
        # Write to a file in /tmp to verify execution
        with open("/tmp/langgraph_node_test.txt", "a") as f:
            f.write("_analyze_query was executed!\n")
        """Analyze user query to determine if chart generation is needed"""
        user_query = state.get("user_query", "")
        
        # Simple keyword-based analysis
        chart_keywords = [
            "chart", "graph", "plot", "visualize", "show", "display",
            "bar", "line", "scatter", "pie", "histogram", "heatmap",
            "trend", "comparison", "distribution", "correlation"
        ]
        
        needs_chart = any(keyword.lower() in user_query.lower() for keyword in chart_keywords)
        
        print(f"[DEBUG] User query: {user_query}")
        print(f"[DEBUG] Needs chart: {needs_chart}")
        print(f"[DEBUG] Detected keywords: {[kw for kw in chart_keywords if kw.lower() in user_query.lower()]}")
        
        state["needs_chart"] = needs_chart
        state["query_analysis"] = {
            "original_query": user_query,
            "chart_required": needs_chart,
            "detected_keywords": [kw for kw in chart_keywords if kw.lower() in user_query.lower()]
        }
        # If not a chart query, get a general LLM response
        if not needs_chart and user_query.strip():
            from app.services.llm_service import llm_service
            try:
                llm_result = await llm_service.generate_chart_code(user_query, state.get("data_context", {}))
                # Use the raw LLM response as text_response
                state["text_response"] = llm_result.get("raw_response", "Hello! How can I help you with your data?")
            except Exception as e:
                state["text_response"] = f"Sorry, I couldn't process your request: {e}"
        
        return state
    
    async def _generate_code(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _generate_code")
        """Generate visualization code using LLM"""
        print(f"[DEBUG] _generate_code called with needs_chart: {state.get('needs_chart', False)}")
        user_query = state.get("user_query", "")
        data_context = state.get("data_context", {})
        
        # Always use LLM for chart generation - it's more intelligent and can analyze the data
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
            # If LLM fails, provide a helpful error message
            state["generated_code"] = ""
            state["chart_type"] = "unknown"
            state["llm_response"] = f"I encountered an error while generating the chart: {str(e)}. Please try rephrasing your request."
            state["clarification_needed"] = True
            return state
    
    async def _execute_code(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _execute_code")
        """Execute the generated code"""
        print(f"[DEBUG] _execute_code called with needs_chart: {state.get('needs_chart', False)}")
        
        if not state.get("needs_chart", False):
            print(f"[DEBUG] No chart needed, skipping execution")
            return state
        
        generated_code = state.get("generated_code", "")
        print(f"[DEBUG] Generated code length: {len(generated_code)}")
        print(f"[DEBUG] Generated code: {generated_code[:200]}...")
        
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
            timeout=30
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
    
    async def _format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered _format_response")
        """Format the final response"""
        if state.get("needs_chart", False):
            # If clarification is needed, return a user message instead of chart
            if state.get("clarification_needed"):
                state["final_response"] = {
                    "type": "clarification",
                    "content": state.get("llm_response", "Please specify which columns and chart type you want."),
                    "message": state.get("llm_response", "Please specify which columns and chart type you want.")
                }
                return state
            # Format chart response
            execution_result = state.get("execution_result", {})
            print(f"[DEBUG] Execution result type: {type(execution_result)}")
            
            # Handle both object and dictionary access
            if isinstance(execution_result, dict):
                # It's a dictionary
                success = execution_result.get('success', False)
                chart_data = execution_result.get('chart_data')
                error = execution_result.get('error')
            else:
                # It's an object (CodeExecutionResponse)
                success = execution_result.success
                chart_data = execution_result.chart_data
                error = execution_result.error
            
            print(f"[DEBUG] Execution result success: {success}")
            print(f"[DEBUG] Execution result chart_data: {chart_data}")
            
            if success and chart_data:
                # Only return success if chart_data is present
                print(f"[DEBUG] Chart data: {chart_data}")
                print(f"[DEBUG] Chart data type: {type(chart_data)}")
                
                # Use the LLM response as content if available, otherwise use a default message
                content = state.get("llm_response", "Chart generated successfully")
                if not content or content == "TEMPLATE":
                    content = "Chart generated successfully"
                
                state["final_response"] = {
                    "type": "chart",
                    "content": content,
                    "chart_data": chart_data,
                    "chart_type": state.get("chart_type", "unknown"),
                    "code": state.get("generated_code", ""),
                    "message": content
                }
                print(f"[DEBUG] Final response: {state['final_response']}")
            else:
                # Check if no code was generated (e.g., when no data context)
                if not state.get("generated_code", "").strip():
                    # No code was generated, likely due to no data context
                    llm_response = state.get("llm_response", "")
                    if llm_response and ("upload" in llm_response.lower() or "data" in llm_response.lower()):
                        # This is a helpful message asking for data upload
                        state["final_response"] = {
                            "type": "message",
                            "content": llm_response,
                            "message": llm_response,
                            "code": ""
                        }
                    else:
                        error_msg = error or 'No code generated'
                        state["final_response"] = {
                            "type": "error",
                            "content": f"Failed to generate chart: {error_msg}",
                            "message": f"Failed to generate chart: {error_msg}",
                            "code": state.get("generated_code", "")
                        }
                else:
                    # Code was generated but execution failed
                    error_msg = error or 'No chart image was generated. Please check your data and prompt.'
                    state["final_response"] = {
                        "type": "error",
                        "content": f"Failed to generate chart: {error_msg}",
                        "message": f"Failed to generate chart: {error_msg}",
                        "code": state.get("generated_code", "")
                    }
        else:
            # Format text response
            state["final_response"] = {
                "type": "text",
                "content": state.get("text_response", "No response generated"),
                "message": state.get("text_response", "No response generated")
            }
        
        return state
    
    async def process_query(self, user_query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        print("[DEBUG] Entered process_query")
        with open("/tmp/langgraph_process_query_test.txt", "a") as f:
            f.write("process_query was called!\n")
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
