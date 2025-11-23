import React, { useState, useEffect } from 'react';
import { Eye, Send, Bot, Calculator, Table, BarChart3, TrendingUp } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useWebSocket } from '../../hooks/useWebSocket';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import CSVPreview from '../Upload/CSVPreview';
import toast from 'react-hot-toast';
import { apiService } from '../../services/api';

interface ChatInterfaceProps {
  latestFileId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ latestFileId }) => {
  const {
    messages,
    loading,
    dataSources,
    setDataSourcesExternal,
    sendMessage,
    isConnected
  } = useChat();
  
  const [showCSVPreview, setShowCSVPreview] = React.useState(false);
  const [selectedFileForPreview, setSelectedFileForPreview] = React.useState<string | null>(null);

  // Clear old localStorage data on mount to ensure fresh start
  React.useEffect(() => {
    const oldFileId = localStorage.getItem('latestFileId');
    if (oldFileId) {
      console.log('ChatInterface: Clearing old localStorage file ID:', oldFileId);
      localStorage.removeItem('latestFileId');
    }
  }, []);

  // Function to get the effective file ID (ALWAYS prioritize backend, never localStorage)
  const getEffectiveFileId = async () => {
    try {
      // ALWAYS try to get the latest file from backend first
      const files = await apiService.getUploadedFiles();
      console.log('ChatInterface: Files from API:', files);
      if (files && files.length > 0) {
        const latestFile = files[0];
        console.log('ChatInterface: Using latest file ID from backend:', latestFile.id);
        
        // Update localStorage with the new file ID
        localStorage.setItem('latestFileId', latestFile.id);
        
        return latestFile.id;
      }
    } catch (error) {
      console.error('ChatInterface: Error fetching latest file from backend:', error);
    }
    
    // If no files in backend, clear localStorage and return null
    console.log('ChatInterface: No files in backend, clearing localStorage');
    localStorage.removeItem('latestFileId');
    return null;
  };

  // Set data sources whenever latestFileId changes or on mount
  React.useEffect(() => {
    const initializeDataSources = async () => {
      const effectiveFileId = await getEffectiveFileId();
      if (effectiveFileId) {
        console.log('ChatInterface: Setting data sources with file ID:', effectiveFileId);
        setDataSourcesExternal([effectiveFileId]);
      } else {
        console.log('ChatInterface: No effective file ID found');
        // Clear localStorage if no files found
        localStorage.removeItem('latestFileId');
      }
    };
    
    initializeDataSources();
  }, [latestFileId, setDataSourcesExternal]);

  const handleSendMessage = async (message: string) => {
    // ALWAYS ensure the latest file ID is set in dataSources before sending
    console.log('ChatInterface: Getting fresh file ID before sending message...');
    const effectiveFileId = await getEffectiveFileId();
    if (effectiveFileId && !dataSources.includes(effectiveFileId)) {
      console.log('ChatInterface: Updating data sources before sending message:', effectiveFileId);
      setDataSourcesExternal([effectiveFileId]);
    }
    
    console.log('ChatInterface: Sending message with dataSources:', dataSources);
    sendMessage(message);
  };

  const handleCSVPreviewClick = async () => {
    console.log('CSV Preview button clicked');
    console.log('Data sources:', dataSources);
    
    if (dataSources.length === 0) {
      console.log('No data sources available');
      toast.error('No files connected to view CSV preview');
      return;
    }
    
    const latestFileId = dataSources[0];
    console.log('Opening CSV preview for file:', latestFileId);
    
    try {
      // Verify file exists before opening preview
      const files = await apiService.getUploadedFiles();
      const fileExists = files.some(file => file.id === latestFileId);
      
      if (!fileExists) {
        toast.error('File not found. Please reconnect the file.');
        return;
      }
      
      setSelectedFileForPreview(latestFileId);
      setShowCSVPreview(true);
      toast.success('Opening CSV preview...');
    } catch (error) {
      console.error('Error opening CSV preview:', error);
      toast.error('Failed to open CSV preview. Please try again.');
    }
  };

  const handleCloseCSVPreview = () => {
    setShowCSVPreview(false);
    setSelectedFileForPreview(null);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Chat with Your Data</h2>
          <p className="text-sm text-gray-500">
            {dataSources.length > 0 
              ? `${dataSources.length} data source${dataSources.length > 1 ? 's' : ''} connected`
              : 'No data sources connected'
            }
          </p>
          {dataSources.length > 0 && (
            <p className="text-xs text-blue-600 mt-1">
              Connected files: {dataSources.join(', ')}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {dataSources.length > 0 && (
            <button
              onClick={handleCSVPreviewClick}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium flex items-center space-x-1"
              title="View CSV preview"
            >
              <Eye className="h-3 w-3" />
              <span>View CSV</span>
            </button>
          )}
        </div>
        
        {/* Always visible CSV preview button */}
        <div className="mt-4">
          <button
            onClick={handleCSVPreviewClick}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium flex items-center justify-center space-x-2"
            title="View CSV preview"
          >
            <Eye className="h-4 w-4" />
            <span>📊 View CSV Data</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} loading={loading} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <MessageInput onSendMessage={handleSendMessage} disabled={loading} />
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="bg-yellow-50 border-t border-yellow-200 p-3">
          <div className="flex items-center space-x-2">
            <Bot className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              Connecting to chat server...
            </span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {messages.length === 0 && !loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask questions about your data, request visualizations, perform calculations, or get insights from your uploaded files and database connections.
            </p>
            {dataSources.length === 0 && (
              <div className="mt-4 p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">
                  💡 Tip: Upload files or connect to a database to get started with data analysis.
                </p>
              </div>
            )}
            {dataSources.length > 0 && (
              <div className="mt-4 space-y-3">
                <div className="p-3 bg-green-50 rounded-md">
                  <p className="text-sm text-green-800 mb-2">
                    ✅ You have {dataSources.length} data source(s) connected. You can now ask questions about your data!
                  </p>
                </div>
                
                {/* Feature Examples */}
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-800 mb-2">Try these examples:</p>
                  <div className="space-y-2 text-xs text-gray-600">
                    <div className="flex items-center space-x-2">
                      <Calculator className="w-3 h-3 text-green-600" />
                      <span>"What's the total cost?" or "Calculate the average balance"</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Table className="w-3 h-3 text-blue-600" />
                      <span>"Show me transactions above $1000" or "Sort by date"</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="w-3 h-3 text-orange-600" />
                      <span>"Create a bar chart of expenses by category"</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-3 h-3 text-purple-600" />
                      <span>"Analyze spending patterns" or "Find trends in the data"</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* CSV Preview Modal */}
      {showCSVPreview && selectedFileForPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
            <CSVPreview 
              fileId={selectedFileForPreview} 
              onClose={handleCloseCSVPreview}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
