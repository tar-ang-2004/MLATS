"""
Database configuration for ATS Resume Checker
Production-ready configuration with environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    
    # Flask settings - generate secure random key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print("⚠️  WARNING: Using generated SECRET_KEY. Set SECRET_KEY environment variable for production.")
    
    # Database configuration
    # PostgreSQL is recommended for production
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Production database (PostgreSQL)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        # Fix for Heroku postgres:// URLs
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    else:
        # Development database (SQLite)
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'ats_resume_checker.db')}"
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Enhanced connection pooling configuration
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        """Dynamic engine options based on database type"""
        if self.DATABASE_URL and 'postgresql' in self.DATABASE_URL:
            # PostgreSQL production configuration
            return {
                'pool_size': 10,           # Base number of connections
                'max_overflow': 20,        # Additional connections when busy
                'pool_pre_ping': True,     # Validate connections before use
                'pool_recycle': 3600,      # Recycle connections every hour
                'pool_timeout': 30,        # Wait time for connection
                'echo': False,             # Disable SQL echo in production
                'connect_args': {
                    'connect_timeout': 10,
                    'options': '-csearch_path=public',
                    'application_name': 'ats_resume_checker'
                }
            }
        else:
            # SQLite development configuration
            return {
                'pool_timeout': 20,
                'pool_recycle': -1,        # SQLite doesn't need connection recycling
                'pool_pre_ping': False,    # Not needed for SQLite
                'echo': False,
                'connect_args': {
                    'check_same_thread': False,  # Allow SQLite usage across threads
                    'timeout': 20
                }
            }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    # Rate limiting (memory-based)
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Analytics and monitoring
    ANALYTICS_ENABLED = os.environ.get('ANALYTICS_ENABLED', 'true').lower() == 'true'
    LOG_PROCESSING_TIMES = os.environ.get('LOG_PROCESSING_TIMES', 'true').lower() == 'true'
    
    # Security settings
    STORE_IP_ADDRESSES = os.environ.get('STORE_IP_ADDRESSES', 'false').lower() == 'true'
    DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', '365'))
    
    # Performance settings
    ASYNC_PROCESSING = os.environ.get('ASYNC_PROCESSING', 'false').lower() == 'true'
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Backup configuration
    BACKUP_DIR = os.environ.get('BACKUP_DIR', './backups')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
    BACKUP_COMPRESS = os.environ.get('BACKUP_COMPRESS', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Use SQLite for development
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'ats_resume_checker_dev.db')}"
    
    # More verbose logging in development
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration with security and performance optimizations"""
    DEBUG = False
    TESTING = False
    
    # Use DATABASE_URL if available, otherwise raise error at runtime
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Normalize old Heroku-style URLs
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/ats_resume_checker'
    
    # Production security - use environment variables (REQUIRED)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Performance optimizations
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
        'pool_pre_ping': True
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable analytics in testing
    ANALYTICS_ENABLED = False
    LOG_PROCESSING_TIMES = False
    STORE_IP_ADDRESSES = False

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, config_map['default'])

# Database connection helper
def get_database_url():
    """Get the database URL for the current environment"""
    config = get_config()
    return config.SQLALCHEMY_DATABASE_URI