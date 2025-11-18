"""
Background Tasks for Resume Processing
Async processing using Celery for better performance
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import traceback

# Import app components
from app import app
from models import db, Resume, ProcessingLog
from ats_components import ResumeParser, ATSScorer
from cache_utils import cache, get_file_hash
from export_csv import export_all_resumes_csv

logger = logging.getLogger(__name__)

# Initialize Celery (will be created when app is available)
celery = None

def init_celery(app):
    """Initialize Celery with Flask app"""
    global celery
    from celery_config import make_celery
    celery = make_celery(app)
    return celery

@app.task(bind=True, name='tasks.process_resume_async')
def process_resume_async(self, resume_id: str, file_path: str, job_description: str = "") -> Dict[str, Any]:
    """
    Process resume asynchronously in background
    
    Args:
        resume_id: Database ID of the resume
        file_path: Path to uploaded resume file
        job_description: Job description text for matching
        
    Returns:
        Processing results dictionary
    """
    try:
        # Update task status
        self.update_state(
            state='STARTED',
            meta={'status': 'Processing resume...', 'progress': 0}
        )
        
        with app.app_context():
            # Get resume from database
            resume = Resume.query.get(resume_id)
            if not resume:
                raise Exception(f"Resume {resume_id} not found in database")
            
            start_time = datetime.now(timezone.utc)
            
            # Check cache first
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            file_hash = get_file_hash(file_content)
            cache_key = f"resume_processing:{file_hash}:{hash(job_description)}"
            
            cached_result = cache.get(cache_key, use_pickle=True)
            if cached_result:
                logger.info(f"Using cached processing results for resume {resume_id}")
                
                # Update resume with cached results
                for key, value in cached_result.items():
                    if hasattr(resume, key):
                        setattr(resume, key, value)
                
                resume.processing_time = 0.1  # Minimal time for cache hit
                db.session.commit()
                
                return {
                    'status': 'success',
                    'resume_id': resume_id,
                    'cached': True,
                    'results': cached_result
                }
            
            # Process resume
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Parsing resume content...', 'progress': 20}
            )
            
            # Initialize processors
            parser = ResumeParser()
            scorer = ATSScorer()
            
            # Parse resume
            parsed_data = parser.parse_resume(file_path)
            
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Analyzing skills and experience...', 'progress': 50}
            )
            
            # Score resume
            if job_description:
                scores = scorer.calculate_ats_score(parsed_data, job_description)
            else:
                scores = scorer.calculate_basic_score(parsed_data)
            
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Finalizing results...', 'progress': 80}
            )
            
            # Prepare results
            processing_results = {
                'overall_score': scores.get('overall_score', 0),
                'skills_score': scores.get('skills_score', 0),
                'experience_score': scores.get('experience_score', 0),
                'education_score': scores.get('education_score', 0),
                'header_score': scores.get('header_score', 0),
                'projects_score': scores.get('projects_score', 0),
                'format_score': scores.get('format_score', 0),
                'classification': scores.get('classification', 'Unknown'),
                'verdict': scores.get('verdict', 'Needs Review'),
                'matched_skills_count': scores.get('matched_skills_count', 0),
                'missing_skills_count': scores.get('missing_skills_count', 0),
                'extracted_text': parsed_data.get('full_text', ''),
                'text_length': len(parsed_data.get('full_text', '')),
                'processing_time': (datetime.now(timezone.utc) - start_time).total_seconds()
            }
            
            # Update resume in database
            for key, value in processing_results.items():
                if hasattr(resume, key):
                    setattr(resume, key, value)
            
            db.session.commit()
            
            # Cache results for future use
            cache.set(cache_key, processing_results, ttl=3600, use_pickle=True)
            
            # Log successful processing
            log_entry = ProcessingLog(
                resume_id=resume_id,
                stage='async_processing',
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                status='success',
                duration=processing_results['processing_time']
            )
            db.session.add(log_entry)
            db.session.commit()
            
            self.update_state(
                state='SUCCESS',
                meta={'status': 'Processing completed', 'progress': 100}
            )
            
            return {
                'status': 'success',
                'resume_id': resume_id,
                'cached': False,
                'results': processing_results
            }
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Async processing failed for resume {resume_id}: {error_message}")
        logger.error(traceback.format_exc())
        
        # Log failed processing
        with app.app_context():
            log_entry = ProcessingLog(
                resume_id=resume_id,
                stage='async_processing',
                start_time=start_time if 'start_time' in locals() else datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                status='failure',
                error_message=error_message
            )
            db.session.add(log_entry)
            db.session.commit()
        
        self.update_state(
            state='FAILURE',
            meta={'status': f'Processing failed: {error_message}', 'error': error_message}
        )
        
        raise Exception(f"Resume processing failed: {error_message}")

@app.task(name='tasks.cleanup_old_files')
def cleanup_old_files(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old uploaded files and temporary data
    
    Args:
        days_old: Remove files older than this many days
        
    Returns:
        Cleanup statistics
    """
    try:
        with app.app_context():
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Find old resumes
            old_resumes = Resume.query.filter(
                Resume.upload_timestamp < cutoff_date
            ).all()
            
            cleaned_files = 0
            cleaned_records = 0
            errors = []
            
            for resume in old_resumes:
                try:
                    # Remove physical file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned_files += 1
                    
                    # Remove database record
                    db.session.delete(resume)
                    cleaned_records += 1
                    
                except Exception as e:
                    errors.append(f"Failed to clean {resume.filename}: {str(e)}")
            
            db.session.commit()
            
            # Clean up cache patterns
            cache.flush_pattern("resume_processing:*")
            
            logger.info(f"Cleanup completed: {cleaned_files} files, {cleaned_records} records removed")
            
            return {
                'status': 'success',
                'cleaned_files': cleaned_files,
                'cleaned_records': cleaned_records,
                'errors': errors,
                'cutoff_date': cutoff_date.isoformat()
            }
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"File cleanup failed: {error_message}")
        return {
            'status': 'error',
            'error': error_message
        }

@app.task(name='tasks.export_csv_async')
def export_csv_async() -> Dict[str, Any]:
    """
    Update CSV export asynchronously
    
    Returns:
        Export status and statistics
    """
    try:
        with app.app_context():
            import models
            export_all_resumes_csv(app, db, models)
            
            # Get export statistics
            export_path = os.path.join('exports', 'all_resumes.csv')
            if os.path.exists(export_path):
                file_size = os.path.getsize(export_path)
                resume_count = Resume.query.count()
                
                logger.info(f"CSV export updated: {resume_count} resumes, {file_size} bytes")
                
                return {
                    'status': 'success',
                    'resume_count': resume_count,
                    'file_size': file_size,
                    'export_path': export_path,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'CSV export completed but file not found'
                }
                
    except Exception as e:
        error_message = str(e)
        logger.error(f"CSV export failed: {error_message}")
        return {
            'status': 'error',
            'error': error_message
        }

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of async task"""
    if not celery:
        return {'status': 'ERROR', 'message': 'Celery not initialized'}
    
    try:
        task = celery.AsyncResult(task_id)
        return {
            'status': task.status,
            'info': task.info,
            'ready': task.ready(),
            'successful': task.successful() if task.ready() else None
        }
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}

# Task queue information
def get_queue_info() -> Dict[str, Any]:
    """Get information about task queues"""
    if not celery:
        return {'error': 'Celery not initialized'}
    
    try:
        inspect = celery.control.inspect()
        return {
            'active': inspect.active(),
            'scheduled': inspect.scheduled(),
            'reserved': inspect.reserved(),
            'stats': inspect.stats()
        }
    except Exception as e:
        return {'error': str(e)}