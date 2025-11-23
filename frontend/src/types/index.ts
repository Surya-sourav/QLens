export interface ChatMessage {
  id?: string;
  content: string;
  messageType: 'user' | 'assistant' | 'system';
  timestamp: string;
  responseType?: 'chart' | 'text' | 'data_manipulation' | 'csv_preview' | 'calculation' | 'analysis';
  chartData?: any;
  chartType?: string;
  chartCode?: string;
  calculationResult?: any;
  dataPreview?: any;
  manipulationResult?: any;
  metadata?: any;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  data_sources?: string[];
}

export interface ChatResponse {
  messageId: string;
  content: string;
  messageType: 'user' | 'assistant' | 'system';
  timestamp: string;
  responseType?: 'chart' | 'text' | 'data_manipulation' | 'csv_preview' | 'calculation' | 'analysis';
  chartData?: any;
  chartType?: string;
  chartCode?: string;
  calculationResult?: any;
  dataPreview?: any;
  manipulationResult?: any;
  metadata?: any;
}

export interface FileUpload {
  id: string;
  filename: string;
  originalFilename: string;
  fileType: string;
  filePath: string;
  size: number;
  uploadedAt: string;
  processed: boolean;
  dataPreview?: any;
}

export interface UploadResponse {
  success: boolean;
  fileId?: string;
  message: string;
  dataPreview?: any;
}

export interface DatabaseConnection {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  schema?: string;
}

export interface DatabaseConnectionResponse {
  success: boolean;
  connectionId?: string;
  message: string;
  tables?: string[];
  schemaInfo?: any;
}

export interface DataSource {
  id: string;
  name: string;
  type: 'file' | 'database';
  connectionInfo?: any;
  schemaInfo?: any;
  createdAt: string;
}

export interface ChartData {
  type: 'matplotlib' | 'plotly';
  data: any;
  format?: string;
}

export interface SessionInfo {
  sessionId: string;
  dataSources: string[];
  createdAt: string;
  lastActivity: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    timestamp: string;
  };
}

export interface WebSocketMessage {
  type: 'message' | 'response' | 'error' | 'chart';
  content?: string;
  chartData?: ChartData;
  chartType?: string;
  code?: string;
  responseType?: string;
  calculationResult?: any;
  dataPreview?: any;
}

export interface FileUploadState {
  files: FileUpload[];
  uploading: boolean;
  error?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  sessionId?: string;
  dataSources: string[];
}

export interface DatabaseState {
  connections: DataSource[];
  selectedConnection?: string;
  selectedTable?: string;
  loading: boolean;
  error?: string;
}

export interface AppState {
  chat: ChatState;
  upload: FileUploadState;
  database: DatabaseState;
}

// CSV Preview Types
export interface CSVPreviewRequest {
  file_id: string;
  page: number;
  page_size: number;
}

export interface CSVPreviewResponse {
  success: boolean;
  data: Record<string, any>[];
  columns: string[];
  totalRows: number;
  currentPage: number;
  totalPages: number;
  pageSize: number;
}

export interface FileInfo {
  success: boolean;
  fileInfo: {
    id: string;
    filename: string;
    fileType: string;
    size: number;
    uploadedAt: string;
    processed: boolean;
  };
  dataInfo: {
    totalRows: number;
    totalColumns: number;
    columns: string[];
    numericColumns: string[];
    categoricalColumns: string[];
    hasHeaders: boolean;
    sampleDataAvailable: boolean;
  };
}

export interface FileColumns {
  success: boolean;
  columns: {
    originalColumns: string[];
    actualColumns: string[];
    numericColumns: string[];
    categoricalColumns: string[];
    dataTypes: Record<string, string>;
    hasHeaders: boolean;
    totalColumns: number;
  };
}

// Agentic Response Types
export interface CalculationResult {
  operation: string;
  result: number | string;
  description: string;
  units?: string;
}

export interface DataManipulationResult {
  operation: string;
  result: Record<string, any>[];
  description: string;
  affectedRows?: number;
  summary?: string;
}
