"""
WSGI Entry Point for Production Deployment
Production-ready Flask application entry point with proper configuration
"""

import os
from app import app
from config import get_config

# Set production environment if not already set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

# Load production configuration
config = get_config()
app.config.from_object(config)

# Ensure we're not in debug mode for production
app.config['DEBUG'] = False

if __name__ == "__main__":
    # This should only be used for development testing
    # In production, use: gunicorn wsgi:app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))