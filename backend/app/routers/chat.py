from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import uuid
from datetime import datetime
from app.models.schemas import ChatRequest, ChatResponse, MessageType, ChatMessage
from app.services.langgraph_orchestrator import orchestrator
from app.models.database import get_db, ChatSession, ChatMessage as ChatMessageModel, FileUpload as FileUploadORM
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a chat message and get response"""
    
    logger.info(f"Chat message request: {request.message[:100]}...")
    
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        
        if not session:
            session = ChatSession(
                id=str(uuid.uuid4()),
                session_id=session_id,
                data_sources=request.data_sources or [],
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            db.add(session)
            db.commit()
            logger.info(f"Created new chat session: {session_id}")
        
        # Save user message
        user_message = ChatMessageModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=request.message,
            message_type=MessageType.USER,
            timestamp=datetime.now()
        )
        db.add(user_message)
        db.commit()
        logger.info(f"Saved user message: {user_message.id}")

        # Detect generic/greeting prompts and respond as an assistant, not with code
        generic_greetings = ["hi", "hello", "hey", "how are you", "good morning", "good afternoon", "good evening"]
        if request.message.strip().lower() in generic_greetings:
            response_content = (
                "Hello! I'm your data assistant. You can upload a CSV or Excel file and ask me questions about your data, request visualizations, or get insights. "
                "How can I help you with your data today?"
            )
            assistant_message = ChatMessageModel(
                id=str(uuid.uuid4()),
                session_id=session_id,
                content=response_content,
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(),
            )
            db.add(assistant_message)
            session.last_activity = datetime.now()
            db.commit()
            return {
                "message_id": assistant_message.id,
                "content": response_content,
                "message_type": MessageType.ASSISTANT,
                "timestamp": assistant_message.timestamp,
                "chartData": None,
                "chartType": None,
                "chartCode": None,
                "metadata": None
            }

        # Prepare data context based on data sources
        data_context = await _prepare_data_context(request.data_sources or [], db)
        logger.info(f"Data context prepared with {len(data_context)} sources")
        
        # DEBUG LOGGING: Print the entire prepared data_context
        logger.info(f"[DEBUG] Prepared data_context: {data_context}")
        
        # Process query through orchestrator
        logger.info("Processing query through orchestrator...")
        result = await orchestrator.process_query(request.message, data_context)
        logger.info(f"Orchestrator result: {result}")
        
        final_response = result.get("final_response", {})
        logger.info(f"Final response: {final_response}")
        
        # Extract response content
        if isinstance(final_response, dict):
            response_content = final_response.get("content", "") or final_response.get("message", "")
        else:
            response_content = str(final_response)
        
        # Ensure we have a response
        if not response_content:
            response_content = "I understand your query. Let me help you analyze your data. Could you please provide more specific details about what you'd like to know?"
        
        logger.info(f"Response content: {response_content}")
        logger.info(f"Chart data: {final_response.get('chart_data')}")
        logger.info(f"Chart type: {final_response.get('chart_type')}")
        
        # Save assistant response
        assistant_message = ChatMessageModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=response_content,
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(),
            chart_data=final_response.get('chart_data'),
            chart_type=final_response.get('chart_type'),
            chart_code=final_response.get('code', '')
        )
        db.add(assistant_message)
        db.commit()
        logger.info(f"Saved assistant message: {assistant_message.id}")
        
        # Update session activity
        session.last_activity = datetime.now()
        db.commit()
        
        return {
            "message_id": assistant_message.id,
            "content": response_content,
            "message_type": MessageType.ASSISTANT,
            "timestamp": assistant_message.timestamp,
            "chartData": final_response.get('chart_data'),
            "chartType": final_response.get('chart_type'),
            "chartCode": final_response.get('code', ''),
            "metadata": final_response.get('metadata')
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(db: Session = Depends(get_db)):
    """List all active chat sessions"""
    try:
        sessions = db.query(ChatSession).filter(ChatSession.is_active == True).all()
        return [
            {
                "id": session.id,
                "session_id": session.session_id,
                "data_sources": session.data_sources,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "is_active": session.is_active
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/session/{session_id}/messages", response_model=List[ChatResponse])
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session"""
    try:
        messages = db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id).order_by(ChatMessageModel.timestamp).all()
        return [
            {
                "message_id": msg.id,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp,
                "chartData": msg.chart_data,
                "chartType": msg.chart_type,
                "chartCode": msg.chart_code,
                "metadata": msg.message_metadata
            }
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session messages: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.is_active = False
            db.commit()
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# WebSocket endpoint for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get database session for data context preparation
            from app.models.database import get_db
            db = next(get_db())
            
            try:
                # Process message through orchestrator
                data_context = await _prepare_data_context(message_data.get("data_sources", []), db)
                result = await orchestrator.process_query(message_data["message"], data_context)
                final_response = result.get("final_response", {})
                
                # Send response back
                response = {
                    "type": "response",
                    "content": final_response.get("content", ""),
                    "chart_data": final_response.get("chart_data"),
                    "chart_type": final_response.get("chart_type"),
                    "code": final_response.get("code")
                }
                
                await manager.send_personal_message(json.dumps(response), websocket)
            finally:
                db.close()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _prepare_data_context(data_sources: List[str], db: Session) -> Dict[str, Any]:
    """Prepare data context for LLM processing"""
    context = {}
    
    if not db:
        return context

    found_file = False
    # Add file data sources
    for source_id in data_sources:
        logger.info(f"[DEBUG] Processing source_id: {source_id}")
        file_record = db.query(FileUploadORM).filter(FileUploadORM.id == source_id).first()
        if file_record and file_record.data_preview:
            found_file = True
            logger.info(f"[DEBUG] Found file record for source_id {source_id}")
            logger.info(f"[DEBUG] File record ID: {file_record.id}")
            logger.info(f"[DEBUG] File record filename: {file_record.filename}")
            logger.info(f"[DEBUG] File record original_filename: {file_record.original_filename}")
            logger.info(f"[DEBUG] File record file_path: {file_record.file_path}")
            
            try:
                # Parse the data preview if it's a JSON string
                if isinstance(file_record.data_preview, str):
                    file_data = json.loads(file_record.data_preview)
                else:
                    file_data = file_record.data_preview
                
                # Convert null values to None for Python compatibility
                file_data = _convert_nulls_to_none(file_data)
                
                # Add file path and type for full file loading
                file_data["file_path"] = file_record.file_path
                file_data["file_type"] = file_record.file_type
                
                logger.info(f"[DEBUG] Added file_path to file_data: {file_data['file_path']}")
                logger.info(f"[DEBUG] Added file_type to file_data: {file_data['file_type']}")
                
                # Add proper column names if headers are available
                if "head" in file_data and len(file_data["head"]) > 0:
                    first_row = file_data["head"][0]
                    # Check if first row contains header information
                    if any('Date' in str(v) or 'Category' in str(v) or 'Description' in str(v) for v in first_row.values()):
                        # Add proper column names to the context
                        file_data["proper_columns"] = list(first_row.values())
                        file_data["column_mapping"] = {
                            old_name: new_name 
                            for old_name, new_name in zip(file_data.get("columns", []), list(first_row.values()))
                        }
                        
                        # Add reverse mapping for LLM to understand the actual column names
                        file_data["actual_column_names"] = {
                            new_name: old_name 
                            for old_name, new_name in zip(file_data.get("columns", []), list(first_row.values()))
                        }
                        
                        # Add a helpful note about the DataFrame structure
                        file_data["dataframe_info"] = {
                            "note": "After header processing, the DataFrame 'df' will have these column names:",
                            "actual_columns": list(first_row.values()),
                            "original_columns": file_data.get("columns", []),
                            "mapping": file_data["column_mapping"]
                        }
                        
                        # Add explicit column name information for LLM
                        file_data["available_columns"] = {
                            "Date": "Date column (from '123456789 - CASH MANAGEMENT ACCOUNT')",
                            "Category": "Category column (from 'ABC Super Fund')", 
                            "Description": "Description column (from 'Unnamed: 2')",
                            "Debit": "Debit column (from 'Unnamed: 3')",
                            "Credit": "Credit column (from 'Unnamed: 4')",
                            "Balance": "Balance column (from 'Unnamed: 5')",
                            "Category Type": "Category Type column (from 'Unnamed: 6')"
                        }
                        
                        # Add a clear instruction for the LLM with specific examples
                        file_data["llm_instruction"] = {
                            "important": "IMPORTANT: When writing code, use these exact column names:",
                            "columns": list(first_row.values()),
                            "example": "Example: Use df['Credit'] not df['Unnamed: 4'], Use df['Category'] not df['ABC Super Fund']",
                            "column_access_methods": {
                                "method1": "Use df['Column Name'] - e.g., df['Credit'], df['Debit'], df['Category']",
                                "method2": "Use df.iloc[:, column_index] - e.g., df.iloc[:, 3] for Credit, df.iloc[:, 2] for Debit",
                                "method3": "Use df.columns to see available column names first"
                            },
                            "specific_instructions": [
                                "DO NOT use df['Unnamed: 3'] - use df['Debit'] instead",
                                "DO NOT use df['Unnamed: 4'] - use df['Credit'] instead", 
                                "DO NOT use df['ABC Super Fund'] - use df['Category'] instead",
                                "DO NOT use df['123456789 - CASH MANAGEMENT ACCOUNT'] - use df['Date'] instead"
                            ]
                        }
                        
                        # Add a DataFrame preview for the LLM to understand the structure
                        file_data["dataframe_preview"] = {
                            "note": "The DataFrame 'df' will look like this after header processing:",
                            "columns": list(first_row.values()),
                            "sample_data": file_data["head"][1:3] if len(file_data["head"]) > 1 else [],
                            "column_indices": {
                                "Date": 0,
                                "Category": 1, 
                                "Description": 2,
                                "Debit": 3,
                                "Credit": 4,
                                "Balance": 5,
                                "Category Type": 6
                            }
                        }
                        
                        logger.info(f"[DEBUG] Added proper column names: {file_data['proper_columns']}")
                        logger.info(f"[DEBUG] Added column mapping: {file_data['column_mapping']}")
                        logger.info(f"[DEBUG] Added LLM instruction: {file_data['llm_instruction']}")
                        logger.info(f"[DEBUG] Added DataFrame preview: {file_data['dataframe_preview']}")
                
                # DEBUG LOGGING: Print columns for diagnosis
                logger.info(f"[DEBUG] Loaded file_data for source {source_id}: columns={file_data.get('columns')}, preview={file_data}")
                context["file_data"] = file_data
                logger.info(f"Added file data context for source: {source_id}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse data preview for source {source_id}: {e}")
                context["file_data"] = file_record.data_preview
            
            # Add file analysis if available
            if file_record and hasattr(file_record, 'data_analysis') and file_record.data_analysis:
                context["file_analysis"] = file_record.data_analysis
                logger.info(f"[DEBUG] Loaded file_analysis for source {source_id}: {file_record.data_analysis[:200]}")
        else:
            logger.warning(f"No file found for source_id: {source_id}")
    if not found_file:
        logger.error(f"No valid file data found for data_sources: {data_sources}")
    # Log the final context sent to LLM
    logger.info(f"[DEBUG] Final data context sent to LLM: {context}")
    return context


def _convert_nulls_to_none(obj):
    """Recursively convert null values to None for Python compatibility"""
    import logging
    logger = logging.getLogger(__name__)
    
    if obj is None:
        return None
    elif isinstance(obj, dict):
        converted = {}
        for k, v in obj.items():
            converted[k] = _convert_nulls_to_none(v)
        return converted
    elif isinstance(obj, list):
        converted = []
        for item in obj:
            converted.append(_convert_nulls_to_none(item))
        return converted
    else:
        return obj