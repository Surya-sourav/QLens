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
      <div className="min-h-screen bg-gray-50">
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
        
        <Header />
        
        <div className="flex">
          <Sidebar />
          
          <main className="flex-1 p-6">
            <Routes>
              {/* Pass latestFileId to ChatInterface and setLatestFileId to FileUpload */}
              <Route path="/" element={<ChatInterface latestFileId={latestFileId} />} />
              <Route path="/upload" element={<FileUpload setLatestFileId={handleFileIdUpdate} />} />
              <Route path="/database" element={<DatabaseConnection />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;