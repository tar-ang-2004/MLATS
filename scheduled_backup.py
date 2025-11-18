#!/usr/bin/env python3
"""
Scheduled Backup Script for ATS Resume Checker
Run this script periodically (e.g., via cron) to create automated backups
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the current directory to Python path to import Flask app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backup.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_scheduled_backup(backup_name=None, compress=True, cleanup_old=True):
    """
    Create a scheduled backup
    
    Args:
        backup_name: Custom backup name (default: auto-generated)
        compress: Whether to compress the backup
        cleanup_old: Whether to clean up old backups
    
    Returns:
        Backup result dictionary
    """
    logger = setup_logging()
    
    try:
        # Import Flask app components
        from models import db
        from backup_manager import BackupManager
        from config import get_config
        from flask import Flask
        
        # Initialize minimal Flask app for database context
        app = Flask(__name__)
        config = get_config()
        app.config.from_object(config)
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Initialize backup manager
            backup_dir = app.config.get('BACKUP_DIR', './backups')
            retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
            
            manager = BackupManager(db, backup_dir, retention_days)
            
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.now(timezone.utc)
                backup_name = f"scheduled_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Creating scheduled backup: {backup_name}")
            
            # Create backup
            result = manager.create_backup(backup_name, compress)
            
            if result.get('success'):
                logger.info(f"Backup created successfully: {backup_name}")
                logger.info(f"Backup file: {result['file_path']}")
                logger.info(f"Backup size: {result['file_size']} bytes")
                logger.info(f"Duration: {result['duration']} seconds")
                
                # Get backup statistics
                stats = manager.get_backup_statistics()
                logger.info(f"Total backups: {stats['total_backups']}")
                logger.info(f"Total backup size: {stats['total_size_mb']} MB")
                
            else:
                logger.error(f"Backup creation failed: {result.get('error')}")
                return False
            
            return True
            
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure this script is run from the ATS Resume Checker directory")
        return False
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return False

def main():
    """Main function for command line execution"""
    parser = argparse.ArgumentParser(description='Create scheduled backup of ATS Resume Checker database')
    parser.add_argument('--name', help='Custom backup name')
    parser.add_argument('--no-compress', action='store_true', help='Disable compression')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup of old backups')
    parser.add_argument('--quiet', action='store_true', help='Suppress output (for cron jobs)')
    
    args = parser.parse_args()
    
    # Setup minimal logging for quiet mode
    if args.quiet:
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler('backup.log')]
        )
    
    # Create backup
    success = create_scheduled_backup(
        backup_name=args.name,
        compress=not args.no_compress,
        cleanup_old=not args.no_cleanup
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()