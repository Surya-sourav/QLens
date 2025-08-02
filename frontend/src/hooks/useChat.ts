import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { WebSocketService } from '../services/websocket';
import { ChatMessage } from '../types';
import toast from 'react-hot-toast';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataSources, setDataSources] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [wsService] = useState(() => new WebSocketService());

  // Function to get the latest file ID from backend
  const getLatestFileId = useCallback(async (): Promise<string | null> => {
    try {
      const files = await apiService.getUploadedFiles();
      console.log('Files from API:', files);
      if (files && files.length > 0) {
        // Return the most recent file (first in the list)
        const latestFile = files[0];
        console.log('Latest file from backend:', latestFile.id);
        
        // Update localStorage with the new file ID
        localStorage.setItem('latestFileId', latestFile.id);
        
        return latestFile.id;
      }
    } catch (error) {
      console.error('Error fetching latest file:', error);
    }
    return null;
  }, []);

  // Function to get effective data sources (ALWAYS prioritize backend, never localStorage)
  const getEffectiveDataSources = useCallback(async (): Promise<string[]> => {
    // ALWAYS try to get the latest file from backend first
    const latestFileId = await getLatestFileId();
    if (latestFileId) {
      console.log('Using latest file ID from backend:', latestFileId);
      return [latestFileId];
    }
    
    // If backend doesn't have files, clear localStorage and return empty
    console.log('No files in backend, clearing localStorage');
    localStorage.removeItem('latestFileId');
    return [];
  }, [getLatestFileId]);

  // Initialize data sources on mount and refresh periodically
  useEffect(() => {
    const initializeDataSources = async () => {
      // Clear any stale localStorage first
      const oldFileId = localStorage.getItem('latestFileId');
      if (oldFileId) {
        console.log('Clearing old localStorage file ID:', oldFileId);
        localStorage.removeItem('latestFileId');
      }
      
      const effectiveSources = await getEffectiveDataSources();
      if (effectiveSources.length > 0) {
        setDataSources(effectiveSources);
        console.log('Initialized data sources:', effectiveSources);
      } else {
        // Clear localStorage if no files found
        localStorage.removeItem('latestFileId');
        console.log('No files found, cleared localStorage');
      }
    };
    
    initializeDataSources();
    
    // Refresh data sources every 10 seconds to catch new uploads
    const interval = setInterval(initializeDataSources, 10000);
    
    return () => clearInterval(interval);
  }, [getEffectiveDataSources]);

  const setDataSourcesExternal = useCallback((sources: string[]) => {
    setDataSources(sources);
    console.log('Data sources set externally:', sources);
  }, []);

  const addDataSource = useCallback((sourceId: string) => {
    setDataSources(prev => {
      if (!prev.includes(sourceId)) {
        const newSources = [...prev, sourceId];
        console.log('Added data source:', sourceId, 'New sources:', newSources);
        return newSources;
      }
      return prev;
    });
  }, []);

  const removeDataSource = useCallback((sourceId: string) => {
    setDataSources(prev => {
      const newSources = prev.filter(id => id !== sourceId);
      console.log('Removed data source:', sourceId, 'New sources:', newSources);
      return newSources;
    });
  }, []);

  const createNewSession = useCallback(() => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
    setMessages([]);
    console.log('Created new session:', newSessionId);
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    // ALWAYS get fresh data sources before sending (don't rely on state)
    console.log('Getting fresh data sources before sending message...');
    const freshSources = await getEffectiveDataSources();
    
    console.log('Fresh data sources:', freshSources);
    console.log('Current dataSources state:', dataSources);
    
    // Use fresh sources if available, otherwise use current state
    const sourcesToUse = freshSources.length > 0 ? freshSources : dataSources;
    
    console.log('Final sources to use:', sourcesToUse);
    
    if (sourcesToUse.length === 0) {
      toast.error('No data files available. Please upload a file first.');
      return;
    }
    
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: message,
      messageType: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      console.log('Sending chat message with data_sources:', sourcesToUse);
      
      const response = await apiService.sendMessage({
        message,
        sessionId: sessionId || undefined,
        data_sources: sourcesToUse,  // FIXED: Use data_sources to match backend schema
      });

      const assistantMessage: ChatMessage = {
        id: response.messageId,
        content: response.content,
        messageType: 'assistant',
        timestamp: response.timestamp,
        chartData: response.chartData,
        chartType: response.chartType,
        chartCode: response.chartCode,
        metadata: response.metadata,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update data sources if they changed
      if (sourcesToUse.length > 0 && JSON.stringify(sourcesToUse) !== JSON.stringify(dataSources)) {
        setDataSources(sourcesToUse);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
      
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        messageType: 'assistant',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [sessionId, dataSources, getEffectiveDataSources]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = async () => {
      if (!sessionId) return;

      try {
        await wsService.connect(sessionId);
        setIsConnected(true);
        
        wsService.on('message', (data) => {
          console.log('WebSocket message received:', data);
          // Handle real-time messages if needed
        });
        
        wsService.on('error', (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        });
        
        wsService.on('close', () => {
          console.log('WebSocket connection closed');
          setIsConnected(false);
        });
        
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      wsService.disconnect();
    };
  }, [sessionId, wsService]);

  // Initialize session on mount
  useEffect(() => {
    if (!sessionId) {
      createNewSession();
    }
  }, [sessionId, createNewSession]);

  return {
    messages,
    loading,
    dataSources,
    setDataSourcesExternal,
    addDataSource,
    removeDataSource,
    sendMessage,
    createNewSession,
    isConnected,
    sessionId,
  };
};
