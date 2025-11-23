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


class ResponseType(str, Enum):
    CHART = "chart"
    TEXT = "text"
    DATA_MANIPULATION = "data_manipulation"
    CSV_PREVIEW = "csv_preview"
    CALCULATION = "calculation"
    ANALYSIS = "analysis"


class QueryIntent(str, Enum):
    VISUALIZATION = "visualization"
    DATA_ANALYSIS = "data_analysis"
    CALCULATION = "calculation"
    DATA_MANIPULATION = "data_manipulation"
    GENERAL_QUERY = "general_query"


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
    messageId: str = Field(alias="message_id")
    content: str
    messageType: MessageType = Field(alias="message_type")
    timestamp: datetime
    responseType: Optional[ResponseType] = Field(None, alias="response_type")
    chartData: Optional[Dict[str, Any]] = None
    chartType: Optional[ChartType] = None
    chartCode: Optional[str] = None
    calculationResult: Optional[Dict[str, Any]] = Field(None, alias="calculation_result")
    dataPreview: Optional[Dict[str, Any]] = Field(None, alias="data_preview")
    manipulationResult: Optional[Dict[str, Any]] = Field(None, alias="manipulation_result")
    metadata: Optional[Dict[str, Any]] = None
    query_intent: Optional[QueryIntent] = None
    query_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class DataManipulationResult(BaseModel):
    operation: str
    result: Any
    description: str
    affected_rows: Optional[int] = None
    summary: Optional[str] = None


class CalculationResult(BaseModel):
    operation: str
    result: Any
    formula: Optional[str] = None
    description: str
    units: Optional[str] = None


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
    execution_type: Optional[str] = "chart"  # "chart", "calculation", "data_manipulation"


class CodeExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    calculation_result: Optional[Dict[str, Any]] = None
    data_manipulation_result: Optional[Dict[str, Any]] = None
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


class CSVPreviewRequest(BaseModel):
    file_id: str
    page: int = 1
    page_size: int = 50


class CSVPreviewResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    columns: List[str]
    total_rows: int
    current_page: int
    total_pages: int
    page_size: int
