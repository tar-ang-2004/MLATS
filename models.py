"""
Database models for ATS Resume Checker
Comprehensive schema for storing parsed resume data with proper relationships
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy import Index
import uuid

db = SQLAlchemy()

class Resume(db.Model):
    """Main resume record with metadata and analysis results"""
    __tablename__ = 'resumes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String(255), nullable=False)
    upload_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_size = db.Column(db.Integer)  # in bytes
    file_type = db.Column(db.String(10))  # pdf, docx
    
    # Analysis results
    overall_score = db.Column(db.Integer, nullable=False)  # 0-100
    classification = db.Column(db.String(50))  # Good Fit, Potential Fit, No Fit
    
    # Section scores
    skills_score = db.Column(db.Float, nullable=False, default=0.0)
    header_score = db.Column(db.Float, nullable=False, default=0.0)
    # Header job title written by candidate at top of resume
    header_job_title = db.Column(db.String(300))
    experience_score = db.Column(db.Float, nullable=False, default=0.0)
    projects_score = db.Column(db.Float, nullable=False, default=0.0)
    education_score = db.Column(db.Float, nullable=False, default=0.0)
    format_score = db.Column(db.Float, nullable=False, default=0.0)
    
    # Job matching data
    job_description_hash = db.Column(db.String(64))  # SHA256 of job description
    job_description_text = db.Column(db.Text)  # Full job description entered by user
    verdict = db.Column(db.String(500))  # Analysis verdict/summary
    matched_skills_count = db.Column(db.Integer, default=0)
    missing_skills_count = db.Column(db.Integer, default=0)
    
    # Raw text and metadata
    extracted_text = db.Column(db.Text)  # Full extracted text
    text_length = db.Column(db.Integer)
    processing_time = db.Column(db.Float)  # seconds
    
    # IP and session tracking (for analytics, optional)
    user_ip = db.Column(db.String(45))  # IPv6 compatible
    session_id = db.Column(db.String(128))
    
    # Relationships
    contact_info = db.relationship('ContactInfo', backref='resume', uselist=False, cascade='all, delete-orphan')
    skills = db.relationship('ResumeSkill', backref='resume', cascade='all, delete-orphan')
    experiences = db.relationship('Experience', backref='resume', cascade='all, delete-orphan')
    educations = db.relationship('Education', backref='resume', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='resume', cascade='all, delete-orphan')
    certifications = db.relationship('Certification', backref='resume', cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='resume', cascade='all, delete-orphan')
    matched_skills = db.relationship('MatchedSkill', backref='resume', cascade='all, delete-orphan')
    missing_skills = db.relationship('MissingSkill', backref='resume', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_resume_timestamp', 'upload_timestamp'),
        Index('idx_resume_score', 'overall_score'),
        Index('idx_resume_classification', 'classification'),
        Index('idx_resume_job_hash', 'job_description_hash'),
    )
    
    def __repr__(self):
        return f'<Resume {self.filename} - Score: {self.overall_score}>'

class ContactInfo(db.Model):
    """Contact information extracted from resume"""
    __tablename__ = 'contact_info'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Personal information
    full_name = db.Column(db.String(200))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Contact details
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    
    # Location
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Professional profiles
    linkedin_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    
    # Additional URLs/profiles as JSON
    other_urls = db.Column(JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ContactInfo {self.full_name} - {self.email}>'

class ResumeSkill(db.Model):
    """Skills extracted from resume"""
    __tablename__ = 'resume_skills'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    skill_name = db.Column(db.String(200), nullable=False)
    skill_category = db.Column(db.String(100))  # Technical, Soft, Language, etc.
    proficiency_level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced, Expert
    years_experience = db.Column(db.Integer)
    is_primary = db.Column(db.Boolean, default=False)  # Key skill for the role
    
    # Context where skill was found
    context_section = db.Column(db.String(100))  # Skills, Experience, Projects, etc.
    confidence_score = db.Column(db.Float)  # NLP confidence in extraction
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_skill_name', 'skill_name'),
        Index('idx_skill_category', 'skill_category'),
    )

class Experience(db.Model):
    """Work experience entries"""
    __tablename__ = 'experiences'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Company information
    company_name = db.Column(db.String(300), nullable=False)
    job_title = db.Column(db.String(300), nullable=False)
    department = db.Column(db.String(200))
    
    # Employment details
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)  # NULL for current position
    is_current = db.Column(db.Boolean, default=False)
    employment_type = db.Column(db.String(50))  # Full-time, Part-time, Contract, etc.
    
    # Location
    location = db.Column(db.String(200))
    is_remote = db.Column(db.Boolean, default=False)
    
    # Job description
    description = db.Column(db.Text)
    responsibilities = db.Column(JSON)  # Array of responsibility strings
    achievements = db.Column(JSON)  # Array of achievement strings
    
    # Calculated fields
    duration_months = db.Column(db.Integer)  # Auto-calculated
    seniority_level = db.Column(db.String(50))  # Junior, Mid, Senior, Lead, Manager, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_experience_company', 'company_name'),
        Index('idx_experience_title', 'job_title'),
        Index('idx_experience_dates', 'start_date', 'end_date'),
    )

class Education(db.Model):
    """Education background"""
    __tablename__ = 'education'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Institution information
    institution_name = db.Column(db.String(300), nullable=False)
    institution_type = db.Column(db.String(100))  # University, College, Bootcamp, etc.
    location = db.Column(db.String(200))
    
    # Degree information
    degree_type = db.Column(db.String(100))  # Bachelor's, Master's, PhD, Certificate, etc.
    degree_name = db.Column(db.String(300))
    major = db.Column(db.String(200))
    minor = db.Column(db.String(200))
    
    # Academic details
    gpa = db.Column(db.Float)
    gpa_scale = db.Column(db.Float, default=4.0)
    honors = db.Column(db.String(200))  # Magna Cum Laude, etc.
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    graduation_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    
    # Additional details
    relevant_coursework = db.Column(JSON)  # Array of course names
    thesis_title = db.Column(db.String(500))
    activities = db.Column(JSON)  # Extracurricular activities
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_education_institution', 'institution_name'),
        Index('idx_education_degree', 'degree_type', 'degree_name'),
    )

class Project(db.Model):
    """Projects mentioned in resume"""
    __tablename__ = 'projects'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Project information
    project_name = db.Column(db.String(300), nullable=False)
    project_type = db.Column(db.String(100))  # Personal, Academic, Professional, Open Source
    description = db.Column(db.Text)
    
    # Project details
    technologies_used = db.Column(JSON)  # Array of technologies
    role = db.Column(db.String(200))  # Developer, Lead, Contributor, etc.
    team_size = db.Column(db.Integer)
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_ongoing = db.Column(db.Boolean, default=False)
    
    # Links
    github_url = db.Column(db.String(500))
    demo_url = db.Column(db.String(500))
    documentation_url = db.Column(db.String(500))
    
    # Impact metrics
    achievements = db.Column(JSON)  # Array of achievement strings
    metrics = db.Column(JSON)  # Performance metrics, user counts, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_project_name', 'project_name'),
        Index('idx_project_type', 'project_type'),
    )

class Certification(db.Model):
    """Certifications and licenses"""
    __tablename__ = 'certifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Certification details
    certification_name = db.Column(db.String(300), nullable=False)
    issuing_organization = db.Column(db.String(300), nullable=False)
    certification_type = db.Column(db.String(100))  # Professional, Technical, Academic, etc.
    
    # Dates
    issue_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Additional information
    credential_id = db.Column(db.String(200))
    verification_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_certification_name', 'certification_name'),
        Index('idx_certification_org', 'issuing_organization'),
    )

class Achievement(db.Model):
    """Awards, honors, and other achievements"""
    __tablename__ = 'achievements'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    # Achievement details
    achievement_name = db.Column(db.String(300), nullable=False)
    achievement_type = db.Column(db.String(100))  # Award, Honor, Publication, Patent, etc.
    issuing_organization = db.Column(db.String(300))
    
    # Description and context
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # Academic, Professional, Community, etc.
    
    # Dates
    date_received = db.Column(db.Date)
    year = db.Column(db.Integer)  # If only year is available
    
    # Additional details
    competition_level = db.Column(db.String(100))  # Local, National, International, etc.
    rank_position = db.Column(db.String(50))  # 1st Place, Top 10%, etc.
    monetary_value = db.Column(db.Float)  # For scholarships, grants, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_achievement_type', 'achievement_type'),
        Index('idx_achievement_date', 'date_received'),
    )

class MatchedSkill(db.Model):
    """Skills that matched the job description"""
    __tablename__ = 'matched_skills'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    skill_name = db.Column(db.String(200), nullable=False)
    match_type = db.Column(db.String(50))  # Exact, Semantic, Partial
    confidence_score = db.Column(db.Float)  # 0.0 to 1.0
    
    # Context from job description
    job_requirement = db.Column(db.Text)  # Original text from job description
    resume_context = db.Column(db.Text)  # Where it was found in resume
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MissingSkill(db.Model):
    """Skills mentioned in job description but not found in resume"""
    __tablename__ = 'missing_skills'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'), nullable=False)
    
    skill_name = db.Column(db.String(200), nullable=False)
    skill_category = db.Column(db.String(100))
    importance_level = db.Column(db.String(50))  # Required, Preferred, Nice-to-have
    
    # Context from job description
    job_requirement = db.Column(db.Text)  # Original text from job description
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobDescription(db.Model):
    """Store job descriptions for analytics"""
    __tablename__ = 'job_descriptions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA256
    
    # Job details
    job_title = db.Column(db.String(300))
    company_name = db.Column(db.String(300))
    job_level = db.Column(db.String(100))  # Entry, Mid, Senior, etc.
    industry = db.Column(db.String(200))
    
    # Full content
    description_text = db.Column(db.Text, nullable=False)
    
    # Extracted requirements
    required_skills = db.Column(JSON)  # Array of required skills
    preferred_skills = db.Column(JSON)  # Array of preferred skills
    required_experience_years = db.Column(db.Integer)
    education_requirements = db.Column(JSON)
    
    # Analytics
    usage_count = db.Column(db.Integer, default=1)
    first_used = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_job_hash', 'content_hash'),
        Index('idx_job_title', 'job_title'),
        Index('idx_job_company', 'company_name'),
    )

# Additional utility tables for analytics and optimization

class ProcessingLog(db.Model):
    """Log processing times and errors for monitoring"""
    __tablename__ = 'processing_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.id'))
    
    # Processing details
    stage = db.Column(db.String(100))  # parse, extract, score, save
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(50))  # success, error, warning
    error_message = db.Column(db.Text)
    error_type = db.Column(db.String(200))
    
    # System info
    server_id = db.Column(db.String(100))  # For load balancing
    memory_usage = db.Column(db.Float)  # MB
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Analytics(db.Model):
    """Daily analytics aggregations"""
    __tablename__ = 'analytics'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = db.Column(db.Date, nullable=False, unique=True)
    
    # Volume metrics
    total_resumes_processed = db.Column(db.Integer, default=0)
    total_unique_users = db.Column(db.Integer, default=0)
    
    # Score distributions
    avg_overall_score = db.Column(db.Float)
    avg_skills_score = db.Column(db.Float)
    avg_experience_score = db.Column(db.Float)
    avg_education_score = db.Column(db.Float)
    
    # Classification breakdown
    good_fit_count = db.Column(db.Integer, default=0)
    potential_fit_count = db.Column(db.Integer, default=0)
    no_fit_count = db.Column(db.Integer, default=0)
    
    # Performance metrics
    avg_processing_time = db.Column(db.Float)
    error_rate = db.Column(db.Float)
    
    # Top skills/industries
    top_skills = db.Column(JSON)  # Array of {skill, count}
    top_companies = db.Column(JSON)  # Array of {company, count}
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)