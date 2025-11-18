from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import sys
import importlib
import hashlib
import time
import logging
from datetime import datetime, date, timezone
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from sqlalchemy import text
import PyPDF2
from docx import Document
import io
import re

# Database imports
from models import db, Resume, ContactInfo, ResumeSkill, Experience, Education, Project
from models import Certification, Achievement, MatchedSkill, MissingSkill, JobDescription
from models import ProcessingLog, Analytics
from config import get_config
from export_csv import register_export_listeners
from flask_migrate import Migrate
from logging_config import setup_logging

# Force reload of ats_components to get latest changes
if 'ats_components' in sys.modules:
    importlib.reload(sys.modules['ats_components'])

# Import new comprehensive ATS engine
try:
    from ats_components import ATSScorer, ResumeParser, ResumeExtractor, ContactExtractor, SemanticMatcher
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML dependencies not available: {e}. Using new comprehensive ATS engine.")
    ML_AVAILABLE = False

# Always use the new comprehensive ATS engine for consistent results
from ats_engine_new import ATSResumeAnalyzer

# Initialize the new ATS engine
ats_analyzer = ATSResumeAnalyzer()

# Create compatibility wrapper classes for existing code
class ATSScorer:
    def __init__(self, *args, **kwargs):
        pass
    
    def score_resume(self, resume_text, job_description=''):
        """Wrapper for new ATS engine - converts to old format"""
        result = ats_analyzer.analyze_resume(resume_text, job_description)
        
        # Convert new format to old format for compatibility
        return {
            'overall_score': result['overall_score'],
            'skills_score': result['section_scores']['skills'],
            'header_score': result['section_scores']['contact_info'],
            'experience_score': result['section_scores']['experience'],
            'projects_score': result['section_scores']['projects'],
            'education_score': result['section_scores']['education'],
            'format_score': result['section_scores']['format_quality'],
            'matched_skills': result['analysis_details']['skills_summary']['matched_skills'],
            'missing_skills': result['analysis_details']['skills_summary']['missing_skills'],
            'message': f"Analysis complete using new comprehensive engine"
        }

class ResumeParser:
    def __init__(self):
        pass
        
    def parse_resume(self, resume_text):
        """Wrapper for new ATS engine - extracts sections"""
        result = ats_analyzer.analyze_resume(resume_text)
        
        # Convert to expected format for backward compatibility
        parsed_sections = result['extracted_data']
        
        # Convert skills format from categorized to simple list
        skills_list = []
        if isinstance(parsed_sections.get('skills'), dict):
            for category, skill_list in parsed_sections['skills'].items():
                skills_list.extend(skill_list)
        else:
            skills_list = parsed_sections.get('skills', [])
        
        return {
            'contact_info': parsed_sections['contact_info'],
            'experience': parsed_sections['experience'],
            'education': parsed_sections['education'],
            'projects': parsed_sections['projects'],
            'skills': skills_list
        }

class ResumeExtractor:
    def extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX files"""
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        else:
            return "Unsupported file format"
    
    def _extract_from_pdf(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def _extract_from_docx(self, file_path):
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            return f"Error extracting DOCX: {str(e)}"

class ContactExtractor:
    def extract_contact_info(self, resume_text):
        """Extract contact information using new engine"""
        result = ats_analyzer.analyze_resume(resume_text)
        return result['extracted_data']['contact_info']

class SemanticMatcher:
    def __init__(self):
        pass
    
    def match_skills(self, resume_text, job_description):
        """Match skills using new engine"""
        result = ats_analyzer.analyze_resume(resume_text, job_description)
        matched = result['analysis_details']['skills_summary']['matched_skills']
        missing = result['analysis_details']['skills_summary']['missing_skills']
        return matched, missing

# Initialize Flask app with configuration
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Setup logging (must be done early)
app_logger, security_logger = setup_logging(app)

# Initialize security extensions
csrf = CSRFProtect(app)

# Configure Talisman for security headers
csp = {
    'default-src': "'self'",
    'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'"],
    'font-src': ["'self'", "https://cdn.jsdelivr.net"],
}

talisman = Talisman(
    app,
    force_https=False,  # Set to True in production
    strict_transport_security=True,
    content_security_policy=csp
)

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Register CSV export listeners
from models import Resume, ContactInfo, ResumeSkill, Experience, Education, Project
register_export_listeners(app, db, {
    'Resume': Resume,
    'ContactInfo': ContactInfo, 
    'ResumeSkill': ResumeSkill,
    'Experience': Experience,
    'Education': Education,
    'Project': Project
})

# Initialize ATS components
try:
    if ML_AVAILABLE:
        ats_scorer = ATSScorer()
        resume_parser = ResumeParser()
        resume_extractor = ResumeExtractor()
        contact_extractor = ContactExtractor()
        semantic_matcher = SemanticMatcher()
    else:
        # Use the wrapper classes that leverage the new engine
        ats_scorer = ATSScorer()
        resume_parser = ResumeParser()
        resume_extractor = ResumeExtractor()
        contact_extractor = ContactExtractor()
        semantic_matcher = SemanticMatcher()
        
    app_logger.info("ATS components initialized successfully")
except Exception as e:
    app_logger.error(f"Failed to initialize ATS components: {e}")
    # Create minimal fallback components
    class MinimalATSScorer:
        def score_resume(self, resume_text, job_description=''):
            return {
                'overall_score': 50.0,
                'skills_score': 50.0,
                'header_score': 50.0,
                'experience_score': 50.0,
                'projects_score': 50.0,
                'education_score': 50.0,
                'format_score': 50.0,
                'matched_skills': [],
                'missing_skills': [],
                'message': 'Minimal scoring - ATS engine unavailable'
            }
    
    ats_scorer = MinimalATSScorer()
    resume_parser = None
    resume_extractor = None
    contact_extractor = None
    semantic_matcher = None

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'txt'}

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    try:
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
            
        elif filename.endswith('.docx'):
            doc = Document(io.BytesIO(file.read()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
            
        elif filename.endswith('.txt'):
            return file.read().decode('utf-8')
            
        else:
            return "Unsupported file format"
            
    except Exception as e:
        app_logger.error(f"Error extracting text from file: {e}")
        return f"Error reading file: {str(e)}"

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/ai')
def ai_page():
    """AI features page"""
    return render_template('ai.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    try:
        # Get recent resumes for dashboard
        recent_resumes = db.session.query(Resume).order_by(Resume.created_at.desc()).limit(10).all()
        
        # Calculate dashboard statistics
        total_resumes = db.session.query(Resume).count()
        avg_score = db.session.query(db.func.avg(Resume.overall_score)).scalar() or 0
        
        # Get score distribution
        score_ranges = {
            'excellent': db.session.query(Resume).filter(Resume.overall_score >= 80).count(),
            'good': db.session.query(Resume).filter(Resume.overall_score.between(60, 79)).count(),
            'needs_improvement': db.session.query(Resume).filter(Resume.overall_score < 60).count()
        }
        
        dashboard_data = {
            'recent_resumes': [{
                'id': resume.id,
                'filename': resume.filename,
                'overall_score': round(resume.overall_score, 1),
                'created_at': resume.created_at.strftime('%Y-%m-%d %H:%M')
            } for resume in recent_resumes],
            'statistics': {
                'total_resumes': total_resumes,
                'average_score': round(avg_score, 1),
                'score_distribution': score_ranges
            }
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        app_logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', data={'recent_resumes': [], 'statistics': {}})

@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_resume():
    """Analyze uploaded resume"""
    try:
        # Check if file was uploaded
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        job_description = request.form.get('job_description', '').strip()
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Please upload PDF, DOCX, or TXT files.'}), 400
        
        # Extract text from file
        resume_text = extract_text_from_file(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({'error': 'Could not extract text from file or file is too short'}), 400
        
        # Perform comprehensive analysis using new engine
        analysis_result = ats_analyzer.analyze_resume(resume_text, job_description)
        
        # Also get old format for compatibility
        score_result = ats_scorer.score_resume(resume_text, job_description)
        parsed_sections = resume_parser.parse_resume(resume_text) if resume_parser else {}
        
        # Store results in database
        try:
            # Create resume record
            resume = Resume(
                filename=secure_filename(file.filename),
                original_text=resume_text[:5000],  # Limit stored text
                overall_score=analysis_result['overall_score'],
                skills_score=analysis_result['section_scores']['skills'],
                experience_score=analysis_result['section_scores']['experience'],
                education_score=analysis_result['section_scores']['education'],
                projects_score=analysis_result['section_scores']['projects'],
                format_score=analysis_result['section_scores']['format_quality'],
                contact_score=analysis_result['section_scores']['contact_info'],
                file_hash=hashlib.md5(resume_text.encode()).hexdigest()
            )
            
            db.session.add(resume)
            db.session.flush()  # Get the ID
            
            # Store contact info
            contact_info = analysis_result['extracted_data']['contact_info']
            if any(contact_info.values()):
                contact = ContactInfo(
                    resume_id=resume.id,
                    name=contact_info.get('name', ''),
                    email=contact_info.get('email', ''),
                    phone=contact_info.get('phone', ''),
                    location=contact_info.get('location', ''),
                    linkedin=contact_info.get('linkedin', ''),
                    github=contact_info.get('github', '')
                )
                db.session.add(contact)
            
            # Store skills
            skills_data = analysis_result['extracted_data']['skills']
            if isinstance(skills_data, dict):
                for category, skill_list in skills_data.items():
                    for skill in skill_list[:20]:  # Limit skills stored
                        skill_record = ResumeSkill(
                            resume_id=resume.id,
                            skill_name=skill,
                            category=category
                        )
                        db.session.add(skill_record)
            
            # Store matched and missing skills
            matched_skills = analysis_result['analysis_details']['skills_summary']['matched_skills']
            missing_skills = analysis_result['analysis_details']['skills_summary']['missing_skills']
            
            for skill in matched_skills[:10]:
                matched = MatchedSkill(resume_id=resume.id, skill_name=skill)
                db.session.add(matched)
            
            for skill in missing_skills[:10]:
                missing = MissingSkill(resume_id=resume.id, skill_name=skill)
                db.session.add(missing)
            
            # Store job description if provided
            if job_description:
                job_desc = JobDescription(
                    resume_id=resume.id,
                    description=job_description[:2000],
                    requirements_extracted=json.dumps(missing_skills[:10])
                )
                db.session.add(job_desc)
            
            db.session.commit()
            app_logger.info(f"Resume analysis completed for file: {file.filename}")
            
        except Exception as db_error:
            app_logger.error(f"Database error during resume storage: {db_error}")
            db.session.rollback()
            # Continue with analysis even if database storage fails
        
        # Calculate average score for comparison
        try:
            avg_score = db.session.query(db.func.avg(Resume.overall_score)).scalar()
            avg_score = float(avg_score) if avg_score else None
        except:
            avg_score = None
        
        # Return comprehensive results
        return jsonify({
            'success': True,
            'overall_score': analysis_result['overall_score'],
            'scores': {
                'contact_info': analysis_result['section_scores']['contact_info'],
                'experience': analysis_result['section_scores']['experience'],
                'education': analysis_result['section_scores']['education'],
                'skills': analysis_result['section_scores']['skills'],
                'projects': analysis_result['section_scores']['projects'],
                'format_quality': analysis_result['section_scores']['format_quality']
            },
            'parsed_sections': {
                'contact_info': analysis_result['extracted_data']['contact_info'],
                'experience': analysis_result['extracted_data']['experience'],
                'education': analysis_result['extracted_data']['education'],
                'skills': [skill for category_skills in analysis_result['extracted_data']['skills'].values() 
                          for skill in category_skills] if isinstance(analysis_result['extracted_data']['skills'], dict) 
                         else analysis_result['extracted_data']['skills'],
                'projects': analysis_result['extracted_data']['projects'],
                'certifications': []  # Add if needed
            },
            'details': analysis_result['analysis_details'],
            'recommendations': analysis_result['recommendations'],
            'average_score': avg_score,
            'message': 'Analysis completed successfully using comprehensive ATS engine'
        })
        
    except Exception as e:
        app_logger.error(f"Resume analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/history')
def get_analysis_history():
    """Get analysis history for user"""
    try:
        # Get recent analyses
        recent_analyses = db.session.query(Resume).order_by(Resume.created_at.desc()).limit(50).all()
        
        history = []
        for resume in recent_analyses:
            history.append({
                'id': resume.id,
                'filename': resume.filename,
                'overall_score': round(resume.overall_score, 1),
                'created_at': resume.created_at.isoformat(),
                'scores': {
                    'contact_info': round(resume.contact_score, 1),
                    'experience': round(resume.experience_score, 1),
                    'education': round(resume.education_score, 1),
                    'skills': round(resume.skills_score, 1),
                    'projects': round(resume.projects_score, 1),
                    'format_quality': round(resume.format_score, 1)
                }
            })
        
        return jsonify({'history': history})
        
    except Exception as e:
        app_logger.error(f"History retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve history'}), 500

@app.route('/export/csv')
def export_csv():
    """Export analysis results as CSV"""
    try:
        from export_csv import generate_csv_export
        return generate_csv_export(db)
    except Exception as e:
        app_logger.error(f"CSV export error: {e}")
        return jsonify({'error': 'Export failed'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ats_engine': 'comprehensive_v2',
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        app_logger.info("Database tables initialized successfully")
    except Exception as e:
        app_logger.error(f"Database initialization error: {e}")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))