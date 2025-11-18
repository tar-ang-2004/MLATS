"""
Comprehensive ATS Resume Analysis Engine
Built from scratch with clean, logical scoring and extraction
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ATSResumeAnalyzer:
    """Complete ATS Resume Analysis Engine - Clean Implementation"""
    
    def __init__(self):
        # Define scoring weights (total = 100%)
        self.WEIGHTS = {
            'contact_info': 0.05,      # 5% - Basic requirement
            'experience': 0.35,        # 35% - Most important
            'education': 0.15,         # 15% - Important but secondary
            'skills': 0.25,           # 25% - Critical for matching
            'projects': 0.10,         # 10% - Shows initiative
            'format_quality': 0.10    # 10% - ATS readability
        }
        
        # Skill categories for better matching
        self.SKILL_CATEGORIES = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
            'web_frontend': ['html', 'css', 'react', 'angular', 'vue', 'typescript', 'bootstrap', 'sass', 'jquery'],
            'web_backend': ['node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'asp.net', 'fastapi'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'nosql'],
            'cloud_platforms': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'heroku', 'digitalocean'],
            'data_science': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn', 'tensorflow', 'pytorch'],
            'tools_frameworks': ['git', 'jenkins', 'docker', 'linux', 'agile', 'scrum', 'jira', 'confluence'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical', 'creative']
        }
        
    def analyze_resume(self, resume_text: str, job_description: str = "") -> Dict[str, Any]:
        """Main analysis function - returns comprehensive ATS score and details"""
        
        # Clean and prepare text
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        resume_lower = resume_text.lower()
        
        # Extract all sections
        contact_info = self._extract_contact_info(resume_text, lines)
        experience = self._extract_experience(resume_text, lines)
        education = self._extract_education(resume_text, lines)
        skills = self._extract_skills(resume_text, lines)
        projects = self._extract_projects(resume_text, lines)
        
        # Calculate section scores
        contact_score = self._score_contact_info(contact_info)
        experience_score = self._score_experience(experience)
        education_score = self._score_education(education)
        skills_score = self._score_skills(skills, job_description)
        projects_score = self._score_projects(projects)
        format_score = self._score_format_quality(resume_text, lines)
        
        # Calculate weighted overall score
        overall_score = (
            contact_score * self.WEIGHTS['contact_info'] +
            experience_score * self.WEIGHTS['experience'] +
            education_score * self.WEIGHTS['education'] +
            skills_score * self.WEIGHTS['skills'] +
            projects_score * self.WEIGHTS['projects'] +
            format_score * self.WEIGHTS['format_quality']
        )
        
        # Generate detailed analysis
        analysis_details = self._generate_analysis_details(
            contact_info, experience, education, skills, projects,
            contact_score, experience_score, education_score, 
            skills_score, projects_score, format_score,
            job_description
        )
        
        return {
            'overall_score': round(overall_score, 1),
            'section_scores': {
                'contact_info': round(contact_score, 1),
                'experience': round(experience_score, 1),
                'education': round(education_score, 1),
                'skills': round(skills_score, 1),
                'projects': round(projects_score, 1),
                'format_quality': round(format_score, 1)
            },
            'extracted_data': {
                'contact_info': contact_info,
                'experience': experience,
                'education': education,
                'skills': skills,
                'projects': projects
            },
            'analysis_details': analysis_details,
            'recommendations': self._generate_recommendations(
                overall_score, contact_score, experience_score, 
                education_score, skills_score, projects_score, format_score
            )
        }
    
    def _extract_contact_info(self, resume_text: str, lines: List[str]) -> Dict[str, Any]:
        """Extract contact information with validation"""
        contact_info = {
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'linkedin': '',
            'github': ''
        }
        
        resume_lower = resume_text.lower()
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone
        phone_patterns = [
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            r'\b\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}\b'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, resume_text)
            if phone_match:
                contact_info['phone'] = phone_match.group()
                break
        
        # Extract LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
            r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
        ]
        for pattern in linkedin_patterns:
            linkedin_match = re.search(pattern, resume_lower)
            if linkedin_match:
                contact_info['linkedin'] = linkedin_match.group()
                break
        
        # Extract GitHub
        github_patterns = [
            r'github\.com/[\w-]+',
            r'www\.github\.com/[\w-]+',
            r'https?://(?:www\.)?github\.com/[\w-]+'
        ]
        for pattern in github_patterns:
            github_match = re.search(pattern, resume_lower)
            if github_match:
                contact_info['github'] = github_match.group()
                break
        
        # Extract name (first few non-section lines)
        potential_names = []
        section_headers = ['experience', 'education', 'skills', 'projects', 'summary', 'objective']
        
        for line in lines[:5]:  # Check first 5 lines
            line_clean = line.strip()
            if (len(line_clean) > 2 and len(line_clean) < 50 and
                not any(header in line.lower() for header in section_headers) and
                not re.search(r'@|http|www|\+|\d{3}', line)):
                potential_names.append(line_clean)
        
        if potential_names:
            contact_info['name'] = potential_names[0]
        
        # Extract location (city, state patterns)
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z]{2}\b'  # City Name, ST
        ]
        for pattern in location_patterns:
            location_match = re.search(pattern, resume_text)
            if location_match:
                contact_info['location'] = location_match.group()
                break
        
        return contact_info
    
    def _extract_experience(self, resume_text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract work experience with detailed parsing"""
        experience = []
        current_job = None
        in_experience_section = False
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Detect experience section
            if any(keyword in line_lower for keyword in ['experience', 'employment', 'work history']) and len(line_clean) < 50:
                in_experience_section = True
                continue
            
            # Stop at other sections
            if (in_experience_section and 
                any(keyword in line_lower for keyword in ['education', 'skills', 'projects', 'certifications']) and 
                len(line_clean) < 50):
                if current_job:
                    experience.append(current_job)
                break
            
            if in_experience_section and line_clean:
                # Job title and company detection
                if (not current_job or 
                    (current_job and len(current_job.get('responsibilities', [])) > 0)):
                    
                    # Save previous job
                    if current_job:
                        experience.append(current_job)
                    
                    # Start new job entry
                    current_job = {
                        'title': '',
                        'company': '',
                        'location': '',
                        'duration': '',
                        'responsibilities': []
                    }
                    
                    # Check if line contains company indicators
                    if any(indicator in line_lower for indicator in [' at ', ' - ', ' | ', '—']):
                        parts = re.split(r'\s+(?:at|@|-|—|\|)\s+', line_clean, 1)
                        if len(parts) == 2:
                            current_job['title'] = parts[0].strip()
                            current_job['company'] = parts[1].strip()
                        else:
                            current_job['title'] = line_clean
                    else:
                        current_job['title'] = line_clean
                
                # Date detection
                elif current_job and re.search(r'\d{1,2}/\d{4}|\d{4}|present|current', line_lower):
                    current_job['duration'] = line_clean
                
                # Location detection
                elif current_job and re.search(r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b', line_clean):
                    current_job['location'] = line_clean
                
                # Responsibility/achievement detection
                elif (current_job and 
                      (line_clean.startswith(('•', '-', '*')) or 
                       re.match(r'^\s*[\u2022\u2023\u25E6\u2043\u2219]\s', line_clean) or
                       any(verb in line_lower[:20] for verb in ['developed', 'implemented', 'managed', 'led', 'created', 'improved']))):
                    
                    # Clean bullet point
                    responsibility = re.sub(r'^[\s•\-\*\u2022\u2023\u25E6\u2043\u2219]+', '', line_clean).strip()
                    if responsibility:
                        current_job['responsibilities'].append(responsibility)
        
        # Add final job
        if current_job:
            experience.append(current_job)
        
        return experience[:5]  # Limit to 5 most recent
    
    def _extract_education(self, resume_text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract education with clear degree/institution separation"""
        education = []
        current_edu = None
        in_education_section = False
        
        # Common degree patterns
        degree_patterns = [
            r'bachelor\s+of\s+\w+', r'master\s+of\s+\w+', r'doctor\s+of\s+\w+',
            r'b\.?\s*[ast]\.?\s*', r'm\.?\s*[ast]\.?\s*', r'ph\.?d\.?',
            r'associate\s+of\s+\w+', r'diploma', r'certificate'
        ]
        
        # Institution indicators
        institution_keywords = ['university', 'college', 'institute', 'school', 'academy']
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Detect education section
            if 'education' in line_lower and len(line_clean) < 50:
                in_education_section = True
                continue
            
            # Stop at other sections
            if (in_education_section and 
                any(keyword in line_lower for keyword in ['experience', 'skills', 'projects']) and 
                len(line_clean) < 50):
                if current_edu:
                    education.append(current_edu)
                break
            
            if in_education_section and line_clean and len(line_clean) > 3:
                
                # Check if this is a degree line
                is_degree = any(re.search(pattern, line_lower) for pattern in degree_patterns)
                
                # Check if this is an institution line
                is_institution = (any(keyword in line_lower for keyword in institution_keywords) and 
                                not is_degree)
                
                # Date line
                is_date = re.search(r'\d{1,2}/\d{4}|\d{4}', line_clean)
                
                if is_institution:
                    # Save previous education entry
                    if current_edu:
                        education.append(current_edu)
                    
                    # Start new education entry
                    current_edu = {
                        'institution': line_clean,
                        'degree': '',
                        'field_of_study': '',
                        'graduation_date': '',
                        'gpa': ''
                    }
                
                elif is_degree and current_edu:
                    current_edu['degree'] = line_clean
                
                elif is_date and current_edu:
                    current_edu['graduation_date'] = line_clean
                
                elif current_edu and not current_edu['field_of_study']:
                    # Check if it's a field of study
                    if any(field in line_lower for field in ['computer science', 'engineering', 'business', 'science', 'arts']):
                        current_edu['field_of_study'] = line_clean
                
                # GPA detection
                gpa_match = re.search(r'gpa:?\s*([0-9]\.[0-9]{1,2})', line_lower)
                if gpa_match and current_edu:
                    current_edu['gpa'] = gpa_match.group(1)
        
        # Add final education
        if current_edu:
            education.append(current_edu)
        
        return education[:3]  # Limit to 3 entries
    
    def _extract_skills(self, resume_text: str, lines: List[str]) -> Dict[str, List[str]]:
        """Extract and categorize skills"""
        skills_by_category = {category: [] for category in self.SKILL_CATEGORIES.keys()}
        all_skills = []
        
        resume_lower = resume_text.lower()
        
        # Find skills section
        skills_section_text = ""
        in_skills_section = False
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['skills', 'technologies', 'technical skills']) and len(line) < 50:
                in_skills_section = True
                continue
            elif in_skills_section and any(keyword in line_lower for keyword in ['experience', 'education', 'projects']) and len(line) < 50:
                break
            elif in_skills_section:
                skills_section_text += line + " "
        
        # If no dedicated skills section, search entire resume
        if not skills_section_text.strip():
            skills_section_text = resume_text
        
        # Extract skills from each category
        for category, skill_list in self.SKILL_CATEGORIES.items():
            found_skills = []
            for skill in skill_list:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, resume_lower):
                    found_skills.append(skill)
                    all_skills.append(skill)
            
            skills_by_category[category] = found_skills
        
        # Extract additional skills from skills section (comma/pipe separated)
        additional_skills = []
        if skills_section_text:
            # Look for comma or pipe separated items
            potential_skills = re.findall(r'\b[A-Za-z][A-Za-z0-9+#.\-_]*\b', skills_section_text)
            for skill in potential_skills:
                if (len(skill) > 2 and skill.lower() not in [s.lower() for s in all_skills] and
                    not any(keyword in skill.lower() for keyword in ['and', 'the', 'with', 'experience', 'skills'])):
                    additional_skills.append(skill)
        
        skills_by_category['other'] = additional_skills[:20]  # Limit additional skills
        
        return skills_by_category
    
    def _extract_projects(self, resume_text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract projects with technologies and descriptions"""
        projects = []
        current_project = None
        in_projects_section = False
        
        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()
            
            # Detect projects section
            if 'project' in line_lower and len(line_clean) < 50:
                in_projects_section = True
                continue
            
            # Stop at other sections
            if (in_projects_section and 
                any(keyword in line_lower for keyword in ['experience', 'education', 'skills', 'certifications']) and 
                len(line_clean) < 50):
                if current_project:
                    projects.append(current_project)
                break
            
            if in_projects_section and line_clean:
                
                # Project title detection (not a bullet point)
                if (not line_clean.startswith(('•', '-', '*')) and 
                    not re.match(r'^\s*[\u2022\u2023\u25E6\u2043\u2219]\s', line_clean)):
                    
                    # Save previous project
                    if current_project:
                        projects.append(current_project)
                    
                    # Extract technologies from parentheses
                    tech_match = re.search(r'\(([^)]+)\)', line_clean)
                    technologies = tech_match.group(1) if tech_match else ''
                    
                    # Clean project name
                    project_name = re.sub(r'\([^)]+\)', '', line_clean).strip()
                    
                    current_project = {
                        'name': project_name,
                        'technologies': technologies,
                        'description': [],
                        'github_link': ''
                    }
                
                # Description/bullet point
                elif current_project:
                    # GitHub link detection
                    if 'github' in line_lower or 'git.io' in line_lower:
                        github_match = re.search(r'https?://[^\s]+', line_clean)
                        if github_match:
                            current_project['github_link'] = github_match.group()
                    else:
                        # Regular description
                        description = re.sub(r'^[\s•\-\*\u2022\u2023\u25E6\u2043\u2219]+', '', line_clean).strip()
                        if description:
                            current_project['description'].append(description)
        
        # Add final project
        if current_project:
            projects.append(current_project)
        
        return projects[:5]  # Limit to 5 projects
    
    def _score_contact_info(self, contact_info: Dict[str, Any]) -> float:
        """Score contact information completeness"""
        score = 0
        
        # Essential fields
        if contact_info['email']:
            score += 40  # Email is critical
        if contact_info['phone']:
            score += 30  # Phone is important
        if contact_info['name']:
            score += 20  # Name should be present
        
        # Optional but valuable fields
        if contact_info['linkedin']:
            score += 5
        if contact_info['github']:
            score += 3
        if contact_info['location']:
            score += 2
        
        return min(score, 100)
    
    def _score_experience(self, experience: List[Dict[str, Any]]) -> float:
        """Score work experience quality and completeness"""
        if not experience:
            return 0
        
        score = 0
        
        for job in experience:
            job_score = 0
            
            # Basic information completeness
            if job.get('title'):
                job_score += 15
            if job.get('company'):
                job_score += 15
            if job.get('duration'):
                job_score += 10
            
            # Responsibilities and achievements
            responsibilities = job.get('responsibilities', [])
            if responsibilities:
                # Score based on number and quality of responsibilities
                job_score += min(30, len(responsibilities) * 5)
                
                # Bonus for quantified achievements
                quantified = sum(1 for resp in responsibilities 
                               if re.search(r'\d+%|\$\d+|increased|improved|reduced|grew', resp.lower()))
                job_score += min(20, quantified * 5)
            
            # Duration bonus (longer experience is generally better)
            if job.get('duration'):
                duration_text = job['duration'].lower()
                if any(indicator in duration_text for indicator in ['year', 'yr']):
                    job_score += 10
            
            score += min(job_score, 80)  # Cap per job at 80
        
        # Average and apply experience count bonus
        if experience:
            average_score = score / len(experience)
            experience_bonus = min(20, len(experience) * 5)  # Bonus for having multiple roles
            final_score = average_score + experience_bonus
        else:
            final_score = 0
        
        return min(final_score, 100)
    
    def _score_education(self, education: List[Dict[str, Any]]) -> float:
        """Score education background"""
        if not education:
            return 20  # Base score for some education assumption
        
        score = 0
        
        for edu in education:
            edu_score = 0
            
            # Institution presence
            if edu.get('institution'):
                edu_score += 30
            
            # Degree information
            if edu.get('degree'):
                degree_lower = edu['degree'].lower()
                if any(level in degree_lower for level in ['master', 'phd', 'doctorate']):
                    edu_score += 40  # Advanced degree
                elif any(level in degree_lower for level in ['bachelor', 'b.tech', 'b.s']):
                    edu_score += 35  # Bachelor's degree
                else:
                    edu_score += 25  # Other degree/certification
            
            # Field relevance (basic check)
            if edu.get('field_of_study'):
                field_lower = edu['field_of_study'].lower()
                if any(field in field_lower for field in ['computer', 'engineering', 'science', 'technology']):
                    edu_score += 15  # Relevant field
                else:
                    edu_score += 10  # Any field specified
            
            # GPA bonus
            if edu.get('gpa'):
                try:
                    gpa_val = float(edu['gpa'])
                    if gpa_val >= 3.5:
                        edu_score += 10
                    elif gpa_val >= 3.0:
                        edu_score += 5
                except ValueError:
                    pass
            
            # Graduation date (recent is better)
            if edu.get('graduation_date'):
                edu_score += 5
            
            score = max(score, edu_score)  # Take highest education score
        
        return min(score, 100)
    
    def _score_skills(self, skills_by_category: Dict[str, List[str]], job_description: str = "") -> float:
        """Score skills based on quantity, diversity, and relevance"""
        total_skills = sum(len(skill_list) for skill_list in skills_by_category.values())
        
        if total_skills == 0:
            return 0
        
        score = 0
        
        # Base score for having skills
        score += min(40, total_skills * 2)  # 2 points per skill, max 40
        
        # Diversity bonus (having skills in multiple categories)
        categories_with_skills = sum(1 for skills in skills_by_category.values() if skills)
        score += min(30, categories_with_skills * 5)  # 5 points per category
        
        # High-value skills bonus
        high_value_skills = ['python', 'java', 'javascript', 'react', 'aws', 'docker', 'kubernetes']
        found_high_value = sum(1 for category_skills in skills_by_category.values() 
                              for skill in category_skills 
                              if skill.lower() in high_value_skills)
        score += min(20, found_high_value * 4)
        
        # Job description matching (if provided)
        if job_description:
            job_desc_lower = job_description.lower()
            matched_skills = sum(1 for category_skills in skills_by_category.values() 
                               for skill in category_skills 
                               if skill.lower() in job_desc_lower)
            score += min(10, matched_skills * 2)
        
        return min(score, 100)
    
    def _score_projects(self, projects: List[Dict[str, Any]]) -> float:
        """Score projects based on completeness and quality indicators"""
        if not projects:
            return 30  # Base score for having some assumed projects
        
        score = 0
        
        for project in projects:
            project_score = 0
            
            # Basic information
            if project.get('name'):
                project_score += 20
            if project.get('technologies'):
                project_score += 15
            if project.get('github_link'):
                project_score += 10
            
            # Description quality
            descriptions = project.get('description', [])
            if descriptions:
                project_score += min(25, len(descriptions) * 8)
                
                # Technical depth indicators
                tech_keywords = ['implemented', 'developed', 'built', 'created', 'designed', 'api', 'database', 'algorithm']
                tech_mentions = sum(1 for desc in descriptions 
                                  for keyword in tech_keywords 
                                  if keyword in desc.lower())
                project_score += min(15, tech_mentions * 3)
            
            score += min(project_score, 70)  # Cap per project
        
        # Average and apply project count bonus
        if projects:
            average_score = score / len(projects)
            project_bonus = min(15, len(projects) * 3)
            final_score = average_score + project_bonus
        else:
            final_score = 30
        
        return min(final_score, 100)
    
    def _score_format_quality(self, resume_text: str, lines: List[str]) -> float:
        """Score resume format and ATS readability"""
        score = 0
        
        # Length appropriateness
        word_count = len(resume_text.split())
        if 400 <= word_count <= 1000:
            score += 25  # Ideal length
        elif 300 <= word_count < 400 or 1000 < word_count <= 1500:
            score += 20  # Acceptable
        elif word_count > 200:
            score += 15  # Minimum content
        
        # Structure indicators
        section_headers = ['experience', 'education', 'skills', 'projects']
        found_sections = sum(1 for header in section_headers 
                           if any(header in line.lower() for line in lines))
        score += min(30, found_sections * 8)  # 8 points per standard section
        
        # Bullet point usage (good for ATS)
        bullet_lines = sum(1 for line in lines 
                          if re.match(r'^\s*[•\-\*\u2022\u2023\u25E6\u2043\u2219]', line))
        score += min(20, bullet_lines * 2)
        
        # Contact information accessibility
        email_present = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text))
        phone_present = bool(re.search(r'\b\+?[0-9\-\.\s\(\)]{10,}\b', resume_text))
        
        if email_present:
            score += 15
        if phone_present:
            score += 10
        
        return min(score, 100)
    
    def _generate_analysis_details(self, contact_info, experience, education, skills, projects,
                                 contact_score, experience_score, education_score, 
                                 skills_score, projects_score, format_score, job_description) -> Dict[str, Any]:
        """Generate detailed analysis breakdown"""
        
        total_skills = sum(len(skill_list) for skill_list in skills.values())
        total_experience_years = len(experience)  # Simplified
        
        # Missing skills analysis (if job description provided)
        missing_skills = []
        matched_skills = []
        
        if job_description:
            job_desc_lower = job_description.lower()
            all_resume_skills = [skill.lower() for category_skills in skills.values() 
                               for skill in category_skills]
            
            # Check for common job requirements
            common_requirements = ['python', 'java', 'javascript', 'sql', 'git', 'linux', 'aws', 'docker']
            for requirement in common_requirements:
                if requirement in job_desc_lower:
                    if requirement in all_resume_skills:
                        matched_skills.append(requirement)
                    else:
                        missing_skills.append(requirement)
        
        return {
            'contact_completeness': {
                'email': bool(contact_info.get('email')),
                'phone': bool(contact_info.get('phone')),
                'name': bool(contact_info.get('name')),
                'linkedin': bool(contact_info.get('linkedin')),
                'github': bool(contact_info.get('github'))
            },
            'experience_summary': {
                'total_positions': len(experience),
                'has_quantified_achievements': any(
                    any(re.search(r'\d+%|\$\d+|increased|improved', resp.lower()) 
                        for resp in job.get('responsibilities', [])) 
                    for job in experience
                ),
                'average_responsibilities_per_job': (
                    sum(len(job.get('responsibilities', [])) for job in experience) / len(experience) 
                    if experience else 0
                )
            },
            'education_summary': {
                'total_degrees': len(education),
                'has_relevant_field': any(
                    any(field in edu.get('field_of_study', '').lower() 
                        for field in ['computer', 'engineering', 'science'])
                    for edu in education
                ),
                'has_advanced_degree': any(
                    any(level in edu.get('degree', '').lower() 
                        for level in ['master', 'phd'])
                    for edu in education
                )
            },
            'skills_summary': {
                'total_skills': total_skills,
                'skill_categories': len([cat for cat, skills_list in skills.items() if skills_list]),
                'matched_skills': matched_skills,
                'missing_skills': missing_skills[:10]  # Limit to top 10
            },
            'projects_summary': {
                'total_projects': len(projects),
                'projects_with_github': sum(1 for proj in projects if proj.get('github_link')),
                'projects_with_tech_details': sum(1 for proj in projects if proj.get('technologies'))
            }
        }
    
    def _generate_recommendations(self, overall_score, contact_score, experience_score, 
                                education_score, skills_score, projects_score, format_score) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on scores"""
        recommendations = []
        
        # Overall score recommendations
        if overall_score < 60:
            recommendations.append({
                'priority': 'high',
                'category': 'overall',
                'title': 'Major Resume Overhaul Needed',
                'description': 'Your resume needs significant improvements across multiple sections to be ATS-competitive.'
            })
        elif overall_score < 75:
            recommendations.append({
                'priority': 'medium',
                'category': 'overall',
                'title': 'Good Foundation, Needs Optimization',
                'description': 'Your resume has potential but needs targeted improvements to maximize ATS compatibility.'
            })
        
        # Section-specific recommendations
        if contact_score < 80:
            recommendations.append({
                'priority': 'high',
                'category': 'contact',
                'title': 'Complete Contact Information',
                'description': 'Ensure your resume includes email, phone, and professional profiles (LinkedIn, GitHub).'
            })
        
        if experience_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': 'experience',
                'title': 'Strengthen Experience Section',
                'description': 'Add quantified achievements, use action verbs, and include specific technologies used.'
            })
        
        if education_score < 60:
            recommendations.append({
                'priority': 'medium',
                'category': 'education',
                'title': 'Clarify Educational Background',
                'description': 'Clearly list degree types, institutions, and graduation dates. Include relevant coursework if applicable.'
            })
        
        if skills_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': 'skills',
                'title': 'Expand Technical Skills',
                'description': 'Add more relevant technical skills and organize them by category (Programming, Tools, Frameworks).'
            })
        
        if projects_score < 70:
            recommendations.append({
                'priority': 'medium',
                'category': 'projects',
                'title': 'Showcase Technical Projects',
                'description': 'Include personal projects with GitHub links and detailed technology stacks used.'
            })
        
        if format_score < 80:
            recommendations.append({
                'priority': 'medium',
                'category': 'format',
                'title': 'Improve ATS Readability',
                'description': 'Use clear section headers, bullet points, and avoid complex formatting that ATS systems cannot parse.'
            })
        
        return recommendations