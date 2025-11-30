"""
Celery Configuration for Background Tasks
- Model training and retraining
- Analytics aggregation
- Data export generation
- Scheduled maintenance tasks
"""

from celery import Celery
from celery.schedules import crontab
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from io import BytesIO
import json

# Initialize Celery
celery_app = Celery(
    'chatbot_tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Periodic Tasks Schedule
celery_app.conf.beat_schedule = {
    'retrain-ensemble-model': {
        'task': 'celery_app.retrain_ensemble_model',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'aggregate-analytics': {
        'task': 'celery_app.aggregate_daily_analytics',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'cleanup-old-data': {
        'task': 'celery_app.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'update-keyword-trends': {
        'task': 'celery_app.update_keyword_trends',
        'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
    },
}

# Database connection for Celery tasks
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/chatbot_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# =====================================
# BACKGROUND TASKS
# =====================================

@celery_app.task(name='celery_app.retrain_ensemble_model')
def retrain_ensemble_model():
    """
    Retrain the ensemble model based on recent user feedback
    and model performance data
    """
    from ai_orchestrator import AIOrchestrator
    
    try:
        db = SessionLocal()
        orchestrator = AIOrchestrator()
        
        # Get recent model performance data (last 7 days)
        from main import ModelResponse, Message
        
        recent_responses = db.query(ModelResponse).join(Message).filter(
            Message.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        # Aggregate performance metrics
        model_stats = {}
        for response in recent_responses:
            model = response.model_name
            if model not in model_stats:
                model_stats[model] = {
                    'total_responses': 0,
                    'selected_count': 0,
                    'avg_latency': 0,
                    'latencies': []
                }
            
            model_stats[model]['total_responses'] += 1
            if response.was_selected:
                model_stats[model]['selected_count'] += 1
            if response.latency_ms:
                model_stats[model]['latencies'].append(response.latency_ms)
        
        # Calculate final metrics and update orchestrator
        for model, stats in model_stats.items():
            if stats['latencies']:
                stats['avg_latency'] = sum(stats['latencies']) / len(stats['latencies'])
            
            selection_rate = stats['selected_count'] / max(stats['total_responses'], 1)
            
            # Update model performance in orchestrator
            # Normalize to 0-1 score
            performance_score = selection_rate
            orchestrator.model_performance[model] = {
                'score': performance_score,
                'count': stats['total_responses'],
                'last_updated': datetime.utcnow().isoformat()
            }
        
        # Save updated performance data
        orchestrator.save_performance_data()
        
        db.close()
        
        return {
            'status': 'success',
            'models_updated': len(model_stats),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@celery_app.task(name='celery_app.aggregate_daily_analytics')
def aggregate_daily_analytics():
    """
    Aggregate daily analytics data for faster dashboard loading
    """
    try:
        db = SessionLocal()
        from main import AnalyticsEvent, User, Message, AdminInsight
        import uuid
        
        # Calculate date range
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Aggregate various metrics
        analytics_data = {
            'date': yesterday.isoformat(),
            'metrics': {}
        }
        
        # User metrics
        total_users = db.query(User).filter(
            User.created_at <= datetime.combine(yesterday, datetime.max.time())
        ).count()
        
        new_users = db.query(User).filter(
            func.date(User.created_at) == yesterday
        ).count()
        
        analytics_data['metrics']['users'] = {
            'total': total_users,
            'new': new_users
        }
        
        # Message metrics
        messages_yesterday = db.query(Message).filter(
            func.date(Message.timestamp) == yesterday
        ).count()
        
        analytics_data['metrics']['messages'] = {
            'total': messages_yesterday
        }
        
        # Top queries
        from sqlalchemy import desc
        top_queries = db.query(
            Message.content,
            func.count(Message.id).label('count')
        ).filter(
            func.date(Message.timestamp) == yesterday,
            Message.role == 'user'
        ).group_by(Message.content).order_by(desc('count')).limit(10).all()
        
        analytics_data['metrics']['top_queries'] = [
            {'query': q[0][:100], 'count': q[1]} for q in top_queries
        ]
        
        # Save aggregated data
        insight = AdminInsight(
            id=str(uuid.uuid4()),
            metric_type='daily_summary',
            aggregated_data=analytics_data,
            date=datetime.combine(yesterday, datetime.min.time())
        )
        db.add(insight)
        db.commit()
        
        db.close()
        
        return {
            'status': 'success',
            'date': yesterday.isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@celery_app.task(name='celery_app.cleanup_old_data')
def cleanup_old_data():
    """
    Clean up old analytics events and archived conversations
    """
    try:
        db = SessionLocal()
        from main import AnalyticsEvent, ConversationDB
        
        # Delete analytics events older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp < cutoff_date
        ).delete()
        
        # Delete archived conversations older than 180 days
        archive_cutoff = datetime.utcnow() - timedelta(days=180)
        deleted_convs = db.query(ConversationDB).filter(
            ConversationDB.is_archived == True,
            ConversationDB.updated_at < archive_cutoff
        ).delete()
        
        db.commit()
        db.close()
        
        return {
            'status': 'success',
            'deleted_events': deleted_events,
            'deleted_conversations': deleted_convs,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@celery_app.task(name='celery_app.update_keyword_trends')
def update_keyword_trends():
    """
    Extract and update keyword trends from recent conversations
    """
    try:
        db = SessionLocal()
        from main import Message, AdminInsight
        import re
        from collections import Counter
        import uuid
        
        # Get messages from last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_messages = db.query(Message).filter(
            Message.timestamp >= yesterday,
            Message.role == 'user'
        ).all()
        
        # Extract keywords (simple approach - can be enhanced with NLTK/spaCy)
        all_words = []
        for msg in recent_messages:
            # Basic keyword extraction
            words = re.findall(r'\b[a-zA-Z]{4,}\b', msg.content.lower())
            all_words.extend(words)
        
        # Count keyword frequencies
        keyword_counts = Counter(all_words)
        
        # Get top 50 keywords
        top_keywords = keyword_counts.most_common(50)
        
        # Compare with previous period for trends
        week_ago = datetime.utcnow() - timedelta(days=7)
        old_messages = db.query(Message).filter(
            Message.timestamp >= week_ago,
            Message.timestamp < yesterday,
            Message.role == 'user'
        ).all()
        
        old_words = []
        for msg in old_messages:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', msg.content.lower())
            old_words.extend(words)
        
        old_counts = Counter(old_words)
        
        # Calculate trends
        keyword_data = []
        for keyword, count in top_keywords:
            old_count = old_counts.get(keyword, 0)
            trend = ((count - old_count) / max(old_count, 1)) * 100 if old_count > 0 else 100
            
            keyword_data.append({
                'keyword': keyword,
                'count': count,
                'trend': round(trend, 2),
                'category': 'general'  # Can be enhanced with classification
            })
        
        # Save keyword trends
        insight = AdminInsight(
            id=str(uuid.uuid4()),
            metric_type='keyword_trends',
            aggregated_data={'keywords': keyword_data},
            date=datetime.utcnow()
        )
        db.add(insight)
        db.commit()
        
        db.close()
        
        return {
            'status': 'success',
            'keywords_analyzed': len(keyword_data),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@celery_app.task(name='celery_app.generate_excel_report')
def generate_excel_report(user_id: str, start_date: str, end_date: str):
    """
    Generate Excel report with analytics data
    """
    try:
        db = SessionLocal()
        from main import Message, User, ModelResponse
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Query data
        messages = db.query(Message).filter(
            Message.timestamp >= start,
            Message.timestamp <= end
        ).all()
        
        # Prepare DataFrames
        message_data = []
        for msg in messages:
            message_data.append({
                'Timestamp': msg.timestamp,
                'Role': msg.role,
                'Content': msg.content[:100],
                'Model Used': msg.model_used,
                'User Feedback': msg.user_feedback
            })
        
        df_messages = pd.DataFrame(message_data)
        
        # Model performance data
        model_responses = db.query(
            ModelResponse.model_name,
            func.count(ModelResponse.id).label('total'),
            func.avg(ModelResponse.latency_ms).label('avg_latency'),
            func.sum(ModelResponse.was_selected.cast(int)).label('selected')
        ).filter(
            ModelResponse.timestamp >= start,
            ModelResponse.timestamp <= end
        ).group_by(ModelResponse.model_name).all()
        
        model_data = [{
            'Model': r[0],
            'Total Responses': r[1],
            'Avg Latency (ms)': round(r[2] or 0, 2),
            'Times Selected': r[3],
            'Selection Rate (%)': round((r[3] / r[1] * 100) if r[1] > 0 else 0, 2)
        } for r in model_responses]
        
        df_models = pd.DataFrame(model_data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_messages.to_excel(writer, sheet_name='Messages', index=False)
            df_models.to_excel(writer, sheet_name='Model Performance', index=False)
        
        output.seek(0)
        
        # In production, upload to S3 and return URL
        # For now, save locally
        filename = f"report_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"/tmp/{filename}"
        
        with open(filepath, 'wb') as f:
            f.write(output.getvalue())
        
        db.close()
        
        return {
            'status': 'success',
            'filepath': filepath,
            'filename': filename,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# =====================================
# UTILITY FUNCTIONS
# =====================================

@celery_app.task
def test_celery():
    """Test task to verify Celery is working"""
    return {
        'status': 'success',
        'message': 'Celery is working!',
        'timestamp': datetime.utcnow().isoformat()
    }

if __name__ == '__main__':
    # For testing
    celery_app.start()