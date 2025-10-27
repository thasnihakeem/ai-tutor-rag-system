"""
FastAPI Backend Server for AI Tutor
Provides REST API endpoints for RAG-powered chat and speech services
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import openai
from backend.rag_pipeline_old import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Tutor API",
    description="Conversational RAG-powered AI tutor with speech capabilities",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_pipeline: Optional[RAGPipeline] = None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Single query request model"""
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is machine learning?"
            }
        }


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Multi-turn chat request model"""
    message: str
    history: Optional[List[ChatMessage]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can you explain neural networks?",
                "history": [
                    {"role": "user", "content": "What is AI?"},
                    {"role": "assistant", "content": "AI is..."}
                ]
            }
        }


class ResponseModel(BaseModel):
    """API response model"""
    text: str
    emotion: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Machine learning is a subset of AI...",
                "emotion": "explaining"
            }
        }


class TranscribeRequest(BaseModel):
    """Speech transcription request"""
    audio_base64: str


# Startup event - Initialize RAG pipeline
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG pipeline when server starts"""
    global rag_pipeline
    
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
        print("⚠️  Please create a .env file with your OpenAI API key")
        return
    
    try:
        print("🚀 Initializing RAG pipeline...")
        rag_pipeline = create_rag_pipeline(OPENAI_API_KEY)
        print("✅ Server ready!")
    except Exception as e:
        print(f"❌ Error initializing RAG pipeline: {e}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "AI Tutor API is running!",
        "status": "online",
        "endpoints": {
            "query": "/query",
            "chat": "/chat",
            "speech-to-text": "/speech-to-text",
            "text-to-speech": "/text-to-speech"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_pipeline_ready": rag_pipeline is not None
    }


# POST /query - Single query endpoint
@app.post("/query", response_model=ResponseModel)
async def query_endpoint(request: QueryRequest):
    """
    Answer a single query using RAG
    
    Args:
        request: QueryRequest with question
        
    Returns:
        ResponseModel with answer text and emotion
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check OpenAI API key."
        )
    
    try:
        # Get answer from RAG pipeline
        result = rag_pipeline.query(request.question)
        
        return ResponseModel(
            text=result["answer"],
            emotion=result["emotion"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# POST /chat - Multi-turn conversation endpoint
@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: ChatRequest):
    """
    Handle multi-turn conversation using RAG
    
    Args:
        request: ChatRequest with current message and history
        
    Returns:
        ResponseModel with answer text and emotion
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check OpenAI API key."
        )
    
    try:
        # Convert history to format expected by RAG pipeline
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
        
        # Get answer from RAG pipeline
        result = rag_pipeline.chat(request.message, conversation_history)
        
        return ResponseModel(
            text=result["answer"],
            emotion=result["emotion"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


# POST /speech-to-text - Transcribe audio to text
@app.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Transcribe audio to text using OpenAI Whisper
    
    Args:
        audio_file: Audio file (webm, mp3, wav, etc.)
        
    Returns:
        Dictionary with transcribed text
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured"
        )
    
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Save temporarily
        temp_file = "temp_audio.webm"
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # Transcribe using OpenAI Whisper
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        with open(temp_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="en"
            )
        
        # Clean up temp file
        os.remove(temp_file)
        
        return {
            "text": transcript.text,
            "success": True
        }
    
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists("temp_audio.webm"):
            os.remove("temp_audio.webm")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )


# POST /text-to-speech - Convert text to speech
@app.post("/text-to-speech")
async def text_to_speech(text: str):
    """
    Convert text to speech using OpenAI TTS
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio URL or base64 encoded audio
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured"
        )
    
    try:
        # Generate speech using OpenAI TTS
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Options: alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        # Save to temporary file
        temp_file = "temp_speech.mp3"
        response.stream_to_file(temp_file)
        
        # Read and encode as base64
        import base64
        with open(temp_file, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()
        
        # Clean up
        os.remove(temp_file)
        
        return {
            "audio_base64": audio_data,
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating speech: {str(e)}"
        )


# DELETE /reset - Reset conversation
@app.delete("/reset")
async def reset_conversation():
    """Reset the conversation memory"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized"
        )
    
    try:
        rag_pipeline.reset_conversation()
        return {"message": "Conversation reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting conversation: {str(e)}"
        )


# Run the server
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🎓 AI TUTOR BACKEND SERVER")
    print("=" * 50)
    print("\n📝 Before starting, make sure you have:")
    print("   1. Created a .env file with OPENAI_API_KEY")
    print("   2. Installed all dependencies: pip install -r requirements.txt")
    print("\n🚀 Starting server on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    print("\n" + "=" * 50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)