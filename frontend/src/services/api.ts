import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ChatRequest,
  ChatResponse,
  UploadResponse,
  DatabaseConnection,
  DatabaseConnectionResponse,
  FileUpload,
  DataSource,
  SessionInfo,
  ApiResponse
} from '../types/index';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.api.post('/chat/message', request);
    return response.data;
  }

  async getSessions(): Promise<SessionInfo[]> {
    const response: AxiosResponse<SessionInfo[]> = await this.api.get('/chat/sessions');
    return response.data;
  }

  async getSessionMessages(sessionId: string): Promise<ChatResponse[]> {
    const response: AxiosResponse<ChatResponse[]> = await this.api.get(`/chat/session/${sessionId}/messages`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<ApiResponse> {
    const response: AxiosResponse<ApiResponse> = await this.api.delete(`/chat/session/${sessionId}`);
    return response.data;
  }

  // Upload endpoints
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<UploadResponse> = await this.api.post('/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getUploadedFiles(): Promise<FileUpload[]> {
    const response: AxiosResponse<FileUpload[]> = await this.api.get('/upload/files');
    return response.data;
  }

  async deleteFile(fileId: string): Promise<ApiResponse> {
    const response: AxiosResponse<ApiResponse> = await this.api.delete(`/upload/file/${fileId}`);
    return response.data;
  }

  // Database endpoints
  async connectDatabase(connection: DatabaseConnection): Promise<DatabaseConnectionResponse> {
    const response: AxiosResponse<DatabaseConnectionResponse> = await this.api.post('/database/connect', connection);
    return response.data;
  }

  async getConnections(): Promise<DataSource[]> {
    const response: AxiosResponse<DataSource[]> = await this.api.get('/database/connections');
    return response.data;
  }

  async getTables(connectionId: string): Promise<string[]> {
    const response: AxiosResponse<string[]> = await this.api.get(`/database/connection/${connectionId}/tables`);
    return response.data;
  }

  async getTablePreview(connectionId: string, tableName: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.get(`/database/connection/${connectionId}/table/${tableName}/preview`);
    return response.data;
  }

  async executeQuery(connectionId: string, query: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post(`/database/connection/${connectionId}/query`, { query });
    return response.data;
  }

  async deleteConnection(connectionId: string): Promise<ApiResponse> {
    const response: AxiosResponse<ApiResponse> = await this.api.delete(`/database/connection/${connectionId}`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.api.get('/health');
    return response.data;
  }

  // API info
  async getApiInfo(): Promise<any> {
    const response: AxiosResponse<any> = await this.api.get('/info');
    return response.data;
  }
}

export const apiService = new ApiService();
