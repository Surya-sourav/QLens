import React from 'react';
import { ChatMessage } from '../../types';
import ChartRenderer from './ChartRenderer';
import { Bot, User, Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessage[];
  loading?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, loading = false }) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="p-4 space-y-4">
      {messages.map((message, index) => (
        <div
          key={message.id || index}
          className={`flex ${message.messageType === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-3xl rounded-lg px-4 py-3 ${
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
    </div>
  );
};

export default MessageList;
