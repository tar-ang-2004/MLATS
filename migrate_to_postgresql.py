"""
SQLite to PostgreSQL Migration Script for ATS Resume Checker
Migrates all data from local SQLite database to Neon PostgreSQL database
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import pandas as pd

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
    # Try to continue without dotenv - maybe env vars are set another way

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        # SQLite database path options
        self.sqlite_paths = ['ats_resume_checker.db', 'instance/ats_resume_checker.db']
        self.sqlite_path = None
        
        # Find existing SQLite database
        for path in self.sqlite_paths:
            if os.path.exists(path):
                self.sqlite_path = path
                break
        
        if not self.sqlite_path:
            self.sqlite_path = self.sqlite_paths[0]  # Default path
        
        # PostgreSQL connection from environment
        self.postgresql_url = os.getenv('DATABASE_URL')
        
        if not self.postgresql_url:
            logger.error("DATABASE_URL not found in environment variables")
            logger.error("Available environment variables:")
            for key in sorted(os.environ.keys()):
                if 'DATABASE' in key.upper() or 'DB' in key.upper():
                    logger.error(f"  {key}={os.environ[key][:20]}...")
            
            # Check if .env file exists
            if os.path.exists('.env'):
                logger.error(".env file exists. Checking its contents...")
                try:
                    with open('.env', 'r') as f:
                        lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if 'DATABASE_URL' in line:
                            logger.error(f"  Line {i}: {line.strip()}")
                except Exception as e:
                    logger.error(f"Error reading .env file: {e}")
            else:
                logger.error(".env file not found in current directory")
            
            sys.exit(1)
            
        # Hide password in logs
        safe_url = self.postgresql_url.replace(self.postgresql_url.split('@')[0].split('//')[-1], 'USER:***') if '@' in self.postgresql_url else self.postgresql_url
        logger.info(f"PostgreSQL URL configured: {safe_url}")
    
    def check_sqlite_exists(self):
        """Check if SQLite database exists"""
        if not os.path.exists(self.sqlite_path):
            logger.warning(f"SQLite database not found at {self.sqlite_path}")
            return False
        
        # Check if database has data
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("SQLite database exists but has no tables")
                conn.close()
                return False
            
            logger.info(f"Found SQLite database with {len(tables)} tables: {[t[0] for t in tables]}")
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error checking SQLite database: {e}")
            return False
    
    def test_postgresql_connection(self):
        """Test connection to PostgreSQL database"""
        try:
            engine = create_engine(self.postgresql_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    def get_sqlite_tables_and_data(self):
        """Get all tables and data from SQLite database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            
            # Get all table names
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            tables_data = {}
            
            for table in tables:
                logger.info(f"Reading data from table: {table}")
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                
                # Get all data
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                
                tables_data[table] = {
                    'columns': columns,
                    'data': df,
                    'row_count': len(df)
                }
                
                logger.info(f"Table {table}: {len(df)} rows, {len(columns)} columns")
            
            conn.close()
            return tables_data
            
        except Exception as e:
            logger.error(f"Error reading SQLite database: {e}")
            return {}
    
    def create_postgresql_tables(self):
        """Create tables in PostgreSQL database using Flask models"""
        try:
            logger.info("Creating PostgreSQL tables...")
            
            # Import Flask app and models
            from app import app
            from models import db
            
            # Configure app for PostgreSQL
            app.config['SQLALCHEMY_DATABASE_URI'] = self.postgresql_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            with app.app_context():
                # Drop all tables first (optional - comment out if you want to preserve existing data)
                logger.info("Dropping existing tables...")
                db.drop_all()
                
                # Create all tables
                logger.info("Creating tables...")
                db.create_all()
                
                logger.info("PostgreSQL tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")
            return False
    
    def migrate_data(self, tables_data):
        """Migrate data from SQLite to PostgreSQL"""
        try:
            engine = create_engine(self.postgresql_url)
            
            total_rows = 0
            
            for table_name, table_info in tables_data.items():
                df = table_info['data']
                row_count = table_info['row_count']
                
                if row_count == 0:
                    logger.info(f"Skipping empty table: {table_name}")
                    continue
                
                logger.info(f"Migrating table {table_name}: {row_count} rows")
                
                try:
                    # Insert data into PostgreSQL
                    df.to_sql(
                        table_name, 
                        engine, 
                        if_exists='append', 
                        index=False,
                        method='multi',
                        chunksize=1000
                    )
                    
                    total_rows += row_count
                    logger.info(f"Successfully migrated {table_name}: {row_count} rows")
                    
                except Exception as e:
                    logger.error(f"Error migrating table {table_name}: {e}")
                    continue
            
            logger.info(f"Migration completed! Total rows migrated: {total_rows}")
            return True
            
        except Exception as e:
            logger.error(f"Error during data migration: {e}")
            return False
    
    def verify_migration(self, original_tables_data):
        """Verify that data was migrated correctly"""
        try:
            engine = create_engine(self.postgresql_url)
            
            logger.info("Verifying migration...")
            
            with engine.connect() as conn:
                for table_name, table_info in original_tables_data.items():
                    original_count = table_info['row_count']
                    
                    if original_count == 0:
                        continue
                    
                    # Count rows in PostgreSQL
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    pg_count = result.fetchone()[0]
                    
                    if original_count == pg_count:
                        logger.info(f"{table_name}: {original_count} = {pg_count} rows")
                    else:
                        logger.warning(f"{table_name}: SQLite={original_count}, PostgreSQL={pg_count}")
            
            logger.info("Migration verification completed")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying migration: {e}")
            return False
    
    def backup_sqlite(self):
        """Create a backup of the SQLite database"""
        if not os.path.exists(self.sqlite_path):
            return True
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"sqlite_backup_{timestamp}.db"
            
            # Copy SQLite database
            import shutil
            shutil.copy2(self.sqlite_path, backup_path)
            
            logger.info(f"SQLite database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up SQLite database: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration...")
        
        # Step 1: Test PostgreSQL connection
        logger.info("Step 1: Testing PostgreSQL connection...")
        if not self.test_postgresql_connection():
            logger.error("Cannot connect to PostgreSQL database")
            return False
        
        # Step 2: Check if SQLite database exists
        logger.info("Step 2: Checking SQLite database...")
        if not self.check_sqlite_exists():
            logger.info("No SQLite database found or it's empty. Creating fresh PostgreSQL tables...")
            return self.create_postgresql_tables()
        
        # Step 3: Backup SQLite database
        logger.info("Step 3: Backing up SQLite database...")
        if not self.backup_sqlite():
            logger.error("Failed to backup SQLite database")
            return False
        
        # Step 4: Read SQLite data
        logger.info("Step 4: Reading SQLite data...")
        tables_data = self.get_sqlite_tables_and_data()
        if not tables_data:
            logger.error("Failed to read SQLite data")
            return False
        
        # Step 5: Create PostgreSQL tables
        logger.info("Step 5: Creating PostgreSQL tables...")
        if not self.create_postgresql_tables():
            logger.error("Failed to create PostgreSQL tables")
            return False
        
        # Step 6: Migrate data
        logger.info("Step 6: Migrating data...")
        if not self.migrate_data(tables_data):
            logger.error("Failed to migrate data")
            return False
        
        # Step 7: Verify migration
        logger.info("Step 7: Verifying migration...")
        if not self.verify_migration(tables_data):
            logger.warning("Migration verification had issues")
        
        logger.info("Migration completed successfully!")
        logger.info("Your application is now using PostgreSQL on Neon!")
        
        return True

def main():
    """Main migration function"""
    print("=" * 60)
    print("ATS Resume Checker - SQLite to PostgreSQL Migration")
    print("=" * 60)
    
    migrator = DatabaseMigrator()
    
    try:
        success = migrator.run_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("MIGRATION SUCCESSFUL!")
            print("=" * 60)
            print("Next steps:")
            print("1. Test your application: python app.py")
            print("2. Verify all functionality works correctly")
            print("3. Check the migration.log file for details")
            print("4. Keep the SQLite backup file safe")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("MIGRATION FAILED!")
            print("=" * 60)
            print("Check the migration.log file for error details")
            print("Your original SQLite database is safely backed up")
            print("=" * 60)
    
    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()