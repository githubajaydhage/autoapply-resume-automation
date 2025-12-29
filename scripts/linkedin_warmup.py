#!/usr/bin/env python3
"""
LinkedIn Warm-Up System
Generates LinkedIn connection requests and messages to warm up leads before email outreach.
This significantly increases response rates by creating familiarity.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import csv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.config import USER_DETAILS
except ImportError:
    USER_DETAILS = {}


class LinkedInProfileFinder:
    """Find LinkedIn profiles for hiring managers and recruiters."""
    
    # Common LinkedIn URL patterns
    LINKEDIN_PATTERNS = [
        r'linkedin\.com/in/([a-zA-Z0-9\-]+)',
        r'linkedin\.com/company/([a-zA-Z0-9\-]+)',
    ]
    
    # Title patterns for hiring decision makers
    DECISION_MAKER_TITLES = [
        'hiring manager', 'talent acquisition', 'recruiter', 'hr manager',
        'engineering manager', 'tech lead', 'head of engineering',
        'vp engineering', 'director of engineering', 'cto', 'founder',
        'people operations', 'hr business partner', 'talent partner'
    ]
    
    @classmethod
    def extract_linkedin_from_jd(cls, description: str) -> List[str]:
        """
        Extract LinkedIn URLs from job description.
        
        Args:
            description: Job description text
            
        Returns:
            List of LinkedIn profile/company URLs
        """
        urls = []
        for pattern in cls.LINKEDIN_PATTERNS:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                urls.append(f"https://linkedin.com/in/{match}")
        return urls
    
    @classmethod
    def generate_search_query(cls, company: str, role: str = "recruiter") -> str:
        """
        Generate LinkedIn search query to find relevant people.
        
        Args:
            company: Company name
            role: Type of person to find
            
        Returns:
            Search query string
        """
        return f'"{company}" {role} site:linkedin.com/in'


class ConnectionRequestGenerator:
    """Generate personalized LinkedIn connection requests."""
    
    # Templates for different scenarios (max 300 chars for connection requests)
    CONNECTION_TEMPLATES = {
        'recruiter_cold': [
            "Hi {name}! I'm a {role} interested in opportunities at {company}. Would love to connect and learn about the team culture.",
            "Hello {name}, I came across {company}'s job posting and I'm impressed by your work. Keen to connect!",
            "Hi {name}! Exploring {role} roles and {company} caught my attention. Would be great to connect.",
        ],
        'hiring_manager': [
            "Hi {name}! I'm a {role} with {years}+ years experience. Interested in {company}'s engineering team. Would love to connect!",
            "Hello {name}, I've been following {company}'s growth. As a {role}, I'd love to learn more about your team.",
        ],
        'mutual_connection': [
            "Hi {name}! We have mutual connections and I'm interested in {role} opportunities at {company}. Would love to connect!",
            "Hello {name}, noticed we share connections. I'm exploring {role} roles and {company} looks exciting!",
        ],
        'after_application': [
            "Hi {name}! I recently applied for the {job_title} role at {company}. Would love to connect and learn more about the team!",
            "Hello {name}, I've applied for a {role} position at {company}. Looking forward to potentially connecting!",
        ],
        'referral_request': [
            "Hi {name}! I'm interested in {job_title} at {company}. Would you be open to a quick chat about the team?",
            "Hello {name}, exploring opportunities at {company}. Would appreciate any insights about the engineering culture!",
        ],
    }
    
    @classmethod
    def generate_connection_request(
        cls,
        template_type: str,
        recruiter_name: str,
        company: str,
        role: str = "Software Engineer",
        years_experience: int = 5,
        job_title: str = ""
    ) -> str:
        """
        Generate a personalized connection request.
        
        Args:
            template_type: Type of template to use
            recruiter_name: Name of person to connect with
            company: Company name
            role: Candidate's role
            years_experience: Years of experience
            job_title: Specific job title applied for
            
        Returns:
            Connection request message (max 300 chars)
        """
        templates = cls.CONNECTION_TEMPLATES.get(template_type, cls.CONNECTION_TEMPLATES['recruiter_cold'])
        
        # Rotate through templates
        template_idx = hash(f"{recruiter_name}{company}") % len(templates)
        template = templates[template_idx]
        
        # Get first name
        first_name = recruiter_name.split()[0] if recruiter_name else "there"
        
        message = template.format(
            name=first_name,
            company=company,
            role=role,
            years=years_experience,
            job_title=job_title or role
        )
        
        # Ensure under 300 characters
        if len(message) > 300:
            message = message[:297] + "..."
        
        return message


class LinkedInMessageGenerator:
    """Generate follow-up messages for connected contacts."""
    
    # Templates for InMail/messages after connecting
    MESSAGE_TEMPLATES = {
        'thank_you_connect': """
Hi {name}!

Thank you for connecting! I'm {my_name}, a {role} with {years}+ years of experience in {skills}.

I noticed {company} is hiring for {job_title}. I'm very interested in this opportunity and would love to learn more about the role and team.

Would you be open to a brief call to discuss? I'm flexible on timing.

Thanks!
{my_name}
""",
        'express_interest': """
Hi {name}!

I hope this message finds you well. I recently came across the {job_title} position at {company} and I'm very excited about it.

My background in {skills} aligns well with what you're looking for. I've attached my resume for your reference.

Would you have 15 minutes for a quick chat about the role?

Best regards,
{my_name}
""",
        'follow_up_application': """
Hi {name}!

I wanted to follow up on my application for the {job_title} role at {company} that I submitted last week.

I'm very enthusiastic about this opportunity given my experience with {skills}. I'd love to discuss how I can contribute to the team.

Looking forward to hearing from you!

Best,
{my_name}
""",
        'ask_for_referral': """
Hi {name}!

Thank you for connecting. I noticed you work at {company} and I'm very interested in the {job_title} role.

My background in {skills} seems like a good fit. Would you be open to referring me for this position?

Happy to share my resume and any other details needed.

Thanks so much!
{my_name}
""",
        'informational_interview': """
Hi {name}!

I'm exploring opportunities in {role} and really admire what {company} is building.

I'd love to learn more about the engineering culture and your experience there. Would you have 15-20 minutes for a quick virtual coffee chat?

No pressure at all - I understand you're busy!

Thanks,
{my_name}
"""
    }
    
    @classmethod
    def generate_message(
        cls,
        message_type: str,
        recruiter_name: str,
        company: str,
        job_title: str,
        my_name: str = None,
        role: str = "Software Engineer",
        years_experience: int = 5,
        skills: str = ""
    ) -> str:
        """
        Generate a personalized LinkedIn message.
        
        Args:
            message_type: Type of message template
            recruiter_name: Recipient's name
            company: Company name
            job_title: Job title
            my_name: Candidate's name
            role: Candidate's role
            years_experience: Years of experience
            skills: Key skills
            
        Returns:
            Formatted message
        """
        template = cls.MESSAGE_TEMPLATES.get(
            message_type, 
            cls.MESSAGE_TEMPLATES['express_interest']
        )
        
        if not my_name:
            my_name = USER_DETAILS.get('name', 'Candidate')
        
        if not skills:
            skills = USER_DETAILS.get('key_skills', 'Python, Data Engineering, Cloud')
        
        first_name = recruiter_name.split()[0] if recruiter_name else "there"
        
        return template.format(
            name=first_name,
            my_name=my_name,
            company=company,
            job_title=job_title,
            role=role,
            years=years_experience,
            skills=skills
        ).strip()


class LinkedInOutreachTracker:
    """Track LinkedIn outreach activities."""
    
    def __init__(self, tracker_path: str = 'data/linkedin_outreach.csv'):
        """Initialize tracker with file path."""
        self.tracker_path = tracker_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create tracker file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.tracker_path), exist_ok=True)
        if not os.path.exists(self.tracker_path):
            with open(self.tracker_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'date', 'profile_url', 'name', 'company', 'title',
                    'action', 'message_type', 'status', 'job_applied'
                ])
    
    def log_outreach(
        self,
        profile_url: str,
        name: str,
        company: str,
        title: str,
        action: str,
        message_type: str = "",
        job_applied: str = ""
    ):
        """
        Log a LinkedIn outreach activity.
        
        Args:
            profile_url: LinkedIn profile URL
            name: Person's name
            company: Company name
            title: Person's title
            action: Action taken (connect_request, message, inmail)
            message_type: Type of message template used
            job_applied: Job that triggered this outreach
        """
        with open(self.tracker_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                profile_url,
                name,
                company,
                title,
                action,
                message_type,
                'sent',
                job_applied
            ])
    
    def get_recent_outreach(self, days: int = 7) -> List[Dict]:
        """Get outreach activities from last N days."""
        if not os.path.exists(self.tracker_path):
            return []
        
        recent = []
        cutoff = datetime.now() - timedelta(days=days)
        
        with open(self.tracker_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    log_date = datetime.strptime(row['date'], '%Y-%m-%d %H:%M')
                    if log_date >= cutoff:
                        recent.append(row)
                except:
                    continue
        
        return recent
    
    def already_contacted(self, profile_url: str) -> bool:
        """Check if profile was already contacted."""
        if not os.path.exists(self.tracker_path):
            return False
        
        with open(self.tracker_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('profile_url', '').lower() == profile_url.lower():
                    return True
        
        return False


class LinkedInWarmUpStrategy:
    """Orchestrate LinkedIn warm-up before email outreach."""
    
    # Recommended sequence for maximum response
    WARMUP_SEQUENCE = [
        {'day': 0, 'action': 'view_profile', 'description': 'View their profile (they get notified)'},
        {'day': 1, 'action': 'follow', 'description': 'Follow their activity'},
        {'day': 2, 'action': 'engage', 'description': 'Like/comment on their post'},
        {'day': 3, 'action': 'connect', 'description': 'Send connection request'},
        {'day': 5, 'action': 'message', 'description': 'Send LinkedIn message'},
        {'day': 7, 'action': 'email', 'description': 'Send email (now they recognize you)'},
    ]
    
    @classmethod
    def generate_warmup_plan(
        cls,
        recruiter_name: str,
        company: str,
        job_title: str,
        profile_url: str = ""
    ) -> Dict:
        """
        Generate a warm-up plan for a specific recruiter.
        
        Args:
            recruiter_name: Recruiter's name
            company: Company name
            job_title: Job being applied for
            profile_url: LinkedIn profile URL
            
        Returns:
            Warm-up plan with daily actions
        """
        my_name = USER_DETAILS.get('name', 'Candidate')
        role = USER_DETAILS.get('target_role', 'Software Engineer')
        years = 5  # Default
        
        plan = {
            'recruiter': recruiter_name,
            'company': company,
            'job_title': job_title,
            'profile_url': profile_url,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'actions': []
        }
        
        for step in cls.WARMUP_SEQUENCE:
            action_date = datetime.now() + timedelta(days=step['day'])
            
            action = {
                'day': step['day'],
                'date': action_date.strftime('%Y-%m-%d'),
                'action': step['action'],
                'description': step['description'],
            }
            
            # Generate content for actions that need it
            if step['action'] == 'connect':
                action['message'] = ConnectionRequestGenerator.generate_connection_request(
                    'recruiter_cold',
                    recruiter_name,
                    company,
                    role
                )
            elif step['action'] == 'message':
                action['message'] = LinkedInMessageGenerator.generate_message(
                    'thank_you_connect',
                    recruiter_name,
                    company,
                    job_title,
                    my_name
                )
            
            plan['actions'].append(action)
        
        return plan
    
    @classmethod
    def generate_batch_warmup_plans(
        cls,
        targets: List[Dict],
        output_path: str = 'data/linkedin_warmup_plans.txt'
    ) -> str:
        """
        Generate warm-up plans for multiple targets.
        
        Args:
            targets: List of dicts with recruiter info
            output_path: Where to save the plans
            
        Returns:
            Path to saved file
        """
        lines = [
            "=" * 70,
            "LINKEDIN WARM-UP STRATEGY PLAYBOOK",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total Targets: {len(targets)}",
            "",
            "📌 STRATEGY: Warm up leads on LinkedIn before email outreach",
            "📌 GOAL: Create familiarity so emails get 3x higher response rate",
            "",
            "=" * 70,
        ]
        
        for i, target in enumerate(targets, 1):
            plan = cls.generate_warmup_plan(
                target.get('name', 'Recruiter'),
                target.get('company', 'Company'),
                target.get('job_title', 'Position'),
                target.get('profile_url', '')
            )
            
            lines.extend([
                "",
                f"TARGET #{i}: {plan['recruiter']} at {plan['company']}",
                f"Job: {plan['job_title']}",
                f"Profile: {plan['profile_url'] or 'Search on LinkedIn'}",
                "-" * 50,
            ])
            
            for action in plan['actions']:
                lines.append(f"  Day {action['day']} ({action['date']}): {action['description']}")
                if 'message' in action:
                    lines.append(f"    Message Preview: {action['message'][:100]}...")
            
            lines.append("")
        
        lines.extend([
            "=" * 70,
            "QUICK TIPS FOR SUCCESS",
            "=" * 70,
            "1. Space out connection requests (max 20-30 per day)",
            "2. Personalize every connection request",
            "3. Engage with their content genuinely before reaching out",
            "4. Use LinkedIn Premium for InMails to non-connections",
            "5. Best times to send: Tuesday-Thursday, 8-10 AM or 5-6 PM",
            "6. Follow up if no response after 5-7 days",
            "7. Thank people who accept your connection",
            "",
        ])
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"LinkedIn warm-up plans saved to: {output_path}")
        return output_path


def generate_linkedin_search_targets(jobs_df, output_path: str = 'data/linkedin_search_targets.txt'):
    """
    Generate LinkedIn search queries to find recruiters for each job.
    
    Args:
        jobs_df: DataFrame with job listings
        output_path: Where to save search queries
    """
    lines = [
        "=" * 70,
        "LINKEDIN SEARCH TARGETS",
        "=" * 70,
        "Use these search queries on LinkedIn to find recruiters/hiring managers",
        "",
    ]
    
    companies_processed = set()
    
    for idx, row in jobs_df.iterrows():
        company = row.get('company', 'Unknown')
        if company in companies_processed or not company or company == 'Unknown':
            continue
        
        companies_processed.add(company)
        
        lines.extend([
            f"\n📌 {company}",
            f"   Recruiter Search: {LinkedInProfileFinder.generate_search_query(company, 'recruiter')}",
            f"   Hiring Manager: {LinkedInProfileFinder.generate_search_query(company, 'engineering manager')}",
            f"   HR Search: {LinkedInProfileFinder.generate_search_query(company, 'talent acquisition')}",
        ])
    
    lines.extend([
        "",
        "=" * 70,
        "SEARCH TIPS",
        "=" * 70,
        "1. Use LinkedIn's search filters: Location, Company, Title",
        "2. Look for '2nd degree' connections for warm intros",
        "3. Check who posted the job on the company's LinkedIn page",
        "4. Look for 'hiring' or 'we're growing' posts from company employees",
        "",
    ])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"LinkedIn search targets saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("LINKEDIN WARM-UP SYSTEM DEMO")
    print("=" * 60)
    
    # Generate sample connection request
    request = ConnectionRequestGenerator.generate_connection_request(
        'recruiter_cold',
        'Priya Sharma',
        'Razorpay',
        'Data Engineer',
        5
    )
    print(f"\nSample Connection Request ({len(request)} chars):")
    print(request)
    
    # Generate sample message
    message = LinkedInMessageGenerator.generate_message(
        'thank_you_connect',
        'Priya Sharma',
        'Razorpay',
        'Senior Data Engineer',
        'John Doe',
        'Data Engineer',
        5,
        'Python, Spark, AWS, Airflow'
    )
    print(f"\nSample LinkedIn Message:")
    print(message)
    
    # Generate warm-up plan
    plan = LinkedInWarmUpStrategy.generate_warmup_plan(
        'Priya Sharma',
        'Razorpay',
        'Senior Data Engineer',
        'https://linkedin.com/in/priya-sharma'
    )
    print(f"\nWarm-Up Plan for {plan['recruiter']}:")
    for action in plan['actions']:
        print(f"  Day {action['day']}: {action['description']}")
