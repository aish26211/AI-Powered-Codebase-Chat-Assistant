"""
Complete System Test
Tests all components of the RAG system
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

def test_config():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("TEST 1: Configuration")
    print("="*60)
    
    from app.config import settings, validate_api_keys
    
    print(f"✓ Chunk size: {settings.chunk_size}")
    print(f"✓ Embedding model: {settings.embedding_model}")
    print(f"✓ Vector store path: {settings.vector_store_path}")
    
    if validate_api_keys():
        print("✓ API keys configured")
    else:
        print("⚠ API keys not configured (needed for queries)")
    
    print("✅ Configuration test passed")

def test_code_parser():
    """Test code parsing"""
    print("\n" + "="*60)
    print("TEST 2: Code Parser")
    print("="*60)
    
    from app.ingestion.code_parser import CodeParser
    
    parser = CodeParser()
    
    # Test Python code
    test_code = '''
def hello_world():
    """A simple function"""
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
'''
    
    chunks = parser.parse_file("test.py", test_code)
    
    print(f"✓ Parsed {len(chunks)} chunks from test code")
    for chunk in chunks:
        print(f"  - {chunk.chunk_type}: {chunk.metadata.get('name', 'N/A')}")
    
    print("✅ Code parser test passed")

def test_vector_store():
    """Test vector store operations"""
    print("\n" + "="*60)
    print("TEST 3: Vector Store")
    print("="*60)
    
    from app.rag.vector_store import VectorStore
    from app.ingestion.code_parser import CodeChunk
    
    # Create test vector store
    vs = VectorStore(
        persist_directory="./test_vectorstore_temp",
        collection_name="test_collection"
    )
    
    print(f"✓ Vector store created: {vs.collection.count()} documents")
    
    # Create test chunks
    test_chunks = [
        CodeChunk(
            content="def authenticate_user(username, password):\n    return verify_credentials(username, password)",
            file_path="auth/login.py",
            start_line=10,
            end_line=12,
            language="python",
            chunk_type="function",
            metadata={'name': 'authenticate_user'}
        ),
        CodeChunk(
            content="class UserManager:\n    def create_user(self, email):\n        return User(email)",
            file_path="models/user.py",
            start_line=5,
            end_line=8,
            language="python",
            chunk_type="class",
            metadata={'name': 'UserManager'}
        )
    ]
    
    # Add chunks
    vs.add_chunks(test_chunks)
    print(f"✓ Added {len(test_chunks)} test chunks")
    
    # Test search
    results = vs.search("how to authenticate users", n_results=2)
    print(f"✓ Search returned {len(results)} results")
    
    if results:
        print(f"  Top result: {results[0]['metadata']['file_path']}")
        print(f"  Similarity: {results[0]['similarity_score']:.2%}")
    
    # Cleanup
    vs.clear()
    print("✓ Cleaned up test data")
    
    print("✅ Vector store test passed")

def test_end_to_end():
    """Test complete workflow"""
    print("\n" + "="*60)
    print("TEST 4: End-to-End Workflow")
    print("="*60)
    
    from app.ingestion.repo_ingestion import RepositoryIngestion
    from app.rag.vector_store import VectorStore
    
    # Create sample repository
    test_repo = Path("./test_repo")
    test_repo.mkdir(exist_ok=True)
    
    # Create sample files
    (test_repo / "main.py").write_text('''
def main():
    """Main entry point"""
    print("Starting application...")
    run_server()

def run_server():
    """Run the web server"""
    server = create_server()
    server.start()
''')
    
    (test_repo / "utils.py").write_text('''
def format_date(date):
    """Format date to string"""
    return date.strftime("%Y-%m-%d")

def parse_config(path):
    """Load configuration file"""
    with open(path) as f:
        return json.load(f)
''')
    
    print(f"✓ Created test repository at {test_repo}")
    
    # Ingest repository
    ingestion = RepositoryIngestion(
        repo_path=str(test_repo),
        supported_extensions=['.py']
    )
    
    chunks = ingestion.ingest_repository()
    print(f"✓ Ingested {len(chunks)} chunks")
    
    # Add to vector store
    vs = VectorStore(
        persist_directory="./test_vectorstore_e2e",
        collection_name="e2e_test"
    )
    vs.add_chunks(chunks)
    print(f"✓ Vector store has {vs.collection.count()} documents")
    
    # Test search
    results = vs.search("how to start the server", n_results=3)
    print(f"✓ Search found {len(results)} relevant chunks")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_repo)
    vs.clear()
    print("✓ Cleaned up test files")
    
    print("✅ End-to-end test passed")

def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪"*30)
    print("CODEBASE RAG CHAT - SYSTEM TESTS")
    print("🧪"*30)
    
    tests = [
        ("Configuration", test_config),
        ("Code Parser", test_code_parser),
        ("Vector Store", test_vector_store),
        ("End-to-End", test_end_to_end)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python run_server.py")
        print("2. Open frontend in browser")
        print("3. Index your repository")
        print("4. Start chatting with your code!")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before proceeding.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()