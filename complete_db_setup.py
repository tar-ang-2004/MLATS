#!/usr/bin/env python3
"""
Complete PostgreSQL Database Setup for ATS Resume Checker
Creates all required tables for the application
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Text, Float, Boolean
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_complete_database():
    """Create all database tables for ATS Resume Checker"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    try:
        logger.info("Creating complete ATS Resume Checker database...")
        engine = create_engine(database_url)
        
        # Create metadata object
        metadata = MetaData()
        
        # Main resumes table
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
        
        # Analysis results table
        analysis_results_table = Table(
            'analysis_results', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('resume_id', Integer, nullable=False),
            Column('analysis_type', String(50), nullable=False),
            Column('score', Float),
            Column('details', Text),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # User sessions table
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
        
        # Processing metrics table
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
        
        # Matched skills table
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
        
        # Missing skills table
        missing_skills_table = Table(
            'missing_skills', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('resume_id', Integer, nullable=False),
            Column('skill_name', String(200), nullable=False),
            Column('skill_category', String(100)),
            Column('importance_level', String(20)),
            Column('job_requirement', String(500)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        logger.info("Creating all database tables...")
        
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
                logger.info(f"  ✓ {table}")
        
        logger.info("Complete database setup successful!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up complete database: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("Complete PostgreSQL Setup for ATS Resume Checker")
    print("="*60)
    
    if create_complete_database():
        print("\n✅ SUCCESS! All database tables created!")
        print("Your ATS Resume Checker database is fully ready!")
        print("\nYou can now run: python app.py")
    else:
        print("\n❌ ERROR: Database setup failed!")
        return False

if __name__ == "__main__":
    main()