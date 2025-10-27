"""
RAG Pipeline Implementation - 100% FREE using Google Gemini
Works with OR without PDF documents!
"""

import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import random


class RAGPipeline:
    """
    RAG (Retrieval Augmented Generation) Pipeline
    Uses Google Gemini API (100% FREE - No credit card required!)
    Works with or without PDF documents - uses Gemini's knowledge as fallback
    """
    
    def __init__(self, documents_path: str = "./documents", google_api_key: str = None):
        """
        Initialize the RAG pipeline
        
        Args:
            documents_path: Path to folder containing PDF/text documents (optional)
            google_api_key: Your Google Gemini API key (FREE from Google AI Studio)
        """
        self.documents_path = documents_path
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.vectorstore = None
        self.chain = None
        self.simple_chain = None  # For when no documents are available
        self.conversation_history = []
        self.has_documents = False
        
        if not self.google_api_key:
            print("⚠️  WARNING: GOOGLE_API_KEY not found!")
            print("Get your FREE API key from: https://makersuite.google.com/app/apikey")
            print("No credit card needed!")
            return
        
        # Initialize LLM first (works without documents)
        print("Initializing Google Gemini LLM (FREE)...")
        try:
            # Try different model names until one works
            for model_name in [        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro-preview-06-05",
        "models/gemini-2.0-flash"]:
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=0.7,
                        google_api_key=self.google_api_key,
                        convert_system_message_to_human=True
                    )
                    print(f"✓ Using model: {model_name}")
                    break
                except Exception as e:
                    print(f"Trying next model... ({model_name} failed)")
                    continue
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            self.llm = None
            return
        
        # Initialize embeddings (only if we'll use documents)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.google_api_key
        )
        
    def load_documents(self) -> List:
        """
        Load PDF documents from the documents folder (optional)
        
        Returns:
            List of loaded documents (empty list if none found)
        """
        print(f"Loading documents from {self.documents_path}...")
        
        if not os.path.exists(self.documents_path):
            os.makedirs(self.documents_path)
            print(f"Created documents folder at {self.documents_path}")
            print("ℹ️  No documents found - will use Gemini's built-in knowledge")
            return []
        
        # Load all PDFs from directory
        try:
            loader = DirectoryLoader(
                self.documents_path,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            
            documents = loader.load()
            if documents:
                print(f"✓ Loaded {len(documents)} document pages")
                self.has_documents = True
            else:
                print("ℹ️  No PDF documents found - will use Gemini's built-in knowledge")
            return documents
        except Exception as e:
            print(f"Note: {e}")
            print("ℹ️  Will use Gemini's built-in knowledge instead")
            return []
    
    def create_vector_store(self, documents: List):
        """
        Split documents and create vector embeddings (only if documents exist)
        
        Args:
            documents: List of loaded documents
        """
        if not documents:
            print("No documents to process - skipping vector store creation")
            return
        
        # Split documents into chunks
        print("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        print(f"✓ Created {len(texts)} text chunks")
        
        # Create vector store with embeddings
        print("Creating vector embeddings with Google API...")
        try:
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
            print("✓ Vector store created successfully!")
        except Exception as e:
            print(f"Error creating vector store: {e}")
            print("Will use Gemini's built-in knowledge instead")
            self.vectorstore = None
        
    def setup_qa_chain(self):
        """
        Setup the Question-Answering chain
        Creates both RAG chain (with docs) and simple chain (without docs)
        """
        # Simple chain without RAG (uses Gemini's knowledge directly)
        simple_prompt = PromptTemplate(
            template="""You are a friendly and helpful AI tutor. Answer the student's question in a clear, structured, and engaging way.

Use this format for your answers:
- Start with a direct answer to the question
- Use bullet points (•) for lists and key points
- Use clear paragraphs for explanations
- Include relevant examples when helpful
- Keep your tone warm and encouraging
- Use emojis sparingly and appropriately

Question: {question}

Helpful Answer:""",
            input_variables=["question"]
        )
        
        self.simple_chain = (
            {"question": RunnablePassthrough()}
            | simple_prompt
            | self.llm
            | StrOutputParser()
        )
        
        # RAG chain with documents (only if vectorstore exists)
        if self.vectorstore:
            rag_prompt = PromptTemplate(
                template="""You are a friendly and helpful AI tutor. Use the following context from the documents to answer the student's question.
                If the context doesn't contain the answer, use your general knowledge. Always be encouraging and supportive.
                
                Context: {context}
                
                Question: {question}
                
                Helpful Answer:""",
                input_variables=["context", "question"]
            )
            
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            self.chain = (
                {
                    "context": retriever | format_docs,
                    "question": RunnablePassthrough()
                }
                | rag_prompt
                | self.llm
                | StrOutputParser()
            )
            
            self.retriever = retriever
            print("✓ RAG Chain with documents setup complete!")
        else:
            self.chain = self.simple_chain
            print("✓ Simple Chain (without documents) setup complete!")
    
    def determine_emotion(self, question: str, answer: str) -> str:
        """
        Determine emotion based on question and answer
        
        Args:
            question: User's question
            answer: AI's answer
            
        Returns:
            Emotion state string
        """
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Thinking emotions
        if any(word in question_lower for word in ["how", "why", "explain", "what is"]):
            return "thinking"
        
        # Happy emotions
        if any(word in answer_lower for word in ["great", "excellent", "wonderful", "correct"]):
            return "happy"
        
        # Explaining emotions
        if len(answer) > 200 or "because" in answer_lower:
            return "explaining"
        
        # Confused emotions
        if any(phrase in answer_lower for phrase in ["don't know", "unclear", "not sure"]):
            return "confused"
        
        # Default neutral
        emotions = ["neutral", "friendly", "encouraging"]
        return random.choice(emotions)
    
    def query(self, question: str) -> Dict:
        """
        Answer a single question using RAG (if documents exist) or Gemini directly
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer and emotion
        """
        if not self.chain:
            return {
                "text": "I'm not ready yet! Please wait for the system to initialize.",
                "emotion": "confused",
                "sources": 0
            }
        
        try:
            # Get answer from chain (RAG or simple)
            answer = self.chain.invoke(question)
            
            # Get source count (only if using RAG)
            source_count = 0
            if self.has_documents and self.retriever:
                try:
                    source_docs = self.retriever.invoke(question)
                    source_count = len(source_docs)
                except:
                    source_count = 0
            
            # Determine emotion
            emotion = self.determine_emotion(question, answer)
            
            return {
                "text": answer,
                "emotion": emotion,
                "sources": source_count
            }
            
        except Exception as e:
            print(f"Error in query: {e}")
            return {
                "text": f"I encountered an error: {str(e)}. Make sure your GOOGLE_API_KEY is valid.",
                "emotion": "confused",
                "sources": 0
            }
    
    def chat(self, message: str, session_id: str = "default") -> Dict:
        """
        Multi-turn conversation with context
        
        Args:
            message: User's message
            session_id: Session identifier for conversation tracking
            
        Returns:
            Dictionary with response and emotion
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Get response using query
        response = self.query(message)
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response["text"]
        })
        
        # Keep only last 10 messages
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return response
    
    def initialize(self):
        """
        Complete initialization of the RAG pipeline
        Works with or without documents!
        """
        print("="*50)
        print("🚀 Initializing AI Tutor (FREE)")
        print("="*50)
        
        if not self.google_api_key:
            print("❌ Cannot initialize without GOOGLE_API_KEY")
            return
        
        # Load documents (optional)
        documents = self.load_documents()
        
        # Create vector store only if we have documents
        if documents:
            self.create_vector_store(documents)
        
        # Setup chain (works with or without documents)
        self.setup_qa_chain()
        
        print("="*50)
        if self.has_documents:
            print("✅ RAG Pipeline Ready with Documents!")
        else:
            print("✅ AI Tutor Ready (Using Gemini's Knowledge)!")
        print("="*50)


# Test function
if __name__ == "__main__":
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    if pipeline.chain:
        response = pipeline.query("What is machine learning?")
        print(f"\n❓ Question: What is machine learning?")
        print(f"💬 Answer: {response['text']}")
        print(f"😊 Emotion: {response['emotion']}")