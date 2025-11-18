"""
Database initialization and management script for ATS Resume Checker
Run this script to create tables, handle migrations, and manage database
"""

import os
import sys
from flask import Flask
from sqlalchemy import text
from models import db, Resume, ContactInfo, ResumeSkill, Experience, Education, Project
from models import Certification, Achievement, MatchedSkill, MissingSkill, JobDescription
from models import ProcessingLog, Analytics
from config import get_config

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    db.init_app(app)
    
    return app

def init_database():
    """Initialize database and create all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating database tables...")
            
            # Create all tables
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'resumes', 'contact_info', 'resume_skills', 'experiences',
                'education', 'projects', 'certifications', 'achievements',
                'matched_skills', 'missing_skills', 'job_descriptions',
                'processing_logs', 'analytics'
            ]
            
            created_tables = [table for table in expected_tables if table in tables]
            
            print(f"✓ Successfully created {len(created_tables)} tables:")
            for table in created_tables:
                print(f"  - {table}")
            
            if len(created_tables) != len(expected_tables):
                missing = set(expected_tables) - set(created_tables)
                print(f"⚠ Missing tables: {missing}")
            
            print("✓ Database initialization completed successfully!")
            
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            return False
    
    return True

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    app = create_app()
    
    with app.app_context():
        try:
            print("⚠ WARNING: This will delete ALL data in the database!")
            confirmation = input("Type 'YES' to confirm: ")
            
            if confirmation == 'YES':
                db.drop_all()
                print("✓ All tables dropped successfully!")
            else:
                print("Operation cancelled.")
                
        except Exception as e:
            print(f"✗ Error dropping tables: {e}")

def reset_database():
    """Reset database by dropping and recreating all tables"""
    print("Resetting database...")
    drop_all_tables()
    init_database()

def check_database_connection():
    """Check if database connection is working"""
    app = create_app()
    
    with app.app_context():
        try:
            # Try a simple query
            result = db.session.execute(text('SELECT 1')).scalar()
            
            if result == 1:
                print("✓ Database connection successful!")
                
                # Get database info
                db_url = app.config['SQLALCHEMY_DATABASE_URI']
                if db_url.startswith('sqlite'):
                    db_type = "SQLite"
                    db_file = db_url.split('///')[-1]
                    print(f"  Database: {db_type} ({db_file})")
                elif db_url.startswith('postgresql'):
                    db_type = "PostgreSQL"
                    print(f"  Database: {db_type}")
                else:
                    print(f"  Database: {db_url}")
                
                return True
                
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

def get_database_stats():
    """Get statistics about the database"""
    app = create_app()
    
    with app.app_context():
        try:
            stats = {}
            
            # Count records in each table
            stats['resumes'] = Resume.query.count()
            stats['contact_info'] = ContactInfo.query.count()
            stats['skills'] = ResumeSkill.query.count()
            stats['experiences'] = Experience.query.count()
            stats['education'] = Education.query.count()
            stats['projects'] = Project.query.count()
            stats['certifications'] = Certification.query.count()
            stats['achievements'] = Achievement.query.count()
            stats['matched_skills'] = MatchedSkill.query.count()
            stats['missing_skills'] = MissingSkill.query.count()
            stats['job_descriptions'] = JobDescription.query.count()
            stats['processing_logs'] = ProcessingLog.query.count()
            
            print("📊 Database Statistics:")
            print("-" * 30)
            for table, count in stats.items():
                print(f"  {table:<20}: {count:>6,}")
            
            # Calculate total records
            total = sum(stats.values())
            print("-" * 30)
            print(f"  {'Total Records':<20}: {total:>6,}")
            
            # Recent activity
            recent_resumes = Resume.query.order_by(Resume.upload_timestamp.desc()).limit(5).all()
            
            if recent_resumes:
                print("\n📅 Recent Activity:")
                print("-" * 50)
                for resume in recent_resumes:
                    print(f"  {resume.filename[:30]:<30} | Score: {resume.overall_score:>3} | {resume.upload_timestamp.strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            print(f"✗ Error getting database stats: {e}")

def backup_database(backup_path=None):
    """Create a backup of the database (SQLite only)"""
    app = create_app()
    
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        if not db_url.startswith('sqlite'):
            print("⚠ Backup is only supported for SQLite databases")
            print("For PostgreSQL, use pg_dump or your hosting provider's backup tools")
            return
        
        try:
            import shutil
            from datetime import datetime
            
            # Get source database file
            source_db = db_url.split('///')[-1]
            
            if not os.path.exists(source_db):
                print(f"✗ Database file not found: {source_db}")
                return
            
            # Create backup filename
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_ats_resume_checker_{timestamp}.db"
            
            # Copy database file
            shutil.copy2(source_db, backup_path)
            
            print(f"✓ Database backed up to: {backup_path}")
            print(f"  Backup size: {os.path.getsize(backup_path):,} bytes")
            
        except Exception as e:
            print(f"✗ Error creating backup: {e}")

def migrate_json_history():
    """Migrate data from JSON score history to database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if old score history file exists
            score_history_file = 'score_history.json'
            
            if not os.path.exists(score_history_file):
                print("No JSON score history file found to migrate")
                return
            
            import json
            from datetime import datetime
            
            with open(score_history_file, 'r') as f:
                history = json.load(f)
            
            print(f"Migrating {len(history)} records from JSON history...")
            
            migrated = 0
            for entry in history:
                try:
                    # Create basic resume record from history
                    resume = Resume(
                        filename=entry.get('filename', 'unknown'),
                        overall_score=int(entry.get('score', 0)),
                        classification='Unknown',
                        upload_timestamp=datetime.fromisoformat(entry['timestamp']) if 'timestamp' in entry else datetime.utcnow()
                    )
                    
                    db.session.add(resume)
                    migrated += 1
                    
                except Exception as e:
                    print(f"Error migrating entry {entry}: {e}")
            
            db.session.commit()
            print(f"✓ Successfully migrated {migrated} records")
            
            # Optionally rename old file
            backup_name = f"{score_history_file}.backup"
            os.rename(score_history_file, backup_name)
            print(f"✓ Original file backed up as {backup_name}")
            
        except Exception as e:
            print(f"✗ Error migrating JSON history: {e}")
            db.session.rollback()

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("ATS Resume Checker - Database Management")
        print("=" * 40)
        print("Usage: python init_db.py <command>")
        print("\nCommands:")
        print("  init      - Initialize database and create tables")
        print("  check     - Check database connection")
        print("  stats     - Show database statistics")
        print("  reset     - Reset database (drops all data!)")
        print("  backup    - Create database backup (SQLite only)")
        print("  migrate   - Migrate from JSON score history")
        print("\nExamples:")
        print("  python init_db.py init")
        print("  python init_db.py check")
        print("  python init_db.py stats")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        init_database()
    elif command == 'check':
        check_database_connection()
    elif command == 'stats':
        get_database_stats()
    elif command == 'reset':
        reset_database()
    elif command == 'backup':
        backup_path = sys.argv[2] if len(sys.argv) > 2 else None
        backup_database(backup_path)
    elif command == 'migrate':
        migrate_json_history()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python init_db.py' for help")

if __name__ == '__main__':
    main()