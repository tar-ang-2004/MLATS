"""
File Processing Time Tracking and Performance Analysis
Tracks processing times for resume analysis pipeline stages
"""

import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from contextlib import contextmanager
import functools

logger = logging.getLogger(__name__)

class ProcessingTimeTracker:
    """
    Track processing times for file analysis pipeline stages
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize processing time tracker
        
        Args:
            max_history: Maximum number of processing records to keep
        """
        self.max_history = max_history
        
        # Processing statistics by stage
        self.stage_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0,
            'last_processed': None,
            'success_count': 0,
            'error_count': 0
        })
        
        # Processing history
        self.processing_history = deque(maxlen=max_history)
        
        # Active processing sessions
        self.active_sessions = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Processing time tracker initialized (max history: {max_history})")
    
    @contextmanager
    def track_stage(self, session_id: str, stage_name: str, metadata: Dict = None):
        """
        Context manager for tracking processing stage time
        
        Args:
            session_id: Unique identifier for processing session
            stage_name: Name of the processing stage
            metadata: Additional metadata for the stage
        """
        start_time = time.time()
        success = True
        error = None
        
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            self.record_stage_time(
                session_id=session_id,
                stage_name=stage_name,
                duration=duration,
                success=success,
                error=error,
                metadata=metadata
            )
    
    def start_session(self, session_id: str, filename: str, file_size: int = None, file_type: str = None):
        """
        Start a new processing session
        
        Args:
            session_id: Unique identifier for the session
            filename: Name of the file being processed
            file_size: Size of the file in bytes
            file_type: Type of the file (pdf, docx, etc.)
        """
        with self._lock:
            self.active_sessions[session_id] = {
                'filename': filename,
                'file_size': file_size,
                'file_type': file_type,
                'start_time': time.time(),
                'stages': {},
                'total_duration': 0.0,
                'success': None,
                'error': None
            }
            
            logger.debug(f"Started processing session {session_id} for file {filename}")
    
    def end_session(self, session_id: str, success: bool = True, error: str = None):
        """
        End a processing session
        
        Args:
            session_id: Session identifier
            success: Whether the session completed successfully
            error: Error message if session failed
        """
        with self._lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session['total_duration'] = time.time() - session['start_time']
                session['success'] = success
                session['error'] = error
                session['end_time'] = time.time()
                
                # Add to history
                history_record = dict(session)
                history_record['session_id'] = session_id
                history_record['timestamp'] = datetime.now(timezone.utc)
                self.processing_history.append(history_record)
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                logger.debug(f"Ended processing session {session_id} (success: {success})")
    
    def record_stage_time(self, session_id: str, stage_name: str, duration: float, 
                         success: bool = True, error: str = None, metadata: Dict = None):
        """
        Record processing time for a specific stage
        
        Args:
            session_id: Session identifier
            stage_name: Name of the processing stage
            duration: Time taken in seconds
            success: Whether the stage completed successfully
            error: Error message if stage failed
            metadata: Additional metadata
        """
        with self._lock:
            # Update stage statistics
            stats = self.stage_stats[stage_name]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['last_processed'] = datetime.now(timezone.utc)
            
            if success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            # Add to active session if it exists
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['stages'][stage_name] = {
                    'duration': duration,
                    'success': success,
                    'error': error,
                    'metadata': metadata,
                    'timestamp': datetime.now(timezone.utc)
                }
    
    def get_stage_statistics(self, stage_name: str = None) -> Dict[str, Any]:
        """
        Get processing statistics for stages
        
        Args:
            stage_name: Specific stage name, or None for all stages
            
        Returns:
            Stage statistics
        """
        with self._lock:
            if stage_name:
                if stage_name in self.stage_stats:
                    stats = dict(self.stage_stats[stage_name])
                    stats['success_rate'] = (stats['success_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
                    stats['error_rate'] = (stats['error_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
                    return {stage_name: stats}
                else:
                    return {}
            else:
                all_stats = {}
                for stage, stats in self.stage_stats.items():
                    stage_stats = dict(stats)
                    stage_stats['success_rate'] = (stage_stats['success_count'] / stage_stats['count'] * 100) if stage_stats['count'] > 0 else 0
                    stage_stats['error_rate'] = (stage_stats['error_count'] / stage_stats['count'] * 100) if stage_stats['count'] > 0 else 0
                    all_stats[stage] = stage_stats
                
                return all_stats
    
    def get_processing_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get processing summary for the specified time period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Processing summary statistics
        """
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            recent_sessions = [
                record for record in self.processing_history
                if record['timestamp'] >= cutoff_time
            ]
            
            if not recent_sessions:
                return {
                    'period_hours': hours,
                    'total_files': 0,
                    'successful_files': 0,
                    'failed_files': 0,
                    'success_rate': 0,
                    'avg_processing_time': 0,
                    'total_processing_time': 0
                }
            
            successful_sessions = [s for s in recent_sessions if s.get('success', False)]
            failed_sessions = [s for s in recent_sessions if not s.get('success', True)]
            
            total_time = sum(s['total_duration'] for s in recent_sessions)
            avg_time = total_time / len(recent_sessions) if recent_sessions else 0
            
            # File type breakdown
            file_type_stats = defaultdict(int)
            for session in recent_sessions:
                file_type = session.get('file_type', 'unknown')
                file_type_stats[file_type] += 1
            
            # Processing time by file size ranges
            size_ranges = {
                'small': 0,    # < 1MB
                'medium': 0,   # 1-5MB
                'large': 0,    # 5-20MB
                'xlarge': 0    # > 20MB
            }
            
            for session in recent_sessions:
                size = session.get('file_size', 0)
                if size < 1024*1024:  # < 1MB
                    size_ranges['small'] += 1
                elif size < 5*1024*1024:  # < 5MB
                    size_ranges['medium'] += 1
                elif size < 20*1024*1024:  # < 20MB
                    size_ranges['large'] += 1
                else:
                    size_ranges['xlarge'] += 1
            
            return {
                'period_hours': hours,
                'total_files': len(recent_sessions),
                'successful_files': len(successful_sessions),
                'failed_files': len(failed_sessions),
                'success_rate': (len(successful_sessions) / len(recent_sessions) * 100) if recent_sessions else 0,
                'avg_processing_time': round(avg_time, 3),
                'total_processing_time': round(total_time, 3),
                'file_types': dict(file_type_stats),
                'file_size_distribution': size_ranges,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent processing sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent processing sessions
        """
        with self._lock:
            recent = list(self.processing_history)[-limit:]
            return [{
                'session_id': record['session_id'],
                'filename': record['filename'],
                'file_type': record.get('file_type'),
                'file_size': record.get('file_size'),
                'total_duration': round(record['total_duration'], 3),
                'success': record.get('success'),
                'error': record.get('error'),
                'stage_count': len(record.get('stages', {})),
                'timestamp': record['timestamp'].isoformat()
            } for record in reversed(recent)]
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get currently active processing sessions
        
        Returns:
            List of active sessions with current runtime
        """
        with self._lock:
            current_time = time.time()
            active = []
            
            for session_id, session in self.active_sessions.items():
                runtime = current_time - session['start_time']
                active.append({
                    'session_id': session_id,
                    'filename': session['filename'],
                    'file_type': session.get('file_type'),
                    'runtime': round(runtime, 3),
                    'stages_completed': len(session.get('stages', {})),
                    'start_time': datetime.fromtimestamp(session['start_time'], timezone.utc).isoformat()
                })
            
            return active
    
    def reset_statistics(self):
        """Reset all processing statistics"""
        with self._lock:
            self.stage_stats.clear()
            self.processing_history.clear()
            self.active_sessions.clear()
            logger.info("Processing time tracking statistics reset")

# Global processing time tracker
processing_tracker = ProcessingTimeTracker()

def track_processing_time(stage_name: str, include_metadata: bool = True):
    """
    Decorator for tracking processing time of functions
    
    Args:
        stage_name: Name of the processing stage
        include_metadata: Whether to include function metadata
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract session_id from args/kwargs
            session_id = kwargs.get('session_id')
            if not session_id and args:
                # Look for session_id in first few arguments
                for arg in args[:3]:
                    if isinstance(arg, str) and len(arg) > 10:
                        session_id = arg
                        break
            
            if not session_id:
                session_id = f"auto_{int(time.time() * 1000)}"
            
            metadata = {
                'function_name': func.__name__,
                'module': func.__module__
            } if include_metadata else None
            
            with processing_tracker.track_stage(session_id, stage_name, metadata):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def get_processing_statistics() -> Dict[str, Any]:
    """
    Get comprehensive processing statistics
    
    Returns:
        Processing statistics and performance data
    """
    return {
        'stage_statistics': processing_tracker.get_stage_statistics(),
        'summary_24h': processing_tracker.get_processing_summary(24),
        'summary_1h': processing_tracker.get_processing_summary(1),
        'recent_sessions': processing_tracker.get_recent_sessions(20),
        'active_sessions': processing_tracker.get_active_sessions()
    }