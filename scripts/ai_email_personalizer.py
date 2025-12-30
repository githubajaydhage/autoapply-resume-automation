"""
🤖 AI EMAIL PERSONALIZER - Smart Email Subject Lines & Content

Uses AI to:
1. Generate attention-grabbing subject lines (A/B tested)
2. Personalize email opening based on company research
3. Add relevant talking points for each application
4. Optimize send times based on patterns
5. Track which personalizations get responses

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AIEmailPersonalizer:
    """
    🤖 AI-Powered Email Personalization Engine
    
    Generates:
    - Compelling subject lines
    - Personalized email openings
    - Company-specific talking points
    - Optimized send recommendations
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # AI Configuration
        self.ai_backend = self._detect_ai_backend()
        
        # User info
        self.applicant_name = USER_DETAILS.get('full_name') or os.getenv('APPLICANT_NAME', '')
        self.first_name = USER_DETAILS.get('first_name') or os.getenv('APPLICANT_FIRST_NAME', self.applicant_name.split()[0] if self.applicant_name else '')
        self.skills = USER_DETAILS.get('key_skills') or os.getenv('APPLICANT_SKILLS', os.getenv('JOB_KEYWORDS', ''))
        self.experience = USER_DETAILS.get('years_experience') or os.getenv('YEARS_EXPERIENCE', '3')
        
        # Performance tracking
        self.performance_path = os.path.join(self.data_path, 'email_performance.json')
        self.performance_data = self._load_performance_data()
        
        logging.info(f"🤖 AI Email Personalizer initialized (backend: {self.ai_backend})")
    
    def _detect_ai_backend(self) -> str:
        """Detect available AI backend."""
        if os.getenv('OPENAI_API_KEY'):
            return 'openai'
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            return 'gemini'
        return 'smart_templates'
    
    def _load_performance_data(self) -> Dict:
        """Load email performance data."""
        if os.path.exists(self.performance_path):
            try:
                with open(self.performance_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'subject_lines': {},
            'openings': {},
            'best_send_times': [],
            'response_patterns': []
        }
    
    def _save_performance_data(self):
        """Save performance data."""
        try:
            with open(self.performance_path, 'w') as f:
                json.dump(self.performance_data, f, indent=2)
        except:
            pass
    
    # =========================================================================
    # SUBJECT LINE GENERATION
    # =========================================================================
    
    def generate_subject_lines(
        self,
        company: str,
        job_title: str,
        hr_name: str = '',
        strategy: str = 'mixed'  # 'professional', 'attention', 'personal', 'mixed'
    ) -> List[str]:
        """
        Generate multiple subject line options.
        
        Returns list of subject lines ranked by expected performance.
        """
        if self.ai_backend != 'smart_templates':
            return self._ai_generate_subjects(company, job_title, hr_name)
        
        subjects = []
        
        # Professional subjects
        professional = [
            f"Application for {job_title} - {self.applicant_name}",
            f"{job_title} Position - {self.experience}+ Years Experience",
            f"Experienced {job_title.split()[0]} Seeking Opportunity at {company}",
        ]
        
        # Attention-grabbing subjects
        attention = [
            f"Ready to Drive Results as Your Next {job_title}",
            f"🎯 {self.first_name} | {job_title} with {self.experience}+ Years Experience",
            f"Let's Talk About {job_title} at {company}",
        ]
        
        # Personal subjects (if HR name known)
        personal = []
        if hr_name and hr_name not in ['HR Team', 'Hiring Team', 'Recruitment', 'Team']:
            personal = [
                f"{hr_name} - {job_title} Application from {self.applicant_name}",
                f"Following Up: {job_title} Opportunity",
            ]
        
        # Value-focused subjects
        value = [
            f"{self.experience} Years of {self._extract_primary_skill()} | {job_title} Application",
            f"Proven {job_title.split()[0]} Ready to Contribute at {company}",
        ]
        
        if strategy == 'professional':
            subjects = professional + value
        elif strategy == 'attention':
            subjects = attention + value
        elif strategy == 'personal':
            subjects = personal + professional if personal else professional
        else:  # mixed
            subjects = attention[:1] + professional[:1] + value[:1]
            if personal:
                subjects.insert(1, personal[0])
        
        return subjects[:4]  # Return top 4 options
    
    def _ai_generate_subjects(self, company: str, job_title: str, hr_name: str) -> List[str]:
        """Use AI to generate subject lines."""
        prompt = f"""Generate 4 compelling email subject lines for a job application.

CONTEXT:
- Applicant: {self.applicant_name}
- Position: {job_title}
- Company: {company}
- HR Name: {hr_name if hr_name else 'Unknown'}
- Experience: {self.experience} years
- Key Skills: {self.skills}

REQUIREMENTS:
- Mix of professional and attention-grabbing
- Under 60 characters each
- No spam trigger words (urgent, act now, free)
- One should include applicant name
- One should highlight experience

Return as JSON array of 4 strings, nothing else."""

        try:
            if self.ai_backend == 'openai':
                import openai
                client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                response = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=200
                )
                result = response.choices[0].message.content
            elif self.ai_backend == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                result = response.text
            
            # Parse JSON
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                return json.loads(json_match.group())[:4]
        except Exception as e:
            logging.warning(f"AI subject generation failed: {e}")
        
        return self.generate_subject_lines(company, job_title, hr_name, 'mixed')
    
    def get_best_subject(self, company: str, job_title: str, hr_name: str = '') -> str:
        """Get the best subject line based on performance data."""
        subjects = self.generate_subject_lines(company, job_title, hr_name)
        
        # Check performance data for similar patterns
        best_patterns = self.performance_data.get('subject_lines', {})
        
        for subject in subjects:
            pattern = self._extract_pattern(subject)
            if pattern in best_patterns and best_patterns[pattern].get('response_rate', 0) > 0.1:
                return subject
        
        # Default to first option
        return subjects[0] if subjects else f"Application for {job_title} - {self.applicant_name}"
    
    def _extract_pattern(self, subject: str) -> str:
        """Extract pattern from subject for performance tracking."""
        # Remove specific names/companies
        pattern = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', subject)
        pattern = re.sub(r'\b[A-Z][a-z]+\b', '[WORD]', pattern)
        return pattern[:50]
    
    def _extract_primary_skill(self) -> str:
        """Extract primary skill from skills list."""
        skills_list = self.skills.split(',') if self.skills else []
        return skills_list[0].strip() if skills_list else 'Professional Skills'
    
    # =========================================================================
    # EMAIL OPENING GENERATION
    # =========================================================================
    
    def generate_opening(
        self,
        company: str,
        job_title: str,
        hr_name: str = '',
        company_info: Dict = None
    ) -> str:
        """
        Generate personalized email opening paragraph.
        """
        if self.ai_backend != 'smart_templates' and company_info:
            return self._ai_generate_opening(company, job_title, hr_name, company_info)
        
        greeting = f"Dear {hr_name}," if hr_name and hr_name not in ['HR Team', 'Hiring Team'] else "Dear Hiring Manager,"
        
        openings = [
            f"""I am writing to express my strong interest in the {job_title} position at {company}. With {self.experience}+ years of experience in {self._extract_primary_skill()}, I am excited about the opportunity to contribute to your team.""",
            
            f"""I was thrilled to discover the {job_title} opening at {company}. My background in {self._extract_primary_skill()} and passion for delivering excellent results make me an ideal candidate for this role.""",
            
            f"""The {job_title} position at {company} immediately caught my attention. With my proven track record in {self._extract_primary_skill()} over the past {self.experience} years, I am confident I can make a meaningful impact on your team.""",
        ]
        
        return f"{greeting}\n\n{random.choice(openings)}"
    
    def _ai_generate_opening(
        self,
        company: str,
        job_title: str,
        hr_name: str,
        company_info: Dict
    ) -> str:
        """Use AI to generate personalized opening."""
        prompt = f"""Write a personalized email opening for a job application.

APPLICANT:
- Name: {self.applicant_name}
- Experience: {self.experience} years
- Skills: {self.skills}

JOB:
- Position: {job_title}
- Company: {company}
- HR Contact: {hr_name if hr_name else 'Hiring Manager'}

COMPANY CONTEXT:
- Industry: {company_info.get('industry', 'Unknown')}
- Recent News: {company_info.get('news', 'None')}
- Values: {company_info.get('values', 'Excellence and innovation')}

Write 2-3 sentences that:
1. Show you researched the company
2. Connect your skills to their needs
3. Express genuine interest

Return only the opening paragraph text."""

        try:
            if self.ai_backend == 'openai':
                import openai
                client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                response = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"AI opening generation failed: {e}")
        
        return self.generate_opening(company, job_title, hr_name)
    
    # =========================================================================
    # FULL EMAIL GENERATION
    # =========================================================================
    
    def generate_full_email(
        self,
        company: str,
        job_title: str,
        cover_letter: str,
        hr_name: str = '',
        include_portfolio: bool = False
    ) -> Dict[str, str]:
        """
        Generate complete personalized email.
        
        Returns:
        {
            'subject': str,
            'body': str,
            'follow_up_subject': str
        }
        """
        subject = self.get_best_subject(company, job_title, hr_name)
        
        # Build email body
        greeting = f"Dear {hr_name}," if hr_name and hr_name not in ['HR Team', 'Hiring Team'] else "Dear Hiring Manager,"
        
        body = f"""{greeting}

{cover_letter}

I have attached my resume for your consideration. I would welcome the opportunity to discuss how my skills and experience align with {company}'s needs.

Thank you for your time and consideration. I look forward to hearing from you."""

        # Add portfolio links if requested
        if include_portfolio:
            portfolio_section = self._get_portfolio_section()
            if portfolio_section:
                body += f"\n\n{portfolio_section}"
        
        body += f"""

Best regards,
{self.applicant_name}
{USER_DETAILS.get('phone', '')}
{USER_DETAILS.get('linkedin_url', '')}"""

        # Generate follow-up subject
        follow_up_subject = f"Following Up: {job_title} Application - {self.applicant_name}"
        
        return {
            'subject': subject,
            'body': body,
            'follow_up_subject': follow_up_subject
        }
    
    def _get_portfolio_section(self) -> str:
        """Get portfolio links section."""
        links = []
        
        github = USER_DETAILS.get('github_url') or os.getenv('APPLICANT_GITHUB', '')
        portfolio = USER_DETAILS.get('portfolio_url') or os.getenv('APPLICANT_PORTFOLIO', '')
        kaggle = USER_DETAILS.get('kaggle_url') or os.getenv('APPLICANT_KAGGLE', '')
        
        if github:
            links.append(f"GitHub: {github}")
        if portfolio:
            links.append(f"Portfolio: {portfolio}")
        if kaggle:
            links.append(f"Kaggle: {kaggle}")
        
        if links:
            return "My Work:\n" + "\n".join(links)
        return ""
    
    # =========================================================================
    # PERFORMANCE TRACKING
    # =========================================================================
    
    def track_send(self, email: str, subject: str, company: str):
        """Track email send for performance analysis."""
        pattern = self._extract_pattern(subject)
        
        if pattern not in self.performance_data['subject_lines']:
            self.performance_data['subject_lines'][pattern] = {
                'sent_count': 0,
                'response_count': 0,
                'response_rate': 0
            }
        
        self.performance_data['subject_lines'][pattern]['sent_count'] += 1
        self._save_performance_data()
    
    def track_response(self, email: str, subject: str):
        """Track response for performance analysis."""
        pattern = self._extract_pattern(subject)
        
        if pattern in self.performance_data['subject_lines']:
            data = self.performance_data['subject_lines'][pattern]
            data['response_count'] += 1
            data['response_rate'] = data['response_count'] / data['sent_count']
            self._save_performance_data()
    
    def get_performance_report(self) -> str:
        """Get performance report."""
        report = "\n📊 EMAIL PERFORMANCE REPORT\n"
        report += "="*50 + "\n"
        
        subjects = self.performance_data.get('subject_lines', {})
        
        if not subjects:
            report += "No performance data yet.\n"
            return report
        
        # Sort by response rate
        sorted_subjects = sorted(
            subjects.items(),
            key=lambda x: x[1].get('response_rate', 0),
            reverse=True
        )
        
        for pattern, data in sorted_subjects[:5]:
            rate = data.get('response_rate', 0) * 100
            sent = data.get('sent_count', 0)
            report += f"  {rate:.1f}% response | Sent: {sent} | Pattern: {pattern[:30]}...\n"
        
        return report


class AICompanyResearcher:
    """
    🔍 AI-Powered Company Research
    
    Gathers information about companies for personalization:
    - Recent news
    - Company culture
    - Key products/services
    - Hiring trends
    """
    
    def __init__(self):
        self.cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'company_research_cache.json'
        )
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except:
            pass
    
    def research_company(self, company: str) -> Dict:
        """
        Research company for personalization.
        """
        # Check cache
        cache_key = company.lower().replace(' ', '_')
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Check if cache is fresh (< 7 days)
            if cached.get('researched_at', ''):
                try:
                    researched = datetime.fromisoformat(cached['researched_at'])
                    if datetime.now() - researched < timedelta(days=7):
                        return cached
                except:
                    pass
        
        # Basic research (no API needed)
        info = {
            'company': company,
            'industry': self._guess_industry(company),
            'values': 'Innovation, Excellence, Teamwork',
            'news': '',
            'researched_at': datetime.now().isoformat()
        }
        
        # Try web search for more info (if available)
        try:
            info.update(self._web_research(company))
        except:
            pass
        
        # Cache result
        self.cache[cache_key] = info
        self._save_cache()
        
        return info
    
    def _guess_industry(self, company: str) -> str:
        """Guess industry from company name."""
        company_lower = company.lower()
        
        tech_keywords = ['tech', 'soft', 'data', 'cloud', 'ai', 'digital', 'labs']
        design_keywords = ['design', 'interior', 'architect', 'studio', 'creative']
        finance_keywords = ['bank', 'finance', 'capital', 'invest', 'insurance']
        
        if any(kw in company_lower for kw in tech_keywords):
            return 'Technology'
        elif any(kw in company_lower for kw in design_keywords):
            return 'Design & Architecture'
        elif any(kw in company_lower for kw in finance_keywords):
            return 'Finance'
        return 'Business'
    
    def _web_research(self, company: str) -> Dict:
        """Basic web research."""
        # This would use DuckDuckGo or similar for real research
        return {}


def main():
    """Test email personalization."""
    personalizer = AIEmailPersonalizer()
    
    # Generate subjects
    subjects = personalizer.generate_subject_lines(
        company="Tech Corp",
        job_title="Data Analyst",
        hr_name="Priya Sharma"
    )
    
    print("\n📧 GENERATED SUBJECT LINES:")
    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s}")
    
    # Generate full email
    email = personalizer.generate_full_email(
        company="Tech Corp",
        job_title="Data Analyst",
        cover_letter="I am excited about this opportunity...",
        hr_name="Priya Sharma"
    )
    
    print(f"\n📧 BEST SUBJECT: {email['subject']}")
    print(f"\n📧 EMAIL BODY:\n{email['body'][:500]}...")


if __name__ == '__main__':
    main()
