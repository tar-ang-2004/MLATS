"""
Celery Configuration for Background Task Processing
Handles async resume processing and file uploads
"""

import os
from celery import Celery
from datetime import timedelta

def make_celery(app):
    """Create Celery app with Flask app context"""
    
    # Redis URL for broker and backend
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/2')
    
    celery = Celery(
        app.import_name,
        backend=redis_url,
        broker=redis_url,
        include=['tasks']  # Import task modules
    )
    
    # Update Celery config
    celery.conf.update(
        # Task settings
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_backend_transport_options={'master_name': 'mymaster'},
        
        # Worker settings
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=1000,
        
        # Task routing
        task_routes={
            'tasks.process_resume_async': {'queue': 'resume_processing'},
            'tasks.cleanup_old_files': {'queue': 'maintenance'},
            'tasks.export_csv_async': {'queue': 'exports'}
        },
        
        # Beat schedule for periodic tasks
        beat_schedule={
            'cleanup-old-files': {
                'task': 'tasks.cleanup_old_files',
                'schedule': timedelta(hours=24),  # Daily cleanup
            },
            'update-csv-export': {
                'task': 'tasks.export_csv_async',
                'schedule': timedelta(minutes=30),  # Update CSV every 30 minutes
            },
        }
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Task status constants
class TaskStatus:
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'
    REVOKED = 'REVOKED'