#!/bin/bash
# Production Deployment Script for ATS Resume Checker

set -euo pipefail

echo "🚀 Starting ATS Resume Checker Production Deployment"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs uploads exports instance

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env_template .env
    echo "⚠️  Please edit .env file with your production settings before continuing!"
    echo "   Especially set a secure SECRET_KEY and database credentials."
    read -p "Press Enter when you've configured .env file..."
fi

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose run --rm web python -c "
from app import app, db
from flask_migrate import upgrade
with app.app_context():
    upgrade()
"

# Start services
echo "🎯 Starting production services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health endpoint
echo "🔍 Checking application health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy and running!"
    echo "🌐 Access your application at: http://localhost:8000"
    echo "📊 View logs with: docker-compose logs -f web"
    echo "🛑 Stop services with: docker-compose down"
else
    echo "❌ Application health check failed. Check logs with: docker-compose logs web"
    exit 1
fi

echo "🎉 Deployment completed successfully!"