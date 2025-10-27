/**
 * Mascot Component
 * Animated avatar that displays emotions and speaks responses
 */

import React, { useEffect, useState } from 'react';
import { speakText, stopSpeaking } from '../utils/tts';
import './Mascot.css';

const Mascot = ({ emotion, isSpeaking, currentMessage, onSpeechEnd }) => {
  const [mouthOpen, setMouthOpen] = useState(false);

  // Animation for mouth movement when speaking
  useEffect(() => {
    if (isSpeaking && currentMessage?.role === 'assistant') {
      // Speak the message
      speakText(currentMessage.text, () => {
        onSpeechEnd();
      });

      // Animate mouth
      const interval = setInterval(() => {
        setMouthOpen(prev => !prev);
      }, 200);

      return () => {
        clearInterval(interval);
      };
    } else {
      setMouthOpen(false);
    }
  }, [isSpeaking, currentMessage]);

  /**
   * Handle stop speaking button
   */
  const handleStopSpeaking = () => {
    stopSpeaking();
    onSpeechEnd();
  };

  /**
   * Get emoji face based on emotion
   */
  const getFaceEmoji = () => {
    const faces = {
      happy: '😊',
      thinking: '🤔',
      explaining: '🧐',
      confused: '😕',
      neutral: '😊',
      friendly: '😄',
      encouraging: '🌟'
    };
    return faces[emotion] || '😊';
  };

  /**
   * Get color scheme based on emotion
   */
  const getEmotionColor = () => {
    const colors = {
      happy: '#4ade80',
      thinking: '#facc15',
      explaining: '#60a5fa',
      confused: '#fb923c',
      neutral: '#a78bfa',
      friendly: '#22d3ee',
      encouraging: '#f472b6'
    };
    return colors[emotion] || '#a78bfa';
  };

  return (
    <div className="mascot-container">
      <div 
        className={`mascot ${isSpeaking ? 'speaking' : ''}`}
        style={{
          borderColor: getEmotionColor(),
          boxShadow: `0 0 30px ${getEmotionColor()}40`
        }}
      >
        {/* Face */}
        <div className="mascot-face">
          <div className="mascot-eyes">
            <div className="eye left-eye"></div>
            <div className="eye right-eye"></div>
          </div>
          
          <div className={`mascot-mouth ${mouthOpen ? 'open' : ''}`}>
            {mouthOpen ? '⭕' : '—'}
          </div>
        </div>

        {/* Emoji overlay */}
        <div className="mascot-emoji">
          {getFaceEmoji()}
        </div>

        {/* Pulse effect when speaking */}
        {isSpeaking && (
          <div className="pulse-ring" style={{ borderColor: getEmotionColor() }}></div>
        )}
      </div>

      {/* Status text */}
      <div className="mascot-status">
        <p style={{ color: getEmotionColor() }}>
          {isSpeaking ? '🎤 Speaking...' : `Feeling ${emotion}`}
        </p>
      </div>

      {/* Stop button - only show when speaking */}
      {isSpeaking && (
        <button 
          className="stop-speaking-btn"
          onClick={handleStopSpeaking}
          title="Stop speaking"
        >
          ⏹️ Stop
        </button>
      )}

      {/* Emotion indicator */}
      <div className="emotion-badge" style={{ background: getEmotionColor() }}>
        {emotion}
      </div>
    </div>
  );
};

export default Mascot;