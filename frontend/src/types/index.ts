export interface ChatMessage {
  id?: string;
  content: string;
  messageType: 'user' | 'assistant' | 'system';
  timestamp: string;
  chartData?: any;
  chartType?: string;
  chartCode?: string;
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
  chartData?: any;
  chartType?: string;
  chartCode?: string;
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
