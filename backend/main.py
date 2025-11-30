"""
Professional Multi-Model AI Chatbot Platform
Enterprise-grade backend with Firebase Auth, PostgreSQL, and ML Ensemble
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import os
from enum import Enum

# Initialize FastAPI
app = FastAPI(
    title="Multi-Model AI Chatbot API",
    version="1.0.0",
    description="Enterprise AI Chatbot with Ensemble Learning"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# =====================================
# MODELS & SCHEMAS
# =====================================

class UserRole(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class AIModel(str, Enum):
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    GPT = "gpt"
    QWEN = "qwen"
    GROK = "grok"
    PERPLX = "perplx"
    COPILOT = "copilot"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Request/Response Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    model_used: Optional[AIModel] = None
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    selected_models: Optional[List[AIModel]] = None
    use_ensemble: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    responses: Dict[str, Any]
    best_response: Dict[str, Any]
    timestamp: datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class Conversation(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

# Admin Models
class AnalyticsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metric_type: Optional[str] = None

class KeywordAnalytics(BaseModel):
    keyword: str
    count: int
    trend: float
    category: str
    last_seen: datetime

# =====================================
# DATABASE MODELS (SQLAlchemy)
# =====================================

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    firebase_uid = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.FREE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    conversations = relationship("ConversationDB", back_populates="user", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")

class ConversationDB(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    model_used = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_feedback = Column(Integer)  # 1-5 star rating
    
    conversation = relationship("ConversationDB", back_populates="messages")
    model_responses = relationship("ModelResponse", back_populates="message")

class ModelResponse(Base):
    __tablename__ = "model_responses"
    
    id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    response_content = Column(Text, nullable=False)
    confidence_score = Column(Float)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)
    cost = Column(Float)
    was_selected = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message", back_populates="model_responses")

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    event_type = Column(String, nullable=False, index=True)
    metadata = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="analytics_events")

class AdminInsight(Base):
    __tablename__ = "admin_insights"
    
    id = Column(String, primary_key=True)
    metric_type = Column(String, nullable=False, index=True)
    aggregated_data = Column(JSON, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/chatbot_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# =====================================
# DEPENDENCIES
# =====================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> User:
    """Verify Firebase token and get user"""
    token = credentials.credentials
    
    # TODO: Implement Firebase token verification
    # For now, mock implementation
    try:
        # import firebase_admin.auth
        # decoded_token = firebase_admin.auth.verify_id_token(token)
        # uid = decoded_token['uid']
        
        # Mock for development
        uid = "mock_user_123"
        user = db.query(User).filter(User.firebase_uid == uid).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# =====================================
# AI MODEL ORCHESTRATOR
# =====================================

from ai_orchestrator import AIOrchestrator

orchestrator = AIOrchestrator()

# =====================================
# API ENDPOINTS
# =====================================

@app.get("/")
async def root():
    return {
        "name": "Multi-Model AI Chatbot API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# =====================================
# AUTHENTICATION ENDPOINTS
# =====================================

@app.post("/auth/register")
async def register(user_data: UserRegistration, db = Depends(get_db)):
    """Register new user with Firebase"""
    try:
        # TODO: Create Firebase user
        # firebase_user = firebase_admin.auth.create_user(
        #     email=user_data.email,
        #     password=user_data.password,
        #     display_name=user_data.full_name
        # )
        
        # Mock for development
        firebase_uid = f"firebase_{user_data.email.split('@')[0]}"
        
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create database user
        import uuid
        new_user = User(
            id=str(uuid.uuid4()),
            email=user_data.email,
            firebase_uid=firebase_uid,
            full_name=user_data.full_name,
            role=UserRole.FREE
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "email": new_user.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login")
async def login(credentials: UserLogin):
    """Login user with Firebase"""
    try:
        # TODO: Verify Firebase credentials
        # Mock response for development
        return {
            "token": "mock_firebase_token_12345",
            "user_id": "mock_user_123",
            "email": credentials.email
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# =====================================
# CONVERSATION ENDPOINTS
# =====================================

@app.post("/conversations", response_model=Conversation)
async def create_conversation(
    data: ConversationCreate,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create new conversation"""
    import uuid
    
    conversation = ConversationDB(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=data.title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return Conversation(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0
    )

@app.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    user: User = Depends(get_current_user),
    db = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get user's conversations"""
    conversations = db.query(ConversationDB).filter(
        ConversationDB.user_id == user.id,
        ConversationDB.is_archived == False
    ).order_by(ConversationDB.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for conv in conversations:
        msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        result.append(Conversation(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))
    
    return result

@app.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get conversation messages"""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.asc()).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "model_used": msg.model_used,
            "timestamp": msg.timestamp,
            "user_feedback": msg.user_feedback
        }
        for msg in messages
    ]

# =====================================
# CHAT ENDPOINTS
# =====================================

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Send message and get AI responses"""
    import uuid
    import time
    
    # Create or get conversation
    if not request.conversation_id:
        conversation = ConversationDB(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=request.message[:50] + ("..." if len(request.message) > 50 else "")
        )
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
    else:
        conversation_id = request.conversation_id
        conversation = db.query(ConversationDB).filter(
            ConversationDB.id == conversation_id,
            ConversationDB.user_id == user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save user message
    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # Get AI responses
    try:
        models_to_use = request.selected_models or list(AIModel)
        
        start_time = time.time()
        ai_responses = await orchestrator.get_all_responses(
            prompt=request.message,
            models=models_to_use
        )
        
        # Get best response using ensemble
        if request.use_ensemble:
            best_response = await orchestrator.get_best_response(
                prompt=request.message,
                responses=ai_responses
            )
        else:
            # Use first successful response
            best_response = next(
                (resp for resp in ai_responses.values() if not resp.get("error")),
                list(ai_responses.values())[0]
            )
        
        # Save assistant message
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=best_response.get("content", ""),
            model_used=best_response.get("model", "ensemble")
        )
        db.add(assistant_message)
        db.commit()
        
        # Save all model responses
        for model_name, response_data in ai_responses.items():
            model_resp = ModelResponse(
                id=str(uuid.uuid4()),
                message_id=assistant_message.id,
                model_name=model_name,
                response_content=response_data.get("content", ""),
                confidence_score=response_data.get("confidence", 0.0),
                latency_ms=response_data.get("latency_ms", 0),
                was_selected=(model_name == best_response.get("model"))
            )
            db.add(model_resp)
        
        db.commit()
        
        # Log analytics event
        analytics_event = AnalyticsEvent(
            id=str(uuid.uuid4()),
            user_id=user.id,
            event_type="chat_message",
            metadata={
                "conversation_id": conversation_id,
                "models_used": models_to_use,
                "query_length": len(request.message),
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
        )
        db.add(analytics_event)
        db.commit()
        
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_message.id,
            responses=ai_responses,
            best_response=best_response,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# =====================================
# ADMIN ENDPOINTS
# =====================================

@app.get("/admin/analytics/overview")
async def get_analytics_overview(
    admin: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Get admin analytics overview"""
    total_users = db.query(User).count()
    active_conversations = db.query(ConversationDB).filter(
        ConversationDB.updated_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    total_messages = db.query(Message).count()
    
    return {
        "total_users": total_users,
        "active_conversations": active_conversations,
        "total_messages": total_messages,
        "timestamp": datetime.utcnow()
    }

@app.get("/admin/analytics/top-questions")
async def get_top_questions(
    admin: User = Depends(require_admin),
    db = Depends(get_db),
    limit: int = 20
):
    """Get most asked questions"""
    from sqlalchemy import func
    
    top_messages = db.query(
        Message.content,
        func.count(Message.id).label('count')
    ).filter(
        Message.role == MessageRole.USER
    ).group_by(Message.content).order_by(func.count(Message.id).desc()).limit(limit).all()
    
    return [
        {"question": msg[0][:200], "count": msg[1]}
        for msg in top_messages
    ]

@app.get("/admin/analytics/keywords")
async def get_keyword_analytics(
    admin: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Get keyword analytics with NLP extraction"""
    # TODO: Implement NLP keyword extraction
    # For now, return mock data
    return [
        {
            "keyword": "pricing",
            "count": 145,
            "trend": 23.5,
            "category": "Product",
            "last_seen": datetime.utcnow()
        },
        {
            "keyword": "integration",
            "count": 89,
            "trend": 15.2,
            "category": "Technical",
            "last_seen": datetime.utcnow()
        }
    ]

@app.get("/admin/analytics/model-performance")
async def get_model_performance(
    admin: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Get AI model performance metrics"""
    from sqlalchemy import func
    
    performance = db.query(
        ModelResponse.model_name,
        func.avg(ModelResponse.confidence_score).label('avg_score'),
        func.avg(ModelResponse.latency_ms).label('avg_latency'),
        func.count(ModelResponse.id).label('usage_count'),
        func.sum(ModelResponse.was_selected.cast(Integer)).label('selected_count')
    ).group_by(ModelResponse.model_name).all()
    
    return [
        {
            "model": p[0],
            "avg_score": round(p[1] or 0, 2),
            "avg_latency_ms": int(p[2] or 0),
            "usage_count": p[3],
            "selected_count": p[4],
            "selection_rate": round((p[4] / p[3] * 100) if p[3] > 0 else 0, 2)
        }
        for p in performance
    ]

@app.get("/admin/analytics/export")
async def export_analytics(
    admin: User = Depends(require_admin),
    db = Depends(get_db),
    format: str = "json"
):
    """Export analytics data"""
    # TODO: Implement Excel export using openpyxl
    data = {
        "users": db.query(User).count(),
        "conversations": db.query(ConversationDB).count(),
        "messages": db.query(Message).count(),
        "export_date": datetime.utcnow().isoformat()
    }
    
    if format == "excel":
        # Use pandas and openpyxl for Excel export
        pass
    
    return data

# =====================================
# WEBSOCKET FOR REAL-TIME CHAT
# =====================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle real-time messages
            await manager.send_message({"status": "received", "data": data}, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)