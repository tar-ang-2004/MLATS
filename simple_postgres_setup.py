#!/usr/bin/env python3
"""
Simple PostgreSQL Setup Script for ATS Resume Checker
Creates the database tables without requiring all app dependencies
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Text, Float, Boolean
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Configure logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create database tables directly using SQLAlchemy"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    try:
        logger.info("Connecting to PostgreSQL database...")
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"Connected successfully! PostgreSQL version: {version[:50]}...")
        
        # Create metadata object
        metadata = MetaData()
        
        # Define the resumes table (main table for ATS Resume Checker)
        resumes_table = Table(
            'resumes', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('filename', String(255), nullable=False),
            Column('upload_timestamp', DateTime, default=datetime.utcnow),
            Column('file_size', Integer),
            Column('file_type', String(50)),
            Column('overall_score', Integer),
            Column('classification', String(100)),
            Column('skills_score', Float),
            Column('header_score', Float),
            Column('header_job_title', String(200)),
            Column('experience_score', Float),
            Column('projects_score', Float),
            Column('education_score', Float),
            Column('format_score', Float),
            Column('job_description_hash', String(64)),
            Column('job_description_text', Text),
            Column('verdict', String(50)),
            Column('matched_skills_count', Integer),
            Column('missing_skills_count', Integer),
            Column('extracted_text', Text),
            Column('text_length', Integer),
            Column('processing_time', Float),
            Column('user_ip', String(45)),
            Column('session_id', String(100))
        )
        
        # Define analysis_results table (for detailed analysis data)
        analysis_results_table = Table(
            'analysis_results', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('resume_id', Integer, nullable=False),
            Column('analysis_type', String(50), nullable=False),
            Column('score', Float),
            Column('details', Text),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Define user_sessions table (for session tracking)
        user_sessions_table = Table(
            'user_sessions', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('session_id', String(100), nullable=False, unique=True),
            Column('user_ip', String(45)),
            Column('user_agent', String(500)),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('last_activity', DateTime, default=datetime.utcnow),
            Column('resume_count', Integer, default=0)
        )
        
        # Define processing_metrics table (for performance monitoring)
        processing_metrics_table = Table(
            'processing_metrics', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('metric_name', String(100), nullable=False),
            Column('metric_value', Float),
            Column('metric_unit', String(20)),
            Column('timestamp', DateTime, default=datetime.utcnow),
            Column('session_id', String(100)),
            Column('additional_data', Text)
        )
        
        # Define matched_skills table (for skill matching results)
        matched_skills_table = Table(
            'matched_skills', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('resume_id', Integer, nullable=False),
            Column('skill_name', String(200), nullable=False),
            Column('match_type', String(50)),
            Column('confidence_score', Float),
            Column('job_requirement', String(500)),
            Column('resume_context', String(500)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        logger.info("Creating database tables...")
        
        # Create all tables
        metadata.create_all(engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            logger.info(f"Successfully created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    
    database_url = os.getenv('DATABASE_URL')
    
    try:
        logger.info("Testing database operations...")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test insert
            conn.execute(text("""
                INSERT INTO resumes (filename, file_type, overall_score, classification)
                VALUES ('test_resume.pdf', 'PDF', 85, 'Qualified')
            """))
            
            # Test select
            result = conn.execute(text("SELECT id, filename, overall_score FROM resumes ORDER BY id DESC LIMIT 1"))
            row = result.fetchone()
            
            if row:
                logger.info(f"Test record created: ID={row[0]}, File={row[1]}, Score={row[2]}")
                
                # Clean up test record
                conn.execute(text(f"DELETE FROM resumes WHERE id = {row[0]}"))
                logger.info("Test record cleaned up")
            
            conn.commit()
        
        logger.info("Database operations test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Database operations test failed: {e}")
        return False

def get_database_info():
    """Get database information"""
    
    database_url = os.getenv('DATABASE_URL')
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Get basic info
            result = conn.execute(text("""
                SELECT 
                    current_database() as db_name,
                    current_user as db_user,
                    version() as pg_version
            """))
            
            info = result.fetchone()
            
            print("\n" + "="*60)
            print("DATABASE INFORMATION")
            print("="*60)
            print(f"Database: {info[0]}")
            print(f"User: {info[1]}")
            print(f"Version: {info[2]}")
            
            # Get table count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            print(f"Tables: {table_count}")
            
            # Get database size
            result = conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.fetchone()[0]
            print(f"Size: {db_size}")
            
            print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return False

def main():
    """Main setup function"""
    print("="*60)
    print("PostgreSQL Database Setup for ATS Resume Checker")
    print("="*60)
    
    # Check environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found!")
        print("Make sure your .env file contains the DATABASE_URL")
        return False
    
    # Step 1: Create tables
    if not create_database_tables():
        print("ERROR: Failed to create database tables")
        return False
    
    # Step 2: Test operations
    if not test_database_operations():
        print("WARNING: Database operations test failed")
        print("Tables created but basic operations may have issues")
    
    # Step 3: Show database info
    get_database_info()
    
    print("\n" + "="*60)
    print("SUCCESS! PostgreSQL database is ready!")
    print("="*60)
    print("Your ATS Resume Checker can now use PostgreSQL!")
    print("")
    print("Next steps:")
    print("1. Install missing dependencies: pip install redis celery tensorflow")
    print("2. Start your application: python app.py")
    print("3. Test by uploading a resume")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)