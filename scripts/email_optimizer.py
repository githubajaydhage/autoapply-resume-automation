"""
Email Optimizer - Maximize interview response rates
Features:
1. Optimal send timing (Tue-Thu, 9-11 AM local time)
2. Personalized company openers (recent news, funding, achievements)
3. Email open/click tracking
4. Recruiter name finder
5. A/B subject line testing
"""

import os
import sys
import re
import json
import random
import logging
import hashlib
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class OptimalSendTimer:
    """Determines the best time to send emails for maximum response."""
    
    # Research-backed optimal send windows (in local time)
    OPTIMAL_DAYS = [1, 2, 3]  # Tuesday, Wednesday, Thursday (0=Monday)
    OPTIMAL_HOURS = [(9, 11), (14, 16)]  # 9-11 AM and 2-4 PM
    
    # Days to avoid
    AVOID_DAYS = [5, 6]  # Saturday, Sunday
    
    def __init__(self):
        self.timezone = 'Asia/Kolkata'  # IST
    
    def is_optimal_time(self) -> Tuple[bool, str]:
        """Check if current time is optimal for sending emails."""
        now = datetime.now()
        day_of_week = now.weekday()
        hour = now.hour
        
        # Check if it's a good day
        if day_of_week in self.AVOID_DAYS:
            return False, "Weekend - emails have 45% lower response rate"
        
        # Check if it's an optimal day
        is_optimal_day = day_of_week in self.OPTIMAL_DAYS
        
        # Check if it's an optimal hour
        is_optimal_hour = any(start <= hour < end for start, end in self.OPTIMAL_HOURS)
        
        if is_optimal_day and is_optimal_hour:
            return True, "🎯 Optimal time! Tue-Thu 9-11 AM has 40% higher response rate"
        elif is_optimal_day:
            return True, "Good day, but better to send 9-11 AM or 2-4 PM"
        elif is_optimal_hour:
            return True, "Good time window"
        else:
            return True, "Acceptable time"
    
    def get_next_optimal_window(self) -> datetime:
        """Get the next optimal send window."""
        now = datetime.now()
        
        # Find next Tuesday-Thursday at 9:30 AM
        days_ahead = 1 - now.weekday()  # Days until Tuesday
        if days_ahead <= 0:
            days_ahead += 7
        
        next_optimal = now.replace(hour=9, minute=30, second=0, microsecond=0)
        next_optimal += timedelta(days=days_ahead)
        
        return next_optimal
    
    def get_send_recommendation(self) -> dict:
        """Get recommendation for when to send emails."""
        is_optimal, reason = self.is_optimal_time()
        
        return {
            'send_now': is_optimal,
            'reason': reason,
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'next_optimal': self.get_next_optimal_window().strftime('%Y-%m-%d %H:%M'),
            'tips': [
                "Tue-Thu emails get 40% higher response",
                "9-11 AM is peak HR activity time",
                "Avoid Fridays after 3 PM and weekends",
                "Monday mornings are too busy - emails get buried"
            ]
        }


class CompanyPersonalizer:
    """Adds personalized company-specific content to emails."""
    
    def __init__(self):
        self.cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'company_insights_cache.json'
        )
        self.cache = self._load_cache()
        
        # Known company achievements/news (fallback data)
        self.COMPANY_HIGHLIGHTS = {
            'razorpay': ['unicorn status', 'processing $60B annually', 'leading Indian fintech'],
            'phonepe': ['500M+ users', 'largest UPI player', 'Walmart-backed'],
            'swiggy': ['quick commerce leader', 'Instamart success', 'IPO-bound'],
            'zomato': ['profitable quarter', 'Blinkit integration', 'public company'],
            'cred': ['premium fintech', 'innovative rewards', 'Kunal Shah founded'],
            'meesho': ['social commerce leader', 'Softbank-backed', 'tier-2/3 focus'],
            'groww': ['top trading app', 'democratizing investments', '50M+ users'],
            'zerodha': ['bootstrapped unicorn', 'largest broker', 'Nithin Kamath'],
            'freshworks': ['NASDAQ listed', 'SaaS leader', 'Chennai-based global'],
            'flipkart': ['Walmart-owned', 'e-commerce leader', 'Big Billion Days'],
            'paytm': ['digital payments pioneer', 'Vijay Shekhar Sharma', 'fintech ecosystem'],
            'ola': ['mobility leader', 'EV push', 'Bhavish Aggarwal'],
            'byju': ['edtech giant', 'global acquisitions', 'learning app'],
            'infosys': ['IT services leader', 'Narayana Murthy legacy', 'digital transformation'],
            'tcs': ['largest IT company', 'consistent growth', '$200B+ market cap'],
            'wipro': ['IT services major', 'sustainability focus', 'Azim Premji legacy'],
            'google': ['search leader', 'AI innovation', 'great culture'],
            'microsoft': ['cloud leader', 'AI with OpenAI', 'Satya Nadella'],
            'amazon': ['e-commerce & cloud giant', 'AWS leader', 'customer obsession'],
            'meta': ['social media leader', 'metaverse vision', 'AI focus'],
        }
    
    def _load_cache(self) -> dict:
        """Load cached company insights."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        """Save company insights cache."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_company_highlight(self, company: str) -> str:
        """Get a personalized highlight for a company."""
        company_lower = company.lower().strip()
        
        # Check known highlights
        for key, highlights in self.COMPANY_HIGHLIGHTS.items():
            if key in company_lower or company_lower in key:
                highlight = random.choice(highlights)
                return highlight
        
        return None
    
    def generate_personalized_opener(self, company: str, job_title: str) -> str:
        """Generate a personalized email opener based on company."""
        highlight = self.get_company_highlight(company)
        
        openers = []
        
        if highlight:
            openers = [
                f"I've been following {company}'s journey, particularly impressed by {highlight}.",
                f"As someone who admires {company}'s {highlight}, I'm excited to apply.",
                f"{company}'s reputation for {highlight} is what draws me to this opportunity.",
                f"I'm particularly excited about {company} because of {highlight}.",
            ]
        else:
            openers = [
                f"I've been researching {company} and am impressed by the innovative work you're doing.",
                f"{company}'s growth trajectory and industry reputation caught my attention.",
                f"I'm excited about the opportunity to contribute to {company}'s continued success.",
                f"The {job_title} role at {company} aligns perfectly with my career goals.",
            ]
        
        return random.choice(openers)
    
    def get_company_values_mention(self, company: str) -> str:
        """Get company values/culture mention for emails."""
        company_lower = company.lower()
        
        culture_map = {
            'google': "innovation and 20% time for personal projects",
            'microsoft': "growth mindset and inclusive culture",
            'amazon': "customer obsession and ownership",
            'razorpay': "solving real problems for Indian businesses",
            'phonepe': "financial inclusion mission",
            'swiggy': "customer-first approach",
            'zomato': "foodtech innovation",
            'flipkart': "customer experience focus",
            'freshworks': "bootstrapped success story",
        }
        
        for key, value in culture_map.items():
            if key in company_lower:
                return f"I resonate with {company}'s focus on {value}."
        
        return f"I'm drawn to {company}'s culture and growth trajectory."


class RecruiterNameFinder:
    """Finds recruiter/HR names for personalized addressing."""
    
    def __init__(self):
        self.cache = {}
        
        # Common HR name patterns from email addresses
        self.name_patterns = [
            r'^([a-z]+)\.([a-z]+)@',  # john.doe@
            r'^([a-z]+)_([a-z]+)@',   # john_doe@
            r'^([a-z]+)([A-Z][a-z]+)@',  # johnDoe@
        ]
    
    def extract_name_from_email(self, email: str) -> Optional[str]:
        """Extract recruiter name from email address."""
        if not email:
            return None
        
        local_part = email.split('@')[0].lower()
        
        # Skip generic emails
        generic = ['hr', 'careers', 'jobs', 'recruiting', 'recruitment', 'talent', 'hiring']
        if any(g in local_part for g in generic):
            return None
        
        # Try to extract name patterns
        for pattern in self.name_patterns:
            match = re.match(pattern, email.lower())
            if match:
                first_name = match.group(1).capitalize()
                return first_name
        
        # Simple name extraction (first part before numbers/special chars)
        name_match = re.match(r'^([a-z]{3,})', local_part)
        if name_match:
            name = name_match.group(1).capitalize()
            if name not in ['Info', 'Admin', 'Support', 'Contact', 'Help']:
                return name
        
        return None
    
    def get_greeting(self, email: str, company: str) -> str:
        """Get personalized greeting based on email."""
        name = self.extract_name_from_email(email)
        
        if name:
            greetings = [
                f"Dear {name},",
                f"Hi {name},",
                f"Hello {name},",
            ]
            return random.choice(greetings)
        else:
            greetings = [
                "Dear Hiring Manager,",
                "Dear Recruitment Team,",
                f"Dear {company} HR Team,",
                "Dear Talent Acquisition Team,",
            ]
            return random.choice(greetings)


class SubjectLineOptimizer:
    """A/B tests and optimizes email subject lines."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.stats_path = os.path.join(self.base_path, 'data', 'subject_line_stats.csv')
        self.stats = self._load_stats()
    
    def _load_stats(self) -> pd.DataFrame:
        """Load subject line performance stats."""
        if os.path.exists(self.stats_path):
            return pd.read_csv(self.stats_path)
        return pd.DataFrame(columns=[
            'subject_template', 'sent_count', 'reply_count', 'reply_rate'
        ])
    
    def _save_stats(self):
        """Save subject line stats."""
        self.stats.to_csv(self.stats_path, index=False)
    
    def get_optimized_subject(self, job_title: str, company: str, experience: str) -> Tuple[str, str]:
        """
        Get an optimized subject line and track which template was used.
        Returns: (subject, template_id)
        """
        # High-performing subject templates (based on email marketing research)
        templates = {
            'specific_role': f"Application: {job_title} - {experience}+ Years Experience",
            'location_focus': f"{job_title} Application - Bangalore - Immediate Availability",
            'value_prop': f"Experienced {job_title} Seeking {company} Opportunity",
            'direct_ask': f"Interested in {job_title} Role at {company}",
            'achievement': f"{job_title} with Proven Track Record - Application",
            'referral_style': f"Regarding {job_title} Opening at {company}",
            'urgent': f"Immediate Availability: {job_title} Position",
            'personalized': f"{job_title} Candidate - {company} Bangalore",
        }
        
        # Select template - prioritize ones with higher reply rates
        if not self.stats.empty:
            # Use templates with proven success
            best_templates = self.stats.nlargest(3, 'reply_rate')['subject_template'].tolist()
            template_id = random.choice(best_templates) if best_templates else random.choice(list(templates.keys()))
        else:
            # Random selection for initial A/B testing
            template_id = random.choice(list(templates.keys()))
        
        subject = templates.get(template_id, templates['specific_role'])
        
        return subject, template_id
    
    def record_send(self, template_id: str):
        """Record that a subject template was used."""
        if template_id in self.stats['subject_template'].values:
            self.stats.loc[self.stats['subject_template'] == template_id, 'sent_count'] += 1
        else:
            new_row = pd.DataFrame([{
                'subject_template': template_id,
                'sent_count': 1,
                'reply_count': 0,
                'reply_rate': 0.0
            }])
            self.stats = pd.concat([self.stats, new_row], ignore_index=True)
        self._save_stats()
    
    def record_reply(self, template_id: str):
        """Record that a subject template got a reply."""
        if template_id in self.stats['subject_template'].values:
            idx = self.stats['subject_template'] == template_id
            self.stats.loc[idx, 'reply_count'] += 1
            sent = self.stats.loc[idx, 'sent_count'].values[0]
            replies = self.stats.loc[idx, 'reply_count'].values[0]
            self.stats.loc[idx, 'reply_rate'] = (replies / sent) * 100 if sent > 0 else 0
            self._save_stats()


class EmailTracker:
    """Track email opens and link clicks."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tracking_path = os.path.join(self.base_path, 'data', 'email_tracking.csv')
    
    def generate_tracking_id(self, email: str, company: str) -> str:
        """Generate unique tracking ID for an email."""
        data = f"{email}_{company}_{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def get_tracking_pixel_url(self, tracking_id: str) -> str:
        """
        Generate tracking pixel URL.
        Note: Requires a tracking server to be set up.
        For now, returns a placeholder.
        """
        # In production, this would point to your tracking server
        # e.g., https://your-tracking-server.com/pixel/{tracking_id}.gif
        return f"https://via.placeholder.com/1x1.gif?id={tracking_id}"
    
    def get_tracked_link(self, original_url: str, tracking_id: str) -> str:
        """
        Generate tracked link that records clicks.
        Note: Requires a redirect server to be set up.
        """
        # In production, this would be a redirect through your server
        return original_url  # For now, return original
    
    def add_tracking_to_email(self, html_body: str, tracking_id: str) -> str:
        """Add tracking pixel to HTML email body."""
        pixel_url = self.get_tracking_pixel_url(tracking_id)
        tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none" />'
        
        # Add before closing body tag
        if '</body>' in html_body:
            return html_body.replace('</body>', f'{tracking_pixel}</body>')
        else:
            return html_body + tracking_pixel


class EmailOptimizer:
    """Main class that combines all optimization features."""
    
    def __init__(self):
        self.timer = OptimalSendTimer()
        self.personalizer = CompanyPersonalizer()
        self.name_finder = RecruiterNameFinder()
        self.subject_optimizer = SubjectLineOptimizer()
        self.tracker = EmailTracker()
    
    def optimize_email(self, 
                      recipient_email: str,
                      company: str,
                      job_title: str,
                      experience: str = "3") -> dict:
        """
        Optimize all aspects of an email for maximum response rate.
        Returns dict with optimized components.
        """
        # Check timing
        timing = self.timer.get_send_recommendation()
        
        # Get personalized greeting
        greeting = self.name_finder.get_greeting(recipient_email, company)
        
        # Get personalized opener
        opener = self.personalizer.generate_personalized_opener(company, job_title)
        
        # Get culture mention
        culture = self.personalizer.get_company_values_mention(company)
        
        # Get optimized subject
        subject, template_id = self.subject_optimizer.get_optimized_subject(
            job_title, company, experience
        )
        
        # Generate tracking ID
        tracking_id = self.tracker.generate_tracking_id(recipient_email, company)
        
        return {
            'greeting': greeting,
            'opener': opener,
            'culture_mention': culture,
            'subject': subject,
            'subject_template_id': template_id,
            'tracking_id': tracking_id,
            'timing': timing,
            'is_optimal_time': timing['send_now'],
        }
    
    def generate_optimized_body(self,
                               recipient_email: str,
                               company: str,
                               job_title: str,
                               applicant_name: str,
                               applicant_phone: str,
                               applicant_linkedin: str,
                               applicant_experience: str,
                               applicant_skills: str,
                               applicant_github: str = '',
                               applicant_portfolio: str = '',
                               applicant_projects: str = '',
                               include_portfolio: bool = False) -> str:
        """Generate a fully optimized email body with optional portfolio links."""
        
        optimization = self.optimize_email(
            recipient_email, company, job_title, applicant_experience
        )
        
        # Build portfolio section only if enabled and links available
        portfolio_section = ""
        if include_portfolio and (applicant_github or applicant_portfolio or applicant_projects):
            portfolio_section = "\n📂 View my work:\n"
            if applicant_github:
                portfolio_section += f"   • GitHub: {applicant_github}\n"
            if applicant_portfolio:
                portfolio_section += f"   • Portfolio: {applicant_portfolio}\n"
            if applicant_projects:
                portfolio_section += f"   • Key Projects: {applicant_projects}\n"
        
        body = f"""{optimization['greeting']}

{optimization['opener']}

I am writing to express my strong interest in the {job_title} position at {company}. With {applicant_experience}+ years of experience in {applicant_skills.split(',')[0].strip()}, I am confident in my ability to contribute effectively to your team.

{optimization['culture_mention']}

My key qualifications include:
• Proficient in {applicant_skills}
• Strong analytical and problem-solving abilities
• Excellent communication and collaboration skills
• Proven track record of delivering results
{portfolio_section}
I am based in Bangalore and immediately available. I prefer Remote/Hybrid work arrangements but am flexible and open to all options.

I have attached my resume for your review. I would welcome the opportunity to discuss how my background and skills can benefit {company}.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
{applicant_name}
📍 Location: Bangalore, Karnataka
📞 {applicant_phone}
🔗 LinkedIn: {applicant_linkedin}"""

        return body


def main():
    """Demo the email optimizer."""
    optimizer = EmailOptimizer()
    
    # Example optimization
    result = optimizer.optimize_email(
        recipient_email="priya.sharma@razorpay.com",
        company="Razorpay",
        job_title="Data Analyst",
        experience="3"
    )
    
    print("="*60)
    print("📧 EMAIL OPTIMIZATION RESULT")
    print("="*60)
    print(f"Greeting: {result['greeting']}")
    print(f"Opener: {result['opener']}")
    print(f"Culture: {result['culture_mention']}")
    print(f"Subject: {result['subject']}")
    print(f"Optimal Time: {result['is_optimal_time']} - {result['timing']['reason']}")
    print("="*60)


if __name__ == "__main__":
    main()
