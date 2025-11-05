# 🤖 AI-Powered Codebase Chat Assistant

An intelligent RAG-based system that enables developers to query entire codebases using natural language. Built with FastAPI, React, ChromaDB, and Groq's Llama 3.3 70B.

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

- **Natural Language Queries**: Ask "Where is authentication handled?" instead of grep-ing through files
- **Semantic Code Search**: ChromaDB vector database with sub-second search across 10,000+ code chunks
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, Go, Rust, C++, and 10+ more
- **Real-Time Indexing**: Background processing with live progress tracking
- **Source Citations**: Every answer includes file paths and line numbers
- **Lightning Fast**: Powered by Groq's Llama 3.3 70B for instant responses

## 🎯 Demo
```bash
You: "Where is user authentication handled?"

AI: Authentication is handled in auth/login.py (lines 45-67). The system uses 
JWT tokens with the authenticate_user() function which validates credentials 
against the database and returns a signed token.

Sources:
📄 auth/login.py (lines 45-67)
📄 middleware/auth_middleware.js (lines 12-28)
```

## 🏗️ Architecture
```
┌─────────────┐      REST API      ┌──────────────┐
│   React UI  │ ◄────────────────► │   FastAPI    │
└─────────────┘                     └──────┬───────┘
                                           │
                                    ┌──────▼────────┐
                                    │  RAG Pipeline │
                                    ├───────────────┤
                                    │ • ChromaDB    │
                                    │ • Embeddings  │
                                    │ • Groq LLM    │
                                    └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- Groq API key ([Get free key](https://console.groq.com))

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/aish26211/AI-Powered-Codebase-Chat-Assistant.git
cd AI-Powered-Codebase-Chat-Assistant
```

**2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# Start server
python run_server.py
```

Backend runs on **http://localhost:8000**

**3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend opens at **http://localhost:3000**

### Usage

1. Open **http://localhost:3000**
2. Enter repository path (e.g., `../backend` or `/path/to/your/project`)
3. Click **"Index Repo"** and wait for completion (~30 seconds)
4. Start asking questions about your code!

## 💡 Example Questions
```
✅ "Where is user authentication handled?"
✅ "How does the API process requests?"
✅ "Show me the database connection logic"
✅ "What does the payment processing flow look like?"
✅ "Find all error handling code"
✅ "Explain the main entry point"
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database for semantic search
- **SentenceTransformers** - all-MiniLM-L6-v2 for embeddings
- **Groq API** - Llama 3.3 70B for fast LLM inference
- **Pydantic** - Data validation and settings

### Frontend
- **React 18** - UI framework
- **Lucide React** - Beautiful icon library
- **CSS3** - Modern glassmorphism design

## 📊 Performance Metrics

| Metric | Performance |
|--------|-------------|
| **Indexing Speed** | 50+ files/second |
| **Query Latency** | < 2 seconds (including LLM) |
| **Search Time** | Sub-second similarity search |
| **Scalability** | Supports 100K+ lines of code |
| **Languages** | 10+ programming languages |

## 📁 Project Structure
```
AI-Powered-Codebase-Chat-Assistant/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration management
│   │   ├── main.py                # FastAPI application
│   │   ├── ingestion/
│   │   │   ├── code_parser.py     # Code parsing & chunking
│   │   │   └── repo_ingestion.py  # Repository processing
│   │   └── rag/
│   │       ├── vector_store.py    # ChromaDB interface
│   │       └── rag_engine.py      # RAG pipeline & LLM
│   ├── run_server.py              # Server startup
│   ├── test_system.py             # Testing suite
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.js                 # Main React component
    │   ├── App.css                # Styling
    │   └── index.js
    ├── public/
    │   └── index.html
    └── package.json
```

## 🔧 Configuration

Edit `backend/.env`:
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (defaults shown)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
VECTOR_STORE_PATH=./vectorstore
```

## 🧪 Testing
```bash
cd backend
source .venv/bin/activate
python test_system.py
```

Expected output:
```
✅ Configuration test passed
✅ Code parser test passed  
✅ Vector store test passed
✅ End-to-end test passed
🎉 All tests passed!
```

## 🔒 Security

- ✅ API keys stored in `.env` (never committed)
- ✅ CORS configured for production
- ✅ Input validation with Pydantic
- ✅ Secure file path handling
- ✅ No sensitive data in vector store

## 🚧 Roadmap

- [ ] Multi-repository support
- [ ] GitHub integration (direct repo URLs)
- [ ] Code diff analysis
- [ ] Export chat history
- [ ] Advanced filters (by language, date, author)
- [ ] Docker deployment
- [ ] CI/CD pipeline

## 🤝 Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 API Documentation

Once server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

### Key Endpoints
```bash
POST   /ingest          # Index a repository
GET    /ingest/status   # Check indexing progress
POST   /query           # Ask a question
POST   /chat            # Multi-turn conversation
GET    /stats           # Vector store statistics
DELETE /reset           # Clear indexed data
```

## Cost

- **Groq API**: FREE tier (10,000 requests/day)
- **Embeddings**: FREE (runs locally)
- **Storage**: FREE (ChromaDB local)
- **Total**: $0/month for personal use! 🎉

## Acknowledgments

- [Groq](https://groq.com) for blazing-fast LLM inference
- [ChromaDB](https://www.trychroma.com/) for excellent vector database
- [FastAPI](https://fastapi.tiangolo.com/) for modern Python web framework
- [Sentence Transformers](https://www.sbert.net/) for embedding models

## 📄 License

MIT License - feel free to use for personal or commercial projects!

## 👨‍💻 Author

**Aish Sinha**
- 📧 Email: aish.sinha26@gmail.com
- 💼 LinkedIn: [linkedin.com/in/aish-sinha](https://linkedin.com/in/aish-sinha)
- 🐙 GitHub: [@aish26211](https://github.com/aish26211)

## 📧 Contact

Questions or feedback? Open an issue or reach out!

---

⭐ **Star this repo if you find it helpful!**

Built with ❤️ using RAG, LLMs, and modern AI tech.
