#!/usr/bin/env python3
"""
Test the actual extraction logic from app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import EnhancedResumeExtractor

# Sample resume text (shorter version for testing)
sample_resume = """TARANG KISHOR | Aspiring Data Scientist
India | Remote | tarangkishor2004@gmail.com | +91 7042366960

EXPERIENCE
Labmentix Pvt. Ltd. — Artificial Intelligence & Data Science Intern
Delhi | Remote · 07/2025 – 12/2025
• Achieved ≥90% model accuracy across multiple AI/ML projects by conducting extensive EDA, data preprocessing, feature engineering, and hyperparameter tuning to optimize model performance and inform data-driven business decisions.
• Reduced model processing time by 15–20% by designing and deploying end-to-end machine learning pipelines that streamlined workflow and improved operational efficiency.
• Enhanced stakeholder decision-making by developing interactive web interfaces using Flask and React.js and delivering actionable dashboards and insights through Tableau and Power BI.

Internship Studio Pvt. Ltd. — Artificial Intelligence & Machine Learning Intern
Delhi | Remote · 06/2025 – 09/2025
• Delivered three independent AI/ML projects utilizing Pandas, TensorFlow, Scikit-learn, NLP, and RNN, achieving an average model accuracy of 86% by implementing robust preprocessing and training strategies.
• Improved facial recognition accuracy by 18% through the application of SVM, CNN, and Computer Vision techniques.

PROJECTS
Advanced News Analysis System (Python, Machine Learning, PyTorch) [GitHub]
• Attained 93.4% ROC-AUC score and 92% confidence by developing an end-to-end news sentiment analysis platform supporting 50+ languages, enabling multilingual text classification.
• Built and deployed a Real-time API for live sentiment tracking on 56,000+ news articles, improving analysis speed and automation efficiency.
• Enhanced category-wise sentiment prediction accuracy by 18% through the use of ensemble ML models combining BERT and LSTM architectures for better contextual understanding.

Vaccination Data Analysis (Python, Matplotlib, Tableau) [GitHub]
• Analyzed 500,000+ WHO vaccination records across 194 countries to uncover global health trends and support data-driven vaccine allocation strategies.
• Ensured 99.2% data integrity by applying rigorous data cleaning, validation, and correlation analysis, identifying a –0.65 correlation between vaccination rate and disease incidence.

EDUCATION
Maharaja Surajmal Institute of Technology (Affiliated with GGSIPU)
Delhi · 10/2022 – 07/2026
Bachelor of Technology – Computer Science and Engineering

SKILLS
• Programming Skills: Python, SQL, Bash, Git, Big Data, Object-Oriented Programming
• Tools & Platforms: Jupyter Notebook, GitHub, MySQL, PostgreSQL, Docker, Tableau, Power BI"""

def test_extraction():
    print("🔍 TESTING ACTUAL EXTRACTION LOGIC")
    print("="*60)
    
    extractor = EnhancedResumeExtractor()
    
    # Test experience extraction
    print("\n📋 TESTING EXPERIENCE EXTRACTION:")
    print("-" * 40)
    experiences = extractor.extract_experience(sample_resume)
    print(f"Found {len(experiences)} experiences:")
    
    for i, exp in enumerate(experiences, 1):
        print(f"\n{i}. Company: {exp.get('company', 'N/A')}")
        print(f"   Title: {exp.get('title', 'N/A')}")
        print(f"   Dates: {exp.get('dates', 'N/A')}")
        print(f"   Location: {exp.get('location', 'N/A')}")
        
        achievements = exp.get('achievements', [])
        print(f"   Achievements ({len(achievements)}):")
        for j, achievement in enumerate(achievements, 1):
            print(f"     {j}. {achievement}")
    
    # Test project extraction
    print(f"\n📋 TESTING PROJECT EXTRACTION:")
    print("-" * 40)
    projects = extractor.extract_projects(sample_resume)
    print(f"Found {len(projects)} projects:")
    
    for i, proj in enumerate(projects, 1):
        print(f"\n{i}. Name: {proj.get('name', 'N/A')}")
        print(f"   Technologies: {proj.get('technologies', 'N/A')}")
        print(f"   GitHub: {proj.get('github', 'N/A')}")
        
        achievements = proj.get('achievements', [])
        print(f"   Achievements ({len(achievements)}):")
        for j, achievement in enumerate(achievements, 1):
            print(f"     {j}. {achievement}")
    
    # Test skills extraction
    print(f"\n📋 TESTING SKILLS EXTRACTION:")
    print("-" * 40)
    skills = extractor.extract_skills(sample_resume)
    print(f"Found {len(skills)} skills:")
    for i, skill in enumerate(skills, 1):
        print(f"  {i:2d}. {skill}")
    
    return experiences, projects, skills

if __name__ == "__main__":
    experiences, projects, skills = test_extraction()
    
    print(f"\n✅ EXTRACTION SUMMARY:")
    print(f"   Experiences: {len(experiences)} (should be 2)")
    print(f"   Projects: {len(projects)} (should be 2)")  
    print(f"   Skills: {len(skills)} (should be many)")
    
    # Check if we got meaningful data
    exp_has_achievements = any(len(exp.get('achievements', [])) > 0 for exp in experiences)
    proj_has_achievements = any(len(proj.get('achievements', [])) > 0 for proj in projects)
    
    print(f"\n🎯 QUALITY CHECK:")
    print(f"   Experiences have achievements: {'✅' if exp_has_achievements else '❌'}")
    print(f"   Projects have achievements: {'✅' if proj_has_achievements else '❌'}")
    print(f"   Skills extracted: {'✅' if len(skills) > 10 else '❌'}")