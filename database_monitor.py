"""
Database Query Monitoring and Performance Analysis
Tracks slow queries, connection pool usage, and database performance
"""

import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """
    Database performance monitoring and query analysis
    """
    
    def __init__(self, slow_query_threshold: float = 1.0, max_history: int = 1000):
        """
        Initialize database monitor
        
        Args:
            slow_query_threshold: Queries slower than this (seconds) are flagged
            max_history: Maximum number of query records to keep
        """
        self.slow_query_threshold = slow_query_threshold
        self.max_history = max_history
        
        # Query statistics
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0,
            'slow_queries': 0
        })
        
        # Recent queries history
        self.query_history = deque(maxlen=max_history)
        self.slow_queries = deque(maxlen=100)  # Keep last 100 slow queries
        
        # Connection pool monitoring
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'pool_size': 0,
            'overflow_connections': 0,
            'invalid_connections': 0,
            'connection_errors': 0
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Database monitor initialized (slow query threshold: {slow_query_threshold}s)")
    
    def record_query(self, query: str, duration: float, parameters: Optional[Dict] = None):
        """
        Record a database query execution
        
        Args:
            query: SQL query string
            duration: Execution time in seconds
            parameters: Query parameters
        """
        with self._lock:
            # Normalize query for statistics (remove parameters, whitespace)
            normalized_query = self._normalize_query(query)
            
            # Update statistics
            stats = self.query_stats[normalized_query]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # Check if it's a slow query
            if duration >= self.slow_query_threshold:
                stats['slow_queries'] += 1
                
                slow_query_record = {
                    'timestamp': datetime.now(timezone.utc),
                    'query': query,
                    'duration': duration,
                    'parameters': parameters,
                    'normalized_query': normalized_query
                }
                self.slow_queries.append(slow_query_record)
                
                logger.warning(f"Slow query detected ({duration:.3f}s): {query[:100]}...")
            
            # Add to history
            query_record = {
                'timestamp': datetime.now(timezone.utc),
                'query': normalized_query,
                'duration': duration,
                'is_slow': duration >= self.slow_query_threshold
            }
            self.query_history.append(query_record)
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize SQL query for grouping statistics
        Removes parameters and excess whitespace
        """
        import re
        
        # Remove extra whitespace and normalize
        normalized = re.sub(r'\s+', ' ', query.strip().upper())
        
        # Replace parameter placeholders
        normalized = re.sub(r'\?', '?', normalized)
        normalized = re.sub(r'%\([^)]+\)s', '?', normalized)
        normalized = re.sub(r'\$\d+', '?', normalized)
        
        # Remove VALUES clause content for INSERT statements
        normalized = re.sub(r'VALUES\s*\([^)]+\)', 'VALUES (?)', normalized)
        
        # Replace IN clauses with placeholders
        normalized = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', normalized)
        
        return normalized
    
    def get_query_statistics(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get query performance statistics
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query statistics sorted by total time
        """
        with self._lock:
            stats_list = []
            
            for query, stats in self.query_stats.items():
                stats_list.append({
                    'query': query[:200] + '...' if len(query) > 200 else query,
                    'count': stats['count'],
                    'total_time': round(stats['total_time'], 3),
                    'avg_time': round(stats['avg_time'], 3),
                    'min_time': round(stats['min_time'], 3),
                    'max_time': round(stats['max_time'], 3),
                    'slow_queries': stats['slow_queries'],
                    'slow_percentage': round((stats['slow_queries'] / stats['count']) * 100, 1)
                })
            
            # Sort by total time (most expensive first)
            stats_list.sort(key=lambda x: x['total_time'], reverse=True)
            
            return stats_list[:limit]
    
    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent slow queries
        
        Args:
            limit: Maximum number of slow queries to return
            
        Returns:
            List of slow query records
        """
        with self._lock:
            recent_slow = list(self.slow_queries)[-limit:]
            return [{
                'timestamp': record['timestamp'].isoformat(),
                'query': record['query'][:500] + '...' if len(record['query']) > 500 else record['query'],
                'duration': round(record['duration'], 3),
                'parameters': str(record['parameters']) if record['parameters'] else None
            } for record in reversed(recent_slow)]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall database performance summary
        
        Returns:
            Performance summary statistics
        """
        with self._lock:
            if not self.query_history:
                return {
                    'total_queries': 0,
                    'slow_queries': 0,
                    'avg_query_time': 0,
                    'slow_query_percentage': 0
                }
            
            recent_queries = list(self.query_history)
            total_queries = len(recent_queries)
            slow_queries = sum(1 for q in recent_queries if q['is_slow'])
            
            total_time = sum(q['duration'] for q in recent_queries)
            avg_time = total_time / total_queries if total_queries > 0 else 0
            
            # Performance over time analysis
            now = datetime.now(timezone.utc)
            last_hour_queries = [
                q for q in recent_queries 
                if (now - q['timestamp']).total_seconds() <= 3600
            ]
            
            return {
                'total_queries': total_queries,
                'slow_queries': slow_queries,
                'slow_query_percentage': round((slow_queries / total_queries) * 100, 2) if total_queries > 0 else 0,
                'avg_query_time': round(avg_time, 3),
                'total_query_time': round(total_time, 3),
                'queries_last_hour': len(last_hour_queries),
                'slow_queries_last_hour': sum(1 for q in last_hour_queries if q['is_slow']),
                'connection_stats': dict(self.connection_stats),
                'monitoring_period': {
                    'start_time': recent_queries[0]['timestamp'].isoformat() if recent_queries else None,
                    'end_time': recent_queries[-1]['timestamp'].isoformat() if recent_queries else None
                }
            }
    
    def update_connection_stats(self, pool_info: Dict[str, Any]):
        """
        Update connection pool statistics
        
        Args:
            pool_info: Connection pool information
        """
        with self._lock:
            self.connection_stats.update(pool_info)
    
    def reset_statistics(self):
        """Reset all monitoring statistics"""
        with self._lock:
            self.query_stats.clear()
            self.query_history.clear()
            self.slow_queries.clear()
            self.connection_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'pool_size': 0,
                'overflow_connections': 0,
                'invalid_connections': 0,
                'connection_errors': 0
            }
            logger.info("Database monitoring statistics reset")

# Global database monitor instance
db_monitor = DatabaseMonitor()

def setup_database_monitoring(app, db):
    """
    Setup SQLAlchemy event listeners for database monitoring
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    
    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time"""
        context._query_start_time = time.time()
    
    @event.listens_for(Engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query completion and duration"""
        if hasattr(context, '_query_start_time'):
            duration = time.time() - context._query_start_time
            db_monitor.record_query(statement, duration, parameters)
    
    @event.listens_for(Engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        """Track database connections"""
        db_monitor.connection_stats['total_connections'] += 1
    
    @event.listens_for(Engine, "close")
    def receive_close(dbapi_connection, connection_record):
        """Track connection closures"""
        db_monitor.connection_stats['active_connections'] = max(0, 
            db_monitor.connection_stats.get('active_connections', 0) - 1)
    
    # Store monitor reference in app for access in routes
    app.db_monitor = db_monitor
    
    logger.info("Database monitoring event listeners registered")

def get_database_performance() -> Dict[str, Any]:
    """
    Get current database performance metrics
    
    Returns:
        Database performance information
    """
    return {
        'summary': db_monitor.get_performance_summary(),
        'top_queries': db_monitor.get_query_statistics(10),
        'slow_queries': db_monitor.get_slow_queries(10)
    }