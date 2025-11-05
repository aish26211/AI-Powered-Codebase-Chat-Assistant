"""
Vector Store - Manage embeddings and semantic search
Uses ChromaDB for vector storage and retrieval
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from pathlib import Path
import json
import uuid

from ..ingestion.code_parser import CodeChunk

class VectorStore:
    """Manage code embeddings and semantic search"""
    
    def __init__(
        self,
        persist_directory: str = "./vectorstore",
        collection_name: str = "codebase_embeddings",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize vector store
        
        Args:
            persist_directory: Where to store the vector database
            collection_name: Name of the collection
            embedding_model: Model to use for embeddings
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print(f"🔧 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"✅ Vector store initialized: {self.collection.count()} documents")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def prepare_chunk_for_storage(self, chunk: CodeChunk) -> Dict:
        """
        Prepare a code chunk for storage
        
        Args:
            chunk: CodeChunk object
            
        Returns:
            Dictionary with id, content, embedding, and metadata
        """
        # Create unique ID
        chunk_id = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
        
        # Prepare content for embedding
        # Include file path context for better retrieval
        embedding_text = f"""
File: {chunk.file_path}
Type: {chunk.chunk_type}
Language: {chunk.language}

{chunk.content}
        """.strip()
        
        # Create embedding
        embedding = self.create_embedding(embedding_text)
        
        # Prepare metadata
        metadata = {
            'file_path': chunk.file_path,
            'start_line': chunk.start_line,
            'end_line': chunk.end_line,
            'language': chunk.language,
            'chunk_type': chunk.chunk_type,
            **chunk.metadata  # Include all additional metadata
        }
        
        return {
            'id': chunk_id,
            'content': chunk.content,
            'embedding': embedding,
            'metadata': metadata
        }
    
    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """Add code chunks to vector store"""
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            texts.append(chunk.content)
            # Generate a unique ID for each chunk
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            
            # Ensure all metadata values are strings
            metadata = {
                "file_path": str(chunk.file_path),
                "start_line": str(chunk.start_line),
                "end_line": str(chunk.end_line)
            }
            metadatas.append(metadata)
        
        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Error adding chunks to vector store: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search for relevant code chunks
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant code chunks with metadata
        """
        # Create query embedding
        query_embedding = self.create_embedding(query)
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return formatted_results
    
    def search_by_file(self, file_path: str, n_results: int = 10) -> List[Dict]:
        """
        Search for all chunks from a specific file
        
        Args:
            file_path: Path to file
            n_results: Maximum number of results
            
        Returns:
            List of chunks from the file
        """
        return self.search(
            query=f"Show code from {file_path}",
            n_results=n_results,
            filter_metadata={'file_path': file_path}
        )
    
    def get_statistics(self) -> Dict:
        """Get statistics about the vector store"""
        total_docs = self.collection.count()
        
        # Get sample of metadata to analyze
        if total_docs > 0:
            sample = self.collection.get(limit=min(100, total_docs))
            
            # Count languages
            languages = {}
            file_types = {}
            
            for metadata in sample['metadatas']:
                lang = metadata.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
                
                chunk_type = metadata.get('chunk_type', 'unknown')
                file_types[chunk_type] = file_types.get(chunk_type, 0) + 1
        else:
            languages = {}
            file_types = {}
        
        return {
            'total_chunks': total_docs,
            'languages': languages,
            'chunk_types': file_types,
            'collection_name': self.collection_name,
            'persist_directory': str(self.persist_directory)
        }
    
    def clear(self):
        """Clear all data from the vector store"""
        print("⚠️  Clearing vector store...")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("✅ Vector store cleared")


# Test the vector store
if __name__ == "__main__":
    from ..ingestion.code_parser import CodeChunk
    
    # Initialize vector store
    vs = VectorStore(persist_directory="./test_vectorstore")
    
    # Create sample chunks
    sample_chunks = [
        CodeChunk(
            content="def authenticate_user(username, password):\n    return check_credentials(username, password)",
            file_path="auth/login.py",
            start_line=10,
            end_line=12,
            language="python",
            chunk_type="function",
            metadata={'name': 'authenticate_user'}
        ),
        CodeChunk(
            content="async function fetchUserData(userId) {\n    const response = await api.get(`/users/${userId}`);\n    return response.data;\n}",
            file_path="api/users.js",
            start_line=5,
            end_line=9,
            language="javascript",
            chunk_type="function",
            metadata={'name': 'fetchUserData'}
        )
    ]
    
    # Add chunks
    vs.add_chunks(sample_chunks)
    
    # Search
    results = vs.search("How do I authenticate a user?", n_results=2)
    print("\n🔍 Search results:")
    for result in results:
        print(f"\n{result['metadata']['file_path']} (score: {result['similarity_score']:.3f})")
        print(result['content'][:100] + "...")
    
    # Statistics
    stats = vs.get_statistics()
    print(f"\n📊 Statistics: {json.dumps(stats, indent=2)}")