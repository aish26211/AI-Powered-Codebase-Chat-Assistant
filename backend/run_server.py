"""
Quick Start Script for Codebase RAG Chat Server
Run this to start the backend API
"""

import uvicorn
import sys
from pathlib import Path
from dotenv import load_dotenv 
load_dotenv()

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings, validate_api_keys

def main():
    """Start the FastAPI server"""
    print("\n" + "="*60)
    print("🚀 CODEBASE RAG CHAT - SERVER STARTUP")
    print("="*60)
    
    # Validate configuration
    print("\n🔧 Checking configuration...")
    
    if not validate_api_keys():
        print("\n❌ Missing API keys!")
        print("Please add the following to your .env file:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        print("\nGet keys from:")
        print("  Anthropic: https://console.anthropic.com/")
        return
    
    print("✅ Configuration valid")
    print(f"📁 Vector store: {settings.vector_store_path}")
    print(f"🤖 Embedding model: {settings.embedding_model}")
    
    print("\n" + "="*60)
    print("Starting server on http://localhost:8000")
    print("="*60)
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    # Start server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

if __name__ == "__main__":
    main()