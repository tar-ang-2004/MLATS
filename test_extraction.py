#!/usr/bin/env python3
"""
Quick test script to debug extraction issues
"""

import re
from typing import List, Dict, Any, Optional

# Sample resume text for testing (from your examples)
sample_resume = """
TARANG KISHOR | Aspiring Data Scientist
India | Remote | tarangkishor2004@gmail.com | +91 7042366960 | linkedin.com/in/tarang-kishor | github.com/tar-ang-2004

SUMMARY
Aspiring Data Scientist with a strong foundation in machine learning, data science, and artificial intelligence. My recent internships have provided me hand-on experience in developing high-accuracy ML models and implementing innovative data-driven solutions. Eager to contribute to impactful machine learning projects leveraging my skills and experience.

SKILLS
• Programming Skills: Python, SQL, Bash, Git, Big Data, Object-Oriented Programming
• Tools & Platforms: Jupyter Notebook, GitHub, MySQL, PostgreSQL, Docker, Tableau, Power BI
• ML Techniques: Statistical Modeling, ELT, Regression, Preprocessing, Fine-tuning, NLP
• Libraries & Frameworks: Pandas, PyTorch, NumPy, Scikit-Learn, Matplotlib, Seaborn, Flask
• Soft Skills: Initiative, Collaboration, Problem-Solving, Communication, Curiosity, Decision-Making

EXPERIENCE
Labmentix Pvt. Ltd. — Artificial Intelligence & Data Science Intern
Delhi | Remote · 07/2025 – 12/2025
• Achieved ≥90% model accuracy across multiple AI/ML projects by conducting extensive EDA, data preprocessing, feature engineering, and hyperparameter tuning to optimize model performance and inform data-driven business decisions.
• Reduced model processing time by 15–20% by designing and deploying end-to-end machine learning pipelines that streamlined workflow and improved operational efficiency.
• Enhanced stakeholder decision-making by developing interactive web interfaces using Flask and React.js and delivering actionable dashboards and insights through Tableau and Power BI.
• Strengthened model interpretability and transparency by integrating SHAP and LIME explainability tools, allowing stakeholders to visualize feature importance and trust model outcomes.

Internship Studio Pvt. Ltd. — Artificial Intelligence & Machine Learning Intern
Delhi | Remote · 06/2025 – 09/2025
• Delivered three independent AI/ML projects utilizing Pandas, TensorFlow, Scikit-learn, NLP, and RNN, achieving an average model accuracy of 86% by implementing robust preprocessing and training strategies.
• Improved facial recognition accuracy by 18% through the application of SVM, CNN, and Computer Vision techniques, optimizing deep learning model architectures for real-world performance.
• Completed the Customer Satisfaction Score (CSAT) prediction project one week ahead of schedule by leveraging Deep Learning frameworks, ensuring timely and high-quality deliverables.

PROJECTS
Advanced News Analysis System (Python, Machine Learning, PyTorch)                     [GitHub]
• Attained 93.4% ROC-AUC score and 92% confidence by developing an end-to-end news sentiment analysis platform supporting 50+ languages, enabling multilingual text classification.
• Built and deployed a Real-time API for live sentiment tracking on 56,000+ news articles, improving analysis speed and automation efficiency.
• Enhanced category-wise sentiment prediction accuracy by 18% through the use of ensemble ML models combining BERT and LSTM architectures for better contextual understanding.

Vaccination Data Analysis (Python, Matplotlib, Tableau)                               [GitHub]
• Analyzed 500,000+ WHO vaccination records across 194 countries to uncover global health trends and support data-driven vaccine allocation strategies.
• Ensured 99.2% data integrity by applying rigorous data cleaning, validation, and correlation analysis, identifying a –0.65 correlation between vaccination rate and disease incidence.
• Designed interactive dashboards in Tableau powered by PostgreSQL databases, allowing stakeholders to visualize regional disparities and vaccination outcomes in real time.

EDUCATION
Maharaja Surajmal Institute of Technology (Affiliated with GGSIPU)
Delhi · 10/2022 – 07/2026
Bachelor of Technology – Computer Science and Engineering

CERTIFICATIONS
• IBM Python for Data Science (2025)
• IBM Python 101 for Data Science (2025)
• IBM Deep Learning with TensorFlow (2025)
• IBM Applied Data Science with Python (2025)
"""

def debug_extract_section(text: str, section_names: List[str]) -> Optional[str]:
    """Debug version of section extraction"""
    print(f"\n=== Debugging section extraction for: {section_names} ===")
    
    # Try multiple patterns
    patterns = [
        # Pattern 1: More flexible section matching
        r'(?i)(?:^|\n)\s*(' + '|'.join(section_names) + r')\s*\n(.*?)(?=\n\s*(?:SUMMARY|SKILLS|EXPERIENCE|PROJECTS|EDUCATION|CERTIFICATIONS)\s*(?:\n|$)|$)',
        # Pattern 2: Even more flexible
        r'(?i)(' + '|'.join(section_names) + r')\s*\n(.*?)(?=\n(?:SUMMARY|SKILLS|EXPERIENCE|PROJECTS|EDUCATION|CERTIFICATIONS)|\Z)',
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\nTrying pattern {i+1}: {pattern}")
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if match:
            content = match.group(2).strip()
            print(f"✓ Pattern {i+1} MATCHED!")
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:200]}...")
            return content
        else:
            print(f"✗ Pattern {i+1} failed")
    
    print("❌ No patterns matched")
    return None

def debug_extract_experience():
    """Debug experience extraction"""
    print("\n" + "="*60)
    print("DEBUGGING EXPERIENCE EXTRACTION")
    print("="*60)
    
    exp_section = debug_extract_section(sample_resume, ['experience', 'work experience'])
    
    if not exp_section:
        print("❌ Could not extract experience section!")
        return []
    
    print(f"\n📄 Experience section extracted ({len(exp_section)} chars):")
    print("-" * 40)
    print(exp_section)
    print("-" * 40)
    
    # Parse experience
    lines = [line.strip() for line in exp_section.split('\n') if line.strip()]
    print(f"\n📝 Lines in experience section: {len(lines)}")
    
    for i, line in enumerate(lines):
        print(f"{i+1:2d}. {line}")
    
    return lines

def debug_extract_projects():
    """Debug project extraction"""
    print("\n" + "="*60)
    print("DEBUGGING PROJECT EXTRACTION")
    print("="*60)
    
    proj_section = debug_extract_section(sample_resume, ['projects', 'personal projects'])
    
    if not proj_section:
        print("❌ Could not extract projects section!")
        return []
    
    print(f"\n📄 Projects section extracted ({len(proj_section)} chars):")
    print("-" * 40)
    print(proj_section)
    print("-" * 40)
    
    # Parse projects
    lines = [line.strip() for line in proj_section.split('\n') if line.strip()]
    print(f"\n📝 Lines in projects section: {len(lines)}")
    
    for i, line in enumerate(lines):
        prefix = "🔸 PROJECT:" if not line.startswith('•') else "🔹 BULLET:"
        print(f"{i+1:2d}. {prefix} {line}")
    
    return lines

if __name__ == "__main__":
    print("🔍 DEBUGGING ATS RESUME EXTRACTION")
    print("="*60)
    
    # Test experience extraction
    exp_lines = debug_extract_experience()
    
    # Test project extraction  
    proj_lines = debug_extract_projects()
    
    print(f"\n✅ SUMMARY:")
    print(f"   Experience lines found: {len(exp_lines)}")
    print(f"   Project lines found: {len(proj_lines)}")