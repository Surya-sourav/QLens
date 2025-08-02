import React, { useState, useEffect } from 'react';
import { FileText, Database, Trash2, Plus, MessageSquare } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useFileUpload } from '../../hooks/useFileUpload';
import { apiService } from '../../services/api';
import { DataSource } from '../../types';
import toast from 'react-hot-toast';

const Sidebar: React.FC = () => {
  const { dataSources, addDataSource, removeDataSource, createNewSession } = useChat();
  const { files } = useFileUpload();
  const [databaseConnections, setDatabaseConnections] = useState<DataSource[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDatabaseConnections();
    loadSessions();
  }, []);

  const loadDatabaseConnections = async () => {
    try {
      const connections = await apiService.getConnections();
      setDatabaseConnections(connections);
    } catch (error) {
      console.error('Error loading database connections:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const sessionList = await apiService.getSessions();
      setSessions(sessionList);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const handleDataSourceToggle = (sourceId: string, type: 'file' | 'database') => {
    if (dataSources.includes(sourceId)) {
      removeDataSource(sourceId);
      toast.success(`${type === 'file' ? 'File' : 'Database'} removed from chat`);
    } else {
      addDataSource(sourceId);
      toast.success(`${type === 'file' ? 'File' : 'Database'} added to chat`);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await apiService.deleteFile(fileId);
      toast.success('File deleted successfully');
      // Refresh files list
      window.location.reload();
    } catch (error) {
      toast.error('Failed to delete file');
    }
  };

  const handleDeleteConnection = async (connectionId: string) => {
    try {
      await apiService.deleteConnection(connectionId);
      toast.success('Database connection deleted');
      loadDatabaseConnections();
    } catch (error) {
      toast.error('Failed to delete database connection');
    }
  };

  return (
    <aside className="w-80 bg-white border-r border-gray-200 p-6 overflow-y-auto">
      <div className="space-y-6">
        {/* New Chat Button */}
        <div>
          <button
            onClick={createNewSession}
            className="w-full flex items-center justify-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Data Sources Section */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Data Sources</h3>
          
          {/* Files */}
          {files.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Files
              </h4>
              <div className="space-y-2">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className={`flex items-center justify-between p-2 rounded-md border ${
                      dataSources.includes(file.id)
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.originalFilename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleDataSourceToggle(file.id, 'file')}
                        className={`p-1 rounded ${
                          dataSources.includes(file.id)
                            ? 'text-primary-600 hover:text-primary-700'
                            : 'text-gray-400 hover:text-gray-600'
                        }`}
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteFile(file.id)}
                        className="p-1 rounded text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Database Connections */}
          {databaseConnections.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Database Connections
              </h4>
              <div className="space-y-2">
                {databaseConnections.map((connection) => (
                  <div
                    key={connection.id}
                    className={`flex items-center justify-between p-2 rounded-md border ${
                      dataSources.includes(connection.id)
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <Database className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {connection.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {connection.connectionInfo?.host}:{connection.connectionInfo?.port}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleDataSourceToggle(connection.id, 'database')}
                        className={`p-1 rounded ${
                          dataSources.includes(connection.id)
                            ? 'text-primary-600 hover:text-primary-700'
                            : 'text-gray-400 hover:text-gray-600'
                        }`}
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteConnection(connection.id)}
                        className="p-1 rounded text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {files.length === 0 && databaseConnections.length === 0 && (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">
                No data sources available.
                <br />
                Upload files or connect to a database to get started.
              </p>
            </div>
          )}
        </div>

        {/* Recent Sessions */}
        {sessions.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Sessions</h3>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((session) => (
                <div
                  key={session.sessionId}
                  className="flex items-center justify-between p-2 rounded-md border border-gray-200 hover:border-gray-300"
                >
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        Session {session.sessionId ? session.sessionId.slice(0, 8) : 'Unknown'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {session.lastActivity ? new Date(session.lastActivity).toLocaleDateString() : ''}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
