import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useFileUpload } from '../../hooks/useFileUpload';
import { Upload, FileText, Trash2, Download, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../services/api';

interface FileUploadProps {
  setLatestFileId?: (id: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ setLatestFileId }) => {
  const { files, uploading, error, uploadFile, deleteFile, clearError } = useFileUpload();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    try {
      for (const file of acceptedFiles) {
        console.log('Uploading file:', file.name);
        
        const uploaded = await uploadFile(file);
        
        if (uploaded && uploaded.fileId) {
          console.log('File uploaded successfully:', uploaded.fileId);
          
          // Store the uploaded file ID in localStorage
          localStorage.setItem('latestFileId', uploaded.fileId);
          
          // Notify parent component
          if (setLatestFileId) {
            setLatestFileId(uploaded.fileId);
          }
          
          toast.success(`File uploaded successfully! File ID: ${uploaded.fileId}`);
          
          // Verify the file is in the backend
          try {
            const backendFiles = await apiService.getUploadedFiles();
            if (backendFiles && backendFiles.length > 0) {
              const latestFile = backendFiles[0];
              console.log('Latest file from backend after upload:', latestFile.id);
              
              // Update localStorage with the latest file ID from backend
              localStorage.setItem('latestFileId', latestFile.id);
              
              // Notify parent component with the correct ID
              if (setLatestFileId) {
                setLatestFileId(latestFile.id);
              }
              
              toast.success(`File processed and ready for chat! Using: ${latestFile.original_filename}`);
            } else {
              console.warn('No files found in backend after upload');
              toast.warning('File uploaded but not found in backend. Please try again.');
            }
          } catch (backendError) {
            console.error('Error fetching latest file from backend:', backendError);
            toast.error('File uploaded but could not verify backend status.');
          }
        } else {
          console.error('Upload response missing fileId:', uploaded);
          toast.error('Upload completed but file ID is missing.');
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed. Please try again.');
    }
  }, [uploadFile, setLatestFileId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false
  });

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

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-400 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? 'Drop the file here' : 'Drag & drop files here'}
        </p>
        <p className="text-sm text-gray-500">
          or click to select files (CSV, Excel)
        </p>
        {uploading && (
          <div className="mt-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Uploading and processing...</p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <Trash2 className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={clearError}
                  className="text-sm font-medium text-red-800 hover:text-red-900"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Uploaded Files</h3>
          <div className="space-y-3">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {file.originalFilename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)} • {formatDate(file.uploadedAt)}
                    </p>
                    {file.dataPreview && (
                      <p className="text-xs text-green-600">
                        ✓ Data preview available
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {file.dataPreview && (
                    <button
                      onClick={() => {
                        console.log('Data preview:', file.dataPreview);
                        toast.success('Data preview available in console');
                      }}
                      className="p-2 text-gray-400 hover:text-gray-600"
                      title="View data preview"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => deleteFile(file.id)}
                    className="p-2 text-gray-400 hover:text-red-600"
                    title="Delete file"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <FileText className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Supported File Types
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>• CSV files (.csv)</p>
              <p>• Excel files (.xlsx, .xls)</p>
              <p>• Maximum file size: 50MB</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
