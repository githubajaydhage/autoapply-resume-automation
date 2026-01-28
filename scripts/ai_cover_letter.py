"""
🤖 AI COVER LETTER GENERATOR - Highly Personalized Cover Letters

Uses AI to generate cover letters that:
1. Match your experience to job requirements
2. Include company-specific personalization
3. Highlight relevant achievements
4. Adapt tone based on company culture
5. Include talking points for specific skills

Supports: OpenAI GPT-4, Google Gemini, Ollama, Claude

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
from typing import Dict, Optional, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AICoverLetterGenerator:
    """
    🤖 AI-Powered Cover Letter Generator
    
    Generates highly personalized cover letters using:
    - Job description analysis
    - Resume skill matching
    - Company research
    - Tone adaptation
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        self.output_path = os.path.join(self.base_path, 'cover_letters')
        os.makedirs(self.output_path, exist_ok=True)
        
        # AI Configuration
        self.ai_backend = self._detect_ai_backend()
        
        # User info
        self.applicant_name = USER_DETAILS.get('full_name') or os.getenv('APPLICANT_NAME', '')
        self.experience = USER_DETAILS.get('years_experience') or os.getenv('YEARS_EXPERIENCE', '3')
        self.skills = USER_DETAILS.get('key_skills') or os.getenv('APPLICANT_SKILLS', os.getenv('JOB_KEYWORDS', ''))
        self.linkedin = USER_DETAILS.get('linkedin_url') or os.getenv('APPLICANT_LINKEDIN', '')
        self.phone = USER_DETAILS.get('phone') or os.getenv('APPLICANT_PHONE', '')
        self.email = USER_DETAILS.get('email') or os.getenv('SENDER_EMAIL', '')
        
        # Templates cache
        self.templates_cache = {}
        
        logging.info(f"🤖 AI Cover Letter Generator initialized (backend: {self.ai_backend})")
    
    def _detect_ai_backend(self) -> str:
        """Detect available AI backend."""
        if os.getenv('OPENAI_API_KEY'):
            return 'openai'
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            return 'gemini'
        if os.getenv('ANTHROPIC_API_KEY'):
            return 'claude'
        if os.getenv('OLLAMA_HOST'):
            return 'ollama'
        return 'template'  # Fallback to smart templates
    
    def generate(
        self,
        company: str,
        job_title: str,
        job_description: str = '',
        hr_name: str = '',
        match_info: Dict = None,
        tone: str = 'professional'  # professional, casual, enthusiastic
    ) -> str:
        """
        Generate a personalized cover letter.
        
        Args:
            company: Company name
            job_title: Position title
            job_description: Full job description
            hr_name: HR/Hiring manager name if known
            match_info: From AI Job Matcher (score, skill_match, personalization)
            tone: Writing tone
        
        Returns:
            Generated cover letter text
        """
        logging.info(f"📝 Generating cover letter for {company} - {job_title}")
        
        if self.ai_backend == 'template':
            return self._generate_template_based(company, job_title, job_description, hr_name, match_info)
        else:
            return self._generate_ai_based(company, job_title, job_description, hr_name, match_info, tone)
    
    def _generate_ai_based(
        self,
        company: str,
        job_title: str,
        job_description: str,
        hr_name: str,
        match_info: Dict,
        tone: str
    ) -> str:
        """Generate cover letter using AI."""
        
        # Prepare context
        matched_skills = match_info.get('skill_match', []) if match_info else []
        personalization = match_info.get('personalization', '') if match_info else ''
        
        prompt = f"""Write a compelling cover letter for this job application.

CANDIDATE INFORMATION:
- Name: {self.applicant_name}
- Experience: {self.experience} years
- Key Skills: {self.skills}
- LinkedIn: {self.linkedin}

JOB DETAILS:
- Company: {company}
- Position: {job_title}
- Description: {job_description[:1500] if job_description else 'Not provided'}

MATCHING INSIGHTS:
- Matched Skills: {', '.join(matched_skills[:8]) if matched_skills else 'General match'}
- Why this is a good fit: {personalization}

REQUIREMENTS:
1. Address to: {hr_name if hr_name else 'Hiring Manager'}
2. Tone: {tone}
3. Length: 250-350 words (3-4 paragraphs)
4. Include:
   - Hook: Why you're excited about this specific role/company
   - Match: How your skills align with requirements
   - Achievement: 1-2 specific accomplishments relevant to this role
   - Call to action: Express enthusiasm for next steps
5. Do NOT include placeholders like [Your Name] - use the actual name provided
6. Do NOT include date, address headers, or "Sincerely" at the end - just the letter body

Write only the cover letter body, nothing else."""

        try:
            if self.ai_backend == 'openai':
                return self._call_openai(prompt)
            elif self.ai_backend == 'gemini':
                return self._call_gemini(prompt)
            elif self.ai_backend == 'claude':
                return self._call_claude(prompt)
            elif self.ai_backend == 'ollama':
                return self._call_ollama(prompt)
        except Exception as e:
            logging.warning(f"AI generation failed: {e}, using template fallback")
            return self._generate_template_based(company, job_title, job_description, hr_name, match_info)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "You are an expert career coach and cover letter writer. Write compelling, personalized cover letters that get interviews."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    def _call_claude(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        response = client.messages.create(
            model=os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307'),
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama (local LLM)."""
        import ollama
        
        response = ollama.chat(
            model=os.getenv('OLLAMA_MODEL', 'llama3.2'),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response['message']['content'].strip()
    
    def _generate_template_based(
        self,
        company: str,
        job_title: str,
        job_description: str,
        hr_name: str,
        match_info: Dict
    ) -> str:
        """Generate cover letter using smart templates."""
        
        # Detect industry
        industry = self._detect_industry(job_title, job_description)
        
        # Get matched skills
        matched_skills = []
        if match_info and match_info.get('skill_match'):
            matched_skills = match_info['skill_match'][:5]
        else:
            # Extract from job description
            matched_skills = self._extract_relevant_skills(job_description)
        
        skills_text = ', '.join(matched_skills) if matched_skills else self.skills
        
        # Greeting
        greeting = f"Dear {hr_name}," if hr_name else "Dear Hiring Manager,"
        
        # Industry-specific templates
        templates = {
            'tech': f"""{greeting}

I am writing to express my strong interest in the {job_title} position at {company}. With {self.experience} years of experience in {skills_text}, I am excited about the opportunity to contribute to your team.

Throughout my career, I have developed expertise in building scalable solutions and delivering impactful results. My technical skills in {skills_text} directly align with the requirements of this role, and I am confident in my ability to make an immediate contribution.

What particularly draws me to {company} is your commitment to innovation and excellence. I am eager to bring my problem-solving abilities and collaborative mindset to your team.

I would welcome the opportunity to discuss how my background and skills would benefit {company}. Thank you for considering my application.

Best regards,
{self.applicant_name}""",

            'design': f"""{greeting}

I am excited to apply for the {job_title} position at {company}. As a creative professional with {self.experience} years of experience in {skills_text}, I am passionate about bringing innovative design solutions to life.

My portfolio demonstrates my expertise in {skills_text}, and I have a proven track record of delivering projects that exceed client expectations. I believe in design that is both aesthetically compelling and functionally excellent.

{company}'s reputation for quality and creativity aligns perfectly with my professional values. I am eager to contribute my skills to your talented team and help bring your vision to life.

I would love the opportunity to discuss how I can contribute to {company}'s continued success. Thank you for your consideration.

Best regards,
{self.applicant_name}""",

            'business': f"""{greeting}

I am writing to apply for the {job_title} position at {company}. With {self.experience} years of experience in {skills_text}, I am well-prepared to contribute to your organization's success.

In my career, I have consistently delivered data-driven insights and strategic recommendations that have improved business outcomes. My analytical skills and attention to detail enable me to identify opportunities and solve complex problems effectively.

I am particularly impressed by {company}'s market position and growth trajectory. I am excited about the opportunity to apply my expertise to help drive continued success.

Thank you for considering my application. I look forward to discussing how I can add value to your team.

Best regards,
{self.applicant_name}""",

            'default': f"""{greeting}

I am writing to express my interest in the {job_title} position at {company}. With {self.experience} years of professional experience, I am confident in my ability to contribute effectively to your team.

My background includes expertise in {skills_text}, which aligns well with the requirements of this role. I am a dedicated professional who takes pride in delivering quality work and exceeding expectations.

I am excited about the opportunity to bring my skills and experience to {company}. I believe my background makes me a strong candidate for this position.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to your team.

Best regards,
{self.applicant_name}"""
        }
        
        return templates.get(industry, templates['default'])
    
    def _detect_industry(self, job_title: str, description: str) -> str:
        """Detect industry from job details."""
        text = f"{job_title} {description}".lower()
        
        tech_keywords = ['software', 'developer', 'engineer', 'data', 'python', 'java', 'cloud', 'devops', 'analyst']
        design_keywords = ['design', 'interior', 'architect', 'autocad', 'creative', 'ui', 'ux', 'graphic']
        business_keywords = ['business', 'analyst', 'manager', 'marketing', 'sales', 'operations', 'finance']
        
        if any(kw in text for kw in tech_keywords):
            return 'tech'
        elif any(kw in text for kw in design_keywords):
            return 'design'
        elif any(kw in text for kw in business_keywords):
            return 'business'
        return 'default'
    
    def _extract_relevant_skills(self, text: str) -> List[str]:
        """Extract relevant skills from text."""
        if not text:
            return []
        
        skill_patterns = [
            r'\b(python|java|sql|excel|tableau|power bi|react|angular|aws|azure)\b',
            r'\b(autocad|revit|sketchup|3ds max|photoshop|figma)\b',
            r'\b(project management|agile|scrum|leadership|communication)\b',
        ]
        
        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, text.lower())
            skills.extend(matches)
        
        return list(set(skills))[:5]
    
    def save_cover_letter(self, company: str, cover_letter: str) -> str:
        """Save cover letter to file."""
        # Clean company name for filename
        safe_company = re.sub(r'[^\w\s-]', '', company)[:30].strip().replace(' ', '_')
        filename = f"cover_letter_{safe_company}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.output_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cover_letter)
        
        return filepath
    
    def generate_batch(self, jobs_df) -> Dict[str, str]:
        """Generate cover letters for multiple jobs."""
        results = {}
        
        for idx, job in jobs_df.iterrows():
            company = job.get('company', 'Unknown')
            job_title = job.get('title', 'Position')
            description = job.get('description', '')
            
            # Get match info if available
            match_info = {
                'skill_match': job.get('matched_skills', '').split(', ') if job.get('matched_skills') else [],
                'personalization': job.get('personalization', '')
            }
            
            cover_letter = self.generate(
                company=company,
                job_title=job_title,
                job_description=description,
                match_info=match_info
            )
            
            filepath = self.save_cover_letter(company, cover_letter)
            results[company] = filepath
            
            logging.info(f"   ✅ Generated for {company}")
        
        return results


def main():
    """Generate sample cover letters."""
    generator = AICoverLetterGenerator()
    
    # Test generation
    cover_letter = generator.generate(
        company="Tech Innovations Ltd",
        job_title="Senior Data Analyst",
        job_description="We are looking for a data analyst with SQL, Python, and Tableau experience...",
        match_info={
            'skill_match': ['python', 'sql', 'tableau'],
            'personalization': 'Strong technical match with data analysis requirements'
        }
    )
    
    print("\n📝 GENERATED COVER LETTER:")
    print("="*60)
    print(cover_letter)
    print("="*60)
    
    # Save it
    filepath = generator.save_cover_letter("Tech Innovations Ltd", cover_letter)
    print(f"\n💾 Saved to: {filepath}")


if __name__ == '__main__':
    main()
