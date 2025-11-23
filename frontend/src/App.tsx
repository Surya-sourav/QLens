import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Header from './components/Common/Header';
import Sidebar from './components/Common/Sidebar';
import ChatInterface from './components/Chat/ChatInterface';
import FileUpload from './components/Upload/FileUpload';
import DatabaseConnection from './components/Upload/DatabaseConnection';
import './index.css';

function App() {
  // State to hold the latest uploaded file ID for chat integration
  const [latestFileId, setLatestFileId] = useState<string | undefined>(undefined);

  // Initialize latestFileId from localStorage on app startup
  useEffect(() => {
    const storedFileId = localStorage.getItem('latestFileId');
    if (storedFileId) {
      console.log('Initializing latestFileId from localStorage:', storedFileId);
      setLatestFileId(storedFileId);
    }
  }, []);

  // Function to update the latest file ID
  const handleFileIdUpdate = (fileId: string) => {
    console.log('App: Updating latest file ID:', fileId);
    setLatestFileId(fileId);
    localStorage.setItem('latestFileId', fileId);
  };

  return (
    <Router>
      <div className="min-h-screen bg-gradient-primary">
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'rgba(17, 24, 39, 0.95)',
              color: '#fff',
              backdropFilter: 'blur(12px)',
              borderRadius: '0.75rem',
              padding: '1rem 1.25rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
        
        <Header />
        
        <div className="flex h-[calc(100vh-4rem)]">
          <Sidebar />
          
          <main className="flex-1 p-6 overflow-hidden">
            <div className="h-full">
              <Routes>
                {/* Pass latestFileId to ChatInterface and setLatestFileId to FileUpload */}
                <Route path="/" element={<ChatInterface latestFileId={latestFileId} />} />
                <Route path="/upload" element={<FileUpload setLatestFileId={handleFileIdUpdate} />} />
                <Route path="/database" element={<DatabaseConnection />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;