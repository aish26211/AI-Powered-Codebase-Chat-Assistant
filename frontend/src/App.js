import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, Code, Loader2, Database, CheckCircle, AlertCircle, FolderOpen, Trash2 } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [repoPath, setRepoPath] = useState('');
  const [indexStatus, setIndexStatus] = useState({ status: 'idle' });
  const [stats, setStats] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchStats();
    checkIndexStatus();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const checkIndexStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/ingest/status`);
      const data = await response.json();
      setIndexStatus(data);
      
      if (data.status === 'processing') {
        setTimeout(checkIndexStatus, 2000);
      } else if (data.status === 'completed') {
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to check status:', error);
    }
  };

  const handleIndexRepo = async () => {
    if (!repoPath.trim()) {
      alert('Please enter a repository path');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath })
      });

      if (response.ok) {
        setMessages([{ role: 'assistant', content: `📦 Indexing repository: ${repoPath}` }]);
        checkIndexStatus();
      } else {
        const error = await response.json();
        alert(`Failed to index: ${error.detail}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;
    if (!stats || stats.total_chunks === 0) {
      alert('Please index a repository first!');
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage, n_results: 5 })
      });

      if (response.ok) {
        const result = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: result.answer,
          sources: result.sources
        }]);
      } else {
        const error = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `❌ Error: ${error.detail}`
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Failed to get response: ${error.message}`
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Clear all indexed data?')) return;
    
    try {
      await fetch(`${API_BASE}/reset`, { method: 'DELETE' });
      setMessages([]);
      setStats(null);
      setIndexStatus({ status: 'idle' });
      alert('Vector store cleared!');
    } catch (error) {
      alert(`Failed to reset: ${error.message}`);
    }
  };

  const getStatusIcon = () => {
    switch (indexStatus.status) {
      case 'processing': return <Loader2 className="icon spin" />;
      case 'completed': return <CheckCircle className="icon success" />;
      case 'error': return <AlertCircle className="icon error" />;
      default: return <Database className="icon" />;
    }
  };

  const isReady = stats && stats.total_chunks > 0;

  return (
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <Code className="icon" />
          </div>
          <div>
            <h1>RAG Chat</h1>
            <p>v1.0.0</p>
          </div>
        </div>
        
        <div className="status-card">
          <div className="status-row">
            <span>Status</span>
            {getStatusIcon()}
          </div>
          <p className="status-text">{indexStatus.status}</p>
          {indexStatus.status === 'processing' && (
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${indexStatus.progress}%` }} />
            </div>
          )}
        </div>

        <div className="index-section">
          <h3>Index Repository</h3>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="../backend"
            className="repo-input"
          />
          <button onClick={handleIndexRepo} disabled={indexStatus.status === 'processing'} className="index-button">
            {indexStatus.status === 'processing' ? (
              <><Loader2 className="icon spin" /> Indexing...</>
            ) : (
              <><FolderOpen className="icon" /> Index Repo</>
            )}
          </button>
        </div>

        {stats && (
          <div className="stats-section">
            <h3>Statistics</h3>
            <div className="stat-item">
              <span>Total Chunks:</span>
              <span>{stats.total_chunks}</span>
            </div>
          </div>
        )}

        <div className="reset-section">
          <button onClick={handleReset} className="reset-button">
            <Trash2 className="icon" />
            Clear Database
          </button>
        </div>
      </div>

      <div className="main-area">
        <div className="chat-header">
          <h2>Chat with Your Codebase</h2>
          <p>{isReady ? '✅ Ready' : '⚠️ Index a repository first'}</p>
        </div>

        <div className="messages-area">
          {messages.length === 0 && isReady && (
            <div className="empty-state">
              <Database className="icon large" />
              <p>Ask anything about your code!</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="bubble">
                {msg.role === 'assistant' && (
                  <div className="header">
                    <FileText className="icon" />
                    <span>AI Assistant</span>
                  </div>
                )}
                <div>{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources">
                    <p>Sources:</p>
                    {msg.sources.map((src, i) => (
                      <div key={i}>📄 {src.file} (lines {src.lines})</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="message assistant">
              <div className="bubble loading">
                <Loader2 className="icon spin" />
                <span>Searching...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isReady ? "Ask about your code..." : "Index first"}
            disabled={!isReady}
          />
          <button onClick={handleSend} disabled={!input.trim() || isProcessing || !isReady}>
            <Send className="icon" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;