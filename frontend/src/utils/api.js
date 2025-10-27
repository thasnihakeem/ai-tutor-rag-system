/**
 * API Utility Functions
 * Handles all backend API communications
 */

import axios from 'axios';

// Backend API base URL
const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 second timeout
});

/**
 * Send a single query to the AI
 * @param {string} question - The question to ask
 * @returns {Promise<Object>} Response with text, emotion, and sources
 */
export const sendQuery = async (question) => {
  try {
    const response = await apiClient.post('/query', { question });
    return response.data;
  } catch (error) {
    console.error('Query error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to send query');
  }
};

/**
 * Send a chat message (multi-turn conversation)
 * @param {string} message - The message to send
 * @param {string} sessionId - Optional session ID
 * @returns {Promise<Object>} Response with text, emotion, and sources
 */
export const sendChatMessage = async (message, sessionId = 'default') => {
  try {
    const response = await apiClient.post('/chat', { 
      message, 
      session_id: sessionId 
    });
    return response.data;
  } catch (error) {
    console.error('Chat error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to send message');
  }
};

/**
 * Transcribe audio to text using STT
 * @param {Blob} audioBlob - Audio file blob
 * @returns {Promise<Object>} Transcription result
 */
export const transcribeAudio = async (audioBlob) => {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    const response = await axios.post(
      `${API_BASE_URL}/transcribe`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 60000 // 60 seconds for audio processing
      }
    );

    return response.data;
  } catch (error) {
    console.error('Transcription error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to transcribe audio');
  }
};

/**
 * Check backend health status
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    return { status: 'offline', rag_ready: false };
  }
};