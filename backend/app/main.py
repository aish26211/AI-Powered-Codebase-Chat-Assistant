"""
FastAPI Server - REST API for Codebase RAG Chat
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from pathlib import Path

from .config import settings
from .ingestion.repo_ingestion import RepositoryIngestion
from .rag.vector_store import VectorStore
from .rag.rag_engine import RAGEngine

# Initialize FastAPI app
app = FastAPI(
    title="Codebase RAG Chat API",
    description="Chat with your codebase using RAG",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
vector_store: Optional[VectorStore] = None
rag_engine: Optional[RAGEngine] = None
indexing_status = {
    'status': 'idle',  # idle, processing, completed, error
    'progress': 0,
    'message': '',
    'files_processed': 0,
    'chunks_created': 0
}

# Pydantic models for request/response
class IngestRequest(BaseModel):
    repo_path: str
    ignore_patterns: Optional[List[str]] = None

class QueryRequest(BaseModel):
    question: str
    n_results: Optional[int] = 5

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    n_results: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]
    num_sources: int

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global vector_store, rag_engine
    
    print("\n" + "="*60)
    print("🚀 Starting Codebase RAG Chat API")
    print("="*60)
    
    try:
        vector_store = VectorStore(
            persist_directory=str(settings.vector_store_path),
            collection_name=settings.collection_name,
            embedding_model=settings.embedding_model
        )
        
        # Check for Groq first, then Anthropic
        if settings.groq_api_key:
            rag_engine = RAGEngine(
                vector_store=vector_store,
                api_key=settings.groq_api_key,
                provider="groq"
            )
        elif settings.anthropic_api_key:
            rag_engine = RAGEngine(
                vector_store=vector_store,
                api_key=settings.anthropic_api_key,
                provider="anthropic"
            )
        else:
            print("⚠️  Warning: No API key configured.")
        
        print("\n✅ API Server Ready!")
        print(f"📊 Vector Store: {vector_store.collection.count()} documents indexed")
        print("="*60 + "\n")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Codebase RAG Chat API",
        "version": "1.0.0",
        "documents_indexed": vector_store.collection.count() if vector_store else 0
    }

@app.get("/stats")
async def get_stats():
    """Get vector store statistics"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    stats = vector_store.get_statistics()
    return stats

@app.post("/ingest")
async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a repository in the background
    """
    if indexing_status['status'] == 'processing':
        raise HTTPException(
            status_code=409, 
            detail="Indexing already in progress"
        )
    
    # Validate repo path
    repo_path = Path(request.repo_path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")
    
    # Start background task
    background_tasks.add_task(
        process_repository,
        str(repo_path),
        request.ignore_patterns
    )
    
    return {
        "message": "Repository ingestion started",
        "repo_path": str(repo_path),
        "status": "processing"
    }

async def process_repository(repo_path: str, ignore_patterns: Optional[List[str]]):
    """Background task to process repository"""
    global indexing_status
    
    try:
        # Initialize ingestion
        ingestion = RepositoryIngestion(
            repo_path=repo_path,
            ignore_patterns=ignore_patterns or settings.ignore_patterns,
            supported_extensions=settings.supported_extensions
        )
        
        # Get chunks
        chunks = ingestion.ingest_repository()
        
        # Update status before vector store operation
        indexing_status['message'] = f'Creating embeddings for {len(chunks)} chunks...'
        indexing_status['progress'] = 50
        
        # Batch process chunks in smaller groups to avoid memory issues
        batch_size = 1000
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            vector_store.add_chunks(batch)
            indexing_status['progress'] = 50 + (i / len(chunks)) * 50
        
        # Update final status
        indexing_status['status'] = 'completed'
        indexing_status['progress'] = 100
        indexing_status['message'] = 'Indexing completed successfully'
        indexing_status['files_processed'] = ingestion.stats['files_processed']
        indexing_status['chunks_created'] = len(chunks)
        
    except Exception as e:
        indexing_status['status'] = 'error'
        indexing_status['message'] = f"Error: {str(e)}"
        print(f"❌ Ingestion error: {e}")

@app.get("/ingest/status")
async def get_ingestion_status():
    """Get current indexing status"""
    return indexing_status

@app.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """
    Query the codebase with a question
    """
    if not rag_engine:
        raise HTTPException(
            status_code=503,
            detail="RAG engine not initialized. Please configure API keys."
        )
    
    if vector_store.collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No code indexed. Please ingest a repository first."
        )
    
    try:
        result = rag_engine.query(
            question=request.question,
            n_results=request.n_results
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/chat")
async def chat_with_codebase(request: ChatRequest):
    """
    Multi-turn conversation with codebase context
    """
    if not rag_engine:
        raise HTTPException(
            status_code=503,
            detail="RAG engine not initialized. Please configure API keys."
        )
    
    try:
        # Convert to format expected by RAG engine
        conversation = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        result = rag_engine.chat(
            conversation_history=conversation,
            n_results=request.n_results
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/search")
async def search_code(query: str, n_results: int = 5):
    """
    Direct semantic search without LLM generation
    """
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    results = vector_store.search(query, n_results=n_results)
    return {
        "query": query,
        "results": results
    }

@app.delete("/reset")
async def reset_vector_store():
    """
    Clear all indexed data
    """
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    vector_store.clear()
    
    global indexing_status
    indexing_status = {
        'status': 'idle',
        'progress': 0,
        'message': 'Vector store cleared',
        'files_processed': 0,
        'chunks_created': 0
    }
    
    return {"message": "Vector store cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)