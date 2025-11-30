@echo off
REM Multi-Model AI Chatbot - Windows Setup Script
REM This creates the entire project automatically!

echo ========================================
echo Multi-Model AI Chatbot Setup
echo ========================================
echo.

REM Create project directory
set PROJECT_NAME=multi-model-chatbot
echo Creating project: %PROJECT_NAME%
mkdir %PROJECT_NAME%
cd %PROJECT_NAME%

REM Create folder structure
echo Creating folders...
mkdir backend
mkdir frontend\src
mkdir frontend\public
mkdir nginx
mkdir logs

echo ✓ Folders created!
echo.

REM Create .env.example
echo Creating configuration files...
(
echo # Database Configuration
echo DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_db
echo REDIS_URL=redis://localhost:6379/0
echo.
echo # AI Model API Keys
echo GEMINI_KEY=your_gemini_api_key_here
echo DEEPSEEK_KEY=your_openrouter_key_here
echo CLAUDE_KEY=your_openrouter_key_here
echo GPT_KEY=your_openrouter_key_here
echo.
echo # Application Settings
echo SECRET_KEY=change-this-secret-key
echo ALLOWED_ORIGINS=http://localhost:3000
echo ENVIRONMENT=development
) > .env.example

copy .env.example .env

REM Create requirements.txt
(
echo fastapi==0.104.1
echo uvicorn[standard]==0.24.0
echo python-multipart==0.0.6
echo websockets==12.0
echo sqlalchemy==2.0.23
echo psycopg2-binary==2.9.9
echo redis==5.0.1
echo python-dotenv==1.0.0
echo pydantic[email]==2.5.0
echo requests==2.31.0
echo httpx==0.25.2
echo aiohttp==3.9.1
echo numpy==1.26.2
echo pandas==2.1.3
echo openpyxl==3.1.2
) > backend\requirements.txt

REM Create package.json
(
echo {
echo   "name": "chatbot-frontend",
echo   "version": "1.0.0",
echo   "private": true,
echo   "dependencies": {
echo     "react": "^18.2.0",
echo     "react-dom": "^18.2.0",
echo     "react-scripts": "5.0.1",
echo     "axios": "^1.6.2"
echo   },
echo   "scripts": {
echo     "start": "react-scripts start",
echo     "build": "react-scripts build"
echo   },
echo   "proxy": "http://localhost:8000"
echo }
) > frontend\package.json

REM Create index.html
(
echo ^<!DOCTYPE html^>
echo ^<html lang="en"^>
echo   ^<head^>
echo     ^<meta charset="utf-8" /^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1" /^>
echo     ^<title^>AI Chatbot^</title^>
echo   ^</head^>
echo   ^<body^>
echo     ^<div id="root"^>^</div^>
echo   ^</body^>
echo ^</html^>
) > frontend\public\index.html

REM Create index.js
(
echo import React from 'react';
echo import ReactDOM from 'react-dom/client';
echo import './App.css';
echo import App from './App';
echo.
echo const root = ReactDOM.createRoot(document.getElementById('root'^)^);
echo root.render(^<App /^>^);
) > frontend\src\index.js

REM Create docker-compose.yml
(
echo version: '3.8'
echo.
echo services:
echo   postgres:
echo     image: postgres:15-alpine
echo     container_name: chatbot_postgres
echo     environment:
echo       POSTGRES_USER: chatbot_user
echo       POSTGRES_PASSWORD: chatbot_password
echo       POSTGRES_DB: chatbot_db
echo     ports:
echo       - "5432:5432"
echo.
echo   redis:
echo     image: redis:7-alpine
echo     container_name: chatbot_redis
echo     ports:
echo       - "6379:6379"
echo.
echo   backend:
echo     build: ./backend
echo     ports:
echo       - "8000:8000"
echo     env_file:
echo       - .env
echo     depends_on:
echo       - postgres
echo       - redis
echo.
echo   frontend:
echo     build: ./frontend
echo     ports:
echo       - "3000:3000"
) > docker-compose.yml

REM Create README
(
echo # Multi-Model AI Chatbot
echo.
echo ## Quick Start
echo.
echo 1. Edit .env file with your API keys
echo 2. Run: docker-compose up
echo 3. Visit: http://localhost:3000
echo.
echo ## Get API Keys
echo - Gemini: https://makersuite.google.com/app/apikey
echo - OpenRouter: https://openrouter.ai/keys
) > README.md

REM Create .gitignore
(
echo .env
echo __pycache__/
echo venv/
echo node_modules/
echo build/
echo *.log
) > .gitignore

REM Create backend Dockerfile
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo COPY requirements.txt .
echo RUN pip install -r requirements.txt
echo COPY . .
echo EXPOSE 8000
echo CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
) > backend\Dockerfile

REM Create frontend Dockerfile
(
echo FROM node:18-alpine
echo WORKDIR /app
echo COPY package*.json ./
echo RUN npm install
echo COPY . .
echo EXPOSE 3000
echo CMD ["npm", "start"]
) > frontend\Dockerfile

echo.
echo ✓ All configuration files created!
echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo NEXT STEPS:
echo.
echo 1. Get API Keys:
echo    - Gemini: https://makersuite.google.com/app/apikey
echo    - OpenRouter: https://openrouter.ai/keys
echo.
echo 2. Edit .env file and add your keys:
echo    notepad .env
echo.
echo 3. Copy these files from artifacts to your project:
echo    - backend\main.py
echo    - backend\ai_orchestrator.py  
echo    - backend\celery_app.py
echo    - frontend\src\App.jsx
echo    - frontend\src\App.css
echo.
echo 4. Start the app:
echo    docker-compose up
echo.
echo 5. Open browser:
echo    http://localhost:3000
echo.
echo Your project is at: %CD%
echo.
pause