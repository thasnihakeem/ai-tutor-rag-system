/**
 * Text-to-Speech Utility
 * Uses Web Speech API for speaking responses
 */

// Global speech synthesis instance
let currentUtterance = null;

/**
 * Clean text for speech - remove markdown symbolsss
 */
const cleanTextForSpeech = (text) => {
  let cleaned = text;
  
  // Remove markdown formatting
  cleaned = cleaned.replace(/\*\*(.+?)\*\*/g, '$1'); // Remove ** for bold
  cleaned = cleaned.replace(/\*(.+?)\*/g, '$1');     // Remove * for italic
  cleaned = cleaned.replace(/###\s*/g, '');          // Remove ### headers
  cleaned = cleaned.replace(/##\s*/g, '');           // Remove ## headers
  cleaned = cleaned.replace(/---/g, '');             // Remove horizontal rules
  cleaned = cleaned.replace(/^\s*[*•]\s+/gm, '');    // Remove bullet points
  cleaned = cleaned.replace(/^\s*\d+\.\s+/gm, '');   // Remove numbered lists
  
  // Remove extra whitespace
  cleaned = cleaned.replace(/\n\n+/g, '. ');         // Replace double newlines with period
  cleaned = cleaned.replace(/\n/g, ' ');             // Replace single newlines with space
  cleaned = cleaned.replace(/\s+/g, ' ');            // Remove extra spaces
  cleaned = cleaned.trim();
  
  return cleaned;
};

/**
 * Speak text using browser's TTS
 * @param {string} text - Text to speak
 * @param {Function} onEnd - Callback when speech ends
 */
export const speakText = (text, onEnd) => {
  // Stop any ongoing speech
  stopSpeaking();

  // Check if speech synthesis is supported
  if (!('speechSynthesis' in window)) {
    console.warn('Speech synthesis not supported');
    if (onEnd) onEnd();
    return;
  }

  // Clean text before speaking (remove markdown symbols)
  const cleanedText = cleanTextForSpeech(text);

  // Create utterance
  currentUtterance = new SpeechSynthesisUtterance(cleanedText);
  
  // Configure voice settings
  currentUtterance.rate = 1.0;    // Speed (0.1 to 10)
  currentUtterance.pitch = 1.0;   // Pitch (0 to 2)
  currentUtterance.volume = 1.0;  // Volume (0 to 1)

  // Try to use a friendly voice
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(voice => 
    voice.lang.startsWith('en') && voice.name.includes('Female')
  ) || voices.find(voice => voice.lang.startsWith('en'));
  
  if (preferredVoice) {
    currentUtterance.voice = preferredVoice;
  }

  // Set up event handlers
  currentUtterance.onend = () => {
    currentUtterance = null;
    if (onEnd) onEnd();
  };

  currentUtterance.onerror = (event) => {
    console.error('Speech synthesis error:', event);
    currentUtterance = null;
    if (onEnd) onEnd();
  };

  // Speak the text
  window.speechSynthesis.speak(currentUtterance);
};

/**
 * Stop current speech
 */
export const stopSpeaking = () => {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  currentUtterance = null;
};

/**
 * Check if currently speaking
 * @returns {boolean} True if speaking
 */
export const isSpeaking = () => {
  return window.speechSynthesis && window.speechSynthesis.speaking;
};

// Load voices when they become available
if ('speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    const voices = window.speechSynthesis.getVoices();
    console.log('Available voices:', voices.length);
  };
}