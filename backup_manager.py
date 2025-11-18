"""
Database Backup and Restore System
Provides automated backup, restore, and backup management functionality
"""

import os
import time
import logging
import subprocess
import shutil
import gzip
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy import text
import tempfile

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Comprehensive database backup and restore manager
    """
    
    def __init__(self, db_instance, backup_dir: str = None, retention_days: int = 30):
        """
        Initialize backup manager
        
        Args:
            db_instance: SQLAlchemy database instance
            backup_dir: Directory to store backups (default: ./backups)
            retention_days: Number of days to keep backups
        """
        self.db = db_instance
        self.engine = db_instance.engine
        self.backup_dir = Path(backup_dir or './backups')
        self.retention_days = retention_days
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup metadata file
        self.metadata_file = self.backup_dir / 'backup_metadata.json'
        
        logger.info(f"Backup manager initialized (directory: {self.backup_dir}, retention: {retention_days} days)")
    
    def create_backup(self, backup_name: str = None, compress: bool = True) -> Dict[str, Any]:
        """
        Create a database backup
        
        Args:
            backup_name: Custom backup name (default: auto-generated)
            compress: Whether to compress the backup file
            
        Returns:
            Backup information and status
        """
        timestamp = datetime.now(timezone.utc)
        
        if not backup_name:
            backup_name = f"ats_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Database-specific backup logic
            if self.engine.dialect.name == 'postgresql':
                backup_info = self._create_postgresql_backup(backup_name, compress, timestamp)
            elif self.engine.dialect.name == 'sqlite':
                backup_info = self._create_sqlite_backup(backup_name, compress, timestamp)
            else:
                raise ValueError(f"Backup not supported for database type: {self.engine.dialect.name}")
            
            # Update metadata
            self._update_backup_metadata(backup_info)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {backup_name}")
            return backup_info
            
        except Exception as e:
            error_msg = f"Backup creation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'backup_name': backup_name,
                'error': error_msg,
                'timestamp': timestamp.isoformat()
            }
    
    def _create_postgresql_backup(self, backup_name: str, compress: bool, timestamp: datetime) -> Dict[str, Any]:
        """Create PostgreSQL backup using pg_dump"""
        
        # Get connection details
        db_url = str(self.engine.url)
        
        # Parse database URL
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(db_url)
        
        db_params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'username': parsed.username,
            'password': parsed.password
        }
        
        # Create backup file path
        backup_file = self.backup_dir / f"{backup_name}.sql"
        if compress:
            backup_file = backup_file.with_suffix('.sql.gz')
        
        try:
            # Prepare pg_dump command
            cmd = [
                'pg_dump',
                '--host', str(db_params['host']),
                '--port', str(db_params['port']),
                '--username', db_params['username'],
                '--dbname', db_params['database'],
                '--no-password',
                '--verbose',
                '--clean',
                '--create'
            ]
            
            # Set environment for password
            env = os.environ.copy()
            if db_params['password']:
                env['PGPASSWORD'] = db_params['password']
            
            # Execute backup
            start_time = time.time()
            
            if compress:
                # Pipe through gzip
                with open(backup_file, 'wb') as f:
                    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env, stderr=subprocess.PIPE)
                    p2 = subprocess.Popen(['gzip'], stdin=p1.stdout, stdout=f, stderr=subprocess.PIPE)
                    p1.stdout.close()
                    
                    stdout, stderr = p2.communicate()
                    returncode = p2.returncode
            else:
                with open(backup_file, 'w') as f:
                    process = subprocess.Popen(cmd, stdout=f, env=env, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    returncode = process.returncode
            
            end_time = time.time()
            
            if returncode != 0:
                raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
            
            # Get file size
            file_size = backup_file.stat().st_size
            
            return {
                'success': True,
                'backup_name': backup_name,
                'file_path': str(backup_file),
                'file_size': file_size,
                'compressed': compress,
                'database_type': 'postgresql',
                'duration': round(end_time - start_time, 2),
                'timestamp': timestamp.isoformat(),
                'database_info': {
                    'host': db_params['host'],
                    'port': db_params['port'],
                    'database': db_params['database']
                }
            }
            
        except Exception as e:
            if backup_file.exists():
                backup_file.unlink()  # Clean up partial file
            raise e
    
    def _create_sqlite_backup(self, backup_name: str, compress: bool, timestamp: datetime) -> Dict[str, Any]:
        """Create SQLite backup using file copy"""
        
        # Get database file path
        db_path = self.engine.url.database
        
        if not db_path or not os.path.exists(db_path):
            raise ValueError("SQLite database file not found")
        
        # Create backup file path
        backup_file = self.backup_dir / f"{backup_name}.sqlite"
        if compress:
            backup_file = backup_file.with_suffix('.sqlite.gz')
        
        try:
            start_time = time.time()
            
            if compress:
                # Copy and compress
                with open(db_path, 'rb') as src, gzip.open(backup_file, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            else:
                # Simple copy
                shutil.copy2(db_path, backup_file)
            
            end_time = time.time()
            
            # Get file sizes
            original_size = os.path.getsize(db_path)
            backup_size = backup_file.stat().st_size
            
            return {
                'success': True,
                'backup_name': backup_name,
                'file_path': str(backup_file),
                'file_size': backup_size,
                'original_size': original_size,
                'compressed': compress,
                'compression_ratio': round((1 - backup_size / original_size) * 100, 1) if compress else 0,
                'database_type': 'sqlite',
                'duration': round(end_time - start_time, 2),
                'timestamp': timestamp.isoformat(),
                'database_info': {
                    'file_path': db_path
                }
            }
            
        except Exception as e:
            if backup_file.exists():
                backup_file.unlink()  # Clean up partial file
            raise e
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_name: Name of the backup to restore
            
        Returns:
            Restore operation status
        """
        try:
            # Find backup file
            backup_info = self._get_backup_info(backup_name)
            if not backup_info:
                return {
                    'success': False,
                    'error': f'Backup {backup_name} not found'
                }
            
            backup_file = Path(backup_info['file_path'])
            if not backup_file.exists():
                return {
                    'success': False,
                    'error': f'Backup file not found: {backup_file}'
                }
            
            # Database-specific restore logic
            if backup_info['database_type'] == 'postgresql':
                result = self._restore_postgresql_backup(backup_file, backup_info)
            elif backup_info['database_type'] == 'sqlite':
                result = self._restore_sqlite_backup(backup_file, backup_info)
            else:
                return {
                    'success': False,
                    'error': f"Restore not supported for database type: {backup_info['database_type']}"
                }
            
            if result['success']:
                logger.info(f"Backup restored successfully: {backup_name}")
            else:
                logger.error(f"Backup restore failed: {backup_name} - {result.get('error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Restore operation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'backup_name': backup_name,
                'error': error_msg
            }
    
    def _restore_postgresql_backup(self, backup_file: Path, backup_info: Dict) -> Dict[str, Any]:
        """Restore PostgreSQL backup using psql"""
        
        # Get connection details
        db_url = str(self.engine.url)
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(db_url)
        
        db_params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'username': parsed.username,
            'password': parsed.password
        }
        
        try:
            # Prepare psql command
            cmd = [
                'psql',
                '--host', str(db_params['host']),
                '--port', str(db_params['port']),
                '--username', db_params['username'],
                '--dbname', db_params['database'],
                '--no-password',
                '--quiet'
            ]
            
            # Set environment for password
            env = os.environ.copy()
            if db_params['password']:
                env['PGPASSWORD'] = db_params['password']
            
            start_time = time.time()
            
            if backup_info.get('compressed'):
                # Decompress and pipe to psql
                with gzip.open(backup_file, 'rt') as f:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE, env=env, text=True)
                    stdout, stderr = process.communicate(input=f.read())
            else:
                with open(backup_file, 'r') as f:
                    process = subprocess.Popen(cmd, stdin=f, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, env=env)
                    stdout, stderr = process.communicate()
            
            end_time = time.time()
            
            if process.returncode != 0:
                return {
                    'success': False,
                    'error': f"psql restore failed: {stderr.decode() if isinstance(stderr, bytes) else stderr}"
                }
            
            return {
                'success': True,
                'backup_name': backup_info['backup_name'],
                'duration': round(end_time - start_time, 2),
                'restored_from': str(backup_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _restore_sqlite_backup(self, backup_file: Path, backup_info: Dict) -> Dict[str, Any]:
        """Restore SQLite backup by replacing database file"""
        
        db_path = self.engine.url.database
        
        try:
            start_time = time.time()
            
            # Create backup of current database
            current_backup = f"{db_path}.backup_{int(time.time())}"
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
            
            try:
                if backup_info.get('compressed'):
                    # Decompress and restore
                    with gzip.open(backup_file, 'rb') as src, open(db_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                else:
                    # Simple copy
                    shutil.copy2(backup_file, db_path)
                
                end_time = time.time()
                
                # Remove current backup on success
                if os.path.exists(current_backup):
                    os.remove(current_backup)
                
                return {
                    'success': True,
                    'backup_name': backup_info['backup_name'],
                    'duration': round(end_time - start_time, 2),
                    'restored_from': str(backup_file)
                }
                
            except Exception as e:
                # Restore original database on failure
                if os.path.exists(current_backup):
                    shutil.move(current_backup, db_path)
                raise e
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Returns:
            List of backup information
        """
        try:
            if not self.metadata_file.exists():
                return []
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            backups = metadata.get('backups', [])
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Add file existence check
            for backup in backups:
                backup_path = Path(backup['file_path'])
                backup['file_exists'] = backup_path.exists()
                if backup['file_exists']:
                    backup['current_file_size'] = backup_path.stat().st_size
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Delete a specific backup
        
        Args:
            backup_name: Name of the backup to delete
            
        Returns:
            Deletion status
        """
        try:
            backup_info = self._get_backup_info(backup_name)
            if not backup_info:
                return {
                    'success': False,
                    'error': f'Backup {backup_name} not found'
                }
            
            # Delete backup file
            backup_file = Path(backup_info['file_path'])
            if backup_file.exists():
                backup_file.unlink()
            
            # Remove from metadata
            self._remove_backup_from_metadata(backup_name)
            
            logger.info(f"Backup deleted: {backup_name}")
            return {
                'success': True,
                'backup_name': backup_name,
                'deleted_file': str(backup_file)
            }
            
        except Exception as e:
            error_msg = f"Failed to delete backup {backup_name}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _update_backup_metadata(self, backup_info: Dict[str, Any]):
        """Update backup metadata file"""
        try:
            metadata = {'backups': []}
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            metadata['backups'].append(backup_info)
            metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update backup metadata: {e}")
    
    def _get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get backup information by name"""
        backups = self.list_backups()
        for backup in backups:
            if backup['backup_name'] == backup_name:
                return backup
        return None
    
    def _remove_backup_from_metadata(self, backup_name: str):
        """Remove backup from metadata file"""
        try:
            if not self.metadata_file.exists():
                return
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata['backups'] = [
                backup for backup in metadata.get('backups', [])
                if backup['backup_name'] != backup_name
            ]
            metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to remove backup from metadata: {e}")
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            backups = self.list_backups()
            
            for backup in backups:
                try:
                    backup_date = datetime.fromisoformat(backup['timestamp'])
                    if backup_date < cutoff_date:
                        self.delete_backup(backup['backup_name'])
                        logger.info(f"Cleaned up old backup: {backup['backup_name']}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup backup {backup['backup_name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics and status
        
        Returns:
            Backup system statistics
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size': 0,
                    'backup_directory': str(self.backup_dir),
                    'retention_days': self.retention_days
                }
            
            total_size = sum(backup.get('file_size', 0) for backup in backups if backup.get('file_exists'))
            successful_backups = [b for b in backups if b.get('success')]
            
            # Latest backup info
            latest_backup = backups[0] if backups else None
            
            return {
                'total_backups': len(backups),
                'successful_backups': len(successful_backups),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'backup_directory': str(self.backup_dir),
                'retention_days': self.retention_days,
                'latest_backup': latest_backup,
                'disk_usage': {
                    'directory': str(self.backup_dir),
                    'exists': self.backup_dir.exists(),
                    'writable': os.access(self.backup_dir, os.W_OK) if self.backup_dir.exists() else False
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting backup statistics: {e}")
            return {
                'error': str(e),
                'backup_directory': str(self.backup_dir),
                'retention_days': self.retention_days
            }

# Global backup manager instance
backup_manager = None

def initialize_backup_manager(db_instance, backup_dir: str = None, retention_days: int = 30):
    """
    Initialize global backup manager
    
    Args:
        db_instance: SQLAlchemy database instance
        backup_dir: Backup directory path
        retention_days: Backup retention period
    """
    global backup_manager
    backup_manager = BackupManager(db_instance, backup_dir, retention_days)
    logger.info("Backup manager initialized")

def get_backup_manager():
    """
    Get global backup manager instance
    
    Returns:
        BackupManager instance or None if not initialized
    """
    return backup_manager