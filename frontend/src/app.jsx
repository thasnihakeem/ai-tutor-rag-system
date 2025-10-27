/**
 * Main App Component
 * Manages the overall application state and layout
 */

import React, { useState } from 'react';
import Mascot from './components/Mascot';
import ChatInterface from './components/ChatInterface';
import { sendChatMessage } from './utils/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [currentEmotion, setCurrentEmotion] = useState('neutral');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handle sending a message to the AI tutor
   */
  const handleSendMessage = async (messageText) => {
    // Add user message to chat
    const userMessage = {
      role: 'user',
      text: messageText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call backend API
      const response = await sendChatMessage(messageText);
      
      // Add AI response to chat
      const aiMessage = {
        role: 'assistant',
        text: response.text,
        emotion: response.emotion,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
      
      // Update mascot emotion
      setCurrentEmotion(response.emotion);
      
      // Trigger speech
      setIsSpeaking(true);
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        text: 'Sorry, I encountered an error. Please try again.',
        emotion: 'confused',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setCurrentEmotion('confused');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle when mascot finishes speaking
   */
  const handleSpeechEnd = () => {
    setIsSpeaking(false);
    setCurrentEmotion('neutral');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎓 AI Tutor</h1>
        <p>Your friendly learning companion</p>
      </header>

      <div className="app-content">
        {/* Mascot Section */}
        <div className="mascot-section">
          <Mascot 
            emotion={currentEmotion}
            isSpeaking={isSpeaking}
            currentMessage={messages[messages.length - 1]}
            onSpeechEnd={handleSpeechEnd}
          />
        </div>

        {/* Chat Section */}
        <div className="chat-section">
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

export default App;