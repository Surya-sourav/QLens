import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, FileText, Info, Columns, Download, Save } from 'lucide-react';
import { apiService } from '../../services/api';
import type { CSVPreviewRequest, CSVPreviewResponse, FileInfo, FileColumns } from '../../types';
import toast from 'react-hot-toast';

interface CSVPreviewProps {
  fileId: string;
  onClose?: () => void;
}

const CSVPreview: React.FC<CSVPreviewProps> = ({ fileId, onClose }) => {
  const [previewData, setPreviewData] = useState<CSVPreviewResponse | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [fileColumns, setFileColumns] = useState<FileColumns | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'info' | 'columns'>('preview');
  const [fileName, setFileName] = useState('');
  const [eolType, setEolType] = useState('CRLF');
  const [includeHeader, setIncludeHeader] = useState(true);

  useEffect(() => {
    loadFileInfo();
    loadFileColumns();
    loadPreviewData();
  }, [fileId]);

  useEffect(() => {
    loadPreviewData();
  }, [currentPage, pageSize]);

  const loadFileInfo = async () => {
    try {
      setLoading(true);
      console.log('Loading file info for:', fileId);
      const info = await apiService.getFileInfo(fileId);
      console.log('File info loaded:', info);
      setFileInfo(info);
      // Set default filename based on uploaded file
      const baseName = info?.fileInfo?.filename?.replace(/\.[^/.]+$/, '') || 'data';
      setFileName(`${baseName} - Sheet1`);
    } catch (error) {
      console.error('Error loading file info:', error);
      toast.error('Failed to load file information');
    } finally {
      setLoading(false);
    }
  };

  const loadFileColumns = async () => {
    try {
      setLoading(true);
      console.log('Loading file columns for:', fileId);
      const columns = await apiService.getFileColumns(fileId);
      console.log('File columns loaded:', columns);
      setFileColumns(columns);
    } catch (error) {
      console.error('Error loading file columns:', error);
      toast.error('Failed to load file columns');
    } finally {
      setLoading(false);
    }
  };

  const loadPreviewData = async () => {
    try {
      setLoading(true);
      console.log('Loading CSV preview data for file:', fileId);
      const request: CSVPreviewRequest = {
        file_id: fileId,
        page: currentPage,
        page_size: pageSize
      };
      console.log('CSV preview request:', request);
      
      // Add timeout and retry logic
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const data = await apiService.getCSVPreview(request);
      clearTimeout(timeoutId);
      
      console.log('CSV preview response:', data);
      setPreviewData(data);
    } catch (error) {
      console.error('Error loading preview data:', error);
      if (error instanceof Error && error.name === 'AbortError') {
        toast.error('Request timed out. Please try again.');
      } else {
        toast.error('Failed to load preview data. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= (previewData?.totalPages || 1)) {
      setCurrentPage(newPage);
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const downloadCSV = async () => {
    try {
      // Get all data for download (not just current page)
      const allDataRequest: CSVPreviewRequest = {
        file_id: fileId,
        page: 1,
        page_size: 10000 // Large number to get all data
      };
      
      const allData = await apiService.getCSVPreview(allDataRequest);
      
      if (!allData || !allData.data || allData.data.length === 0) {
        toast.error('No data available for download');
        return;
      }

      // Convert data to CSV format
      const csvContent = convertToCSV(allData.data, allData.columns, includeHeader, eolType);
      
      // Create and download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `${fileName}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success('CSV file downloaded successfully!');
    } catch (error) {
      console.error('Error downloading CSV:', error);
      toast.error('Failed to download CSV file');
    }
  };

  const convertToCSV = (data: any[], columns: string[], includeHeader: boolean, eol: string) => {
    const eolChar = eol === 'CRLF' ? '\r\n' : '\n';
    let csv = '';
    
    // Add header if requested
    if (includeHeader) {
      csv += columns.map(col => `"${col}"`).join(',') + eolChar;
    }
    
    // Add data rows
    data.forEach(row => {
      const rowData = columns.map(col => {
        const value = row[col];
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        const stringValue = value !== null && value !== undefined ? String(value) : '';
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      });
      csv += rowData.join(',') + eolChar;
    });
    
    return csv;
  };

  if (loading && !previewData && !fileInfo) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-2">Loading file preview...</span>
      </div>
    );
  }

  // Error state
  if (!fileInfo && !loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-red-500 text-lg mb-2">⚠️ Error Loading File</div>
          <p className="text-gray-600 mb-4">Unable to load file information. Please try again.</p>
          <button
            onClick={() => {
              loadFileInfo();
              loadFileColumns();
              loadPreviewData();
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <FileText className="h-6 w-6 text-primary-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {fileInfo?.fileInfo?.filename || 'File Preview'}
            </h3>
            <p className="text-sm text-gray-500">
              {fileInfo?.dataInfo?.totalRows || 0} rows × {fileInfo?.dataInfo?.totalColumns || 0} columns
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-4">
          <button
            onClick={() => setActiveTab('preview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'preview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Data Preview
          </button>
          <button
            onClick={() => setActiveTab('info')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'info'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Info className="inline h-4 w-4 mr-1" />
            File Info
          </button>
          <button
            onClick={() => setActiveTab('columns')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'columns'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Columns className="inline h-4 w-4 mr-1" />
            Columns
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'preview' && (
          <div>
            {/* Download Controls - Similar to screenshot */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-700">Save Your result:</span>
                  <input
                    type="text"
                    value={fileName}
                    onChange={(e) => setFileName(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-1 text-sm w-48"
                    placeholder="Enter filename"
                  />
                  <span className="text-sm text-gray-500">.csv or .xlsx</span>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-700">EOL:</span>
                    <select
                      value={eolType}
                      onChange={(e) => setEolType(e.target.value)}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value="CRLF">CRLF</option>
                      <option value="LF">LF</option>
                    </select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="includeHeader"
                      checked={includeHeader}
                      onChange={(e) => setIncludeHeader(e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <label htmlFor="includeHeader" className="text-sm text-gray-700">
                      Include Header
                    </label>
                  </div>
                  <button
                    onClick={downloadCSV}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download CSV</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  Page {currentPage} of {previewData?.totalPages || 1}
                </span>
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value={25}>25 rows</option>
                  <option value={50}>50 rows</option>
                  <option value={100}>100 rows</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= (previewData?.totalPages || 1)}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Data Table */}
            {previewData && (
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {/* Column letters row - like in screenshot */}
                      <th className="px-2 py-1 text-xs text-gray-400 border-r border-gray-200"></th>
                      {previewData.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-2 py-1 text-xs text-gray-400 border-r border-gray-200"
                        >
                          {String.fromCharCode(69 + index)} {/* Start from E like in screenshot */}
                        </th>
                      ))}
                    </tr>
                    <tr>
                      {/* Row numbers column */}
                      <th className="px-2 py-2 text-xs font-medium text-gray-500 bg-gray-50 border-r border-gray-200"></th>
                      {previewData.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-2 py-2 text-xs font-medium text-gray-500 bg-gray-50 border-r border-gray-200"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {previewData.data.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50">
                        {/* Row number */}
                        <td className="px-2 py-2 text-xs text-gray-400 border-r border-gray-200 text-center">
                          {rowIndex + 1}
                        </td>
                        {previewData.columns.map((column, colIndex) => (
                          <td
                            key={colIndex}
                            className="px-2 py-2 text-xs text-gray-900 border-r border-gray-200"
                          >
                            {row[column] !== null && row[column] !== undefined
                              ? String(row[column])
                              : ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'info' && fileInfo && (
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">File Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">File Details</h5>
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Filename:</dt>
                      <dd className="text-gray-900">{fileInfo.fileInfo.filename}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Type:</dt>
                      <dd className="text-gray-900">{fileInfo.fileInfo.fileType}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Size:</dt>
                      <dd className="text-gray-900">{formatFileSize(fileInfo.fileInfo.size)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Uploaded:</dt>
                      <dd className="text-gray-900">{formatDate(fileInfo.fileInfo.uploadedAt)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Processed:</dt>
                      <dd className="text-gray-900">
                        {fileInfo.fileInfo.processed ? 'Yes' : 'No'}
                      </dd>
                    </div>
                  </dl>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Data Information</h5>
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Total Rows:</dt>
                      <dd className="text-gray-900">{fileInfo.dataInfo.totalRows}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Total Columns:</dt>
                      <dd className="text-gray-900">{fileInfo.dataInfo.totalColumns}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Has Headers:</dt>
                      <dd className="text-gray-900">{fileInfo.dataInfo.hasHeaders ? 'Yes' : 'No'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Numeric Columns:</dt>
                      <dd className="text-gray-900">{fileInfo.dataInfo.numericColumns.length}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Categorical Columns:</dt>
                      <dd className="text-gray-900">{fileInfo.dataInfo.categoricalColumns.length}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'columns' && fileColumns && (
          <div>
            <h4 className="text-lg font-medium text-gray-900 mb-4">Column Information</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Column Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {fileColumns.columns.actualColumns.map((column, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {column}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {fileColumns.columns.dataTypes[column] || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {fileColumns.columns.numericColumns.includes(column) && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Numeric
                          </span>
                        )}
                        {fileColumns.columns.categoricalColumns.includes(column) && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Categorical
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CSVPreview; 