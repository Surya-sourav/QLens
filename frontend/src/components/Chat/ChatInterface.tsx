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
  
  // Debug: Log messages state changes
  React.useEffect(() => {
    console.log('ChatInterface: messages state changed:', messages);
    console.log('ChatInterface: messages.length:', messages.length);
  }, [messages]);
  
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

      {/* Empty State - Shows before first message */}
      {messages.length === 0 && !loading && (
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 bg-gradient-to-br from-slate-700 to-slate-900 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Send className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-600 mb-4">
              Ask questions about your data, request visualizations, perform calculations, or get insights from your uploaded files and database connections.
            </p>
            {dataSources.length === 0 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 <strong>Tip:</strong> Upload files or connect to a database to get started with data analysis.
                </p>
              </div>
            )}
            {dataSources.length > 0 && (
              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800 font-medium">
                    ✅ You have {dataSources.length} data source(s) connected. You can now ask questions about your data!
                  </p>
                </div>
                
                {/* Feature Examples */}
                <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
                  <p className="text-sm font-semibold text-gray-900 mb-3">Try these examples:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-700">
                    <div className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                      <Calculator className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>"What's the total cost?" or "Calculate the average balance"</span>
                    </div>
                    <div className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                      <Table className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span>"Show me transactions above $1000" or "Sort by date"</span>
                    </div>
                    <div className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                      <BarChart3 className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span>"Create a bar chart of expenses by category"</span>
                    </div>
                    <div className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                      <TrendingUp className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                      <span>"Analyze spending patterns" or "Find trends in the data"</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
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
      
      {/* CSV Preview Modal */}
      {showCSVPreview && selectedFileForPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full h-[90vh] flex">
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
