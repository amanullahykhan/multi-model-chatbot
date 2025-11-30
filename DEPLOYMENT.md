# 🚀 Production Deployment Guide

Complete guide for deploying the Multi-Model AI Chatbot to production.

## 📋 Pre-Deployment Checklist

- [ ] All API keys obtained and tested
- [ ] Firebase project configured
- [ ] PostgreSQL database provisioned
- [ ] Redis cache provisioned
- [ ] Domain name registered
- [ ] SSL certificates obtained
- [ ] AWS/Cloud provider account setup
- [ ] Monitoring tools configured
- [ ] Backup strategy defined

## 🏗️ Architecture Overview

```
                                   ┌─────────────────┐
                                   │   CloudFront    │
                                   │      (CDN)      │
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    │                                               │
            ┌───────▼────────┐                            ┌────────▼────────┐
            │  S3 (Frontend) │                            │  ALB (Backend)  │
            └────────────────┘                            └────────┬────────┘
                                                                   │
                                                    ┌──────────────┴──────────────┐
                                                    │                             │
                                            ┌───────▼────────┐          ┌────────▼────────┐
                                            │  ECS Fargate   │          │  ECS Fargate    │
                                            │   (Backend)    │          │   (Celery)      │
                                            └───────┬────────┘          └────────┬────────┘
                                                    │                            │
                                    ┌───────────────┴────────────────────────────┘
                                    │
                        ┌───────────┴────────────┐
                        │                        │
                ┌───────▼────────┐      ┌───────▼──────────┐
                │  RDS Postgres  │      │  ElastiCache     │
                │    (Database)  │      │     (Redis)      │
                └────────────────┘      └──────────────────┘
```

## 🐳 Docker Production Build

### Backend Dockerfile (Production)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Frontend Dockerfile (Production)

```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## ☁️ AWS Deployment (Recommended)

### Step 1: Setup RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier chatbot-db \
    --db-instance-class db.t3.small \
    --engine postgres \
    --engine-version 15.3 \
    --master-username chatbot_admin \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 20 \
    --storage-type gp3 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name your-subnet-group \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --multi-az \
    --publicly-accessible false

# Get endpoint
aws rds describe-db-instances \
    --db-instance-identifier chatbot-db \
    --query 'DBInstances[0].Endpoint.Address'
```

### Step 2: Setup ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id chatbot-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 1 \
    --cache-subnet-group-name your-subnet-group \
    --security-group-ids sg-xxxxx

# Get endpoint
aws elasticache describe-cache-clusters \
    --cache-cluster-id chatbot-redis \
    --show-cache-node-info
```

### Step 3: Setup ECR (Docker Registry)

```bash
# Create repositories
aws ecr create-repository --repository-name chatbot-backend
aws ecr create-repository --repository-name chatbot-celery

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push images
docker build -t chatbot-backend ./backend
docker tag chatbot-backend:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/chatbot-backend:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/chatbot-backend:latest
```

### Step 4: Setup ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name chatbot-cluster

# Create task definition (save as task-definition.json)
{
  "family": "chatbot-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/chatbot-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:chatbot/db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatbot-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster chatbot-cluster \
    --service-name chatbot-backend \
    --task-definition chatbot-backend:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Step 5: Setup Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name chatbot-alb \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
    --name chatbot-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxx \
    --target-type ip \
    --health-check-path /health

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:... \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### Step 6: Setup Secrets Manager

```bash
# Store database credentials
aws secretsmanager create-secret \
    --name chatbot/database \
    --secret-string '{"url":"postgresql://user:pass@endpoint:5432/chatbot"}'

# Store API keys
aws secretsmanager create-secret \
    --name chatbot/api-keys \
    --secret-string '{
      "gemini": "your-key",
      "openrouter": "your-key"
    }'
```

### Step 7: Setup CloudWatch Monitoring

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/chatbot-backend
aws logs create-log-group --log-group-name /ecs/chatbot-celery

# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name ChatbotMetrics \
    --dashboard-body file://dashboard-config.json
```

### Step 8: Deploy Frontend to S3 + CloudFront

```bash
# Create S3 bucket
aws s3 mb s3://chatbot-frontend-prod

# Configure bucket for static hosting
aws s3 website s3://chatbot-frontend-prod \
    --index-document index.html \
    --error-document index.html

# Build and deploy frontend
cd frontend
npm run build
aws s3 sync build/ s3://chatbot-frontend-prod --delete

# Create CloudFront distribution
aws cloudfront create-distribution \
    --origin-domain-name chatbot-frontend-prod.s3.amazonaws.com \
    --default-root-object index.html
```

## 🔐 Security Configuration

### 1. IAM Roles

Create IAM role for ECS tasks:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "s3:PutObject",
        "s3:GetObject",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Security Groups

**Backend Security Group:**
- Inbound: 8000 from ALB only
- Outbound: 443 to internet (API calls)
- Outbound: 5432 to RDS
- Outbound: 6379 to Redis

**Database Security Group:**
- Inbound: 5432 from backend only

**Redis Security Group:**
- Inbound: 6379 from backend only

### 3. Environment Variables

Production `.env` (stored in Secrets Manager):

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-256-bit-secret-key
ALLOWED_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
SENTRY_DSN=https://...

# Firebase
FIREBASE_PROJECT_ID=...
FIREBASE_PRIVATE_KEY=...
FIREBASE_CLIENT_EMAIL=...

# AI APIs
GEMINI_KEY=...
DEEPSEEK_KEY=...
CLAUDE_KEY=...
GPT_KEY=...
```

## 📊 Monitoring & Logging

### CloudWatch Metrics

Monitor these key metrics:
- ECS CPU/Memory utilization
- RDS connections and performance
- Redis hit/miss ratio
- ALB request count and latency
- Lambda errors (if using)

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

### Log Aggregation

All logs go to CloudWatch Logs with structured JSON:

```python
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push backend
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/chatbot-backend:latest ./backend
          docker push $ECR_REGISTRY/chatbot-backend:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster chatbot-cluster \
            --service chatbot-backend \
            --force-new-deployment
```

## 🔧 Database Migrations

### Alembic Setup

```bash
# Initialize Alembic
cd backend
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations in production
alembic upgrade head
```

### Migration in Production

```bash
# SSH to ECS task or run as one-off task
aws ecs run-task \
    --cluster chatbot-cluster \
    --task-definition chatbot-migration \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

## 📈 Scaling Strategy

### Auto-scaling Configuration

```bash
# Backend service auto-scaling
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/chatbot-cluster/chatbot-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10

# CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/chatbot-cluster/chatbot-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration \
    '{"TargetValue":70,"PredefinedMetricSpecification":{"PredefinedMetricType":"ECSServiceAverageCPUUtilization"}}'
```

## 💾 Backup Strategy

### Database Backups

```bash
# Automated daily backups (already configured in RDS)
# Manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier chatbot-db \
    --db-snapshot-identifier chatbot-manual-snapshot-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier chatbot-db-restored \
    --db-snapshot-identifier chatbot-manual-snapshot-20240101
```

### Application Data Backup

```bash
# Export to S3 daily (Celery task)
@celery_app.task
def backup_to_s3():
    # Backup conversations, analytics, etc.
    pass
```

## 🚨 Disaster Recovery

### Recovery Time Objective (RTO): 1 hour
### Recovery Point Objective (RPO): 24 hours

**Recovery Steps:**
1. Restore database from latest snapshot (15 min)
2. Deploy ECS services to new cluster (20 min)
3. Update DNS records (15 min)
4. Verify functionality (10 min)

## 📝 Maintenance

### Regular Tasks

**Daily:**
- Check CloudWatch alarms
- Review error logs
- Monitor API usage

**Weekly:**
- Review performance metrics
- Check disk space
- Update dependencies (security patches)

**Monthly:**
- Database performance tuning
- Cost optimization review
- Security audit

## 🎯 Performance Benchmarks

Target metrics:
- API Response Time: < 500ms (p95)
- Database Query Time: < 100ms (p95)
- Page Load Time: < 2s
- Uptime: 99.9%
- Error Rate: < 0.1%

## 📞 Support & Troubleshooting

### Common Issues

**High Latency:**
```bash
# Check ECS task health
aws ecs describe-tasks --cluster chatbot-cluster --tasks $(aws ecs list-tasks --cluster chatbot-cluster --query 'taskArns[0]' --output text)

# Check database performance
aws rds describe-db-instance-attribute --db-instance-identifier chatbot-db
```

**Database Connection Issues:**
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx

# Test connection from ECS
aws ecs execute-command \
    --cluster chatbot-cluster \
    --task task-id \
    --command "psql -h endpoint -U user -d chatbot"
```

## ✅ Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] SSL certificates valid
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Backup jobs running
- [ ] DNS propagated
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Team trained on operations

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Version:** _______________