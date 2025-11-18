"""
Database Administration and Maintenance Utilities
Provides database health monitoring, maintenance operations, and optimization tools
"""

import os
import time
import logging
import psutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text, inspect
from models import db

logger = logging.getLogger(__name__)

class DatabaseAdmin:
    """
    Database administration and maintenance utilities
    """
    
    def __init__(self, db_instance):
        """
        Initialize database admin with database instance
        
        Args:
            db_instance: SQLAlchemy database instance
        """
        self.db = db_instance
        self.engine = db_instance.engine
        self.inspector = inspect(self.engine)
        
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get comprehensive database information
        
        Returns:
            Database information and statistics
        """
        try:
            # Basic database info
            db_info = {
                'engine': str(self.engine.url).split('@')[0] + '@[hidden]',  # Hide credentials
                'driver': self.engine.dialect.name,
                'server_version': None,
                'current_time': datetime.now(timezone.utc).isoformat()
            }
            
            # Get database version and stats
            with self.engine.connect() as conn:
                # Database-specific queries
                if self.engine.dialect.name == 'postgresql':
                    result = conn.execute(text("SELECT version()"))
                    db_info['server_version'] = result.scalar()
                    
                    # PostgreSQL specific statistics
                    result = conn.execute(text("""
                        SELECT 
                            pg_database_size(current_database()) as db_size,
                            (SELECT count(*) FROM pg_stat_activity) as connections,
                            current_setting('max_connections') as max_connections
                    """))
                    row = result.fetchone()
                    if row:
                        db_info.update({
                            'database_size_bytes': row[0],
                            'database_size_mb': round(row[0] / 1024 / 1024, 2),
                            'active_connections': row[1],
                            'max_connections': row[2]
                        })
                        
                elif self.engine.dialect.name == 'sqlite':
                    result = conn.execute(text("SELECT sqlite_version()"))
                    db_info['server_version'] = f"SQLite {result.scalar()}"
                    
                    # SQLite database file size
                    if hasattr(self.engine.url, 'database'):
                        db_file = self.engine.url.database
                        if db_file and os.path.exists(db_file):
                            file_size = os.path.getsize(db_file)
                            db_info.update({
                                'database_size_bytes': file_size,
                                'database_size_mb': round(file_size / 1024 / 1024, 2)
                            })
                
                # Get table information
                table_info = self._get_table_statistics()
                db_info['tables'] = table_info
                
                return db_info
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {
                'error': str(e),
                'engine': str(self.engine.url).split('@')[0] + '@[hidden]',
                'driver': self.engine.dialect.name
            }
    
    def _get_table_statistics(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all tables
        
        Returns:
            List of table statistics
        """
        tables = []
        
        try:
            table_names = self.inspector.get_table_names()
            
            for table_name in table_names:
                try:
                    # Get row count
                    with self.engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = result.scalar()
                    
                    # Get column information
                    columns = self.inspector.get_columns(table_name)
                    
                    # Get indexes
                    indexes = self.inspector.get_indexes(table_name)
                    
                    table_info = {
                        'name': table_name,
                        'row_count': row_count,
                        'column_count': len(columns),
                        'index_count': len(indexes),
                        'columns': [col['name'] for col in columns],
                        'indexes': [idx['name'] for idx in indexes if idx.get('name')]
                    }
                    
                    # PostgreSQL specific table size
                    if self.engine.dialect.name == 'postgresql':
                        with self.engine.connect() as conn:
                            result = conn.execute(text(f"""
                                SELECT pg_total_relation_size('{table_name}') as table_size
                            """))
                            size = result.scalar()
                            if size:
                                table_info['size_bytes'] = size
                                table_info['size_mb'] = round(size / 1024 / 1024, 2)
                    
                    tables.append(table_info)
                    
                except Exception as e:
                    logger.warning(f"Error getting statistics for table {table_name}: {e}")
                    tables.append({
                        'name': table_name,
                        'error': str(e)
                    })
                    
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            
        return tables
    
    def run_maintenance(self, operations: List[str] = None) -> Dict[str, Any]:
        """
        Run database maintenance operations
        
        Args:
            operations: List of operations to run (analyze, vacuum, reindex)
            
        Returns:
            Results of maintenance operations
        """
        if operations is None:
            operations = ['analyze']
        
        results = {}
        
        for operation in operations:
            try:
                if operation == 'analyze':
                    results['analyze'] = self._run_analyze()
                elif operation == 'vacuum' and self.engine.dialect.name == 'postgresql':
                    results['vacuum'] = self._run_vacuum()
                elif operation == 'reindex' and self.engine.dialect.name == 'postgresql':
                    results['reindex'] = self._run_reindex()
                else:
                    results[operation] = {
                        'status': 'skipped',
                        'message': f'Operation {operation} not supported for {self.engine.dialect.name}'
                    }
                    
            except Exception as e:
                logger.error(f"Maintenance operation {operation} failed: {e}")
                results[operation] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operations': results
        }
    
    def _run_analyze(self) -> Dict[str, Any]:
        """Run database statistics update (ANALYZE)"""
        try:
            with self.engine.connect() as conn:
                if self.engine.dialect.name == 'postgresql':
                    conn.execute(text("ANALYZE"))
                    conn.commit()
                elif self.engine.dialect.name == 'sqlite':
                    conn.execute(text("ANALYZE"))
                    conn.commit()
                
            return {
                'status': 'success',
                'message': 'Database statistics updated successfully'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _run_vacuum(self) -> Dict[str, Any]:
        """Run database vacuum (PostgreSQL only)"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
            
            return {
                'status': 'success',
                'message': 'Database vacuum completed successfully'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _run_reindex(self) -> Dict[str, Any]:
        """Rebuild database indexes (PostgreSQL only)"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("REINDEX DATABASE CONCURRENTLY"))
                conn.commit()
            
            return {
                'status': 'success',
                'message': 'Database reindex completed successfully'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information
        
        Returns:
            Connection pool and active connection information
        """
        connection_info = {
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Connection pool information
            if hasattr(self.engine.pool, 'size'):
                connection_info['pool'] = {
                    'size': self.engine.pool.size(),
                    'checked_in': self.engine.pool.checkedin(),
                    'checked_out': self.engine.pool.checkedout(),
                    'overflow': self.engine.pool.overflow(),
                    'invalid': self.engine.pool.invalid()
                }
            
            # Database-specific connection information
            if self.engine.dialect.name == 'postgresql':
                with self.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT 
                            state,
                            COUNT(*) as count
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                        GROUP BY state
                    """))
                    
                    connection_states = {}
                    for row in result:
                        connection_states[row[0] or 'idle'] = row[1]
                    
                    connection_info['active_connections'] = connection_states
                    
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            connection_info['error'] = str(e)
        
        return connection_info
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        Get system resource information
        
        Returns:
            System CPU, memory, and disk usage
        """
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            
            # Disk information for current directory
            disk = psutil.disk_usage('.')
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(memory.available / 1024 / 1024 / 1024, 2),
                    'used_gb': round(memory.used / 1024 / 1024 / 1024, 2),
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'usage_percent': disk.percent
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }

# Global database admin instance
db_admin = None

def initialize_database_admin(db_instance):
    """
    Initialize global database admin instance
    
    Args:
        db_instance: SQLAlchemy database instance
    """
    global db_admin
    db_admin = DatabaseAdmin(db_instance)
    logger.info("Database admin initialized")

def get_database_admin():
    """
    Get global database admin instance
    
    Returns:
        DatabaseAdmin instance or None if not initialized
    """
    return db_admin