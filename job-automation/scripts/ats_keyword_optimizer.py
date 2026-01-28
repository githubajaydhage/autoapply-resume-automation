#!/usr/bin/env python3
"""
ATS Keyword Optimizer - Maximize Resume Visibility in Applicant Tracking Systems
This module extracts keywords from job descriptions and optimizes resume content
to pass ATS filters and rank higher in recruiter searches.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Set
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.config import USER_DETAILS
except ImportError:
    USER_DETAILS = {}


class ATSKeywordExtractor:
    """Extract important keywords from job descriptions for ATS optimization."""
    
    # Common technical skills by category
    SKILL_CATEGORIES = {
        'programming_languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'golang',
            'rust', 'ruby', 'php', 'scala', 'kotlin', 'swift', 'r', 'matlab', 'perl',
            'sql', 'bash', 'shell', 'powershell', 'html', 'css', 'sass', 'less'
        ],
        'frameworks': [
            'react', 'angular', 'vue', 'nextjs', 'next.js', 'nodejs', 'node.js',
            'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot',
            'rails', 'ruby on rails', '.net', 'asp.net', 'laravel', 'symfony',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'spark', 'hadoop', 'kafka', 'airflow', 'dbt'
        ],
        'cloud_devops': [
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
            'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd',
            'circleci', 'argocd', 'helm', 'prometheus', 'grafana', 'datadog',
            'cloudformation', 'pulumi', 'vagrant', 'openshift', 'lambda', 'serverless'
        ],
        'databases': [
            'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sql server', 'sqlite', 'neo4j',
            'mariadb', 'cockroachdb', 'couchdb', 'influxdb', 'timescaledb'
        ],
        'data_engineering': [
            'etl', 'data pipeline', 'data warehouse', 'snowflake', 'redshift',
            'bigquery', 'databricks', 'data lake', 'data modeling', 'dbt',
            'apache beam', 'fivetran', 'airbyte', 'data quality'
        ],
        'machine_learning': [
            'machine learning', 'deep learning', 'nlp', 'natural language processing',
            'computer vision', 'neural network', 'llm', 'gpt', 'bert', 'transformer',
            'regression', 'classification', 'clustering', 'reinforcement learning',
            'feature engineering', 'model deployment', 'mlops', 'a/b testing'
        ],
        'soft_skills': [
            'leadership', 'communication', 'problem solving', 'teamwork',
            'agile', 'scrum', 'kanban', 'project management', 'stakeholder',
            'cross-functional', 'mentoring', 'collaboration'
        ],
        'certifications': [
            'aws certified', 'azure certified', 'gcp certified', 'pmp', 'scrum master',
            'cissp', 'cka', 'ckad', 'terraform certified', 'databricks certified'
        ]
    }
    
    # Keywords that indicate seniority level
    SENIORITY_KEYWORDS = {
        'entry': ['entry level', 'junior', 'associate', 'graduate', 'fresher', '0-2 years'],
        'mid': ['mid-level', 'intermediate', '2-5 years', '3-5 years', '3+ years'],
        'senior': ['senior', 'lead', 'principal', 'staff', '5+ years', '7+ years', '8+ years'],
        'management': ['manager', 'director', 'head of', 'vp', 'chief', 'cto', 'cio']
    }
    
    def __init__(self):
        """Initialize the keyword extractor."""
        self.all_skills = set()
        for category_skills in self.SKILL_CATEGORIES.values():
            self.all_skills.update(category_skills)
    
    def extract_keywords(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract relevant keywords from a job description.
        
        Args:
            job_description: Full text of the job posting
            
        Returns:
            Dictionary with categorized keywords
        """
        text = job_description.lower()
        extracted = {}
        
        for category, skills in self.SKILL_CATEGORIES.items():
            found_skills = []
            for skill in skills:
                # Use word boundary matching for accuracy
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text):
                    found_skills.append(skill)
            if found_skills:
                extracted[category] = found_skills
        
        # Extract years of experience
        exp_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience',
            r'experience\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['experience_years'] = match.group(0)
                break
        
        # Detect seniority level
        for level, keywords in self.SENIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    extracted['seniority_level'] = level
                    break
            if 'seniority_level' in extracted:
                break
        
        return extracted
    
    def get_keyword_frequency(self, job_description: str) -> Counter:
        """
        Get frequency count of important keywords in job description.
        
        Args:
            job_description: Full text of the job posting
            
        Returns:
            Counter with keyword frequencies
        """
        text = job_description.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Filter to only relevant keywords
        relevant_words = [w for w in words if w in self.all_skills or len(w) > 3]
        return Counter(relevant_words)


class ResumeKeywordMatcher:
    """Match resume keywords against job requirements."""
    
    def __init__(self, resume_text: str):
        """
        Initialize with resume content.
        
        Args:
            resume_text: Full text of the resume
        """
        self.resume_text = resume_text.lower()
        self.extractor = ATSKeywordExtractor()
        self.resume_keywords = self._extract_resume_keywords()
    
    def _extract_resume_keywords(self) -> Set[str]:
        """Extract all relevant keywords from resume."""
        keywords = set()
        for category_skills in self.extractor.SKILL_CATEGORIES.values():
            for skill in category_skills:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, self.resume_text):
                    keywords.add(skill)
        return keywords
    
    def calculate_match_score(self, job_description: str) -> Dict:
        """
        Calculate how well resume matches job requirements.
        
        Args:
            job_description: Full text of the job posting
            
        Returns:
            Dictionary with match score and details
        """
        job_keywords = self.extractor.extract_keywords(job_description)
        
        # Flatten job keywords
        required_skills = set()
        for category, skills in job_keywords.items():
            if category not in ['experience_years', 'seniority_level']:
                required_skills.update(skills)
        
        if not required_skills:
            return {
                'match_percentage': 100,
                'matched_skills': [],
                'missing_skills': [],
                'recommendation': 'Job has no specific skill requirements'
            }
        
        matched = self.resume_keywords & required_skills
        missing = required_skills - self.resume_keywords
        
        match_percentage = (len(matched) / len(required_skills)) * 100
        
        # Generate recommendation
        if match_percentage >= 80:
            recommendation = "🟢 STRONG MATCH - High priority application"
        elif match_percentage >= 60:
            recommendation = "🟡 GOOD MATCH - Worth applying with tailored resume"
        elif match_percentage >= 40:
            recommendation = "🟠 PARTIAL MATCH - Consider if role aligns with career goals"
        else:
            recommendation = "🔴 WEAK MATCH - May not pass ATS filters"
        
        return {
            'match_percentage': round(match_percentage, 1),
            'matched_skills': sorted(list(matched)),
            'missing_skills': sorted(list(missing)),
            'total_required': len(required_skills),
            'recommendation': recommendation,
            'job_keywords': job_keywords
        }
    
    def generate_optimization_suggestions(self, job_description: str) -> List[str]:
        """
        Generate suggestions to optimize resume for this job.
        
        Args:
            job_description: Full text of the job posting
            
        Returns:
            List of actionable suggestions
        """
        match_result = self.calculate_match_score(job_description)
        suggestions = []
        
        if match_result['missing_skills']:
            top_missing = match_result['missing_skills'][:5]
            suggestions.append(
                f"Add these keywords if you have the skills: {', '.join(top_missing)}"
            )
        
        # Check for keyword frequency
        freq = self.extractor.get_keyword_frequency(job_description)
        top_keywords = [word for word, count in freq.most_common(10) 
                       if word in self.extractor.all_skills]
        
        if top_keywords:
            suggestions.append(
                f"Emphasize these frequently mentioned skills: {', '.join(top_keywords[:5])}"
            )
        
        # Seniority alignment
        job_keywords = match_result.get('job_keywords', {})
        if 'seniority_level' in job_keywords:
            level = job_keywords['seniority_level']
            suggestions.append(
                f"Tailor experience descriptions to match {level}-level expectations"
            )
        
        return suggestions


class ATSScorePredictor:
    """Predict how a resume will score in an ATS system."""
    
    # Weights for different factors
    WEIGHTS = {
        'skill_match': 0.40,
        'keyword_density': 0.20,
        'format_score': 0.15,
        'experience_match': 0.15,
        'education_match': 0.10
    }
    
    def __init__(self, resume_text: str):
        """
        Initialize with resume content.
        
        Args:
            resume_text: Full text of the resume
        """
        self.resume_text = resume_text
        self.matcher = ResumeKeywordMatcher(resume_text)
    
    def _calculate_format_score(self) -> float:
        """Score resume formatting for ATS compatibility."""
        score = 100
        text = self.resume_text
        
        # Penalties for ATS-unfriendly elements
        if len(text) < 500:
            score -= 20  # Too short
        if len(text) > 10000:
            score -= 10  # Too long
        
        # Check for standard sections
        standard_sections = ['experience', 'education', 'skills', 'summary']
        found_sections = sum(1 for s in standard_sections if s in text.lower())
        score -= (4 - found_sections) * 5
        
        # Check for contact info
        has_email = bool(re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text))
        has_phone = bool(re.search(r'\b\d{10}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', text))
        
        if not has_email:
            score -= 10
        if not has_phone:
            score -= 5
        
        return max(0, score)
    
    def _calculate_experience_match(self, job_description: str) -> float:
        """Score experience alignment."""
        job_keywords = self.matcher.extractor.extract_keywords(job_description)
        
        if 'experience_years' not in job_keywords:
            return 80  # No specific requirement
        
        # Extract years from resume
        exp_match = re.search(r'(\d+)\+?\s*years?', self.resume_text.lower())
        if exp_match:
            resume_years = int(exp_match.group(1))
            
            # Parse required years
            req_match = re.search(r'(\d+)', job_keywords['experience_years'])
            if req_match:
                required_years = int(req_match.group(1))
                
                if resume_years >= required_years:
                    return 100
                elif resume_years >= required_years - 1:
                    return 80
                else:
                    return 50
        
        return 60  # Cannot determine
    
    def predict_ats_score(self, job_description: str) -> Dict:
        """
        Predict overall ATS score for a job application.
        
        Args:
            job_description: Full text of the job posting
            
        Returns:
            Dictionary with predicted score and breakdown
        """
        match_result = self.matcher.calculate_match_score(job_description)
        
        scores = {
            'skill_match': match_result['match_percentage'],
            'keyword_density': min(100, len(self.matcher.resume_keywords) * 5),
            'format_score': self._calculate_format_score(),
            'experience_match': self._calculate_experience_match(job_description),
            'education_match': 80  # Default assumption
        }
        
        # Calculate weighted score
        total_score = sum(
            scores[factor] * weight 
            for factor, weight in self.WEIGHTS.items()
        )
        
        # Generate pass prediction
        if total_score >= 75:
            prediction = "🟢 HIGH PASS PROBABILITY - Resume likely to reach recruiter"
        elif total_score >= 60:
            prediction = "🟡 MODERATE PASS PROBABILITY - May need keyword optimization"
        elif total_score >= 45:
            prediction = "🟠 LOW PASS PROBABILITY - Significant tailoring needed"
        else:
            prediction = "🔴 UNLIKELY TO PASS - Consider if this role is a good fit"
        
        return {
            'overall_score': round(total_score, 1),
            'score_breakdown': scores,
            'prediction': prediction,
            'skill_analysis': match_result,
            'optimization_suggestions': self.matcher.generate_optimization_suggestions(job_description)
        }


class KeywordInjector:
    """Intelligently inject missing keywords into resume content."""
    
    def __init__(self):
        """Initialize the keyword injector."""
        self.extractor = ATSKeywordExtractor()
    
    def suggest_skill_additions(
        self, 
        resume_text: str, 
        job_description: str,
        candidate_skills: List[str] = None
    ) -> Dict[str, str]:
        """
        Suggest where and how to add missing keywords.
        
        Args:
            resume_text: Current resume content
            job_description: Target job description
            candidate_skills: Skills the candidate actually has but didn't mention
            
        Returns:
            Dictionary with section-specific suggestions
        """
        matcher = ResumeKeywordMatcher(resume_text)
        match_result = matcher.calculate_match_score(job_description)
        
        missing = set(match_result['missing_skills'])
        
        # If candidate provided their actual skills, filter to only those
        if candidate_skills:
            candidate_skill_set = set(s.lower() for s in candidate_skills)
            missing = missing & candidate_skill_set
        
        suggestions = {}
        
        if not missing:
            suggestions['summary'] = "Resume already contains all required keywords!"
            return suggestions
        
        # Categorize missing skills for targeted suggestions
        categorized_missing = {}
        for skill in missing:
            for category, skills in self.extractor.SKILL_CATEGORIES.items():
                if skill in skills:
                    if category not in categorized_missing:
                        categorized_missing[category] = []
                    categorized_missing[category].append(skill)
                    break
        
        # Generate section-specific suggestions
        if 'programming_languages' in categorized_missing:
            langs = categorized_missing['programming_languages']
            suggestions['skills_section'] = (
                f"Add to Technical Skills: {', '.join(langs)}"
            )
        
        if 'frameworks' in categorized_missing:
            frameworks = categorized_missing['frameworks']
            suggestions['experience_section'] = (
                f"Mention in project descriptions: {', '.join(frameworks)}"
            )
        
        if 'cloud_devops' in categorized_missing:
            devops = categorized_missing['cloud_devops']
            suggestions['infrastructure'] = (
                f"Add DevOps/Cloud experience: {', '.join(devops)}"
            )
        
        if 'soft_skills' in categorized_missing:
            soft = categorized_missing['soft_skills']
            suggestions['summary_section'] = (
                f"Incorporate into summary: {', '.join(soft)}"
            )
        
        return suggestions


def analyze_job_fit(resume_path: str, job_title: str, job_description: str) -> Dict:
    """
    Comprehensive analysis of resume-job fit for ATS optimization.
    
    Args:
        resume_path: Path to resume file
        job_title: Title of the job
        job_description: Full job description
        
    Returns:
        Complete analysis with scores and suggestions
    """
    # Read resume
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_text = f.read()
    except Exception as e:
        return {'error': f'Could not read resume: {str(e)}'}
    
    # Run analysis
    predictor = ATSScorePredictor(resume_text)
    result = predictor.predict_ats_score(job_description)
    
    # Add job info
    result['job_title'] = job_title
    result['resume_file'] = resume_path
    
    # Add keyword injection suggestions
    injector = KeywordInjector()
    candidate_skills = USER_DETAILS.get('key_skills', '').split(',')
    result['keyword_suggestions'] = injector.suggest_skill_additions(
        resume_text, job_description, candidate_skills
    )
    
    return result


def generate_ats_report(jobs_df, resume_path: str, output_path: str = 'data/ats_report.txt'):
    """
    Generate ATS optimization report for multiple jobs.
    
    Args:
        jobs_df: DataFrame with job listings
        resume_path: Path to resume file
        output_path: Where to save the report
    """
    import pandas as pd
    
    # Read resume once
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_text = f.read()
    except Exception:
        resume_text = ""
    
    if not resume_text:
        print("Could not read resume for ATS analysis")
        return
    
    predictor = ATSScorePredictor(resume_text)
    
    report_lines = [
        "=" * 60,
        "ATS KEYWORD OPTIMIZATION REPORT",
        "=" * 60,
        f"Resume analyzed: {resume_path}",
        f"Jobs analyzed: {len(jobs_df)}",
        "",
        "TOP MATCHING JOBS (by ATS score):",
        "-" * 40
    ]
    
    scores = []
    for idx, row in jobs_df.iterrows():
        job_desc = str(row.get('description', ''))
        if not job_desc or len(job_desc) < 50:
            continue
            
        result = predictor.predict_ats_score(job_desc)
        scores.append({
            'title': row.get('title', 'Unknown'),
            'company': row.get('company', 'Unknown'),
            'score': result['overall_score'],
            'matched': len(result['skill_analysis']['matched_skills']),
            'missing': len(result['skill_analysis']['missing_skills']),
            'prediction': result['prediction']
        })
    
    # Sort by score
    scores.sort(key=lambda x: x['score'], reverse=True)
    
    for i, job in enumerate(scores[:10], 1):
        report_lines.append(f"\n{i}. {job['title']} at {job['company']}")
        report_lines.append(f"   ATS Score: {job['score']}% | Matched: {job['matched']} | Missing: {job['missing']}")
        report_lines.append(f"   {job['prediction']}")
    
    # Aggregate most common missing skills
    if scores:
        report_lines.extend([
            "",
            "=" * 60,
            "SKILLS GAP ANALYSIS",
            "=" * 60,
            "",
            "Most commonly missing skills across all jobs:"
        ])
        
        # Would need to track missing skills across all jobs
        # This is a simplified version
        report_lines.append("(Run detailed analysis on individual jobs for specific gaps)")
    
    report_lines.extend([
        "",
        "=" * 60,
        "RECOMMENDATIONS",
        "=" * 60,
        "",
        "1. Focus on jobs with 60%+ ATS score for best results",
        "2. Tailor resume keywords for top matches",
        "3. Use exact keyword phrases from job descriptions",
        "4. Include both acronyms and full forms (AWS and Amazon Web Services)",
        "5. Quantify achievements with numbers and metrics",
        ""
    ])
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"ATS report generated: {output_path}")
    return scores


if __name__ == "__main__":
    # Test with sample data
    sample_job = """
    Senior Python Developer
    
    Requirements:
    - 5+ years of experience with Python
    - Strong knowledge of Django or Flask
    - Experience with PostgreSQL and Redis
    - AWS experience (EC2, S3, Lambda)
    - Docker and Kubernetes
    - CI/CD pipelines
    - Excellent communication skills
    """
    
    sample_resume = """
    JOHN DOE
    Software Engineer
    john@email.com | 555-1234
    
    SUMMARY
    Experienced software developer with 6 years of experience building web applications.
    
    SKILLS
    Python, JavaScript, Django, React, PostgreSQL, MySQL, Docker, AWS, Git
    
    EXPERIENCE
    Senior Developer at Tech Corp (2020-Present)
    - Built REST APIs using Django and Flask
    - Deployed applications on AWS EC2 and S3
    - Implemented CI/CD with GitHub Actions
    
    EDUCATION
    BS Computer Science
    """
    
    matcher = ResumeKeywordMatcher(sample_resume)
    result = matcher.calculate_match_score(sample_job)
    
    print("\n=== ATS Keyword Analysis ===")
    print(f"Match Score: {result['match_percentage']}%")
    print(f"Matched Skills: {', '.join(result['matched_skills'])}")
    print(f"Missing Skills: {', '.join(result['missing_skills'])}")
    print(f"Recommendation: {result['recommendation']}")
    
    predictor = ATSScorePredictor(sample_resume)
    ats_result = predictor.predict_ats_score(sample_job)
    
    print(f"\nPredicted ATS Score: {ats_result['overall_score']}%")
    print(f"Prediction: {ats_result['prediction']}")
    print("\nOptimization Suggestions:")
    for suggestion in ats_result['optimization_suggestions']:
        print(f"  • {suggestion}")
