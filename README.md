# 🤖 Professional Multi-Model AI Chatbot Platform

Enterprise-grade chatbot platform with intelligent ensemble learning, supporting 8+ AI models with self-improving recommendations.

## 🌟 Features

### Core Features
- ✅ **Multi-Model Integration**: Gemini, DeepSeek, Claude, GPT, Qwen, Perplexity, Grok, Copilot
- ✅ **Smart Ensemble Learning**: AI-powered model selection and response ranking
- ✅ **Self-Improving Algorithm**: Learns from user feedback and historical performance
- ✅ **Persistent Chat History**: Full conversation management with sidebar navigation
- ✅ **Real-Time Updates**: WebSocket support for live chat synchronization
- ✅ **Professional UI**: Modern, responsive design with dark mode support

### Authentication & Authorization
- ✅ Firebase Authentication (Email/Password, OAuth)
- ✅ Role-Based Access Control (Free, Premium, Admin)
- ✅ JWT Token Management
- ✅ Rate Limiting & Abuse Prevention

### Admin Dashboard
- ✅ User Analytics & Statistics
- ✅ Top Questions & Keyword Analysis
- ✅ AI Model Performance Metrics
- ✅ Excel/CSV Export Functionality
- ✅ Real-Time Charts & Visualizations

### Technical Excellence
- ✅ PostgreSQL Database with SQLAlchemy ORM
- ✅ Redis Caching for Performance
- ✅ Celery Background Task Queue
- ✅ Docker & Docker Compose Ready
- ✅ Production-Ready Architecture
- ✅ Comprehensive Error Handling

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-model-chatbot.git
cd multi-model-chatbot
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Database
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_db
REDIS_URL=redis://localhost:6379/0

# Firebase (Get from Firebase Console)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com

# AI Model API Keys
GEMINI_KEY=your_gemini_api_key
DEEPSEEK_KEY=your_openrouter_key
CLAUDE_KEY=your_openrouter_key
GPT_KEY=your_openrouter_key
QWEN_KEY=your_openrouter_key
PERPLX_KEY=your_openrouter_key

# Application
SECRET_KEY=your-super-secret-key-change-this
```

### 3. Option A: Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Option B: Manual Setup

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### Start Redis & PostgreSQL

```bash
# Using Docker for databases only
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=chatbot_password postgres:15-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

## 🔑 Getting API Keys

### 1. Google Gemini
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy to `GEMINI_KEY` in `.env`

### 2. OpenRouter (for DeepSeek, Claude, GPT, etc.)
1. Sign up at [OpenRouter.ai](https://openrouter.ai/)
2. Go to Keys section
3. Create a new API key
4. Use the same key for all OpenRouter models:
   - `DEEPSEEK_KEY`
   - `CLAUDE_KEY`
   - `GPT_KEY`
   - `QWEN_KEY`
   - `PERPLX_KEY`

### 3. Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication → Email/Password
4. Go to Project Settings → Service Accounts
5. Generate new private key
6. Copy credentials to `.env`

## 📚 Project Structure

```
multi-model-chatbot/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── ai_orchestrator.py         # AI model orchestration & ensemble learning
│   ├── models.py                  # Database models
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Backend container
│   └── tests/                     # Backend tests
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── App.css               # Styles
│   │   └── index.js              # Entry point
│   ├── package.json              # Node dependencies
│   ├── Dockerfile                # Frontend container
│   └── public/                   # Static assets
│
├── docker-compose.yml            # Docker orchestration
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🎯 Usage Guide

### For Regular Users

1. **Register/Login**
   - Open http://localhost:3000
   - Create an account or sign in
   - Start chatting immediately

2. **Select AI Models**
   - Click "Models" button in header
   - Select 2-4 models for comparison
   - Toggle "Smart Ensemble" for best response

3. **Chat Features**
   - Type message and press Enter
   - View all model responses in details
   - Rate responses with 👍/👎
   - Search past conversations

### For Admins

1. **Access Admin Panel**
   - Login with admin account
   - Click "Admin Panel" in sidebar
   - View comprehensive analytics

2. **Analytics Features**
   - User statistics and growth
   - Top questions analysis
   - Keyword trends and categories
   - AI model performance comparison
   - Export data to Excel

## 🔧 Configuration

### Model Selection Intelligence

The AI Orchestrator automatically selects best models based on:
- Query type (coding, creative, research, etc.)
- Historical model performance
- Response quality metrics
- User feedback

### Ensemble Learning

The system uses weighted scoring:
- 40% Response Quality (NLP-based)
- 30% Model Confidence
- 20% Historical Performance
- 10% Speed/Latency

### Rate Limiting

Default limits (configurable in `.env`):
- 100 requests/minute per user
- 10,000 requests/day per user

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests

```bash
cd frontend
npm test
```

### API Testing

```bash
# Test all AI models
python backend/api_tester.py

# Check API documentation
curl http://localhost:8000/docs
```

## 📊 Database Schema

### Main Tables

**users**
- User authentication and profile data
- Role-based permissions

**conversations**
- Chat conversation metadata
- User associations

**messages**
- Individual chat messages
- User feedback ratings

**model_responses**
- AI model outputs
- Performance metrics

**analytics_events**
- User behavior tracking
- System events

**admin_insights**
- Aggregated analytics
- Keyword trends

## 🚢 Production Deployment

### AWS Deployment

1. **Setup RDS PostgreSQL**
```bash
aws rds create-db-instance \
  --db-instance-identifier chatbot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourPassword123
```

2. **Setup ElastiCache Redis**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id chatbot-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

3. **Deploy to ECS**
```bash
# Build and push Docker images
docker build -t chatbot-backend ./backend
docker tag chatbot-backend:latest YOUR_ECR_REPO/backend:latest
docker push YOUR_ECR_REPO/backend:latest

# Deploy with ECS
aws ecs update-service --cluster chatbot-cluster --service backend --force-new-deployment
```

### Environment Variables (Production)

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/chatbot
REDIS_URL=redis://elasticache-endpoint:6379
ALLOWED_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file
   - Use AWS Secrets Manager in production
   - Rotate API keys regularly

2. **Authentication**
   - Enable 2FA for admin accounts
   - Use strong password requirements
   - Implement session timeout

3. **API Security**
   - Rate limiting enabled by default
   - CORS configured properly
   - Input validation on all endpoints

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**2. AI Model API Errors**
```bash
# Test API keys
python backend/api_tester.py

# Check rate limits
# Wait a few minutes and try again
```

**3. Frontend Can't Connect to Backend**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify CORS settings in main.py
# Check REACT_APP_API_URL in frontend
```

## 📈 Performance Optimization

### Database Optimization
- Indexes on frequently queried columns
- Connection pooling enabled
- Materialized views for analytics

### Caching Strategy
- Redis for session management
- Response caching (1-hour TTL)
- Database query result caching

### Frontend Optimization
- Code splitting and lazy loading
- Virtual scrolling for chat history
- Debounced search inputs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenRouter for AI model access
- Firebase for authentication
- FastAPI for backend framework
- React for frontend framework

## 📞 Support

- Documentation: https://docs.yourdomain.com
- Email: support@yourdomain.com
- Discord: https://discord.gg/yourinvite

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Multi-model integration
- ✅ Basic ensemble learning
- ✅ User authentication
- ✅ Admin dashboard

### Phase 2 (Next)
- 🔄 Advanced NLP keyword extraction
- 🔄 Voice input/output
- 🔄 File upload support
- 🔄 Multi-language support

### Phase 3 (Future)
- 📅 Mobile applications (iOS/Android)
- 📅 API for third-party integration
- 📅 Custom model fine-tuning
- 📅 Enterprise SSO integration

---

**Built with ❤️ for the AI community**