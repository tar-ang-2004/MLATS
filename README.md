# 🚀 ATS Resume Checker

A comprehensive, production-ready ATS (Applicant Tracking System) resume analysis tool built with Flask, featuring advanced ML-powered scoring, real-time monitoring, and enterprise-grade optimizations.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Production Deployment](#-production-deployment)
- [Monitoring & Analytics](#-monitoring--analytics)
- [Backup & Recovery](#-backup--recovery)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Features

### Core Functionality
- **📄 Multi-format Support**: PDF and DOCX resume parsing
- **🎯 ATS Scoring**: Comprehensive scoring across 6 key areas
- **🔍 Semantic Matching**: Advanced skill matching using sentence transformers
- **📊 Detailed Analytics**: Section-by-section analysis with recommendations
- **💼 Contact Extraction**: Automatic extraction of contact information

### Production Optimizations
- **⚡ Redis Caching**: ML model result caching and enhanced rate limiting
- **🔄 Async Processing**: Background task processing with Celery
- **🏊 Connection Pooling**: Optimized database performance
- **🧠 Smart Model Loading**: Singleton pattern for ML model management
- **📈 Prometheus Metrics**: Comprehensive application monitoring
- **🏥 Health Checks**: Detailed component status monitoring
- **🔍 Query Monitoring**: Database performance tracking and slow query detection
- **⏱️ Processing Analytics**: Stage-by-stage performance analysis
- **💾 Automated Backup**: PostgreSQL/SQLite backup with scheduling

### Security & Reliability
- **🛡️ CSRF Protection**: Cross-site request forgery protection
- **🔒 Security Headers**: Comprehensive security with Flask-Talisman
- **🚦 Rate Limiting**: Intelligent rate limiting with Redis backend
- **📝 Audit Logging**: Comprehensive logging and audit trails
- **🔄 Graceful Degradation**: Optional dependency management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis Server (optional, for caching and async processing)
- PostgreSQL (optional, for production)

### 1-Minute Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ats-resume-checker.git
cd ats-resume-checker

# Install dependencies
pip install -r requirements.txt

# Configure environment (modify .env as needed)
# The .env file contains production-ready defaults

# Initialize database
python init_db.py

# Run the application
python app.py
```

Visit `http://localhost:5000` and start analyzing resumes! 🎉

## 📦 Installation

### Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ats-resume-checker.git
   cd ats-resume-checker
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download ML Models**
   ```bash
   python -c "
   from sentence_transformers import SentenceTransformer
   SentenceTransformer('all-MiniLM-L6-v2')
   print('✅ Models downloaded successfully')
   "
   ```

5. **Configure Environment**
   ```bash
   # The .env file is already configured with production defaults
   # Edit .env file with your specific settings if needed
   ```

6. **Initialize Database**
   ```bash
   python init_db.py
   ```

7. **Run Development Server**
   ```bash
   python app.py
   ```

### Production Setup

For production deployment, see the [Production Deployment](#-production-deployment) section.

## ⚙️ Configuration

### Environment Variables

The application uses environment variables for configuration. The included `.env` file contains production-ready defaults that you can customize:

#### Essential Configuration
```bash
# Security (REQUIRED for production)
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/ats_resume_checker

# Redis (optional but recommended)
REDIS_URL=redis://localhost:6379/1
```

#### Performance Optimization
```bash
# Enable async processing
ASYNC_PROCESSING=true
CELERY_BROKER_URL=redis://localhost:6379/2

# Database connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Caching
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300
```

#### Monitoring & Backup
```bash
# Prometheus metrics
METRICS_ENABLED=true

# Backup configuration
BACKUP_DIR=./backups
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESS=true

# Analytics
ANALYTICS_ENABLED=true
LOG_PROCESSING_TIMES=true
```

### Database Configuration

#### SQLite (Development)
```bash
# No DATABASE_URL needed - SQLite is used automatically
```

#### PostgreSQL (Production)
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/ats_resume_checker

# Create database
createdb ats_resume_checker
python init_db.py
```

#### Database Migration
```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## 📖 Usage

### Web Interface

1. **Upload Resume**: Navigate to the home page and upload a PDF or DOCX resume
2. **Add Job Description**: Paste the target job description
3. **Analyze**: Click "Analyze Resume" to get comprehensive scoring
4. **Review Results**: View detailed breakdown across all scoring categories

### API Usage

The application provides a comprehensive REST API:

```python
import requests

# Analyze resume via API
files = {'resume': open('resume.pdf', 'rb')}
data = {'job_description': 'Python developer position...'}

response = requests.post('http://localhost:5000/analyze', 
                        files=files, data=data)
result = response.json()

print(f"Overall Score: {result['overall_score']}")
print(f"Matched Skills: {result['details']['matched_skills']}")
```

### Command Line Tools

#### Backup Management
```bash
# Create manual backup
python scheduled_backup.py --name manual_backup

# List backups
curl http://localhost:5000/api/backup/list

# Restore from backup
curl -X POST http://localhost:5000/api/backup/restore/backup_name
```

#### Database Maintenance
```bash
# Run database maintenance
curl -X POST http://localhost:5000/api/database/maintenance \
  -H "Content-Type: application/json" \
  -d '{"operations": ["analyze", "vacuum"]}'
```

## 🔌 API Documentation

### Core Endpoints

#### Resume Analysis
```http
POST /analyze
Content-Type: multipart/form-data

Parameters:
- resume (file): PDF or DOCX file
- job_description (string): Target job description

Response:
{
  "success": true,
  "overall_score": 85,
  "classification": "Good Match",
  "scores": {
    "skills": 90.5,
    "experience": 80.0,
    "education": 85.5,
    ...
  },
  "details": {
    "matched_skills": ["Python", "Flask"],
    "missing_skills": ["React", "AWS"]
  }
}
```

#### Resume Management
```http
GET /api/resumes                    # List processed resumes
GET /api/resumes/{id}              # Get specific resume details
DELETE /api/resumes/{id}           # Delete resume (with retention check)
```

### Monitoring Endpoints

#### Health Monitoring
```http
GET /health                        # Basic health check
GET /api/admin/dashboard          # Administrative overview
```

#### Database Performance
```http
GET /api/database/performance     # Query performance metrics
GET /api/database/slow-queries    # Slow query analysis
GET /api/database/info           # Database information
```

#### Processing Analytics
```http
GET /api/processing/statistics    # Processing performance stats
GET /api/processing/active       # Currently active sessions
GET /api/processing/recent       # Recent processing history
```

#### Backup Management
```http
POST /api/backup/create          # Create new backup
GET /api/backup/list            # List all backups
POST /api/backup/restore/{name} # Restore from backup
DELETE /api/backup/delete/{name} # Delete backup
```

### Rate Limits

| Endpoint Category | Rate Limit |
|------------------|------------|
| Resume Analysis | 10/minute |
| Database Admin | 3/hour |
| Backup Operations | 3/hour (create), 2/hour (restore) |
| Monitoring | 30/minute |
| General API | 200/hour |

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ats
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: ats
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5
preload_app = True
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/ats-resume-checker
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/ats-resume-checker/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Cloud Platform Deployment

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=postgresql://...
heroku config:set REDIS_URL=redis://...

# Add buildpacks
heroku buildpacks:add heroku/python

# Deploy
git push heroku main

# Run migrations
heroku run python init_db.py
```

#### Railway
```bash
# Install Railway CLI
railway login
railway init

# Set environment variables
railway variables:set SECRET_KEY=your-secret-key

# Deploy
railway up
```

#### DigitalOcean App Platform
```yaml
# .do/app.yaml
name: ats-resume-checker
services:
- name: web
  source_dir: /
  github:
    repo: your-username/ats-resume-checker
    branch: main
  run_command: gunicorn --worker-tmp-dir /dev/shm wsgi:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
  - key: REDIS_URL
    value: ${redis.DATABASE_URL}
databases:
- name: db
  engine: PG
  version: "14"
- name: redis
  engine: REDIS
  version: "7"
```

## 📊 Monitoring & Analytics

### Application Metrics

The application exposes Prometheus metrics at `/metrics`:

```bash
# Key metrics available
ats_processing_duration_seconds    # Processing time by stage
ats_resume_score_distribution     # Score distribution
ats_skill_matches_total          # Skill matching statistics
ats_database_queries_total       # Database query metrics
ats_cache_operations_total       # Cache hit/miss rates
```

### Grafana Dashboard

Import the included Grafana dashboard (`monitoring/grafana-dashboard.json`) for comprehensive monitoring:

- Processing performance trends
- Database query performance
- Cache efficiency metrics
- System resource utilization
- Business metrics (scores, matches, etc.)

### Log Analysis

Structured logging is available in multiple formats:

```bash
# Application logs
tail -f logs/app.log

# Processing performance logs
grep "PROCESSING_TIME" logs/app.log

# Security audit logs
grep "SECURITY" logs/security.log

# Database performance logs
grep "SLOW_QUERY" logs/app.log
```

### Alerting

Set up alerts for critical metrics:

```yaml
# prometheus/alerts.yml
groups:
- name: ats-resume-checker
  rules:
  - alert: HighProcessingTime
    expr: ats_processing_duration_seconds{stage="resume_scoring"} > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High resume processing time detected"

  - alert: DatabaseSlowQueries
    expr: rate(ats_database_queries_total{status="slow"}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High number of slow database queries"
```

## 💾 Backup & Recovery

### Automated Backups

Set up automated backups using the included script:

```bash
# Daily backups at 2 AM
0 2 * * * cd /path/to/ats && python scheduled_backup.py --quiet

# Weekly backups with longer retention
0 3 * * 0 cd /path/to/ats && BACKUP_RETENTION_DAYS=90 python scheduled_backup.py --name weekly_$(date +\%Y\%m\%d) --quiet
```

### Manual Backup Operations

```bash
# Create immediate backup
curl -X POST http://localhost:5000/api/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "pre_deployment", "compress": true}'

# List all backups
curl http://localhost:5000/api/backup/list

# Restore from backup (CAUTION: This overwrites current data)
curl -X POST http://localhost:5000/api/backup/restore/backup_name
```

### Disaster Recovery

1. **Database Corruption**: Restore from most recent backup
2. **Data Loss**: Use point-in-time recovery for PostgreSQL
3. **System Failure**: Deploy from git repository + restore database

See `BACKUP_README.md` for comprehensive backup documentation.

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test category
python -m pytest tests/test_ats_components.py
```

### Integration Tests
```bash
# Test database operations
python -m pytest tests/test_database.py

# Test API endpoints
python -m pytest tests/test_api.py

# Test file processing
python -m pytest tests/test_processing.py
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:5000
```

### Performance Testing
```bash
# Test processing performance
python test_scoring.py

# Verify production optimizations
python verify_production.py
```

## 🔧 Development

### Code Structure

```
ats-resume-checker/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── config.py             # Configuration management
├── ats_components.py     # Core ATS functionality
├── requirements.txt      # Python dependencies
├── 
├── optimization/         # Production optimizations
│   ├── cache_utils.py    # Redis caching
│   ├── celery_config.py  # Background processing
│   ├── metrics.py        # Prometheus metrics
│   ├── database_monitor.py # Query monitoring
│   ├── backup_manager.py # Backup system
│   └── processing_tracker.py # Performance tracking
│
├── templates/           # HTML templates
├── static/             # CSS, JS, images
├── uploads/            # Uploaded files
├── backups/            # Database backups
├── logs/              # Application logs
├── tests/             # Test suite
└── docs/              # Documentation
```

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Implement Feature**
   - Add code in appropriate modules
   - Include comprehensive error handling
   - Add logging and metrics
   - Update configuration if needed

3. **Add Tests**
   ```bash
   # Add unit tests
   tests/test_new_feature.py
   
   # Add integration tests
   tests/integration/test_new_feature.py
   ```

4. **Update Documentation**
   - Update README.md
   - Add API documentation
   - Include configuration examples

5. **Submit Pull Request**

### Code Style

The project follows PEP 8 with some modifications:

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Security check
bandit -r .
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

### Reporting Issues

Please use the [GitHub Issues](https://github.com/yourusername/ats-resume-checker/issues) page to report bugs or request features.

Include:
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment information
- Relevant log outputs

## 📞 Support

- **Documentation**: Full documentation in the `/docs` directory
- **API Reference**: Available at `/api/docs` when running the application
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/ats-resume-checker/issues)
- **Discussions**: Join discussions in [GitHub Discussions](https://github.com/yourusername/ats-resume-checker/discussions)

## 🏆 Acknowledgments

- **Sentence Transformers**: For semantic similarity matching
- **spaCy**: For natural language processing
- **Flask Ecosystem**: For the robust web framework
- **Scikit-learn**: For machine learning capabilities
- **Contributors**: Thanks to all who have contributed to this project

## 📝 Changelog

### v2.0.0 (Latest)
- ✨ Added comprehensive production optimizations
- 🚀 Redis caching and async processing
- 📊 Prometheus metrics and monitoring
- 💾 Automated backup system
- 🔍 Database query monitoring
- ⏱️ Processing time analytics
- 🏥 Enhanced health checks

### v1.0.0
- 🎉 Initial release
- 📄 Multi-format resume parsing
- 🎯 ATS scoring algorithm
- 🔍 Semantic skill matching
- 📊 Web interface and API

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by the ATS Resume Checker Team**

[Website](https://your-domain.com) • [Documentation](https://docs.your-domain.com) • [API Reference](https://api.your-domain.com)

</div>