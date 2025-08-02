import { useState, useCallback, useEffect } from 'react';
import { FileUpload, UploadResponse } from '../types';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

export const useFileUpload = () => {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing files on mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = useCallback(async () => {
    try {
      const uploadedFiles = await apiService.getUploadedFiles();
      setFiles(uploadedFiles);
    } catch (error) {
      console.error('Error loading files:', error);
      setError('Failed to load uploaded files');
    }
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    // Validate file type
    const allowedTypes = [
      'text/csv',
      'application/csv',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ];

    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type. Please upload CSV or Excel files only.');
      return null;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File size too large. Please upload files smaller than 10MB.');
      return null;
    }

    setUploading(true);
    setError(null);

    try {
      const response: UploadResponse = await apiService.uploadFile(file);
      
      if (response.success && response.fileId) {
        // Add the new file to the list
        const newFile: FileUpload = {
          id: response.fileId,
          filename: file.name,
          originalFilename: file.name,
          fileType: file.type,
          filePath: '', // This would be set by the backend
          size: file.size,
          uploadedAt: new Date().toISOString(),
          processed: true,
          dataPreview: response.dataPreview
        };
        
        setFiles(prev => [...prev, newFile]);
        toast.success('File uploaded successfully');
        return newFile;
      } else {
        setError(response.message || 'Upload failed');
        toast.error(response.message || 'Upload failed');
        return null;
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload file');
      toast.error('Failed to upload file');
      return null;
    } finally {
      setUploading(false);
    }
  }, []);

  const deleteFile = useCallback(async (fileId: string) => {
    try {
      const response = await apiService.deleteFile(fileId);
      
      if (response.success) {
        setFiles(prev => prev.filter(file => file.id !== fileId));
        toast.success('File deleted successfully');
      } else {
        setError(response.message || 'Failed to delete file');
        toast.error(response.message || 'Failed to delete file');
      }
    } catch (error) {
      console.error('Delete error:', error);
      setError('Failed to delete file');
      toast.error('Failed to delete file');
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const getFileById = useCallback((fileId: string) => {
    return files.find(file => file.id === fileId);
  }, [files]);

  const getFilePreview = useCallback((fileId: string) => {
    const file = getFileById(fileId);
    return file?.dataPreview;
  }, [getFileById]);

  // Expose the latest uploaded file ID for chat integration
  const latestFileId = files.length > 0 ? files[files.length - 1].id : undefined;

  return {
    files,
    uploading,
    error,
    uploadFile,
    deleteFile,
    loadFiles,
    clearError,
    getFileById,
    getFilePreview,
    latestFileId
  };
};
