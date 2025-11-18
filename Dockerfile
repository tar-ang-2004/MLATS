# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=wsgi.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p logs uploads exports static templates && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Remove any development/test files
RUN rm -rf __pycache__ *.pyc .git .gitignore README.md *.md

# Switch to non-root user
USER appuser

# Create volume for persistent data
VOLUME ["/app/logs", "/app/uploads", "/app/exports"]

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]