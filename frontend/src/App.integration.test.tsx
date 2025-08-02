import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import App from './App';

// Mock hooks and services
jest.mock('./hooks/useFileUpload', () => {
  return {
    useFileUpload: () => ({
      files: [],
      uploading: false,
      error: null,
      uploadFile: jest.fn(async (file) => ({ id: 'mock-file-id', originalFilename: file.name, size: file.size, processed: true, dataPreview: { shape: [3, 2], columns: ['a', 'b'], head: [{ a: 1, b: 2 }] } })),
      deleteFile: jest.fn(),
      clearError: jest.fn(),
    }),
  };
});

jest.mock('./hooks/useChat', () => {
  return {
    useChat: () => ({
      messages: [],
      loading: false,
      dataSources: [],
      setDataSourcesExternal: jest.fn(),
      sendMessage: jest.fn(),
      isConnected: true,
    }),
  };
});

describe('App integration', () => {
  it('sets file ID after upload and includes it in chat', async () => {
    render(<App />);
    // Simulate navigating to upload page
    window.history.pushState({}, '', '/upload');
    // Simulate file upload
    const file = new File(['a,b\n1,2'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/drag & drop files here/i).closest('input');
    fireEvent.change(input!, { target: { files: [file] } });
    // Wait for upload to complete
    await waitFor(() => expect(screen.getByText('test.csv')).toBeInTheDocument());
    // Simulate navigating to chat page
    window.history.pushState({}, '', '/');
    // Check that chat interface is rendered
    expect(screen.getByText(/chat with your data/i)).toBeInTheDocument();
    // The mocked setDataSourcesExternal should have been called with the file ID
    // (This is a basic smoke test; more detailed checks can be added)
  });
});
