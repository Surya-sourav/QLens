import React, { useState } from 'react';
import { ChartData } from '../../types';
import { Eye, Code, Download, Copy } from 'lucide-react';
import toast from 'react-hot-toast';

interface ChartRendererProps {
  chartData: ChartData;
  chartType?: string;
  chartCode?: string;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ chartData, chartType, chartCode }) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'code'>('chart');

  const handleCopyCode = () => {
    if (chartCode) {
      navigator.clipboard.writeText(chartCode);
      toast.success('Code copied to clipboard');
    }
  };

  const handleDownloadChart = () => {
    if (chartData.type === 'matplotlib' && chartData.data) {
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${chartData.data}`;
      link.download = `chart-${Date.now()}.png`;
      link.click();
    }
  };

  const renderChart = () => {
    if (chartData.type === 'matplotlib') {
      return (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <img
            src={`data:image/png;base64,${chartData.data}`}
            alt="Generated chart"
            className="w-full h-auto max-h-96 object-contain"
          />
        </div>
      );
    } else if (chartData.type === 'plotly') {
      // For plotly charts, you would need to render them using react-plotly.js
      return (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center text-gray-500">
            Plotly chart rendering not implemented yet
          </div>
        </div>
      );
    }
    return null;
  };

  const renderCode = () => {
    if (!chartCode) return null;

    return (
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-300">Generated Code</span>
          <button
            onClick={handleCopyCode}
            className="flex items-center space-x-1 text-gray-400 hover:text-white transition-colors"
          >
            <Copy className="w-4 h-4" />
            <span className="text-xs">Copy</span>
          </button>
        </div>
        <pre className="text-sm text-gray-300 overflow-x-auto">
          <code>{chartCode}</code>
        </pre>
      </div>
    );
  };

  return (
    <div className="mt-4">
      {/* Chart Type Badge */}
      {chartType && (
        <div className="mb-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
            {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart
          </span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 mb-3">
        <button
          onClick={() => setActiveTab('chart')}
          className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'chart'
              ? 'bg-primary-100 text-primary-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Eye className="w-4 h-4" />
          <span>Chart</span>
        </button>
        {chartCode && (
          <button
            onClick={() => setActiveTab('code')}
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'code'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Code className="w-4 h-4" />
            <span>Code</span>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="bg-gray-50 rounded-lg p-4">
        {activeTab === 'chart' ? (
          <div>
            {renderChart()}
            {chartData.type === 'matplotlib' && (
              <div className="mt-3 flex justify-end">
                <button
                  onClick={handleDownloadChart}
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          renderCode()
        )}
      </div>
    </div>
  );
};

export default ChartRenderer;
