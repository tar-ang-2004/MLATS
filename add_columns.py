#!/usr/bin/env python3
"""
Add new columns to existing database
"""

import sqlite3
import os

def add_columns():
    """Add job_description_text and verdict columns to resumes table"""
    db_path = "ats_resume_checker_dev.db"
    
    if not os.path.exists(db_path):
        print("Database not found. Please run 'python init_db.py init' first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'job_description_text' not in columns:
            print("Adding job_description_text column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN job_description_text TEXT")
            
        if 'verdict' not in columns:
            print("Adding verdict column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN verdict VARCHAR(500)")
        
        conn.commit()
        print("✓ Database updated successfully!")
        
        # Show updated columns
        cursor.execute("PRAGMA table_info(resumes)")
        print("\nUpdated resumes table columns:")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()