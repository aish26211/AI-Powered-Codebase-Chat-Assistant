"""
Configuration Management
This module handles all application settings and environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
   # API Keys
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(None, alias="GROQ_API_KEY")
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Vector Store Settings
    vector_store_path: Path = Path("./vectorstore")
    collection_name: str = "codebase_embeddings"
    
    # LLM Settings
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    
    # Code Parsing
    max_file_size: int = 1_000_000  # 1MB
    supported_extensions: list = [
        ".py", ".js", ".jsx", ".ts", ".tsx", 
        ".java", ".cpp", ".c", ".go", ".rs",
        ".rb", ".php", ".md", ".txt", ".json",
        ".yaml", ".yml", ".toml"
    ]
    
    # Repository Settings
    repo_path: Optional[Path] = None
    ignore_patterns: list = [
        "node_modules", "__pycache__", ".git",
        "venv", "env", "build", "dist",
        ".pytest_cache", ".vscode", ".idea"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

# Helper functions
def get_settings() -> Settings:
    """Get application settings"""
    return settings

def validate_api_keys() -> bool:
    """Check if required API keys are configured"""
    if not settings.groq_api_key and not settings.anthropic_api_key:
        print("⚠️  Warning: No API key configured!")
        print("Add GROQ_API_KEY to .env file")
        return False
    if settings.groq_api_key:
        print(f"✅ Groq API key configured (using Llama)")
    return True

if __name__ == "__main__":
    # Test configuration loading
    print("🔧 Configuration loaded successfully!")
    print(f"Embedding Model: {settings.embedding_model}")
    print(f"Chunk Size: {settings.chunk_size}")
    print(f"Vector Store: {settings.vector_store_path}")
    print(f"API Keys configured: {validate_api_keys()}")