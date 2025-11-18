"""
Database migration script for ATS Resume Checker
Handle migration from integer IDs to UUIDs if needed
"""

import os
from sqlalchemy import create_engine, inspect, text
from models import db
from config import get_config
from app import app

def check_existing_tables():
    """Check what tables exist and their structure"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Existing tables: {tables}")
            
            if 'resumes' in tables:
                columns = inspector.get_columns('resumes')
                print("Resume table columns:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            
            return tables
    except Exception as e:
        print(f"Error checking tables: {e}")
        return []

def drop_and_recreate():
    """Drop all tables and recreate with proper schema"""
    try:
        with app.app_context():
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables with new schema...")
            db.create_all()
            print("Database recreated successfully!")
            return True
    except Exception as e:
        print(f"Error recreating database: {e}")
        return False

if __name__ == "__main__":
    print("ATS Resume Checker Database Migration")
    print("=" * 50)
    
    # Check existing tables
    existing_tables = check_existing_tables()
    
    if existing_tables:
        print("\nExisting database found. To avoid compatibility issues,")
        print("we'll drop and recreate all tables with the new schema.")
        
        response = input("Continue? (y/N): ").lower().strip()
        if response == 'y':
            if drop_and_recreate():
                print("\n✅ Database migration completed successfully!")
            else:
                print("\n❌ Database migration failed!")
        else:
            print("Migration cancelled.")
    else:
        print("No existing tables found. Creating new database...")
        if drop_and_recreate():
            print("\n✅ Database created successfully!")
        else:
            print("\n❌ Database creation failed!")