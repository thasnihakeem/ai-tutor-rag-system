/**
 * Chat Interface Component
 * Handles text input, voice input, and message display
 */

import React, { useState, useRef, useEffect } from 'react';
import { transcribeAudio } from '../utils/api';
import './ChatInterface.css';

const ChatInterface = ({ messages, onSendMessage, isLoading }) => {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Handle sending text message
   */
  const handleSendText = () => {
    if (inputText.trim() && !isLoading) {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  /**
   * Start recording audio
   */
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleAudioTranscription(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  /**
   * Stop recording audio
   */
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  /**
   * Transcribe audio to text
   */
  const handleAudioTranscription = async (audioBlob) => {
    setIsTranscribing(true);
    try {
      const result = await transcribeAudio(audioBlob);
      if (result.success) {
        setInputText(result.text);
      } else {
        alert('Could not transcribe audio: ' + result.error);
      }
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Transcription failed. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  /**
   * Toggle recording
   */
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  /**
   * Format timestamp
   */
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  /**
   * Format message text with proper HTML - removes markdown symbols
   */
  const formatMessage = (text) => {
    let formatted = text;
    
    // Convert bold text **text** to <strong>
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert headers ### to <h3> (remove ###)
    formatted = formatted.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    
    // Convert horizontal rules ---
    formatted = formatted.replace(/^---$/gm, '<hr/>');
    
    // Convert bullet points * or • to proper list items (remove the *)
    formatted = formatted.replace(/^\s*[*•]\s+(.+)$/gm, '<li>$1</li>');
    
    // Convert numbered lists 1. 2. etc
    formatted = formatted.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
    
    // Wrap consecutive <li> items in <ul> tags
    formatted = formatted.replace(/(<li>.*?<\/li>(\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
    
    // Convert double line breaks to paragraph breaks
    formatted = formatted.replace(/\n\n+/g, '</p><p>');
    
    // Convert single line breaks to <br/>
    formatted = formatted.replace(/\n/g, '<br/>');
    
    // Wrap entire content in paragraph if needed
    if (!formatted.startsWith('<')) {
      formatted = '<p>' + formatted + '</p>';
    }
    
    // Clean up any empty paragraphs
    formatted = formatted.replace(/<p><\/p>/g, '');
    
    return formatted;
  };

  return (
    <div className="chat-interface">
      {/* Messages Container */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>👋 Welcome to AI Tutor!</h2>
            <p>Ask me anything you'd like to learn. I'm here to help!</p>
            <div className="example-questions">
              <p><strong>Try asking:</strong></p>
              <button onClick={() => setInputText("What is machine learning?")}>
                What is machine learning?
              </button>
              <button onClick={() => setInputText("Explain photosynthesis")}>
                Explain photosynthesis
              </button>
              <button onClick={() => setInputText("How do I solve quadratic equations?")}>
                How do I solve quadratic equations?
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div 
              key={index} 
              className={`message ${message.role}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🎓'}
              </div>
              <div className="message-content">
                <div 
                  className="message-text"
                  dangerouslySetInnerHTML={{ 
                    __html: formatMessage(message.text) 
                  }}
                />
                <div className="message-time">{formatTime(message.timestamp)}</div>
              </div>
            </div>
          ))
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">🎓</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Container */}
      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question or click the mic to speak..."
            disabled={isLoading || isRecording || isTranscribing}
            rows="2"
          />
          
          {/* Microphone Button */}
          <button
            className={`mic-button ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            disabled={isLoading || isTranscribing}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? '⏹️' : '🎤'}
          </button>

          {/* Send Button */}
          <button
            className="send-button"
            onClick={handleSendText}
            disabled={!inputText.trim() || isLoading || isRecording || isTranscribing}
          >
            {isTranscribing ? '⏳' : '📤'}
          </button>
        </div>

        {/* Status indicators */}
        {isRecording && (
          <div className="status-indicator recording">
            🔴 Recording... Click again to stop
          </div>
        )}
        {isTranscribing && (
          <div className="status-indicator transcribing">
            ⏳ Transcribing audio...
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;