#!/usr/bin/env python3
"""
PostgreSQL Setup and Migration Script
Installs dependencies and migrates to Neon PostgreSQL database
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python packages for PostgreSQL"""
    print("📦 Installing PostgreSQL dependencies...")
    
    required_packages = [
        'psycopg2-binary',  # PostgreSQL adapter
        'pandas',           # For data migration
        'sqlalchemy',       # Database toolkit
        'python-dotenv'     # Environment variables
    ]
    
    try:
        for package in required_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        
        print("✅ All dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def run_connection_test():
    """Run the PostgreSQL connection test"""
    print("\n🔍 Testing PostgreSQL connection...")
    
    try:
        result = subprocess.run([sys.executable, 'test_postgresql_connection.py'], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Connection test passed!")
            return True
        else:
            print("❌ Connection test failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running connection test: {e}")
        return False

def run_migration():
    """Run the database migration"""
    print("\n🚀 Running database migration...")
    
    try:
        result = subprocess.run([sys.executable, 'migrate_to_postgresql.py'], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            return True
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

def verify_env_file():
    """Verify that .env file exists and has DATABASE_URL"""
    print("🔍 Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'DATABASE_URL' not in content:
            print("❌ DATABASE_URL not found in .env file!")
            return False
            
        if 'postgresql://neondb_owner' in content:
            print("✅ Neon PostgreSQL DATABASE_URL found in .env")
            return True
        else:
            print("⚠️ DATABASE_URL found but might not be configured for Neon")
            return True
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def backup_sqlite():
    """Create backup of SQLite database if it exists"""
    sqlite_files = ['ats_resume_checker.db', 'instance/ats_resume_checker.db']
    
    for sqlite_file in sqlite_files:
        if os.path.exists(sqlite_file):
            print(f"💾 Creating backup of {sqlite_file}...")
            
            try:
                import shutil
                from datetime import datetime
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"sqlite_backup_{timestamp}.db"
                
                shutil.copy2(sqlite_file, backup_name)
                print(f"✅ Backup created: {backup_name}")
                return True
                
            except Exception as e:
                print(f"❌ Error creating backup: {e}")
                return False
    
    print("ℹ️ No SQLite database found to backup")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 ATS Resume Checker - PostgreSQL Setup")
    print("=" * 60)
    print("This script will:")
    print("1. Install required PostgreSQL dependencies")
    print("2. Test connection to your Neon database")
    print("3. Backup existing SQLite data (if any)")
    print("4. Migrate data to PostgreSQL")
    print("=" * 60)
    
    # Step 1: Verify environment
    if not verify_env_file():
        print("\n❌ Environment configuration issue. Please check your .env file.")
        return False
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return False
    
    # Step 3: Test connection
    if not run_connection_test():
        print("\n❌ Connection test failed. Please check your DATABASE_URL.")
        return False
    
    # Step 4: Backup SQLite (if exists)
    if not backup_sqlite():
        print("\n⚠️ Backup failed, but continuing with migration...")
    
    # Step 5: Ask user confirmation
    print("\n" + "=" * 60)
    print("🔄 Ready to migrate to PostgreSQL!")
    print("=" * 60)
    
    response = input("Continue with migration? (y/N): ").lower().strip()
    
    if response != 'y' and response != 'yes':
        print("❌ Migration cancelled by user.")
        return False
    
    # Step 6: Run migration
    if not run_migration():
        print("\n❌ Migration failed.")
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Your ATS Resume Checker is now using PostgreSQL on Neon!")
    print()
    print("Next steps:")
    print("1. Test your application: python app.py")
    print("2. Upload a resume to verify everything works")
    print("3. Check your Neon dashboard to see the data")
    print("4. Your SQLite backup is safely stored")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)