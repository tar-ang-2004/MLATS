"""Logging Configuration for Production and Development"""

import logging
import logging.config
import os
from datetime import datetime

def setup_logging(app):
    """Setup structured logging for the Flask application"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file names with timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '[%(asctime)s] %(levelname)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG' if app.debug else 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file_info': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': os.path.join(log_dir, f'app_info_{timestamp}.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': os.path.join(log_dir, f'app_error_{timestamp}.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'security_log': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'json',
                'filename': os.path.join(log_dir, f'security_{timestamp}.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file_info', 'file_error'],
                'level': 'DEBUG' if app.debug else 'INFO',
                'propagate': False
            },
            'security': {
                'handlers': ['security_log', 'file_error'],
                'level': 'WARNING',
                'propagate': False
            },
            'werkzeug': {
                'handlers': ['file_info'],
                'level': 'INFO',
                'propagate': False
            },
            'sqlalchemy.engine': {
                'handlers': ['file_info'] if not app.debug else ['console'],
                'level': 'WARNING' if not app.debug else 'INFO',
                'propagate': False
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set Flask app logger
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Add security logger
    security_logger = logging.getLogger('security')
    
    # Store reference in app for use in views
    app.security_logger = security_logger
    
    app.logger.info("Logging configuration initialized")
    
    return app.logger, security_logger