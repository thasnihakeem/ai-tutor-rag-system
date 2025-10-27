"""
RAG Pipeline Implementation - Compatible with LangChain 0.3+
This file handles document loading, vector storage, and question answering
"""

import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import random

class RAGPipeline:
    """
    RAG (Retrieval Augmented Generation) Pipeline
    Loads documents, creates embeddings, and answers questions
    """
    
    def __init__(self, documents_path: str = "./documents", openai_api_key: str = None):
        """
        Initialize the RAG pipeline
        
        Args:
            documents_path: Path to folder containing PDF/text documents
            openai_api_key: Your OpenAI API key
        """
        self.documents_path = documents_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.vectorstore = None
        self.chain = None
        self.conversation_history = []
        
        # Initialize embeddings model (runs locally, no API key needed)
        print("Loading embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
    def load_documents(self) -> List:
        """
        Load PDF documents from the documents folder
        
        Returns:
            List of loaded documents
        """
        print(f"Loading documents from {self.documents_path}...")
        
        if not os.path.exists(self.documents_path):
            os.makedirs(self.documents_path)
            print(f"Created documents folder at {self.documents_path}")
            print("Please add PDF files to this folder!")
            return []
        
        # Load all PDFs from directory
        try:
            loader = DirectoryLoader(
                self.documents_path,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            
            documents = loader.load()
            print(f"Loaded {len(documents)} document pages")
            return documents
        except Exception as e:
            print(f"Error loading documents: {e}")
            return []
    
    def create_vector_store(self, documents: List):
        """
        Split documents and create vector embeddings
        
        Args:
            documents: List of loaded documents
        """
        if not documents:
            print("No documents to process!")
            return
        
        # Split documents into chunks
        print("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        print(f"Created {len(texts)} text chunks")
        
        # Create vector store with embeddings
        print("Creating vector embeddings (this may take a minute)...")
        self.vectorstore = FAISS.from_documents(texts, self.embeddings)
        print("Vector store created successfully!")
        
    def setup_qa_chain(self):
        """
        Setup the Question-Answering chain with LLM using LCEL
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Run create_vector_store first!")
        
        # Custom prompt template for the tutor
        prompt_template = """You are a friendly and helpful AI tutor. Use the following context to answer the student's question.
        If you don't know the answer, say so honestly. Always be encouraging and supportive.
        
        Context: {context}
        
        Question: {question}
        
        Helpful Answer:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Initialize LLM (using OpenAI GPT)
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=self.openai_api_key
        )
        
        # Create retriever
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Create chain using LCEL (LangChain Expression Language)
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        self.retriever = retriever
        
        print("QA Chain setup complete!")
    
    def determine_emotion(self, question: str, answer: str) -> str:
        """
        Determine emotion based on question and answer
        
        Args:
            question: User's question
            answer: AI's answer
            
        Returns:
            Emotion state string
        """
        # Simple emotion detection logic
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
        Answer a single question using RAG
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer and emotion
        """
        if not self.chain:
            return {
                "text": "I'm not ready yet! Please wait for the system to initialize.",
                "emotion": "confused"
            }
        
        try:
            # Get answer from RAG chain
            answer = self.chain.invoke(question)
            
            # Get source documents
            source_docs = self.retriever.invoke(question)
            
            # Determine emotion
            emotion = self.determine_emotion(question, answer)
            
            return {
                "text": answer,
                "emotion": emotion,
                "sources": len(source_docs)
            }
            
        except Exception as e:
            print(f"Error in query: {e}")
            return {
                "text": f"I encountered an error: {str(e)}",
                "emotion": "confused"
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
        """
        print("="*50)
        print("Initializing AI Tutor RAG Pipeline")
        print("="*50)
        
        # Load documents
        documents = self.load_documents()
        
        if documents:
            # Create vector store
            self.create_vector_store(documents)
            
            # Setup QA chain
            self.setup_qa_chain()
            
            print("="*50)
            print("RAG Pipeline Ready!")
            print("="*50)
        else:
            print("WARNING: No documents loaded. Add PDFs to the documents folder!")


# Test function
if __name__ == "__main__":
    # Test the pipeline
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    # Test query
    if pipeline.chain:
        response = pipeline.query("What is machine learning?")
        print(f"\nQuestion: What is machine learning?")
        print(f"Answer: {response['text']}")
        print(f"Emotion: {response['emotion']}")