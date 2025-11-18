# Updated: Comprehensive ATS Resume Checker Flask Application
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import sys
import importlib
import hashlib
import time
import logging
import traceback
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
from typing import Dict, List, Any, Optional, Tuple
import statistics

# Database imports
from models import db, Resume, ContactInfo, ResumeSkill, Experience, Education, Project
from models import Certification, Achievement, MatchedSkill, MissingSkill, JobDescription
from models import ProcessingLog, Analytics
from config import get_config
from export_csv import register_export_listeners
from flask_migrate import Migrate

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ats_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Enhanced security configuration
csrf = CSRFProtect(app)
talisman = Talisman(
    app,
    force_https=app.config.get('FLASK_ENV') == 'production',
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'", 
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com",
            "https://cdnjs.cloudflare.com"
        ],
        'style-src': [
            "'self'", 
            "'unsafe-inline'",
            "https://cdnjs.cloudflare.com"
        ],
        'font-src': [
            "'self'",
            "https://cdnjs.cloudflare.com"
        ]
    }
)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Database setup
db.init_app(app)
migrate = Migrate(app, db)

# CSV export setup
register_export_listeners(app)

# Create upload directory
os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

# Enhanced Contact Extractor
class ContactExtractor:
    """Extract contact information from resume text"""
    
    def __init__(self):
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # Enhanced phone pattern to capture various formats including international
        self.phone_patterns = [
            r'\+\d{1,4}[\s-]?\(?\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,6}',  # International format
            r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',  # US format
            r'\d{10,}',  # Simple 10+ digit sequence
            r'\+?\d{1,4}[\s()-\.]{0,3}\d{6,14}'  # General international
        ]
        self.linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        self.github_pattern = r'github\.com/[\w-]+'
        self.name_patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s*$',  # Proper case names
            r'^([A-Z\s]{2,50})$'  # All caps names (less preferred)
        ]
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text"""
        lines = [line.strip() for line in text.split('\n')[:10] if line.strip()]
        
        for line in lines:
            # Skip lines with emails, phones, or URLs
            if (re.search(self.email_pattern, line) or 
                any(re.search(pattern, line) for pattern in self.phone_patterns) or
                'linkedin.com' in line.lower() or 'github.com' in line.lower()):
                continue
            
            # Check for name patterns
            for pattern in self.name_patterns:
                match = re.match(pattern, line)
                if match:
                    name = match.group(1).strip()
                    # Filter out common non-names
                    if not any(word.lower() in name.lower() for word in 
                             ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'engineer', 'developer']):
                        return name
        
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number with enhanced pattern matching"""
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean and validate phone number
                cleaned = re.sub(r'[^\d+]', '', match)
                if len(cleaned) >= 10:  # Minimum valid phone length
                    return match.strip()
        return None
    
    def extract_contact(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive contact information"""
        return {
            'full_name': self.extract_name(text),
            'email': self._extract_first_match(self.email_pattern, text),
            'phone': self.extract_phone(text),
            'linkedin': self._extract_first_match(self.linkedin_pattern, text),
            'github': self._extract_first_match(self.github_pattern, text)
        }
    
    def _extract_first_match(self, pattern: str, text: str) -> Optional[str]:
        """Extract first match for a given pattern"""
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches[0] if matches else None


class EnhancedResumeExtractor:
    """Enhanced resume content extraction with improved parsing"""
    
    def __init__(self):
        # Comprehensive skill database
        self.technical_skills = {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby', 
                'php', 'swift', 'kotlin', 'scala', 'go', 'rust', 'r', 'matlab',
                'perl', 'shell', 'bash', 'powershell', 'sql', 'plsql', 'nosql'
            ],
            'web_frameworks': [
                'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask',
                'spring', 'rails', 'laravel', 'asp.net', 'blazor', 'nextjs', 'nuxtjs',
                'fastapi', 'tornado', 'bottle', 'pyramid'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb',
                'oracle', 'sqlite', 'cassandra', 'neo4j', 'influxdb', 'mariadb',
                'cosmos', 'firestore', 'couchdb'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
                'jenkins', 'gitlab', 'github', 'circleci', 'travis', 'helm', 'vagrant',
                'prometheus', 'grafana', 'elk', 'splunk'
            ],
            'data_science': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'opencv', 'nltk', 'spacy', 'matplotlib', 'seaborn', 'plotly', 'tableau',
                'powerbi', 'spark', 'hadoop', 'kafka', 'airflow', 'mlflow'
            ],
            'mobile': [
                'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
                'cordova', 'phonegap', 'swiftui', 'objective-c'
            ]
        }
        
        self.all_skills = []
        for category in self.technical_skills.values():
            self.all_skills.extend(category)
        
        # Education patterns
        self.degree_patterns = [
            r'bachelor(?:\'s)?(?:\s+of)?(?:\s+science)?(?:\s+in)?',
            r'master(?:\'s)?(?:\s+of)?(?:\s+science)?(?:\s+in)?',
            r'phd|doctorate|doctoral',
            r'associate(?:\'s)?(?:\s+degree)?',
            r'diploma(?:\s+in)?',
            r'certificate(?:\s+in)?',
            r'b\.?tech|btech|b\.?e\.?|be|bs|ba|bsc|ms|msc|mba|me|mtech'
        ]
        
        self.institution_indicators = [
            'university', 'college', 'institute', 'school', 'academy', 'iit', 'nit', 'iiit'
        ]
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills with enhanced pattern matching"""
        text_lower = text.lower()
        found_skills = set()
        
        # Check for skills in dedicated skills section first
        skills_section = self._extract_section(text, ['skills', 'technical skills', 'core competencies', 'technologies'])
        
        # Extract structured skills from skills section (like in your resume format)
        if skills_section:
            self._extract_structured_skills(skills_section, found_skills)
        
        # Check entire document for technical skills
        for skill in self.all_skills:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(skill.lower()) + r'(?:js|\.js)?\b', text_lower):
                found_skills.add(skill.title())
        
        # Extract additional skills from context
        self._extract_contextual_skills(text, found_skills)
        
        return list(found_skills)[:50]  # Limit to reasonable number
    
    def _extract_structured_skills(self, skills_section: str, found_skills: set):
        """Extract skills from structured format like in resumes"""
        lines = [line.strip() for line in skills_section.split('\n') if line.strip()]
        
        for line in lines:
            # Handle bullet point format: "• Programming Skills: Python, SQL, Bash, Git..."
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    skills_text = parts[1]
                    # Extract comma-separated skills
                    skill_candidates = [s.strip() for s in re.split(r'[,;&]', skills_text) if s.strip()]
                    for skill in skill_candidates:
                        # Clean up skill name
                        skill = re.sub(r'^[•\-\*\s]+', '', skill).strip()
                        skill = re.sub(r'[,.]$', '', skill).strip()
                        if len(skill) > 1 and len(skill) < 30:  # Reasonable length
                            found_skills.add(skill.title())
            else:
                # Handle direct listing format
                skill_candidates = [s.strip() for s in re.split(r'[,;&•\-\*]', line) if s.strip()]
                for skill in skill_candidates:
                    skill = skill.strip()
                    if len(skill) > 1 and len(skill) < 30 and not skill.lower().startswith(('programming', 'tools', 'ml techniques', 'libraries')):
                        found_skills.add(skill.title())
    
    def _extract_contextual_skills(self, text: str, found_skills: set):
        """Extract skills from context and project descriptions"""
        # Common technical terms that might appear in projects/experience
        contextual_skills = [
            'api', 'rest', 'restful', 'microservices', 'backend', 'frontend',
            'database', 'sql', 'nosql', 'crud', 'mvc', 'oop', 'agile', 'scrum',
            'ci/cd', 'devops', 'cloud', 'deployment', 'testing', 'debugging',
            'optimization', 'performance', 'scalability', 'security'
        ]
        
        text_lower = text.lower()
        for skill in contextual_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.add(skill.upper() if skill in ['api', 'rest', 'sql', 'crud', 'mvc', 'oop'] else skill.title())
    
    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience with comprehensive parsing including achievements"""
        experience_section = self._extract_section(text, ['experience', 'work experience', 'employment', 'professional experience'])
        
        if not experience_section:
            return []
        
        experiences = []
        lines = [line.strip() for line in experience_section.split('\n') if line.strip()]
        current_exp = None
        current_achievements = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for company/title header
            if self._is_experience_header(line):
                # Save previous experience
                if current_exp:
                    if current_achievements:
                        current_exp['achievements'] = current_achievements
                    experiences.append(current_exp)
                
                # Parse new experience header
                current_exp = self._parse_experience_header(line)
                current_achievements = []
                i += 1
                
                # Look for dates/location in next line
                if i < len(lines) and self._contains_date_or_location(lines[i]):
                    dates, location = self._parse_date_location(lines[i])
                    if dates:
                        current_exp['dates'] = dates
                    if location:
                        current_exp['location'] = location
                    i += 1
                
                # Continue parsing achievements until next company header
                while i < len(lines) and not self._is_experience_header(lines[i]):
                    achievement_line = lines[i].strip()
                    
                    # Check for bullet points or achievement lines
                    if (achievement_line.startswith(('•', '-', '*', '·')) or 
                        (achievement_line and len(achievement_line) > 15 and not self._contains_date_or_location(achievement_line))):
                        
                        achievement = achievement_line.lstrip('•-*· ').strip()
                        if len(achievement) > 15:  # Must be meaningful
                            current_achievements.append(achievement)
                    
                    i += 1
            else:
                i += 1
        
        # Don't forget the last experience
        if current_exp:
            if current_achievements:
                current_exp['achievements'] = current_achievements
            experiences.append(current_exp)
        
        return experiences[:10]
    
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education with enhanced parsing for various formats"""
        education_section = self._extract_section(text, ['education', 'academic', 'qualification', 'educational background'])
        
        if not education_section:
            return []
        
        educations = []
        lines = [line.strip() for line in education_section.split('\n') if line.strip()]
        
        current_edu = None
        
        for i, line in enumerate(lines):
            # Check for institution names or degree patterns
            if (any(indicator in line.lower() for indicator in self.institution_indicators) or 
                self._is_degree_line(line)):
                
                # Save previous education
                if current_edu:
                    # Set default degree if not found
                    if 'degree' not in current_edu:
                        current_edu['degree'] = 'Degree not specified'
                    educations.append(current_edu)
                
                # Determine if this line is institution or degree
                if any(indicator in line.lower() for indicator in self.institution_indicators):
                    # This is an institution
                    institution_line = line
                    # Extract CGPA/Grade if present in the same line
                    cgpa_match = re.search(r'[–—-]\s*(\d+\.\d+)\s*(?:cgpa|gpa)', line.lower())
                    if cgpa_match:
                        institution_line = re.sub(r'[–—-]\s*\d+\.\d+\s*(?:cgpa|gpa).*$', '', line, flags=re.IGNORECASE).strip()
                        cgpa = cgpa_match.group(1)
                    else:
                        cgpa = None
                        
                    current_edu = {'institution': institution_line}
                    if cgpa:
                        current_edu['cgpa'] = cgpa
                else:
                    # This is a degree line
                    current_edu = {'degree': line, 'institution': 'Institution not specified'}
                
                # Look for additional info in surrounding lines
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j]
                    
                    # Look for dates
                    if self._contains_date(next_line):
                        current_edu['dates'] = self._extract_dates(next_line)
                    
                    # Look for degree if we have institution
                    elif 'degree' not in current_edu and self._is_degree_line(next_line):
                        current_edu['degree'] = next_line
                    
                    # Look for CGPA/Grade
                    elif 'cgpa' not in current_edu:
                        cgpa_match = re.search(r'(?:cgpa|gpa)\s*:?\s*(\d+\.\d+)', next_line.lower())
                        grade_match = re.search(r'grade\s*:?\s*(\d+%)', next_line.lower())
                        if cgpa_match:
                            current_edu['cgpa'] = cgpa_match.group(1)
                        elif grade_match:
                            current_edu['grade'] = grade_match.group(1)
        
        # Don't forget the last education
        if current_edu:
            if 'degree' not in current_edu:
                current_edu['degree'] = 'Degree not specified'
            educations.append(current_edu)
        
        return educations[:5]
    
    def extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects with comprehensive parsing for structured formats"""
        # Try multiple section name patterns
        projects_section = self._extract_section(text, ['projects', 'personal projects', 'key projects', 'project'])
        
        if not projects_section:
            # Fallback: look for project patterns in the entire text
            project_patterns = [
                r'(Advanced News Analysis System|Vaccination Data Analysis|Task Management Application|Academic Management System|Sentiment Analysis Model).*?(?=\n(?:[A-Z][A-Za-z\s]+(?:\([^)]+\))?\s*(?:\n|$))|(?:\n\s*(?:EDUCATION|SKILLS|EXPERIENCE|CERTIFICATIONS)))',
            ]
            
            for pattern in project_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                if matches:
                    projects_section = '\n'.join(matches)
                    break
        
        if not projects_section:
            return []
        
        projects = []
        lines = [line.strip() for line in projects_section.split('\n') if line.strip()]
        
        current_project = None
        current_achievements = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is a project title (not a bullet point)
            if not line.startswith(('•', '-', '*', '·')) and self._is_project_title(line):
                # Save previous project if exists
                if current_project:
                    if current_achievements:
                        current_project['achievements'] = current_achievements
                    projects.append(current_project)
                
                # Start new project
                project_name = line
                technologies = ''
                github_link = ''
                
                # Extract technologies and GitHub link from the same line
                tech_match = re.search(r'\(([^)]+)\)\s*(?:\[GitHub\])?\s*$', line)
                if tech_match:
                    technologies = tech_match.group(1)
                    project_name = re.sub(r'\s*\([^)]+\)\s*(?:\[GitHub\])?\s*$', '', line).strip()
                
                if '[GitHub]' in line or 'GitHub' in line:
                    github_link = 'Available on GitHub'
                
                current_project = {
                    'name': project_name,
                    'technologies': technologies,
                    'github': github_link,
                    'achievements': []
                }
                current_achievements = []
                i += 1
                
                # Continue parsing achievements until next project
                while i < len(lines) and not self._is_project_title(lines[i].strip()):
                    achievement_line = lines[i].strip()
                    
                    # Check for bullet points
                    if achievement_line.startswith(('•', '-', '*', '·')):
                        achievement = achievement_line.lstrip('•-*· ').strip()
                        if len(achievement) > 10:  # Meaningful achievement
                            current_achievements.append(achievement)
                    
                    i += 1
            else:
                i += 1
        
        # Don't forget the last project
        if current_project:
            if current_achievements:
                current_project['achievements'] = current_achievements
            projects.append(current_project)
        
        return projects[:10]
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications and achievements"""
        cert_section = self._extract_section(text, [
            'certifications', 'certificates', 'achievements', 'awards', 'honors'
        ])
        
        if not cert_section:
            return []
        
        # Split by bullets or newlines
        certs = []
        entries = re.split(r'\n\s*[•\-\*]\s*|\n+', cert_section)
        
        for entry in entries:
            entry = entry.strip()
            if 10 <= len(entry) <= 200:  # Reasonable length
                certs.append(entry)
        
        return certs[:15]
    
    def extract_header_title(self, text: str) -> Optional[str]:
        """Extract job title from resume header"""
        lines = [line.strip() for line in text.split('\n')[:10] if line.strip()]
        
        title_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'scientist', 'designer',
            'architect', 'consultant', 'specialist', 'lead', 'senior', 'junior'
        ]
        
        for line in lines:
            # Skip contact information
            if (re.search(r'@', line) or re.search(r'\+?\d{10,}', line) or
                'linkedin.com' in line.lower() or 'github.com' in line.lower()):
                continue
            
            # Check for title keywords
            if any(keyword in line.lower() for keyword in title_keywords):
                return line.title()
        
        return None
    
    # Helper methods
    def _extract_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract a specific section from resume with robust pattern matching"""
        # Define all possible section headers for proper boundaries
        all_sections = [
            'SUMMARY', 'OBJECTIVE', 'PROFILE',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'TECHNOLOGIES',
            'EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT', 'PROFESSIONAL EXPERIENCE',
            'PROJECTS', 'PERSONAL PROJECTS', 'KEY PROJECTS',
            'EDUCATION', 'ACADEMIC', 'QUALIFICATION', 'EDUCATIONAL BACKGROUND',
            'CERTIFICATIONS', 'CERTIFICATES', 'ACHIEVEMENTS', 'AWARDS', 'HONORS'
        ]
        
        # Create pattern for section boundaries (must be at start of line and all caps)
        boundary_pattern = r'(?=\n\s*(?:' + '|'.join(all_sections) + r')\s*(?:\n|$))'
        
        # Try multiple patterns with proper boundary detection
        patterns = [
            # Pattern 1: Section header followed by content until next section
            r'(?i)(?:^|\n)\s*(' + '|'.join(section_names) + r')\s*\n(.*?)' + boundary_pattern,
            # Pattern 2: Section header followed by content until end of text
            r'(?i)(?:^|\n)\s*(' + '|'.join(section_names) + r')\s*\n(.*?)(?=\Z)',
            # Pattern 3: More flexible matching
            r'(?i)(' + '|'.join(section_names) + r')\s*\n([\s\S]*?)(?=' + boundary_pattern + '|\Z)'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(2).strip()
                # Must have substantial content and not be just whitespace
                if len(content) > 10 and not content.isspace():
                    return content
        
        return None
    
    def _is_experience_header(self, line: str) -> bool:
        """Check if line is an experience header"""
        return (('—' in line or '–' in line or '-' in line) and 
                len(line) > 10 and len(line) < 150 and
                not line.startswith('•'))
    
    def _parse_experience_header(self, line: str) -> Dict[str, str]:
        """Parse experience header to extract company and title"""
        # Try different separators in order of preference
        separators = ['—', '–', ' — ', ' – ', ' - ', ' | ', ' at ', '@']
        
        for sep in separators:
            if sep in line:
                parts = [part.strip() for part in line.split(sep, 1)]
                if len(parts) == 2:
                    # Determine which part is company vs title based on common patterns
                    part1, part2 = parts[0], parts[1]
                    
                    # If first part has company indicators (Pvt, Ltd, Inc, Corp)
                    if any(indicator in part1.lower() for indicator in ['pvt', 'ltd', 'inc', 'corp', 'llc', 'company', 'technologies', 'studio']):
                        return {'company': part1, 'title': part2}
                    # If second part has company indicators
                    elif any(indicator in part2.lower() for indicator in ['pvt', 'ltd', 'inc', 'corp', 'llc', 'company', 'technologies', 'studio']):
                        return {'company': part2, 'title': part1}
                    # Default: first part is company
                    else:
                        return {'company': part1, 'title': part2}
        
        # Check if it's just a company name (has company indicators)
        if any(indicator in line.lower() for indicator in ['pvt', 'ltd', 'inc', 'corp', 'llc', 'company', 'technologies', 'studio']):
            return {'company': line, 'title': 'Not specified'}
        
        # Fallback: assume it's just a title
        return {'company': 'Not specified', 'title': line}
    
    def _contains_date_or_location(self, line: str) -> bool:
        """Check if line contains dates or location information"""
        return (bool(re.search(r'\d{4}', line)) or 
                any(location in line.lower() for location in 
                    ['remote', 'delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune']))
    
    def _parse_date_location(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract dates and location from a line"""
        dates = None
        location = None
        
        # Extract dates
        date_match = re.search(r'\d{2}/\d{4}.*?\d{2}/\d{4}|\d{4}.*?\d{4}|present|current', line, re.IGNORECASE)
        if date_match:
            dates = date_match.group()
        
        # Extract location
        location_patterns = ['remote', 'delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune']
        for loc in location_patterns:
            if loc in line.lower():
                location = loc.title()
                break
        
        return dates, location
    
    def _contains_date(self, line: str) -> bool:
        """Check if line contains date information"""
        return bool(re.search(r'\d{4}', line))
    
    def _extract_dates(self, line: str) -> Optional[str]:
        """Extract date range from line"""
        date_match = re.search(r'\d{4}.*?\d{4}|.*?present|.*?current', line, re.IGNORECASE)
        return date_match.group().strip() if date_match else None
    
    def _extract_degree_info(self, line: str) -> Optional[str]:
        """Extract degree information from line"""
        for pattern in self.degree_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return None
    
    def _is_degree_line(self, line: str) -> bool:
        """Check if line contains degree information"""
        degree_indicators = [
            'bachelor', 'master', 'phd', 'doctorate', 'diploma', 'certificate',
            'b.tech', 'b.e.', 'm.tech', 'm.e.', 'mba', 'mca', 'bca', 
            'computer science', 'engineering', 'technology', '12th standard',
            'cbse', 'intermediate', 'higher secondary'
        ]
        
        return any(indicator in line.lower() for indicator in degree_indicators)
    
    def _is_project_title(self, line: str) -> bool:
        """Check if line is a project title"""
        # Should not be a bullet point
        if line.startswith(('•', '-', '*', '·')):
            return False
            
        # Should have reasonable length
        if len(line) < 10 or len(line) > 200:
            return False
        
        # Strong indicators of project titles
        has_tech_parens = bool(re.search(r'\([^)]+\)\s*(?:\[GitHub\])?\s*$', line))
        has_github_link = '[GitHub]' in line or 'GitHub' in line
        
        # Project-like keywords
        project_indicators = [
            'system', 'platform', 'application', 'tool', 'framework', 'model',
            'analysis', 'management', 'tracking', 'prediction', 'classification',
            'dashboard', 'api', 'website', 'app', 'portal', 'service', 'data'
        ]
        
        has_project_keywords = any(keyword in line.lower() for keyword in project_indicators)
        
        # If it has tech stack in parentheses or GitHub link, it's likely a project
        if has_tech_parens or has_github_link:
            return True
        
        # If it has project keywords and looks like a title (title case), probably a project
        if has_project_keywords and (line[0].isupper() or line.count(' ') >= 2):
            return True
            
        return False
    
    def _is_job_title_line(self, line: str) -> bool:
        """Check if line is a job title (often in italic)"""
        job_title_indicators = [
            'intern', 'engineer', 'developer', 'analyst', 'scientist', 'manager',
            'specialist', 'consultant', 'lead', 'senior', 'junior', 'associate'
        ]
        
        return any(indicator in line.lower() for indicator in job_title_indicators)
    
    def _is_achievement_line(self, line: str) -> bool:
        """Check if line is an achievement (even without bullet)"""
        if line.startswith(('•', '-', '*', '·')):
            return True
        
        # Lines that start with action verbs are likely achievements
        action_verbs = [
            'achieved', 'developed', 'implemented', 'created', 'built', 'designed',
            'delivered', 'improved', 'enhanced', 'optimized', 'reduced', 'increased',
            'managed', 'led', 'coordinated', 'analyzed', 'processed', 'trained',
            'deployed', 'integrated', 'automated', 'streamlined', 'collaborated'
        ]
        
        first_word = line.split()[0].lower() if line.split() else ''
        return first_word in action_verbs


class SemanticMatcher:
    """Simple semantic matching using text similarity"""
    
    def __init__(self):
        pass
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_matching_skills(self, resume_skills: List[str], required_skills: List[str]) -> Tuple[List[str], List[str]]:
        """Find matched and missing skills"""
        if not resume_skills or not required_skills:
            return [], required_skills or []
        
        matched = []
        missing = []
        
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        
        for req_skill in required_skills:
            req_skill_clean = req_skill.lower().strip()
            
            # Exact match
            if req_skill_clean in resume_skills_lower:
                matched.append(req_skill)
                continue
            
            # Partial match (contains)
            match_found = False
            for resume_skill in resume_skills_lower:
                if (req_skill_clean in resume_skill or 
                    resume_skill in req_skill_clean or
                    self.calculate_similarity(req_skill_clean, resume_skill) > 0.6):
                    matched.append(req_skill)
                    match_found = True
                    break
            
            if not match_found:
                missing.append(req_skill)
        
        return matched, missing


class ComprehensiveATSScorer:
    """Comprehensive ATS scoring system with enhanced algorithms"""
    
    def __init__(self, skills_weight=0.35, header_weight=0.10, experience_weight=0.20,
                 projects_weight=0.10, education_weight=0.15, format_weight=0.10):
        self.skills_weight = skills_weight
        self.header_weight = header_weight
        self.experience_weight = experience_weight
        self.projects_weight = projects_weight
        self.education_weight = education_weight
        self.format_weight = format_weight
        
        self.extractor = EnhancedResumeExtractor()
        self.contact_extractor = ContactExtractor()
        self.semantic_matcher = SemanticMatcher()
    
    def extract_job_requirements(self, job_desc: str) -> Dict[str, List[str]]:
        """Extract requirements from job description"""
        # Extract skills using the same method as resume
        skills = self.extractor.extract_skills(job_desc)
        
        # Extract additional keywords
        keywords = self._extract_keywords(job_desc)
        
        # Combine and deduplicate
        all_requirements = list(set(skills + keywords))
        
        return {
            'skills': skills,
            'keywords': keywords,
            'all_requirements': all_requirements
        }
    
    def score_skills(self, resume: str, job_desc: str) -> Dict[str, Any]:
        """Enhanced skills scoring"""
        resume_skills = self.extractor.extract_skills(resume)
        job_requirements = self.extract_job_requirements(job_desc)
        required_skills = job_requirements['all_requirements']
        
        if not required_skills:
            return {
                'score': 65.0,  # Default score when no requirements
                'matched': resume_skills[:10],  # Show some skills found
                'missing': [],
                'matched_count': len(resume_skills[:10]),
                'missing_count': 0
            }
        
        matched, missing = self.semantic_matcher.find_matching_skills(resume_skills, required_skills)
        
        # Enhanced scoring algorithm
        match_ratio = len(matched) / len(required_skills) if required_skills else 0
        skill_count_bonus = min(len(resume_skills) * 2, 20)  # Bonus for having many skills
        
        # Base score from match ratio
        if match_ratio >= 0.8:
            base_score = 85 + (match_ratio - 0.8) * 75  # 85-100
        elif match_ratio >= 0.6:
            base_score = 70 + (match_ratio - 0.6) * 75  # 70-85
        elif match_ratio >= 0.4:
            base_score = 50 + (match_ratio - 0.4) * 100  # 50-70
        else:
            base_score = match_ratio * 125  # 0-50
        
        final_score = min(base_score + skill_count_bonus, 100.0)
        
        return {
            'score': final_score,
            'matched': matched,
            'missing': missing,
            'matched_count': len(matched),
            'missing_count': len(missing)
        }
    
    def score_header(self, resume: str) -> float:
        """Score contact information and header"""
        contact = self.contact_extractor.extract_contact(resume)
        header_title = self.extractor.extract_header_title(resume)
        
        score = 0
        
        # Contact information scoring
        if contact.get('email'):
            score += 30
        if contact.get('phone'):
            score += 25
        if contact.get('linkedin'):
            score += 15
        if contact.get('github'):
            score += 10
        
        # Professional title bonus
        if header_title:
            score += 20
        
        return min(score, 100.0)
    
    def score_experience(self, resume: str, job_desc: str) -> float:
        """Enhanced experience scoring"""
        experiences = self.extractor.extract_experience(resume)
        
        if not experiences:
            return 15.0  # Some points for effort
        
        score = 0
        
        # Base points for having experience
        score += min(len(experiences) * 25, 75)  # Up to 75 points for multiple experiences
        
        # Quality assessment
        job_requirements = self.extract_job_requirements(job_desc)
        exp_text = ' '.join([
            f"{exp.get('company', '')} {exp.get('title', '')} {exp.get('location', '')}"
            for exp in experiences
        ]).lower()
        
        # Keyword relevance
        relevant_keywords = 0
        for req in job_requirements['all_requirements'][:15]:  # Check top 15 requirements
            if req.lower() in exp_text:
                relevant_keywords += 1
        
        if job_requirements['all_requirements']:
            keyword_score = (relevant_keywords / min(15, len(job_requirements['all_requirements']))) * 25
            score += keyword_score
        
        return min(score, 100.0)
    
    def score_projects(self, resume: str, job_desc: str) -> float:
        """Enhanced projects scoring"""
        projects = self.extractor.extract_projects(resume)
        
        if not projects:
            return 20.0  # Minimum score
        
        score = 50  # Base score for having projects
        
        # Bonus for multiple projects
        if len(projects) >= 3:
            score += 20
        elif len(projects) >= 2:
            score += 15
        
        # Technology relevance
        job_requirements = self.extract_job_requirements(job_desc)
        proj_text = ' '.join([proj.get('name', '') + ' ' + proj.get('technologies', '') 
                            for proj in projects]).lower()
        
        tech_matches = 0
        for req in job_requirements['skills']:
            if req.lower() in proj_text:
                tech_matches += 1
        
        if job_requirements['skills']:
            tech_score = (tech_matches / len(job_requirements['skills'])) * 30
            score += tech_score
        
        return min(score, 100.0)
    
    def score_education(self, resume: str) -> float:
        """Enhanced education scoring"""
        educations = self.extractor.extract_education(resume)
        
        if not educations:
            return 30.0  # Some points for having section
        
        score = 60  # Base score for having education
        
        # Degree level assessment
        edu_text = ' '.join([edu.get('degree', '') + ' ' + edu.get('institution', '') 
                           for edu in educations]).lower()
        
        if any(keyword in edu_text for keyword in ['phd', 'doctorate', 'ph.d']):
            score += 25
        elif any(keyword in edu_text for keyword in ['master', 'msc', 'mba', 'm.tech']):
            score += 20
        elif any(keyword in edu_text for keyword in ['bachelor', 'btech', 'engineering']):
            score += 15
        
        # Institution quality indicators
        if any(keyword in edu_text for keyword in ['iit', 'nit', 'iiit', 'university', 'institute']):
            score += 15
        
        return min(score, 100.0)
    
    def score_format(self, resume: str) -> float:
        """Enhanced format scoring"""
        score = 0
        
        # Section presence
        sections = ['experience', 'education', 'skills', 'projects']
        for section in sections:
            if re.search(rf'(?i)\b{section}\b', resume):
                score += 15
        
        # Structure indicators
        if re.search(r'[•\-\*]', resume):  # Bullet points
            score += 15
        
        # Length assessment
        word_count = len(resume.split())
        if 200 <= word_count <= 800:  # Optimal length
            score += 25
        elif 100 <= word_count < 200 or 800 < word_count <= 1200:
            score += 15
        else:
            score += 5
        
        return min(score, 100.0)
    
    def calculate_overall_score(self, resume: str, job_desc: str) -> Dict[str, Any]:
        """Calculate comprehensive ATS score"""
        try:
            # Get individual scores
            skills_result = self.score_skills(resume, job_desc)
            header_score = self.score_header(resume)
            experience_score = self.score_experience(resume, job_desc)
            projects_score = self.score_projects(resume, job_desc)
            education_score = self.score_education(resume)
            format_score = self.score_format(resume)
            
            # Calculate weighted overall score
            overall_score = (
                skills_result['score'] * self.skills_weight +
                header_score * self.header_weight +
                experience_score * self.experience_weight +
                projects_score * self.projects_weight +
                education_score * self.education_weight +
                format_score * self.format_weight
            )
            
            # Determine classification
            if overall_score >= 70:
                classification = "Good Fit"
                badge_color = "success"
            elif overall_score >= 50:
                classification = "Potential Fit"
                badge_color = "warning"
            else:
                classification = "Needs Improvement"
                badge_color = "danger"
            
            return {
                'overall_score': round(overall_score, 1),
                'classification': classification,
                'badge_color': badge_color,
                'scores': {
                    'skills': round(skills_result['score'], 1),
                    'header': round(header_score, 1),
                    'experience': round(experience_score, 1),
                    'projects': round(projects_score, 1),
                    'education': round(education_score, 1),
                    'format': round(format_score, 1)
                },
                'details': {
                    'matched_skills': skills_result['matched'],
                    'missing_skills': skills_result['missing'],
                    'matched_count': skills_result['matched_count'],
                    'missing_count': skills_result['missing_count']
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            return self._get_fallback_score()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from job description"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'can', 'could', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'
        }
        
        # Extract words of reasonable length
        words = re.findall(r'\b[a-zA-Z+#\.]{2,25}\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) >= 3]
        
        # Get unique keywords, maintaining order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:25]  # Limit to top 25
    
    def _get_fallback_score(self) -> Dict[str, Any]:
        """Fallback score in case of errors"""
        return {
            'overall_score': 45.0,
            'classification': 'Analysis Error',
            'badge_color': 'warning',
            'scores': {
                'skills': 40.0,
                'header': 50.0,
                'experience': 45.0,
                'projects': 40.0,
                'education': 50.0,
                'format': 45.0
            },
            'details': {
                'matched_skills': [],
                'missing_skills': ['Analysis failed - please try again'],
                'matched_count': 0,
                'missing_count': 1
            }
        }


class ResumeProcessor:
    """Comprehensive resume processing pipeline"""
    
    def __init__(self):
        self.scorer = ComprehensiveATSScorer()
        self.extractor = EnhancedResumeExtractor()
        self.contact_extractor = ContactExtractor()
    
    def extract_text_from_file(self, file) -> str:
        """Extract text from uploaded file"""
        try:
            filename = secure_filename(file.filename)
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                return self._extract_from_pdf(file)
            elif file_ext == 'docx':
                return self._extract_from_docx(file)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            text = ""
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if not text.strip():
                raise ValueError("Could not extract text from PDF. The file might be image-based or corrupted.")
            
            return text
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to process PDF file: {str(e)}")
    
    def _extract_from_docx(self, file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(file.read()))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"
            
            if not text.strip():
                raise ValueError("Could not extract text from DOCX file.")
            
            return text
            
        except Exception as e:
            logger.error(f"DOCX extraction error: {str(e)}")
            raise ValueError(f"Failed to process DOCX file: {str(e)}")
    
    def parse_resume_sections(self, text: str) -> Dict[str, Any]:
        """Parse resume into structured sections"""
        try:
            return {
                'skills': self.extractor.extract_skills(text),
                'experience': self.extractor.extract_experience(text),
                'education': self.extractor.extract_education(text),
                'projects': self.extractor.extract_projects(text),
                'certifications': self.extractor.extract_certifications(text),
                'header_title': self.extractor.extract_header_title(text)
            }
        except Exception as e:
            logger.error(f"Error parsing resume sections: {str(e)}")
            return {
                'skills': [],
                'experience': [],
                'education': [],
                'projects': [],
                'certifications': [],
                'header_title': None
            }
    
    def process_resume(self, file, job_description: str) -> Dict[str, Any]:
        """Complete resume processing pipeline"""
        try:
            start_time = time.time()
            
            # Extract text
            logger.info("Extracting text from resume file...")
            resume_text = self.extract_text_from_file(file)
            
            if len(resume_text.strip()) < 100:
                raise ValueError("Resume text is too short. Please ensure the file contains readable content.")
            
            # Extract contact information
            logger.info("Extracting contact information...")
            contact_info = self.contact_extractor.extract_contact(resume_text)
            
            # Parse resume sections
            logger.info("Parsing resume sections...")
            parsed_sections = self.parse_resume_sections(resume_text)
            
            # Calculate scores
            logger.info("Calculating ATS scores...")
            scoring_result = self.scorer.calculate_overall_score(resume_text, job_description)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Compile final result
            result = {
                'filename': secure_filename(file.filename),
                'processing_time': round(processing_time, 2),
                'text_length': len(resume_text),
                'extracted_text': resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text,
                'contact_info': contact_info,
                'parsed_sections': parsed_sections,
                **scoring_result
            }
            
            logger.info(f"Resume processing completed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            raise


# Initialize processor
processor = ResumeProcessor()

# Route handlers
@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/ai')
def ai():
    """AI information page"""
    return render_template('ai.html')

@app.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    return render_template('dashboard.html')

@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
@csrf.exempt
def analyze_resume():
    """Main resume analysis endpoint"""
    try:
        # Validate request
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        if 'job_description' not in request.form:
            return jsonify({'error': 'No job description provided'}), 400
        
        file = request.files['resume']
        job_description = request.form['job_description'].strip()
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not job_description:
            return jsonify({'error': 'Job description cannot be empty'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'docx'}
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'Only PDF and DOCX files are supported'}), 400
        
        # Process resume
        logger.info(f"Starting analysis for file: {file.filename}")
        result = processor.process_resume(file, job_description)
        
        # Calculate average score for comparison (if multiple resumes processed)
        try:
            with db.engine.connect() as conn:
                avg_result = conn.execute(text("SELECT AVG(overall_score) as avg_score FROM resumes WHERE overall_score > 0")).fetchone()
                if avg_result and avg_result[0]:
                    result['average_score'] = float(avg_result[0])
        except Exception as e:
            logger.warning(f"Could not calculate average score: {str(e)}")
            result['average_score'] = None
        
        # Store in database (optional - can be disabled for privacy)
        try:
            if app.config.get('STORE_ANALYTICS', True):
                store_analysis_result(result, job_description, request.remote_addr)
        except Exception as e:
            logger.warning(f"Could not store analytics: {str(e)}")
        
        return jsonify(result)
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'An error occurred during analysis. Please try again.'}), 500

def store_analysis_result(result: Dict[str, Any], job_description: str, user_ip: str):
    """Store analysis result in database"""
    try:
        # Create resume record
        resume = Resume(
            filename=result['filename'],
            overall_score=int(result['overall_score']),
            classification=result['classification'],
            skills_score=result['scores']['skills'],
            header_score=result['scores']['header'],
            experience_score=result['scores']['experience'],
            projects_score=result['scores']['projects'],
            education_score=result['scores']['education'],
            format_score=result['scores']['format'],
            job_description_text=job_description,
            job_description_hash=hashlib.sha256(job_description.encode()).hexdigest(),
            matched_skills_count=result['details']['matched_count'],
            missing_skills_count=result['details']['missing_count'],
            extracted_text=result.get('extracted_text', ''),
            text_length=result.get('text_length', 0),
            processing_time=result.get('processing_time', 0),
            user_ip=user_ip if app.config.get('STORE_IP_ADDRESSES', False) else None,
            header_job_title=result['parsed_sections'].get('header_title')
        )
        
        db.session.add(resume)
        db.session.flush()  # Get the resume ID
        
        # Store contact information
        contact_info = result.get('contact_info', {})
        if any(contact_info.values()):
            contact = ContactInfo(
                resume_id=resume.id,
                full_name=contact_info.get('full_name'),
                email=contact_info.get('email'),
                phone=contact_info.get('phone'),
                linkedin_url=contact_info.get('linkedin'),
                github_url=contact_info.get('github')
            )
            db.session.add(contact)
        
        # Store matched skills
        for skill in result['details']['matched_skills']:
            matched_skill = MatchedSkill(
                resume_id=resume.id,
                skill_name=skill,
                match_type='detected',
                confidence_score=0.8
            )
            db.session.add(matched_skill)
        
        # Store missing skills
        for skill in result['details']['missing_skills']:
            missing_skill = MissingSkill(
                resume_id=resume.id,
                skill_name=skill,
                importance_level='required'
            )
            db.session.add(missing_skill)
        
        db.session.commit()
        logger.info(f"Analysis result stored in database with ID: {resume.id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error storing analysis result: {str(e)}")

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files with proper headers"""
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def file_too_large(error):
    """Handle file size errors"""
    return jsonify({'error': 'File size exceeds 16MB limit'}), 413

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limiting"""
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

# Initialize database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
