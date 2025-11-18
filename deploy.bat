@echo off
REM Production Deployment Script for ATS Resume Checker (Windows)

echo 🚀 Starting ATS Resume Checker Production Deployment

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not available. Please install Docker Desktop with Compose.
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist exports mkdir exports
if not exist instance mkdir instance

REM Copy environment template if .env doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env_template .env
    echo ⚠️  Please edit .env file with your production settings before continuing!
    echo    Especially set a secure SECRET_KEY and database credentials.
    pause
)

REM Build Docker image
echo 🏗️  Building Docker image...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    pause
    exit /b 1
)

REM Run database migrations
echo 🗄️  Running database migrations...
docker-compose run --rm web python -c "from app import app, db; from flask_migrate import upgrade; app.app_context().push(); upgrade()"

REM Start services
echo 🎯 Starting production services...
docker-compose up -d

REM Wait for services to be healthy
echo ⏳ Waiting for services to be healthy...
timeout /t 10 /nobreak

REM Check health endpoint
echo 🔍 Checking application health...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application is healthy and running!
    echo 🌐 Access your application at: http://localhost:8000
    echo 📊 View logs with: docker-compose logs -f web
    echo 🛑 Stop services with: docker-compose down
) else (
    echo ❌ Application health check failed. Check logs with: docker-compose logs web
    pause
    exit /b 1
)

echo 🎉 Deployment completed successfully!
pause