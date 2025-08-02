from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"
    VIOLIN = "violin"
    UNKNOWN = "unknown"


class DatabaseConnection(BaseModel):
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    schema: Optional[str] = None


class FileUpload(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_path: str
    size: int
    uploaded_at: datetime
    processed: bool = False
    data_preview: Optional[Dict[str, Any]] = None
    data_analysis: Optional[str] = None  # LLM-driven data analysis output


class FileUploadCreate(BaseModel):
    """Schema for creating file upload records (used by upload manager)"""
    filename: str
    file_type: str
    size: int
    uploaded_at: datetime


class ChatMessage(BaseModel):
    id: Optional[str] = None
    content: str
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    data_sources: Optional[List[str]] = None


class ChatResponse(BaseModel):
    message_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    chartData: Optional[Dict[str, Any]] = None
    chartType: Optional[ChartType] = None
    chartCode: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DataSource(BaseModel):
    id: str
    name: str
    type: str  # "file" or "database"
    connection_info: Optional[Dict[str, Any]] = None
    schema_info: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)


class CodeExecutionRequest(BaseModel):
    code: str
    data_context: Optional[Dict[str, Any]] = None
    timeout: int = 30


class CodeExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    execution_time: float


class UploadResponse(BaseModel):
    success: bool
    fileId: Optional[str] = None
    message: str
    data_preview: Optional[Dict[str, Any]] = None


class DatabaseConnectionResponse(BaseModel):
    success: bool
    connection_id: Optional[str] = None
    message: str
    tables: Optional[List[str]] = None
    schema_info: Optional[Dict[str, Any]] = None


class SessionInfo(BaseModel):
    session_id: str
    data_sources: List[str]
    created_at: datetime
    last_activity: datetime
