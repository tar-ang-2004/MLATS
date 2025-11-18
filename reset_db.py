#!/usr/bin/env python3
"""
Reset Database Schema for Heroku PostgreSQL
Drops all tables and recreates them with proper UUID schema
"""

import os
import sys
from config import get_config
from models import db
from flask import Flask
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database schema"""
    # Initialize Flask app with configuration
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Initialize database with app
    db.init_app(app)
    
    with app.app_context():
        try:
            logger.info("Connecting to database...")
            
            # Drop all tables
            logger.info("Dropping all existing tables...")
            db.drop_all()
            
            # Create all tables with new schema
            logger.info("Creating new tables with UUID schema...")
            db.create_all()
            
            logger.info("Database reset completed successfully!")
            
            # Test connection
            from sqlalchemy import text
            result = db.session.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            logger.info(f"Connected to: {version}")
            
            # Check table creation
            result = db.session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {tables}")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    reset_database()