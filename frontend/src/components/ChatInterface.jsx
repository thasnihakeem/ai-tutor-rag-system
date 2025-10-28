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
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000
        } 
      });
      
      // Use the best available format
      let options = { mimeType: 'audio/webm' };
      
      // Try to use WAV if supported
      if (MediaRecorder.isTypeSupported('audio/wav')) {
        options = { mimeType: 'audio/wav' };
      } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options = { mimeType: 'audio/webm;codecs=opus' };
      }
      
      const mediaRecorder = new MediaRecorder(stream, options);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });
        
        // Convert to WAV in browser before sending
        await convertToWavAndTranscribe(audioBlob, stream);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  /**
   * Convert audio to WAV format and transcribe
   */
  const convertToWavAndTranscribe = async (audioBlob, stream) => {
    try {
      // Create audio context
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
      
      // Convert blob to array buffer
      const arrayBuffer = await audioBlob.arrayBuffer();
      
      // Decode audio data
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Convert to WAV
      const wavBlob = audioBufferToWav(audioBuffer);
      
      // Send WAV file to backend
      await handleAudioTranscription(wavBlob);
      
      // Stop all tracks
      stream.getTracks().forEach(track => track.stop());
      
    } catch (error) {
      console.error('Error converting audio:', error);
      alert('Error processing audio. Please try again.');
      stream.getTracks().forEach(track => track.stop());
    }
  };

  /**
   * Convert AudioBuffer to WAV Blob
   */
  const audioBufferToWav = (audioBuffer) => {
    const numChannels = 1; // Mono
    const sampleRate = audioBuffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;
    
    const channelData = audioBuffer.getChannelData(0);
    const samples = new Int16Array(channelData.length);
    
    // Convert float samples to 16-bit PCM
    for (let i = 0; i < channelData.length; i++) {
      const sample = Math.max(-1, Math.min(1, channelData[i]));
      samples[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    }
    
    // Create WAV file
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    
    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * bitDepth / 8, true);
    view.setUint16(32, numChannels * bitDepth / 8, true);
    view.setUint16(34, bitDepth, true);
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);
    
    // Write PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
      view.setInt16(offset, samples[i], true);
      offset += 2;
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
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