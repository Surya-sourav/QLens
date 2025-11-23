import React, { useState } from 'react';
import type { ChatMessage } from '../../types';
import ChartRenderer from './ChartRenderer';
import CSVPreview from '../Upload/CSVPreview';
import { Bot, User, Loader2, Calculator, Table, BarChart3, TrendingUp, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

interface MessageListProps {
  messages: ChatMessage[];
  loading?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, loading = false }) => {
  const [showCSVPreview, setShowCSVPreview] = useState(false);
  const [selectedFileForPreview, setSelectedFileForPreview] = useState<string | null>(null);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getResponseTypeIcon = (responseType?: string) => {
    switch (responseType) {
      case 'calculation':
        return <Calculator className="w-4 h-4 text-green-600" />;
      case 'data_manipulation':
        return <Table className="w-4 h-4 text-blue-600" />;
      case 'analysis':
        return <TrendingUp className="w-4 h-4 text-purple-600" />;
      case 'chart':
        return <BarChart3 className="w-4 h-4 text-orange-600" />;
      default:
        return null;
    }
  };

  const getResponseTypeLabel = (responseType?: string) => {
    switch (responseType) {
      case 'calculation':
        return 'Calculation';
      case 'data_manipulation':
        return 'Data Manipulation';
      case 'analysis':
        return 'Analysis';
      case 'chart':
        return 'Visualization';
      default:
        return 'Response';
    }
  };

  const handleCSVPreviewClick = async () => {
    try {
      // Get the latest file ID from localStorage or try to fetch from backend
      const latestFileId = localStorage.getItem('latestFileId');
      if (latestFileId) {
        setSelectedFileForPreview(latestFileId);
        setShowCSVPreview(true);
      } else {
        toast.success('Please upload a file first to view CSV preview');
      }
    } catch (error) {
      console.error('Error opening CSV preview:', error);
      toast.error('Failed to open CSV preview');
    }
  };

  const handleCloseCSVPreview = () => {
    setShowCSVPreview(false);
    setSelectedFileForPreview(null);
  };

  const renderCalculationResult = (calculationResult: any) => {
    if (!calculationResult) return null;

    return (
      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-2">
          <Calculator className="w-4 h-4 text-green-600" />
          <span className="text-sm font-medium text-green-800">Calculation Result</span>
        </div>
        <div className="text-lg font-bold text-green-900">
          {calculationResult.result}
          {calculationResult.units && (
            <span className="text-sm font-normal text-green-700 ml-1">
              {calculationResult.units}
            </span>
          )}
        </div>
        {calculationResult.description && (
          <p className="text-sm text-green-700 mt-1">{calculationResult.description}</p>
        )}
      </div>
    );
  };

  const renderDataManipulationResult = (manipulationResult: any) => {
    if (!manipulationResult) return null;

    return (
      <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-2">
          <Table className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">Data Manipulation</span>
        </div>
        <p className="text-sm text-blue-700 mb-2">{manipulationResult.description}</p>
        {manipulationResult.affected_rows && (
          <p className="text-xs text-blue-600">
            Affected rows: {manipulationResult.affected_rows}
          </p>
        )}
        
        {/* CSV Viewer Button */}
        <div className="mt-3">
          <button
            onClick={handleCSVPreviewClick}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium flex items-center space-x-1"
            title="View CSV preview"
          >
            <Eye className="h-3 w-3" />
            <span>View CSV Preview</span>
          </button>
        </div>
        
        {manipulationResult.result && manipulationResult.result.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-medium text-blue-800 mb-1">Preview (first few rows):</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b border-blue-200">
                    {Object.keys(manipulationResult.result[0]).map((key) => (
                      <th key={key} className="text-left py-1 px-2 text-blue-700">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {manipulationResult.result.slice(0, 3).map((row: any, index: number) => (
                    <tr key={index} className="border-b border-blue-100">
                      {Object.values(row).map((value: any, colIndex: number) => (
                        <td key={colIndex} className="py-1 px-2 text-blue-900">
                          {String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-4 space-y-4">
      {messages.map((message, index) => (
        <div
          key={message.id || index}
          className={`flex ${message.messageType === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-4xl rounded-lg px-4 py-3 ${
              message.messageType === 'user'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            {/* Message Header */}
            <div className="flex items-center space-x-2 mb-2">
              {message.messageType === 'user' ? (
                <User className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
              <span className="text-xs opacity-75">
                {message.messageType === 'user' ? 'You' : 'QLens'}
              </span>
              {message.responseType && message.messageType === 'assistant' && (
                <>
                  {getResponseTypeIcon(message.responseType)}
                  <span className="text-xs opacity-75">
                    {getResponseTypeLabel(message.responseType)}
                  </span>
                </>
              )}
              <span className="text-xs opacity-50">
                {formatTime(message.timestamp)}
              </span>
            </div>

            {/* Message Content */}
            <div className="prose prose-sm max-w-none">
              {message.content && (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
            </div>

            {/* Chart Data */}
            {message.chartData && (
              <div className="mt-3">
                <ChartRenderer
                  chartData={message.chartData}
                  chartType={message.chartType}
                  chartCode={message.chartCode}
                />
              </div>
            )}

            {/* Calculation Result */}
            {message.calculationResult && (
              renderCalculationResult(message.calculationResult)
            )}

            {/* Data Manipulation Result */}
            {message.manipulationResult && (
              renderDataManipulationResult(message.manipulationResult)
            )}
          </div>
        </div>
      ))}

      {/* Loading Indicator */}
      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 rounded-lg px-4 py-3">
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm text-gray-600">Generating response...</span>
            </div>
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

export default MessageList;
