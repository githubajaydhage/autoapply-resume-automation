"""
Resume Keyword Optimizer - Analyzes job descriptions and optimizes resume for ATS
Extracts keywords from JDs and scores resume match percentage
"""

import re
import os
import sys
import logging
import pandas as pd
from collections import Counter
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from utils.config import BASE_RESUME_PATH, USER_DETAILS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ResumeOptimizer:
    """Analyzes job descriptions and optimizes resume keywords for ATS."""
    
    # Common technical skills by category
    SKILL_CATEGORIES = {
        'programming': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'golang',
            'rust', 'scala', 'kotlin', 'swift', 'php', 'r', 'matlab', 'perl', 'shell', 'bash'
        ],
        'data_analysis': [
            'sql', 'excel', 'tableau', 'power bi', 'powerbi', 'looker', 'qlik', 'sisense',
            'data analysis', 'data analytics', 'business intelligence', 'bi', 'reporting',
            'dashboards', 'kpi', 'metrics', 'visualization', 'data visualization'
        ],
        'data_science': [
            'machine learning', 'ml', 'deep learning', 'neural network', 'nlp',
            'natural language processing', 'computer vision', 'tensorflow', 'pytorch',
            'keras', 'scikit-learn', 'sklearn', 'pandas', 'numpy', 'scipy', 'matplotlib',
            'seaborn', 'jupyter', 'statistics', 'statistical', 'regression', 'classification'
        ],
        'cloud': [
            'aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'cloud computing',
            's3', 'ec2', 'lambda', 'dynamodb', 'redshift', 'bigquery', 'snowflake',
            'databricks', 'spark', 'hadoop', 'kafka', 'airflow', 'docker', 'kubernetes', 'k8s'
        ],
        'databases': [
            'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
            'oracle', 'sql server', 'sqlite', 'cassandra', 'neo4j', 'nosql', 'database'
        ],
        'web': [
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'nodejs', 'express',
            'django', 'flask', 'fastapi', 'spring', 'rest api', 'graphql', 'microservices'
        ],
        'soft_skills': [
            'communication', 'leadership', 'teamwork', 'problem solving', 'analytical',
            'critical thinking', 'project management', 'agile', 'scrum', 'stakeholder',
            'presentation', 'collaboration', 'mentoring', 'cross-functional'
        ],
        'tools': [
            'git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'trello',
            'jenkins', 'ci/cd', 'terraform', 'ansible', 'linux', 'unix', 'windows'
        ]
    }
    
    # Common job title keywords
    JOB_TITLE_KEYWORDS = [
        'analyst', 'engineer', 'developer', 'scientist', 'manager', 'lead', 'senior',
        'junior', 'associate', 'principal', 'staff', 'architect', 'consultant',
        'specialist', 'coordinator', 'administrator', 'director', 'head', 'vp'
    ]
    
    # Experience level indicators
    EXPERIENCE_LEVELS = {
        'entry': ['fresher', 'entry level', 'junior', '0-2 years', '1-2 years', 'graduate'],
        'mid': ['mid level', 'intermediate', '2-5 years', '3-5 years', '4-6 years'],
        'senior': ['senior', 'lead', '5+ years', '6+ years', '7+ years', '8+ years', 'experienced'],
        'expert': ['principal', 'staff', 'architect', '10+ years', 'director', 'head', 'vp']
    }
    
    def __init__(self):
        self.resume_path = BASE_RESUME_PATH
        self.resume_text = self._extract_resume_text()
        self.resume_skills = self._extract_skills_from_text(self.resume_text)
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
    def _extract_resume_text(self) -> str:
        """Extract text from resume file."""
        if not os.path.exists(self.resume_path):
            logging.warning(f"Resume not found at {self.resume_path}")
            return ""
        
        ext = os.path.splitext(self.resume_path)[1].lower()
        
        if ext == '.pdf' and PDF_AVAILABLE:
            try:
                doc = fitz.open(self.resume_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text.lower()
            except Exception as e:
                logging.error(f"Error reading PDF: {e}")
                return ""
        
        elif ext == '.docx' and DOCX_AVAILABLE:
            try:
                doc = Document(self.resume_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text.lower()
            except Exception as e:
                logging.error(f"Error reading DOCX: {e}")
                return ""
        
        elif ext == '.txt':
            try:
                with open(self.resume_path, 'r', encoding='utf-8') as f:
                    return f.read().lower()
            except Exception as e:
                logging.error(f"Error reading TXT: {e}")
                return ""
        
        return ""
    
    def _extract_skills_from_text(self, text: str) -> set:
        """Extract skills mentioned in text."""
        text_lower = text.lower()
        found_skills = set()
        
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                # Use word boundary matching for accurate skill detection
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill)
        
        return found_skills
    
    def _extract_keywords_from_jd(self, job_description: str) -> dict:
        """Extract important keywords from job description."""
        # Handle NaN/None/non-string values
        if job_description is None or (isinstance(job_description, float) and pd.isna(job_description)):
            return {'skills': {}, 'min_experience': 0, 'experience_level': 'entry', 'education': [], 'actions': []}
        
        jd_lower = str(job_description).lower()
        
        # Extract skills
        skills = self._extract_skills_from_text(jd_lower)
        
        # Extract experience requirements
        experience_pattern = r'(\d+)\+?\s*(?:to\s*\d+)?\s*years?'
        experience_matches = re.findall(experience_pattern, jd_lower)
        min_experience = min([int(x) for x in experience_matches]) if experience_matches else 0
        
        # Determine experience level
        experience_level = 'entry'
        for level, keywords in self.EXPERIENCE_LEVELS.items():
            for keyword in keywords:
                if keyword in jd_lower:
                    experience_level = level
                    break
        
        # Extract education requirements
        education_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'bca', 'mca', 
                            'b.e.', 'm.e.', 'bsc', 'msc', 'mba', 'degree', 'graduate']
        education = [edu for edu in education_keywords if edu in jd_lower]
        
        # Extract common action words (what the job requires)
        action_words = ['develop', 'design', 'implement', 'analyze', 'manage', 'lead',
                       'build', 'create', 'optimize', 'maintain', 'support', 'collaborate',
                       'coordinate', 'research', 'test', 'deploy', 'monitor', 'automate']
        required_actions = [word for word in action_words if word in jd_lower]
        
        return {
            'skills': skills,
            'min_experience': min_experience,
            'experience_level': experience_level,
            'education': education,
            'actions': required_actions
        }
    
    def calculate_match_score(self, job_description: str) -> dict:
        """Calculate how well resume matches the job description."""
        jd_keywords = self._extract_keywords_from_jd(job_description)
        jd_skills = jd_keywords['skills']
        
        if not jd_skills:
            return {
                'score': 0,
                'matching_skills': [],
                'missing_skills': [],
                'recommendation': 'Could not extract skills from job description'
            }
        
        # Calculate skill match
        matching_skills = self.resume_skills.intersection(jd_skills)
        missing_skills = jd_skills - self.resume_skills
        
        skill_score = (len(matching_skills) / len(jd_skills)) * 100 if jd_skills else 0
        
        # Calculate experience match
        user_experience = int(USER_DETAILS.get('years_experience', '3'))
        exp_required = jd_keywords['min_experience']
        exp_score = 100 if user_experience >= exp_required else (user_experience / exp_required) * 100
        
        # Overall score (skills 70%, experience 30%)
        overall_score = (skill_score * 0.7) + (exp_score * 0.3)
        
        # Generate recommendation
        if overall_score >= 80:
            recommendation = "Excellent match! Apply immediately."
        elif overall_score >= 60:
            recommendation = "Good match. Consider highlighting these skills in cover letter."
        elif overall_score >= 40:
            recommendation = "Moderate match. Focus on transferable skills."
        else:
            recommendation = "Low match. Consider upskilling or finding better-fit roles."
        
        return {
            'score': round(overall_score, 1),
            'skill_score': round(skill_score, 1),
            'experience_score': round(exp_score, 1),
            'matching_skills': sorted(list(matching_skills)),
            'missing_skills': sorted(list(missing_skills)),
            'jd_keywords': jd_keywords,
            'recommendation': recommendation
        }
    
    def generate_keyword_suggestions(self, job_description: str) -> dict:
        """Generate suggestions to improve resume for this job."""
        match_result = self.calculate_match_score(job_description)
        
        suggestions = {
            'add_to_resume': [],
            'highlight_skills': match_result['matching_skills'],
            'cover_letter_focus': [],
            'overall_tips': []
        }
        
        # Skills to add (if you have them but didn't mention)
        missing = match_result['missing_skills']
        if missing:
            suggestions['add_to_resume'] = missing[:5]  # Top 5 missing skills
            suggestions['cover_letter_focus'] = [
                f"Emphasize your experience with {', '.join(match_result['matching_skills'][:3])}" if match_result['matching_skills'] else "",
                f"Address gaps in: {', '.join(missing[:3])}" if missing else ""
            ]
        
        # Overall tips based on score
        if match_result['score'] < 50:
            suggestions['overall_tips'] = [
                "Consider taking online courses for missing skills",
                "Look for similar roles with lower skill requirements",
                "Focus on transferable skills in your application"
            ]
        elif match_result['score'] < 70:
            suggestions['overall_tips'] = [
                "Strong candidate - customize your resume for this role",
                "Prepare examples of your experience with matching skills",
                "Research the company to personalize your application"
            ]
        else:
            suggestions['overall_tips'] = [
                "Excellent fit - apply immediately!",
                "Prepare for technical interview questions on your top skills",
                "Consider reaching out directly to the hiring manager"
            ]
        
        return suggestions
    
    def analyze_jobs_from_csv(self) -> pd.DataFrame:
        """Analyze all jobs from jobs_today.csv and score them."""
        jobs_path = os.path.join(self.data_dir, 'jobs_today.csv')
        
        if not os.path.exists(jobs_path):
            logging.warning("No jobs file found")
            return pd.DataFrame()
        
        df = pd.read_csv(jobs_path)
        
        results = []
        for idx, row in df.iterrows():
            job_title = row.get('title', row.get('job_title', ''))
            company = row.get('company', '')
            
            # Use job title + company as basic JD if no description
            jd = row.get('description', f"{job_title} at {company}")
            
            match = self.calculate_match_score(jd)
            
            results.append({
                'job_title': job_title,
                'company': company,
                'match_score': match['score'],
                'matching_skills': ', '.join(match['matching_skills'][:5]),
                'missing_skills': ', '.join(match['missing_skills'][:5]),
                'recommendation': match['recommendation'],
                'job_url': row.get('url', row.get('job_url', ''))
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('match_score', ascending=False)
        
        # Save results
        output_path = os.path.join(self.data_dir, 'job_match_scores.csv')
        results_df.to_csv(output_path, index=False)
        logging.info(f"💾 Saved job match scores to {output_path}")
        
        return results_df
    
    def get_resume_skills_report(self) -> dict:
        """Generate a report of skills found in resume."""
        skills_by_category = {}
        
        for category, skills in self.SKILL_CATEGORIES.items():
            found = [s for s in skills if s in self.resume_skills]
            if found:
                skills_by_category[category] = found
        
        return {
            'total_skills': len(self.resume_skills),
            'skills_by_category': skills_by_category,
            'all_skills': sorted(list(self.resume_skills))
        }


def main():
    """Main function to analyze resume and jobs."""
    logging.info("="*60)
    logging.info("📝 RESUME KEYWORD OPTIMIZER")
    logging.info("="*60)
    
    optimizer = ResumeOptimizer()
    
    # Resume skills report
    resume_report = optimizer.get_resume_skills_report()
    logging.info(f"\n📋 RESUME ANALYSIS:")
    logging.info(f"   Total skills detected: {resume_report['total_skills']}")
    
    for category, skills in resume_report['skills_by_category'].items():
        logging.info(f"   {category.upper()}: {', '.join(skills)}")
    
    # Analyze jobs
    logging.info(f"\n🎯 ANALYZING JOBS FOR MATCH SCORES...")
    results = optimizer.analyze_jobs_from_csv()
    
    if not results.empty:
        logging.info(f"\n📊 TOP MATCHING JOBS:")
        for idx, row in results.head(10).iterrows():
            score = row['match_score']
            emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            logging.info(f"   {emoji} {row['match_score']}% - {row['job_title']} at {row['company']}")
        
        # Summary stats
        high_match = len(results[results['match_score'] >= 70])
        medium_match = len(results[(results['match_score'] >= 50) & (results['match_score'] < 70)])
        low_match = len(results[results['match_score'] < 50])
        
        logging.info(f"\n📈 SUMMARY:")
        logging.info(f"   🟢 High match (70%+): {high_match} jobs")
        logging.info(f"   🟡 Medium match (50-70%): {medium_match} jobs")
        logging.info(f"   🔴 Low match (<50%): {low_match} jobs")
    
    logging.info("="*60)
    logging.info("✅ Resume optimization complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
