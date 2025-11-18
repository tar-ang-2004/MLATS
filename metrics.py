"""
Prometheus Metrics Configuration
Provides comprehensive application monitoring and observability
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge, Summary, Info

logger = logging.getLogger(__name__)

class ApplicationMetrics:
    """
    Custom metrics collector for ATS Resume Checker
    Provides business-specific metrics beyond basic HTTP metrics
    """
    
    def __init__(self):
        """Initialize custom metrics"""
        
        # Resume processing metrics
        self.resume_processing_duration = Histogram(
            'resume_processing_duration_seconds',
            'Time spent processing resumes',
            ['processing_stage', 'status']
        )
        
        self.resume_processing_total = Counter(
            'resume_processing_total',
            'Total number of resume processing attempts',
            ['status', 'file_type']
        )
        
        self.resume_scores = Histogram(
            'resume_scores',
            'Distribution of resume scores',
            ['score_type'],
            buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        )
        
        # File upload metrics
        self.file_upload_size = Histogram(
            'file_upload_size_bytes',
            'Size of uploaded files',
            ['file_type'],
            buckets=[1024, 10240, 102400, 1048576, 10485760, 16777216]  # 1KB to 16MB
        )
        
        self.file_upload_duration = Histogram(
            'file_upload_duration_seconds',
            'Time spent processing file uploads',
            ['file_type', 'status']
        )
        
        # ML model metrics
        self.ml_model_inference_duration = Histogram(
            'ml_model_inference_duration_seconds',
            'Time spent on ML model inference',
            ['model_type', 'operation']
        )
        
        self.ml_model_memory_usage = Gauge(
            'ml_model_memory_usage_bytes',
            'Memory usage of ML models',
            ['model_name']
        )
        
        # Database metrics
        self.database_query_duration = Histogram(
            'database_query_duration_seconds',
            'Duration of database queries',
            ['query_type', 'table']
        )
        
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Number of active database connections'
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'status']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)'
        )
        
        # Business metrics
        self.resumes_by_classification = Counter(
            'resumes_by_classification_total',
            'Total resumes by classification',
            ['classification']
        )
        
        self.active_users = Gauge(
            'active_users_current',
            'Current number of active users'
        )
        
        # System metrics
        self.application_info = Info(
            'application_info',
            'Application version and build information'
        )
        
        # Error tracking
        self.errors_total = Counter(
            'errors_total',
            'Total application errors',
            ['error_type', 'component']
        )
        
        # Initialize application info
        self.application_info.info({
            'version': '1.0.0',
            'python_version': self._get_python_version(),
            'environment': 'production'
        })
        
        # Internal tracking
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Application metrics initialized")
    
    def _get_python_version(self) -> str:
        """Get Python version string"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def record_resume_processing(self, duration: float, status: str, file_type: str, scores: Dict[str, float]):
        """Record resume processing metrics"""
        self.resume_processing_duration.labels(
            processing_stage='complete',
            status=status
        ).observe(duration)
        
        self.resume_processing_total.labels(
            status=status,
            file_type=file_type
        ).inc()
        
        # Record scores
        for score_type, score in scores.items():
            if isinstance(score, (int, float)) and score is not None:
                self.resume_scores.labels(score_type=score_type).observe(score)
    
    def record_file_upload(self, file_size: int, duration: float, file_type: str, status: str):
        """Record file upload metrics"""
        self.file_upload_size.labels(file_type=file_type).observe(file_size)
        self.file_upload_duration.labels(file_type=file_type, status=status).observe(duration)
    
    def record_ml_inference(self, model_type: str, operation: str, duration: float):
        """Record ML model inference time"""
        self.ml_model_inference_duration.labels(
            model_type=model_type,
            operation=operation
        ).observe(duration)
    
    def record_database_query(self, query_type: str, table: str, duration: float):
        """Record database query metrics"""
        self.database_query_duration.labels(
            query_type=query_type,
            table=table
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics"""
        status = 'hit' if hit else 'miss'
        self.cache_operations_total.labels(operation=operation, status=status).inc()
        
        # Update hit ratio
        if operation == 'get':
            if hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
            
            total_ops = self._cache_hits + self._cache_misses
            if total_ops > 0:
                ratio = self._cache_hits / total_ops
                self.cache_hit_ratio.set(ratio)
    
    def record_resume_classification(self, classification: str):
        """Record resume classification"""
        self.resumes_by_classification.labels(classification=classification).inc()
    
    def record_error(self, error_type: str, component: str):
        """Record application error"""
        self.errors_total.labels(error_type=error_type, component=component).inc()
    
    def update_active_users(self, count: int):
        """Update active users count"""
        self.active_users.set(count)
    
    def update_model_memory(self, model_name: str, memory_bytes: int):
        """Update ML model memory usage"""
        self.ml_model_memory_usage.labels(model_name=model_name).set(memory_bytes)

# Global metrics instance
app_metrics = ApplicationMetrics()

def init_metrics(app):
    """Initialize Prometheus metrics for Flask app"""
    try:
        # Initialize Flask-Prometheus metrics
        metrics = PrometheusMetrics(app)
        
        # Add custom metrics endpoint info
        metrics.info(
            'flask_app_info',
            'Application Information',
            version='1.0.0',
            environment=app.config.get('ENV', 'development')
        )
        
        # Register custom metrics with the registry
        app.metrics = app_metrics
        
        logger.info("Prometheus metrics initialized successfully")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus metrics: {e}")
        app.metrics = None
        return None

def track_processing_time(operation: str, component: str = 'general'):
    """
    Decorator to track processing time for functions
    
    Args:
        operation: Name of the operation being tracked
        component: Component name for error tracking
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Record successful execution
                duration = time.time() - start_time
                if hasattr(app_metrics, 'ml_model_inference_duration'):
                    app_metrics.ml_model_inference_duration.labels(
                        model_type=component,
                        operation=operation
                    ).observe(duration)
                
                return result
                
            except Exception as e:
                # Record error
                app_metrics.record_error(
                    error_type=type(e).__name__,
                    component=component
                )
                raise
        
        return wrapper
    return decorator

def track_database_query(query_type: str, table: str):
    """
    Decorator to track database query performance
    
    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Target table name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                app_metrics.record_database_query(query_type, table, duration)
                return result
            except Exception as e:
                app_metrics.record_error(
                    error_type=type(e).__name__,
                    component='database'
                )
                raise
        return wrapper
    return decorator