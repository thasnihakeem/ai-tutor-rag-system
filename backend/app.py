"""
FastAPI Backend Server for AI Tutor - 100% FREE VERSION
Uses Google Gemini (FREE) instead of OpenAI
All requirements met with zero cost!
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import speech_recognition as sr
from io import BytesIO
from rag_pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Tutor API - FREE VERSION",
    description="Conversational RAG-powered AI tutor with Google Gemini (100% FREE!)",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_pipeline: Optional[RAGPipeline] = None
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


# Pydantic models
class QueryRequest(BaseModel):
    """Single query request model"""
    question: str


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Multi-turn chat request model"""
    message: str
    session_id: Optional[str] = "default"


class ResponseModel(BaseModel):
    """API response model"""
    text: str
    emotion: str
    sources: Optional[int] = 0


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG pipeline when server starts"""
    global rag_pipeline
    
    if not GOOGLE_API_KEY:
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables")
        print("⚠️  Get your FREE key from: https://makersuite.google.com/app/apikey")
        print("⚠️  No credit card required!")
        return
    
    try:
        print("🚀 Initializing RAG pipeline with Google Gemini (FREE)...")
        rag_pipeline = RAGPipeline(
            documents_path="./documents",
            google_api_key=GOOGLE_API_KEY
        )
        rag_pipeline.initialize()
        print("✅ Server ready!")
    except Exception as e:
        print(f"❌ Error initializing RAG pipeline: {e}")


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "AI Tutor API is running! (100% FREE with Google Gemini)",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "query": "POST /query - Single question",
            "chat": "POST /chat - Multi-turn conversation",
            "transcribe": "POST /transcribe - Speech to text",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_pipeline_ready": rag_pipeline is not None and rag_pipeline.chain is not None,
        "api_type": "Google Gemini (FREE)"
    }


@app.post("/query", response_model=ResponseModel)
async def query_endpoint(request: QueryRequest):
    """
    POST /query - Answer a single query using RAG
    
    Requirements Met:
    - ✓ RAG pipeline with LangChain + Vector DB
    - ✓ Returns text + emotion state
    
    Args:
        request: QueryRequest with question
        
    Returns:
        ResponseModel with answer, emotion, and source count
    """
    if not rag_pipeline or not rag_pipeline.chain:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check GOOGLE_API_KEY and documents folder."
        )
    
    try:
        result = rag_pipeline.query(request.question)
        
        return ResponseModel(
            text=result["text"],
            emotion=result["emotion"],
            sources=result.get("sources", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: ChatRequest):
    """
    POST /chat - Multi-turn conversation using RAG
    
    Requirements Met:
    - ✓ Multi-turn conversation support
    - ✓ Returns text + emotion state
    - ✓ Maintains context across messages
    
    Args:
        request: ChatRequest with message and session_id
        
    Returns:
        ResponseModel with answer, emotion, and source count
    """
    if not rag_pipeline or not rag_pipeline.chain:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check GOOGLE_API_KEY and documents folder."
        )
    
    try:
        result = rag_pipeline.chat(request.message, request.session_id)
        
        return ResponseModel(
            text=result["text"],
            emotion=result["emotion"],
            sources=result.get("sources", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    POST /transcribe - Speech-to-Text using Google Speech Recognition (FREE)
    Simplified version without audio conversion
    
    Args:
        audio: Audio file (preferably WAV format)
        
    Returns:
        Dictionary with transcribed text
    """
    import tempfile
    import os
    
    temp_file = None
    
    try:
        # Read audio file
        audio_data = await audio.read()
        content_type = audio.content_type or "audio/webm"
        
        print(f"📥 Received audio: {len(audio_data)} bytes, type: {content_type}")
        
        # Determine file extension
        if "wav" in content_type.lower():
            suffix = '.wav'
        elif "webm" in content_type.lower():
            suffix = '.webm'
        elif "ogg" in content_type.lower():
            suffix = '.ogg'
        else:
            suffix = '.wav'  # Default
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        print(f"💾 Saved to: {temp_filename}")
        
        # Initialize speech recognizer with adjusted settings
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        
        # Try to recognize the audio
        try:
            with sr.AudioFile(temp_filename) as source:
                print("🎧 Loading audio file...")
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                # Record the audio
                audio_content = recognizer.record(source)
                print("✅ Audio loaded successfully")
            
            # Use Google Speech Recognition (FREE!)
            print("🗣️ Transcribing with Google Speech Recognition...")
            text = recognizer.recognize_google(audio_content, language='en-US')
            
            print(f"✅ Transcribed: '{text}'")
            
            # Clean up
            os.unlink(temp_filename)
            
            return {
                "success": True,
                "text": text
            }
            
        except ValueError as ve:
            print(f"❌ Audio format error: {ve}")
            os.unlink(temp_filename)
            
            return {
                "success": False,
                "error": "Audio format not supported. Please use WAV format or check your browser settings."
            }
            
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            os.unlink(temp_filename)
            
            return {
                "success": False,
                "error": "Could not understand audio. Please speak clearly and try again."
            }
            
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            os.unlink(temp_filename)
            
            return {
                "success": False,
                "error": "Speech recognition service temporarily unavailable. Please try again."
            }
        
    except Exception as e:
        print(f"❌ Transcription error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up if file exists
        if temp_file and os.path.exists(temp_filename):
            os.unlink(temp_filename)
        
        return {
            "success": False,
            "error": f"Error processing audio: {str(e)}"
        }


@app.get("/emotions")
async def get_emotions():
    """Get available emotion states"""
    return {
        "emotions": [
            "happy",
            "thinking", 
            "explaining",
            "confused",
            "neutral",
            "friendly",
            "encouraging"
        ]
    }


@app.delete("/reset")
async def reset_conversation():
    """Reset conversation memory"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized"
        )
    
    try:
        rag_pipeline.conversation_history = []
        return {
            "success": True,
            "message": "Conversation reset successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting conversation: {str(e)}"
        )


# Run the server
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🎓 AI TUTOR BACKEND SERVER - 100% FREE VERSION")
    print("=" * 60)
    print("\n✅ FREE Features:")
    print("   • Google Gemini LLM (no credit card needed!)")
    print("   • Google Speech Recognition (STT)")
    print("   • RAG with FAISS Vector DB")
    print("   • Multi-turn conversations")
    print("   • Emotion detection")
    print("\n📝 Setup Instructions:")
    print("   1. Get FREE Google API key: https://makersuite.google.com/app/apikey")
    print("   2. Create .env file: GOOGLE_API_KEY=your-key-here")
    print("   3. Add PDF documents to ./documents/ folder")
    print("\n🚀 Starting server on http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)