"""
🤖 AI-POWERED JOB MATCHER - Intelligent Resume-to-Job Matching

Uses AI/ML to:
1. Semantic matching between resume and job descriptions
2. Score jobs based on skill fit, experience, and preferences
3. Identify skill gaps and suggest improvements
4. Prioritize applications based on match quality
5. Learn from application outcomes

Supports: OpenAI, Google Gemini, Ollama (local), or TF-IDF fallback

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Try to import AI libraries
AI_BACKEND = None
try:
    import openai
    AI_BACKEND = 'openai'
except ImportError:
    pass

if not AI_BACKEND:
    try:
        import google.generativeai as genai
        AI_BACKEND = 'gemini'
    except ImportError:
        pass

if not AI_BACKEND:
    try:
        import ollama
        AI_BACKEND = 'ollama'
    except ImportError:
        pass

# Fallback to TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AIJobMatcher:
    """
    🤖 AI-Powered Job Matching Engine
    
    Features:
    - Semantic similarity scoring
    - Skill extraction and matching
    - Experience level analysis
    - Culture fit indicators
    - Application priority ranking
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        self.resumes_path = os.path.join(self.base_path, 'resumes')
        
        # AI Configuration
        self.ai_backend = self._detect_ai_backend()
        self.model = self._get_model()
        
        # Cache for embeddings
        self.embedding_cache_path = os.path.join(self.data_path, 'embedding_cache.json')
        self.embedding_cache = self._load_embedding_cache()
        
        # Resume content (loaded once)
        self.resume_text = self._load_resume()
        self.resume_skills = self._extract_skills_from_text(self.resume_text)
        
        logging.info(f"🤖 AI Job Matcher initialized (backend: {self.ai_backend})")
        logging.info(f"📄 Resume loaded: {len(self.resume_text)} chars, {len(self.resume_skills)} skills detected")
    
    def _detect_ai_backend(self) -> str:
        """Detect available AI backend."""
        # Check for API keys
        if os.getenv('OPENAI_API_KEY'):
            return 'openai'
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            return 'gemini'
        if os.getenv('OLLAMA_HOST') or AI_BACKEND == 'ollama':
            return 'ollama'
        if SKLEARN_AVAILABLE:
            return 'tfidf'
        return 'keyword'
    
    def _get_model(self) -> str:
        """Get model name for the backend."""
        models = {
            'openai': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'gemini': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            'ollama': os.getenv('OLLAMA_MODEL', 'llama3.2'),
            'tfidf': 'sklearn-tfidf',
            'keyword': 'keyword-match'
        }
        return models.get(self.ai_backend, 'keyword-match')
    
    def _load_embedding_cache(self) -> Dict:
        """Load embedding cache."""
        if os.path.exists(self.embedding_cache_path):
            try:
                with open(self.embedding_cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_embedding_cache(self):
        """Save embedding cache."""
        try:
            with open(self.embedding_cache_path, 'w') as f:
                json.dump(self.embedding_cache, f)
        except:
            pass
    
    def _load_resume(self) -> str:
        """Load resume content."""
        resume_filename = os.getenv('RESUME_FILENAME', 'resume.pdf')
        resume_path = os.path.join(self.resumes_path, resume_filename)
        
        # Try to read PDF
        if resume_path.endswith('.pdf') and os.path.exists(resume_path):
            try:
                import PyPDF2
                with open(resume_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ' '.join(page.extract_text() for page in reader.pages)
                    return text
            except:
                pass
        
        # Try text file
        txt_path = resume_path.replace('.pdf', '.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Fall back to skills from environment
        skills = os.getenv('JOB_KEYWORDS', '')
        applicant_skills = os.getenv('APPLICANT_SKILLS', '')
        target_role = os.getenv('APPLICANT_TARGET_ROLE', '')
        experience = os.getenv('YEARS_EXPERIENCE', '3')
        
        return f"""
        Target Role: {target_role}
        Experience: {experience} years
        Skills: {skills} {applicant_skills}
        """
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using pattern matching."""
        # Common technical skills patterns
        skill_patterns = [
            # Programming languages
            r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|swift|kotlin|php|scala|r)\b',
            # Data & Analytics
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|tableau|power bi|excel|pandas|numpy|spark|hadoop)\b',
            # Frameworks
            r'\b(react|angular|vue|django|flask|spring|nodejs|express|fastapi|tensorflow|pytorch|keras)\b',
            # Cloud & DevOps
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible|ci/cd|git|github|gitlab)\b',
            # Design & Architecture
            r'\b(autocad|revit|sketchup|3ds max|rhino|solidworks|figma|adobe|photoshop|illustrator)\b',
            # Soft skills
            r'\b(leadership|communication|teamwork|problem.solving|analytical|project management|agile|scrum)\b',
        ]
        
        text_lower = text.lower()
        skills = set()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.update(matches)
        
        return list(skills)
    
    # =========================================================================
    # AI MATCHING METHODS
    # =========================================================================
    
    def match_job(self, job: Dict) -> Dict:
        """
        Calculate match score between resume and job.
        
        Returns:
        {
            'score': 0-100,
            'skill_match': [],
            'skill_gaps': [],
            'experience_fit': 'good/partial/low',
            'recommendation': 'apply/maybe/skip',
            'personalization': 'string with talking points'
        }
        """
        job_title = job.get('title', '')
        job_description = job.get('description', '')
        company = job.get('company', '')
        
        job_text = f"{job_title} {job_description} {company}"
        
        # Use appropriate matching method
        if self.ai_backend in ['openai', 'gemini', 'ollama']:
            return self._ai_match(job)
        elif self.ai_backend == 'tfidf':
            return self._tfidf_match(job_text)
        else:
            return self._keyword_match(job)
    
    def _ai_match(self, job: Dict) -> Dict:
        """Use LLM for intelligent matching."""
        job_title = job.get('title', '')
        job_description = job.get('description', '')[:1500]  # Truncate for API limits
        company = job.get('company', '')
        
        prompt = f"""Analyze this job match for a candidate.

CANDIDATE PROFILE:
{self.resume_text[:2000]}

JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {job_description}

Provide a JSON response with:
{{
    "score": <0-100 match percentage>,
    "skill_match": [<list of matching skills>],
    "skill_gaps": [<skills in job but not in resume>],
    "experience_fit": "<good/partial/low>",
    "recommendation": "<apply/maybe/skip>",
    "personalization": "<2-3 sentences on why this is a good fit, for cover letter>"
}}

Only respond with valid JSON, no other text."""

        try:
            if self.ai_backend == 'openai':
                return self._openai_match(prompt)
            elif self.ai_backend == 'gemini':
                return self._gemini_match(prompt)
            elif self.ai_backend == 'ollama':
                return self._ollama_match(prompt)
        except Exception as e:
            logging.warning(f"AI match failed: {e}, falling back to keyword match")
            return self._keyword_match(job)
    
    def _openai_match(self, prompt: str) -> Dict:
        """Use OpenAI for matching."""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a job matching AI. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        return self._parse_ai_response(result_text)
    
    def _gemini_match(self, prompt: str) -> Dict:
        """Use Google Gemini for matching."""
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel(self.model)
        
        response = model.generate_content(prompt)
        return self._parse_ai_response(response.text)
    
    def _ollama_match(self, prompt: str) -> Dict:
        """Use Ollama (local LLM) for matching."""
        import ollama
        
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_ai_response(response['message']['content'])
    
    def _parse_ai_response(self, text: str) -> Dict:
        """Parse AI response into structured format."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Return default if parsing fails
        return {
            'score': 50,
            'skill_match': [],
            'skill_gaps': [],
            'experience_fit': 'partial',
            'recommendation': 'maybe',
            'personalization': ''
        }
    
    def _tfidf_match(self, job_text: str) -> Dict:
        """Use TF-IDF for semantic similarity."""
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
        try:
            tfidf_matrix = vectorizer.fit_transform([self.resume_text, job_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            score = int(similarity * 100)
        except:
            score = 50
        
        # Extract job skills
        job_skills = self._extract_skills_from_text(job_text)
        skill_match = [s for s in job_skills if s in self.resume_skills]
        skill_gaps = [s for s in job_skills if s not in self.resume_skills]
        
        return {
            'score': score,
            'skill_match': skill_match,
            'skill_gaps': skill_gaps,
            'experience_fit': 'good' if score > 60 else 'partial' if score > 40 else 'low',
            'recommendation': 'apply' if score > 60 else 'maybe' if score > 40 else 'skip',
            'personalization': f"Strong match in: {', '.join(skill_match[:5])}" if skill_match else ''
        }
    
    def _keyword_match(self, job: Dict) -> Dict:
        """Simple keyword matching fallback."""
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        # Get keywords from environment
        keywords = os.getenv('JOB_KEYWORDS', '').lower().split(',')
        keywords = [k.strip() for k in keywords if k.strip()]
        
        # Count matches
        matches = [k for k in keywords if k in job_text]
        score = int((len(matches) / max(len(keywords), 1)) * 100)
        
        # Extract job skills
        job_skills = self._extract_skills_from_text(job_text)
        skill_match = [s for s in job_skills if s in self.resume_skills]
        skill_gaps = [s for s in job_skills if s not in self.resume_skills]
        
        return {
            'score': min(score + len(skill_match) * 5, 100),
            'skill_match': skill_match,
            'skill_gaps': skill_gaps,
            'experience_fit': 'good' if score > 60 else 'partial' if score > 40 else 'low',
            'recommendation': 'apply' if score > 50 else 'maybe' if score > 30 else 'skip',
            'personalization': ''
        }
    
    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================
    
    def score_all_jobs(self, jobs_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Score all jobs in the jobs dataframe.
        Adds match_score, recommendation, skill_match columns.
        """
        logging.info("🤖 AI Job Matching - Scoring all jobs...")
        
        if jobs_df is None:
            jobs_path = os.path.join(self.data_path, 'jobs_today.csv')
            if not os.path.exists(jobs_path):
                logging.warning("No jobs file found")
                return pd.DataFrame()
            jobs_df = pd.read_csv(jobs_path)
        
        if jobs_df.empty:
            return jobs_df
        
        scores = []
        recommendations = []
        skill_matches = []
        personalizations = []
        
        for idx, job in jobs_df.iterrows():
            try:
                result = self.match_job(job.to_dict())
                scores.append(result.get('score', 50))
                recommendations.append(result.get('recommendation', 'maybe'))
                skill_matches.append(', '.join(result.get('skill_match', [])[:5]))
                personalizations.append(result.get('personalization', ''))
                
                if (idx + 1) % 10 == 0:
                    logging.info(f"   Scored {idx + 1}/{len(jobs_df)} jobs...")
                    
            except Exception as e:
                logging.debug(f"Error scoring job {idx}: {e}")
                scores.append(50)
                recommendations.append('maybe')
                skill_matches.append('')
                personalizations.append('')
        
        # Add columns
        jobs_df['ai_match_score'] = scores
        jobs_df['ai_recommendation'] = recommendations
        jobs_df['matched_skills'] = skill_matches
        jobs_df['personalization'] = personalizations
        
        # Sort by score
        jobs_df = jobs_df.sort_values('ai_match_score', ascending=False)
        
        # Save enhanced jobs
        output_path = os.path.join(self.data_path, 'ai_scored_jobs.csv')
        jobs_df.to_csv(output_path, index=False)
        
        # Stats
        apply_count = len(jobs_df[jobs_df['ai_recommendation'] == 'apply'])
        maybe_count = len(jobs_df[jobs_df['ai_recommendation'] == 'maybe'])
        skip_count = len(jobs_df[jobs_df['ai_recommendation'] == 'skip'])
        
        logging.info(f"✅ AI Scoring Complete!")
        logging.info(f"   🎯 Strong matches (apply): {apply_count}")
        logging.info(f"   🤔 Possible matches (maybe): {maybe_count}")
        logging.info(f"   ⏭️ Low matches (skip): {skip_count}")
        
        return jobs_df
    
    def get_top_matches(self, n: int = 20) -> pd.DataFrame:
        """Get top N job matches."""
        scored_path = os.path.join(self.data_path, 'ai_scored_jobs.csv')
        
        if os.path.exists(scored_path):
            df = pd.read_csv(scored_path)
        else:
            df = self.score_all_jobs()
        
        return df.head(n)
    
    def analyze_skill_gaps(self) -> Dict:
        """Analyze common skill gaps across all jobs."""
        scored_path = os.path.join(self.data_path, 'ai_scored_jobs.csv')
        
        if not os.path.exists(scored_path):
            self.score_all_jobs()
        
        jobs_df = pd.read_csv(scored_path)
        
        # Count skill gaps
        all_gaps = []
        for _, job in jobs_df.iterrows():
            desc = str(job.get('description', ''))
            gaps = self._extract_skills_from_text(desc)
            for gap in gaps:
                if gap not in self.resume_skills:
                    all_gaps.append(gap)
        
        # Count occurrences
        gap_counts = {}
        for gap in all_gaps:
            gap_counts[gap] = gap_counts.get(gap, 0) + 1
        
        # Sort by frequency
        sorted_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'top_skill_gaps': sorted_gaps[:10],
            'total_unique_gaps': len(set(all_gaps)),
            'recommendation': "Consider adding these skills to improve match rates"
        }


def main():
    """Run AI job matching."""
    matcher = AIJobMatcher()
    
    # Score all jobs
    scored_jobs = matcher.score_all_jobs()
    
    if not scored_jobs.empty:
        # Show top matches
        print("\n🎯 TOP JOB MATCHES:")
        print("="*60)
        top = matcher.get_top_matches(10)
        for _, job in top.iterrows():
            print(f"  {job.get('ai_match_score', 0)}% | {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}")
            if job.get('matched_skills'):
                print(f"       Skills: {job.get('matched_skills')}")
        
        # Show skill gaps
        print("\n📊 SKILL GAP ANALYSIS:")
        print("="*60)
        gaps = matcher.analyze_skill_gaps()
        for skill, count in gaps['top_skill_gaps'][:5]:
            print(f"  {skill}: mentioned in {count} job postings")


if __name__ == '__main__':
    main()
