"""
ATS Components - Extracted from notebook for Flask app
Contains: ATSScorer, ResumeParser, ResumeExtractor, ContactExtractor, SemanticMatcher
"""

import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Any

# Import model manager for optimized model loading
from model_manager import get_sentence_transformer, get_tfidf_vectorizer

class SemanticMatcher:
    """Semantic matching using sentence transformers"""
    
    def __init__(self):
        self.model = None  # Lazy load when needed
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Lazy load model
        if self.model is None:
            self.model = get_sentence_transformer()
        
        embeddings = self.model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def find_matching_skills(self, resume_skills: List[str], required_skills: List[str]) -> tuple:
        """Find matched and missing skills"""
        if not resume_skills or not required_skills:
            return [], required_skills
        
        matched = []
        missing = []
        
        resume_skills_lower = [s.lower().strip() for s in resume_skills]
        
        for req_skill in required_skills:
            req_skill_clean = req_skill.lower().strip()
            
            # Exact match
            if req_skill_clean in resume_skills_lower:
                matched.append(req_skill)
                continue
            
            # Semantic match (similarity > 0.7)
            match_found = False
            for resume_skill in resume_skills:
                similarity = self.calculate_similarity(req_skill, resume_skill)
                if similarity > 0.7:
                    matched.append(req_skill)
                    match_found = True
                    break
            
            if not match_found:
                missing.append(req_skill)
        
        return matched, missing


class ContactExtractor:
    """Extract contact information from resume"""
    
    def extract_contact(self, text: str) -> Dict[str, Any]:
        """Extract email, phone, LinkedIn, GitHub"""
        contact = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None
        }
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact['email'] = emails[0]
        
        # Phone - use a permissive international-friendly pattern and return the full match
        phone_pattern = r'\+?\d[\d\s().\-]{6,}\d'
        phones = re.findall(phone_pattern, text)
        if phones:
            # phones is a list of full-match strings (no capture groups)
            contact['phone'] = phones[0].strip()
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text.lower())
        if linkedin:
            contact['linkedin'] = linkedin[0]
        
        # GitHub
        github_pattern = r'github\.com/[\w-]+'
        github = re.findall(github_pattern, text.lower())
        if github:
            contact['github'] = github[0]
        
        return contact


class ResumeExtractor:
    """Extract structured information from resume text"""
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using comprehensive pattern matching"""
        # Comprehensive skill list (technical skills commonly found in resumes)
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'rails',
            'html', 'css', 'sass', 'bootstrap', 'tailwind',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'oracle',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab', 'github',
            'git', 'linux', 'bash', 'powershell', 'rest', 'graphql', 'microservices', 'api',
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision', 'tensorflow', 'pytorch', 'scikit-learn',
            'data science', 'data analysis', 'pandas', 'numpy', 'matplotlib', 'tableau', 'power bi',
            'agile', 'scrum', 'jira', 'confluence', 'ci/cd', 'devops', 'testing', 'junit', 'pytest',
            'react native', 'flutter', 'android', 'ios', 'mobile', 'frontend', 'backend', 'full stack',
            'security', 'oauth', 'jwt', 'encryption', 'networking', 'cloud', 'serverless', 'lambda'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        # First, check for skills section
        skills_section = re.search(r'(?i)(skills?|technical skills?|core competencies)(.*?)(?=\n\n[A-Z]|education|experience|projects|$)', 
                                   text, re.DOTALL)
        
        if skills_section:
            skills_text = skills_section.group(2).lower()
            # Check each known skill
            for skill in common_skills:
                if skill in skills_text:
                    found_skills.append(skill)
        
        # Also check entire text for skills (in case no dedicated section)
        for skill in common_skills:
            if skill in text_lower and skill not in found_skills:
                found_skills.append(skill)
        
        return found_skills[:30]  # Return top 30
    
    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience with improved ATS parsing"""
        experience = []
        
        # Find experience section - match section headers flexibly
        exp_section = re.search(r'(?i)\n(EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|PROFESSIONAL EXPERIENCE)\s*\n(.*?)(?=\n(?:SKILLS|EDUCATION|PROJECTS|CERTIFICATIONS|ACHIEVEMENTS|AWARDS|REFERENCES)\s*\n|$)', 
                               text, re.DOTALL)
        
        if exp_section:
            exp_text = exp_section.group(2).strip()
            
            # ATS-specific parsing: Look for "Company — Title" pattern
            company_title_pattern = r'([A-Za-z][A-Za-z\s&\.,]+(?:Pvt\.|Ltd\.|Inc\.|LLC|Studio|Solutions|Technologies|Systems|Corporation|Corp\.)?)\s*[—–-]\s*([A-Za-z][^\n]+)'
            
            lines = exp_text.split('\n')
            current_entry = []
            entries = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # COMPLETELY SKIP bullet points, achievements, and incomplete lines
                if (re.match(r'^\s*[•\-\*·]\s*', line) or 
                    any(keyword in line.lower() for keyword in ['achieved', 'reduced', 'enhanced', 'delivered', 'built', 'developed', 'implemented', 'designed', 'created', 'managed', 'led', 'improved', 'completed', 'strengthened', 'optimizing', 'engineering', 'frameworks', 'ensuring']) or
                    line.endswith('—') or line.endswith('-') or len(line) < 15):
                    continue
                    
                # Check if this line is a company-title header
                header_match = re.match(company_title_pattern, line)
                if header_match:
                    # Save previous entry if exists
                    if current_entry:
                        entries.append('\n'.join(current_entry))
                    
                    # Start new entry
                    company = header_match.group(1).strip()
                    title = header_match.group(2).strip()
                    current_entry = [f"{company} — {title}"]
                    continue
                
                # Only add location/date lines - be very strict
                if current_entry and len(current_entry) == 1:  # Only add first line after header
                    if (any(keyword in line.lower() for keyword in ['delhi', 'remote', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune']) or 
                        re.search(r'\d{2}/\d{4}', line)) and not any(bad in line.lower() for bad in ['achieved', 'reduced', 'enhanced', 'developed']):
                        current_entry.append(line)
            
            # Add the last entry
            if current_entry:
                entries.append('\n'.join(current_entry))
            
            # Convert to required format
            for entry in entries[:5]:
                if len(entry.strip()) > 20:
                    experience.append({'text': entry.strip()})
        
        return experience
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education"""
        education = []
        
        # More comprehensive pattern to find education section
        edu_section = re.search(r'(?i)\n?(EDUCATION|ACADEMIC|QUALIFICATION)S?\s*\n(.*?)(?=\n(?:PROJECTS?|SKILLS?|EXPERIENCE|CERTIFICATIONS?|ACHIEVEMENTS?|AWARDS?|REFERENCES?)\s*\n|$)', 
                               text, re.DOTALL)
        
        if edu_section:
            edu_text = edu_section.group(2).strip()
            lines = edu_text.split('\n')
            
            # Combine related lines into complete education entries
            current_entry = []
            entries = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a new institution line
                if any(keyword in line.lower() for keyword in ['institute', 'university', 'college', 'school']) and len(line) > 15:
                    # Save previous entry if exists
                    if current_entry:
                        entries.append('\n'.join(current_entry))
                    # Start new entry
                    current_entry = [line]
                elif current_entry and len(current_entry) < 4:  # Add related lines (location, dates, degree)
                    current_entry.append(line)
            
            # Don't forget the last entry
            if current_entry:
                entries.append('\n'.join(current_entry))
            
            # Process entries to create structured education data
            for entry in entries[:3]:  # Max 3 entries
                if len(entry.strip()) > 15:
                    education.append({'text': entry.strip()})
        
        return education
    
    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract projects with improved ATS parsing"""
        projects = []
        
        # Find projects section - more flexible pattern
        proj_section = re.search(r'(?i)\n(PROJECTS?|PERSONAL PROJECTS?|KEY PROJECTS?)\s*\n(.*?)(?=\n(?:SKILLS|EDUCATION|EXPERIENCE|CERTIFICATIONS|ACHIEVEMENTS|AWARDS|REFERENCES)\s*\n|$)', 
                                text, re.DOTALL)
        
        if proj_section:
            proj_text = proj_section.group(2).strip()
            
            lines = proj_text.split('\n')
            current_project = []
            projects_list = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for project header - either with technologies in parentheses or project keywords
                is_project_header = (
                    re.match(r'^[A-Za-z][^\n(]*\([^)]+\)', line) or  # "Project Name (Tech1, Tech2)"
                    any(keyword in line for keyword in ['System', 'Analysis', 'Platform', 'API', 'Dashboard', 'Application', 'Model', 'Framework', 'Tool']) and
                    not any(bullet in line for bullet in ['•', '－', '*', '-']) and
                    len(line) > 10 and len(line) < 100
                )
                
                if is_project_header:
                    # Save previous project
                    if current_project:
                        projects_list.append('\n'.join(current_project))
                    
                    # Start new project - only keep the title line, no bullet descriptions
                    current_project = [line]
                elif current_project and not re.match(r'^\s*[•\-\*·]\s*', line) and len(current_project) == 1:
                    # Only add first non-bullet line after header (like GitHub links)
                    if '[GitHub]' in line or 'github.com' in line.lower() or len(line) < 50:
                        current_project.append(line)
            
            # Add the last project
            if current_project:
                projects_list.append('\n'.join(current_project))
            
            # Convert to required format - only keep project titles and tech stacks
            for project in projects_list[:5]:
                project_clean = project.strip()
                if len(project_clean) > 15:
                    # Extract just the main title line, ignore bullet descriptions
                    main_line = project_clean.split('\n')[0]
                    projects.append({'text': main_line})
        
        return projects
    
    def extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """Extract certifications and achievements"""
        certifications = []
        
        # Find certifications/achievements section
        cert_section = re.search(
            r'(?i)\n(CERTIFICATIONS?|CERTIFICATES?|ACHIEVEMENTS?|AWARDS?|HONORS?|ACCOMPLISHMENTS?)\s*\n(.*?)(?=\n(?:SKILLS|EDUCATION|EXPERIENCE|PROJECTS|REFERENCES|INTERESTS)\s*\n|$)', 
            text, re.DOTALL
        )
        
        if cert_section:
            cert_text = cert_section.group(2).strip()
            
            # Strategy 1: Split by bullet points or dashes
            entries = re.split(r'\n\s*[•\-\*]\s*', cert_text)
            
            # Strategy 2: Split by newlines if we don't have bullets
            if len(entries) < 2:
                entries = re.split(r'\n+', cert_text)
            
            # Clean and filter entries
            for entry in entries[:10]:  # Max 10 certifications
                entry_clean = entry.strip()
                # Filter out very short entries or section headers
                if len(entry_clean) > 10 and not re.match(r'^(CERTIFICATIONS?|CERTIFICATES?|ACHIEVEMENTS?|AWARDS?)', entry_clean, re.IGNORECASE):
                    certifications.append({'text': entry_clean[:300]})
        
        return certifications

    def extract_header_title(self, text: str) -> str:
        """Try to extract the job title that a candidate writes in the resume header.

        Heuristics:
        - Look at the first 6-8 non-empty lines.
        - Skip lines that look like emails, phones, urls.
        - Prefer lines containing common title keywords (Engineer, Manager, Developer, Analyst, Scientist, Lead, Director, Intern, Student, Designer, Architect, Consultant, Officer).
        - Otherwise pick the second non-empty line (often title after name) or the shortest reasonable line.
        """
        if not text:
            return ''

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return ''

        # Only consider the top portion of the resume
        top_lines = lines[:8]

        # Patterns to skip
        email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        phone_re = re.compile(r'\+?\d[\d\s().\-]{6,}\d')
        url_re = re.compile(r'(linkedin\.com|github\.com|http[s]?://)')

        # common modifiers to strip (aspiring -> Data Scientist)
        leading_mods = re.compile(r"^(?:aspiring|seeking|looking for|passionate about|experienced|motivated|enthusiastic|results-driven|skilled|senior|junior|jr\.?|sr\.?|mid[- ]level)\b\s*", re.I)

        # canonical multi-word title phrases to prefer (longer phrases first)
        multi_titles = [
            'machine learning engineer', 'data scientist', 'data engineer', 'machine learning researcher',
            'artificial intelligence engineer', 'software engineer', 'product manager', 'project manager',
            'data analyst', 'business analyst', 'research scientist', 'devops engineer', 'ml engineer'
        ]

        single_keywords = ['engineer', 'developer', 'manager', 'analyst', 'scientist', 'lead', 'director', 'intern', 'designer', 'architect', 'consultant', 'officer', 'specialist', 'associate', 'principal']

        candidates = []
        for ln in top_lines:
            # split on separators to handle headers like "NAME | Aspiring Data Scientist"
            parts = re.split(r'[\|\u2013\u2014\-—]+', ln)
            for part in parts:
                p = part.strip()
                low = p.lower()
                if not p:
                    continue
                if email_re.search(p) or phone_re.search(p) or url_re.search(low):
                    continue
                if len(p) < 2 or len(p) > 120:
                    continue
                candidates.append(p)

        # 1) Check for exact multi-word titles
        for c in candidates:
            cl = c.lower()
            for mt in multi_titles:
                if mt in cl:
                    # strip leading modifiers
                    cleaned = leading_mods.sub('', c).strip()
                    # find and return the shortest substring that contains the title phrase
                    idx = cl.find(mt)
                    # try to return the matched phrase capitalized
                    return mt.title()

        # 2) Check for single keywords and return a small window around keyword
        for c in candidates:
            cl = c.lower()
            for kw in single_keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', cl):
                    # strip leading modifiers
                    s = leading_mods.sub('', c).strip()
                    # extract up to 3 words around the keyword
                    words = s.split()
                    # find keyword index
                    idxs = [i for i,w in enumerate([w.lower().strip('.,') for w in words]) if w == kw]
                    if idxs:
                        i = idxs[0]
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        candidate_title = ' '.join(words[start:end])
                        # Clean punctuation
                        candidate_title = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', candidate_title)
                        return candidate_title.title()

        # 3) As a last resort, if a candidate line contains two or three words (likely name + title), pick second line
        if candidates:
            # prefer candidate that is two-to-five words and not largely uppercase (name)
            for c in candidates:
                w = c.split()
                if 1 < len(w) <= 6 and not c.isupper():
                    cleaned = leading_mods.sub('', c).strip()
                    return cleaned.title()

        return ''


class ResumeParser:
    """Main parser that uses extractor"""
    
    def __init__(self):
        self.extractor = ResumeExtractor()
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse resume and return structured data"""
        return {
            'skills': self.extractor.extract_skills(text),
            'experience': self.extractor.extract_experience(text),
            'education': self.extractor.extract_education(text),
            'projects': self.extractor.extract_projects(text),
            'certifications': self.extractor.extract_certifications(text),
            'header_title': self.extractor.extract_header_title(text)
        }


class ATSScorer:
    """Score resume against job description"""
    
    def __init__(self, skills_weight=0.40, header_weight=0.10, experience_weight=0.15,
                 projects_weight=0.05, education_weight=0.20, format_weight=0.10):
        self.skills_weight = skills_weight
        self.header_weight = header_weight
        self.experience_weight = experience_weight
        self.projects_weight = projects_weight
        self.education_weight = education_weight
        self.format_weight = format_weight
        
        self.semantic_matcher = SemanticMatcher()
        self.resume_extractor = ResumeExtractor()
        self.contact_extractor = ContactExtractor()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from job description"""
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                       'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                       'can', 'could', 'may', 'might', 'must', 'shall'}
        
        words = re.findall(r'\b[a-zA-Z+#]{2,}\b', text.lower())
        keywords = [w for w in words if w not in common_words]
        
        # Get unique keywords, keep order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)
        
        return unique_keywords[:30]  # Top 30 keywords
    
    def score_skills(self, resume: str, job_desc: str) -> Dict[str, Any]:
        """Score skills match with improved scaling"""
        resume_skills = self.resume_extractor.extract_skills(resume)
        required_skills = self.resume_extractor.extract_skills(job_desc)
        
        if not required_skills:
            required_skills = self.extract_keywords(job_desc)[:15]
        
        matched, missing = self.semantic_matcher.find_matching_skills(resume_skills, required_skills)
        
        if not required_skills:
            score = 50.0
        else:
            match_percentage = len(matched) / len(required_skills)
            
            # Improved scaling: reward high match percentages
            if match_percentage >= 0.80:  # 80%+ match
                score = 85 + (match_percentage - 0.80) * 75  # 85-100 range
            elif match_percentage >= 0.60:  # 60-79% match
                score = 70 + (match_percentage - 0.60) * 75  # 70-85 range
            elif match_percentage >= 0.40:  # 40-59% match
                score = 50 + (match_percentage - 0.40) * 100  # 50-70 range
            else:  # < 40% match
                score = match_percentage * 125  # 0-50 range
        
        return {
            'score': min(score, 100.0),
            'matched': matched,
            'missing': missing,
            'matched_count': len(matched),
            'missing_count': len(missing)
        }
    
    def score_header(self, resume: str) -> float:
        """Score contact information completeness"""
        contact = self.contact_extractor.extract_contact(resume)
        
        score = 0
        if contact['email']:
            score += 40
        if contact['phone']:
            score += 30
        if contact['linkedin']:
            score += 15
        if contact['github']:
            score += 15
        
        return min(score, 100.0)
    
    def score_experience(self, resume: str, job_desc: str) -> float:
        """Score experience relevance with ATS-optimized approach"""
        experience = self.resume_extractor.extract_experience(resume)
        
        if not experience:
            return 0.0
        
        exp_text = ' '.join([e['text'] for e in experience]).lower()
        
        # Base score for having properly structured experience (60 points)
        base_score = 60 if len(experience) >= 1 else 0
        
        # 1. Keyword matching (25 points) - relevance to job
        job_skills = self.resume_extractor.extract_skills(job_desc)
        if job_skills:
            matched_count = sum(1 for skill in job_skills if skill.lower() in exp_text)
            match_percentage = matched_count / len(job_skills) if len(job_skills) > 0 else 0
            
            # More generous scoring for ATS format
            if match_percentage >= 0.30:  # 30%+ skills mentioned is excellent for internships
                keyword_score = 20 + (match_percentage - 0.30) * 17  # 20-25 points
            elif match_percentage >= 0.15:  # 15-30% skills mentioned is good
                keyword_score = 15 + (match_percentage - 0.15) * 33  # 15-20 points
            else:
                keyword_score = match_percentage * 100  # 0-15 points
            
            keyword_score = min(keyword_score, 25)
        else:
            keyword_score = 20  # Default good score if no job skills to match
        
        # 2. Quality bonus for multiple structured experiences (15 points)
        if len(experience) >= 2:
            # Check for proper ATS format (Company — Title structure)
            ats_format_count = sum(1 for e in experience if '—' in e['text'] or '–' in e['text'])
            if ats_format_count >= 2:
                quality_score = 15  # Full points for proper ATS format
            elif ats_format_count >= 1:
                quality_score = 12
            else:
                quality_score = 8
        elif len(experience) == 1:
            quality_score = 10
        else:
            quality_score = 0
        
        return min(base_score + keyword_score + quality_score, 100.0)
    
    def score_projects(self, resume: str, job_desc: str) -> float:
        """Score projects relevance with ATS-optimized approach"""
        projects = self.resume_extractor.extract_projects(resume)
        
        if not projects:
            return 0.0
        
        proj_text = ' '.join([p['text'] for p in projects]).lower()
        
        # Base score for having structured projects (65 points)
        base_score = 65 if len(projects) >= 1 else 0
        
        # 1. Technology stack bonus (20 points) - for projects with technologies listed
        tech_indicators = ['python', 'machine learning', 'pytorch', 'tensorflow', 'java', 'javascript', 'react', 'node', 'sql', 'mongodb', 'docker', 'aws', 'azure', 'git', 'github', 'api', 'flask', 'django', 'pandas', 'numpy', 'matplotlib', 'tableau', 'scikit-learn', 'opencv', 'nltk']
        tech_count = sum(1 for tech in tech_indicators if tech in proj_text)
        
        if tech_count >= 5:  # 5+ technologies mentioned
            tech_score = 20
        elif tech_count >= 3:  # 3-4 technologies
            tech_score = 15
        elif tech_count >= 1:  # 1-2 technologies
            tech_score = 10
        else:
            tech_score = 5
        
        # 2. Project quality bonus (15 points) - for multiple well-structured projects
        if len(projects) >= 2:
            # Check for proper project format with technologies in parentheses
            has_tech_format = any('(' in p['text'] and ')' in p['text'] for p in projects)
            if has_tech_format:
                quality_score = 15
            else:
                quality_score = 10
        elif len(projects) == 1:
            quality_score = 8
        else:
            quality_score = 0
        
        return min(base_score + tech_score + quality_score, 100.0)
        
        # 3. Quality bonus: 25 points for 2+ detailed, impactful projects
        if len(projects) >= 2:
            # Check for achievement indicators (metrics, outcomes)
            achievement_keywords = ['%', 'achieved', 'accuracy', 'performance', 'deployed', 'built', 'developed', 'improved']
            has_achievements = any(kw in proj_text for kw in achievement_keywords)
            
            if has_achievements:
                quality_score = 25  # Full points for 2+ projects with measurable outcomes
            else:
                quality_score = 20  # Good but not exceptional
        elif len(projects) == 1:
            quality_score = 15
        else:
            quality_score = 0
        
        return min(keyword_score + semantic_score + quality_score, 100.0)
    
    def score_education(self, resume: str) -> float:
        """Score education section with ATS-optimized approach"""
        education = self.resume_extractor.extract_education(resume)
        
        if not education:
            return 0.0
        
        # Base score for having education (70 points)
        base_score = 70
        
        edu_text = ' '.join([e['text'] for e in education]).lower()
        
        # Degree level bonus (20 points)
        if any(keyword in edu_text for keyword in ['phd', 'doctorate', 'ph.d']):
            degree_score = 20
        elif any(keyword in edu_text for keyword in ['master', 'msc', 'mba', 'm.tech', 'mtech']):
            degree_score = 18
        elif any(keyword in edu_text for keyword in ['bachelor', 'bsc', 'bs', 'b.tech', 'btech', 'engineering', 'technology', 'computer science']):
            degree_score = 15
        else:
            degree_score = 10  # Some degree mentioned
        
        # Institution quality bonus (10 points)
        quality_indicators = ['institute', 'university', 'college', 'technology', 'engineering', 'iit', 'nit', 'bits', 'iiit']
        if any(indicator in edu_text for indicator in quality_indicators):
            institution_score = 10
        else:
            institution_score = 5
        
        return min(base_score + degree_score + institution_score, 100.0)
    
    def score_format(self, resume: str) -> float:
        """Score resume formatting quality"""
        score = 0
        
        # Check for sections
        sections = ['experience', 'education', 'skills']
        for section in sections:
            if re.search(f'(?i)\\b{section}\\b', resume):
                score += 20
        
        # Check for bullet points or structure
        if '•' in resume or '-' in resume or '*' in resume:
            score += 20
        
        # Check length (not too short, not too long)
        length = len(resume)
        if 500 <= length <= 3000:
            score += 20
        elif 300 <= length < 500 or 3000 < length <= 5000:
            score += 10
        
        return min(score, 100.0)
    
    def score_resume(self, resume: str, job_desc: str) -> Dict[str, Any]:
        """Calculate overall ATS score with holistic assessment"""
        skills_result = self.score_skills(resume, job_desc)
        header_score = self.score_header(resume)
        experience_score = self.score_experience(resume, job_desc)
        projects_score = self.score_projects(resume, job_desc)
        education_score = self.score_education(resume)
        format_score = self.score_format(resume)
        
        overall_score = (
            skills_result['score'] * self.skills_weight +
            header_score * self.header_weight +
            experience_score * self.experience_weight +
            projects_score * self.projects_weight +
            education_score * self.education_weight +
            format_score * self.format_weight
        )
        
        # Holistic excellence bonus: reward resumes that excel across multiple dimensions
        # This compensates for potentially unreliable semantic similarity scores
        experience_entries = self.resume_extractor.extract_experience(resume)
        project_entries = self.resume_extractor.extract_projects(resume)
        
        skill_match_rate = skills_result['matched_count'] / (skills_result['matched_count'] + skills_result['missing_count']) if (skills_result['matched_count'] + skills_result['missing_count']) > 0 else 0
        
        # Apply bonus if multiple strong signals align
        if (skill_match_rate >= 0.70  # 70%+ skills matched
            and skills_result['score'] >= 80  # Strong skills score
            and len(experience_entries) >= 2  # Multiple experiences
            and len(project_entries) >= 2  # Multiple projects
            and experience_score >= 65  # Decent experience relevance
            and projects_score >= 60):  # Decent project relevance
            
            # Award up to 8 points bonus (pushes 78% → 86%)
            bonus = 8.0
            overall_score = min(overall_score + bonus, 100.0)
        
        return {
            'overall_score': overall_score,
            'skills_score': skills_result['score'],
            'header_score': header_score,
            'experience_score': experience_score,
            'projects_score': projects_score,
            'education_score': education_score,
            'format_score': format_score,
            'matched_skills': skills_result['matched'],
            'missing_skills': skills_result['missing'],
            'matched_count': skills_result['matched_count'],
            'missing_count': skills_result['missing_count']
        }
