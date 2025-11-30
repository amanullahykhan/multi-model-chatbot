import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Available AI Models
const AI_MODELS = [
  { id: 'gemini', name: 'Google Gemini', icon: '🤖', color: '#4285f4' },
  { id: 'deepseek', name: 'DeepSeek', icon: '🧠', color: '#6c5ce7' },
  { id: 'claude', name: 'Claude', icon: '🎭', color: '#d97706' },
  { id: 'gpt', name: 'ChatGPT', icon: '💬', color: '#10a37f' },
  { id: 'qwen', name: 'Qwen', icon: '🌟', color: '#e74c3c' },
  { id: 'perplx', name: 'Perplexity', icon: '🔍', color: '#3498db' },
];

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  
  // Chat state
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedModels, setSelectedModels] = useState(['gemini', 'deepseek', 'claude']);
  const [useEnsemble, setUseEnsemble] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Admin state
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Check for stored token
    const token = localStorage.getItem('authToken');
    if (token) {
      setIsAuthenticated(true);
      fetchUserData(token);
      fetchConversations(token);
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchUserData = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      setIsAdmin(response.data.role === 'admin');
    } catch (error) {
      console.error('Failed to fetch user data:', error);
    }
  };

  const fetchConversations = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    
    try {
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API_URL}${endpoint}`, { email, password });
      
      const token = response.data.token;
      localStorage.setItem('authToken', token);
      setIsAuthenticated(true);
      setShowAuthModal(false);
      
      fetchUserData(token);
      fetchConversations(token);
    } catch (error) {
      alert(error.response?.data?.detail || 'Authentication failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setIsAuthenticated(false);
    setUser(null);
    setConversations([]);
    setMessages([]);
    setCurrentConversation(null);
  };

  const createNewConversation = async () => {
    const token = localStorage.getItem('authToken');
    try {
      const response = await axios.post(
        `${API_URL}/conversations`,
        { title: 'New Conversation' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const newConv = response.data;
      setConversations([newConv, ...conversations]);
      setCurrentConversation(newConv);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const loadConversation = async (conversationId) => {
    const token = localStorage.getItem('authToken');
    try {
      const response = await axios.get(
        `${API_URL}/conversations/${conversationId}/messages`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setMessages(response.data);
      setCurrentConversation(conversations.find(c => c.id === conversationId));
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const token = localStorage.getItem('authToken');
    const userMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Add user message immediately
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages([...messages, tempUserMsg]);

    try {
      const response = await axios.post(
        `${API_URL}/chat`,
        {
          conversation_id: currentConversation?.id,
          message: userMessage,
          selected_models: selectedModels,
          use_ensemble: useEnsemble
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Add AI response
      const aiMessage = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.best_response.content,
        model_used: response.data.best_response.model,
        all_responses: response.data.responses,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Update current conversation
      if (!currentConversation) {
        setCurrentConversation({ id: response.data.conversation_id });
        fetchConversations(token);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleModel = (modelId) => {
    setSelectedModels(prev => 
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  // Login/Register Modal
  if (!isAuthenticated) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1>🤖 Multi-Model AI Chatbot</h1>
            <p>Enterprise-grade AI powered by multiple models</p>
          </div>
          
          <div className="auth-tabs">
            <button
              className={authMode === 'login' ? 'active' : ''}
              onClick={() => setAuthMode('login')}
            >
              Login
            </button>
            <button
              className={authMode === 'register' ? 'active' : ''}
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth} className="auth-form">
            <input
              type="email"
              name="email"
              placeholder="Email address"
              required
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              required
            />
            <button type="submit" className="btn-primary">
              {authMode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="auth-features">
            <div className="feature">
              <span className="feature-icon">🚀</span>
              <span>8 AI Models</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🧠</span>
              <span>Smart Ensemble</span>
            </div>
            <div className="feature">
              <span className="feature-icon">💾</span>
              <span>Chat History</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Chat Interface
  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>💬 Chats</h2>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="btn-icon">
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <button onClick={createNewConversation} className="btn-new-chat">
          ➕ New Conversation
        </button>

        <div className="conversations-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`conversation-item ${currentConversation?.id === conv.id ? 'active' : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              <div className="conv-title">{conv.title}</div>
              <div className="conv-meta">
                {conv.message_count} messages • {new Date(conv.updated_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">👤</div>
            <div className="user-details">
              <div className="user-email">{user?.email}</div>
              <div className="user-role">{user?.role || 'Free'}</div>
            </div>
          </div>
          {isAdmin && (
            <button onClick={() => setShowAdminPanel(true)} className="btn-admin">
              📊 Admin Panel
            </button>
          )}
          <button onClick={handleLogout} className="btn-logout">
            🚪 Logout
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-content">
        {/* Header */}
        <header className="chat-header">
          <div className="header-left">
            <h1>Multi-Model AI Chat</h1>
            {currentConversation && (
              <span className="conversation-title">{currentConversation.title}</span>
            )}
          </div>
          
          <div className="header-right">
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="btn-models"
            >
              🎯 Models ({selectedModels.length})
            </button>
            
            <label className="ensemble-toggle">
              <input
                type="checkbox"
                checked={useEnsemble}
                onChange={(e) => setUseEnsemble(e.target.checked)}
              />
              <span>Smart Ensemble</span>
            </label>
          </div>
        </header>

        {/* Model Selector */}
        {showModelSelector && (
          <div className="model-selector">
            <h3>Select AI Models</h3>
            <div className="model-grid">
              {AI_MODELS.map(model => (
                <button
                  key={model.id}
                  className={`model-btn ${selectedModels.includes(model.id) ? 'selected' : ''}`}
                  onClick={() => toggleModel(model.id)}
                  style={{ borderColor: selectedModels.includes(model.id) ? model.color : '#ddd' }}
                >
                  <span className="model-icon">{model.icon}</span>
                  <span className="model-name">{model.name}</span>
                  {selectedModels.includes(model.id) && <span className="checkmark">✓</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>👋 Welcome to Multi-Model AI Chat!</h2>
              <p>Start a conversation and get responses from multiple AI models</p>
              <div className="suggestions">
                <button onClick={() => setInputMessage("Explain quantum computing in simple terms")}>
                  Explain quantum computing
                </button>
                <button onClick={() => setInputMessage("Write a Python function to sort a list")}>
                  Help me code
                </button>
                <button onClick={() => setInputMessage("Tell me a creative story about AI")}>
                  Tell me a story
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={msg.id || idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-role">
                      {msg.role === 'user' ? 'You' : msg.model_used || 'AI'}
                    </span>
                    <span className="message-time">{formatTimestamp(msg.timestamp)}</span>
                  </div>
                  <div className="message-text">{msg.content}</div>
                  
                  {msg.all_responses && (
                    <details className="all-responses">
                      <summary>View all {Object.keys(msg.all_responses).length} model responses</summary>
                      <div className="responses-grid">
                        {Object.entries(msg.all_responses).map(([model, resp]) => (
                          <div key={model} className="response-card">
                            <div className="response-header">
                              <strong>{model}</strong>
                              {resp.error ? (
                                <span className="error-badge">❌ Error</span>
                              ) : (
                                <span className="success-badge">✓ {resp.latency_ms}ms</span>
                              )}
                            </div>
                            <div className="response-content">
                              {resp.error || resp.content?.substring(0, 150) + '...'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="message assistant loading">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
                <p>Processing with {selectedModels.length} AI models...</p>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message here..."
            disabled={isLoading}
            className="message-input"
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="btn-send"
          >
            {isLoading ? '⏳' : '🚀'} Send
          </button>
        </form>
      </main>

      {/* Admin Panel Modal */}
      {showAdminPanel && (
        <AdminPanel onClose={() => setShowAdminPanel(false)} />
      )}
    </div>
  );
}

// Admin Panel Component
function AdminPanel({ onClose }) {
  const [analytics, setAnalytics] = useState(null);
  const [topQuestions, setTopQuestions] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [modelPerformance, setModelPerformance] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    const token = localStorage.getItem('authToken');
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [analyticsRes, questionsRes, keywordsRes, performanceRes] = await Promise.all([
        axios.get(`${API_URL}/admin/analytics/overview`, { headers }),
        axios.get(`${API_URL}/admin/analytics/top-questions`, { headers }),
        axios.get(`${API_URL}/admin/analytics/keywords`, { headers }),
        axios.get(`${API_URL}/admin/analytics/model-performance`, { headers })
      ]);

      setAnalytics(analyticsRes.data);
      setTopQuestions(questionsRes.data);
      setKeywords(keywordsRes.data);
      setModelPerformance(performanceRes.data);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    }
  };

  const exportData = async () => {
    const token = localStorage.getItem('authToken');
    try {
      const response = await axios.get(`${API_URL}/admin/analytics/export`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { format: 'json' }
      });
      
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${new Date().toISOString()}.json`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="admin-panel" onClick={(e) => e.stopPropagation()}>
        <div className="admin-header">
          <h2>📊 Admin Dashboard</h2>
          <button onClick={onClose} className="btn-close">✕</button>
        </div>

        <div className="admin-tabs">
          <button
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={activeTab === 'questions' ? 'active' : ''}
            onClick={() => setActiveTab('questions')}
          >
            Top Questions
          </button>
          <button
            className={activeTab === 'keywords' ? 'active' : ''}
            onClick={() => setActiveTab('keywords')}
          >
            Keywords
          </button>
          <button
            className={activeTab === 'performance' ? 'active' : ''}
            onClick={() => setActiveTab('performance')}
          >
            Model Performance
          </button>
        </div>

        <div className="admin-content">
          {activeTab === 'overview' && analytics && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{analytics.total_users}</div>
                <div className="stat-label">Total Users</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{analytics.active_conversations}</div>
                <div className="stat-label">Active Conversations</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{analytics.total_messages}</div>
                <div className="stat-label">Total Messages</div>
              </div>
            </div>
          )}

          {activeTab === 'questions' && (
            <div className="data-table">
              <h3>Most Asked Questions</h3>
              <table>
                <thead>
                  <tr>
                    <th>Question</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {topQuestions.map((q, idx) => (
                    <tr key={idx}>
                      <td>{q.question}</td>
                      <td>{q.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'keywords' && (
            <div className="data-table">
              <h3>Keyword Analytics</h3>
              <table>
                <thead>
                  <tr>
                    <th>Keyword</th>
                    <th>Count</th>
                    <th>Trend</th>
                    <th>Category</th>
                  </tr>
                </thead>
                <tbody>
                  {keywords.map((k, idx) => (
                    <tr key={idx}>
                      <td>{k.keyword}</td>
                      <td>{k.count}</td>
                      <td className={k.trend > 0 ? 'trend-up' : 'trend-down'}>
                        {k.trend > 0 ? '↑' : '↓'} {Math.abs(k.trend)}%
                      </td>
                      <td>{k.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="data-table">
              <h3>AI Model Performance</h3>
              <table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Avg Score</th>
                    <th>Avg Latency</th>
                    <th>Usage Count</th>
                    <th>Selection Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {modelPerformance.map((m, idx) => (
                    <tr key={idx}>
                      <td><strong>{m.model}</strong></td>
                      <td>{m.avg_score}/10</td>
                      <td>{m.avg_latency_ms}ms</td>
                      <td>{m.usage_count}</td>
                      <td>{m.selection_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="admin-footer">
          <button onClick={exportData} className="btn-export">
            📥 Export Data (Excel)
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;