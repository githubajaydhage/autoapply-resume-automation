"""
Interview Success Suite - Maximize interview-to-offer conversion
Features:
1. Skills Match Filter - Only apply to 70%+ match jobs
2. Interview Prep Generator - Auto-create company research
3. Thank You Email Automation - Post-interview follow-up
4. Weekly Summary Digest - Activity report
"""

import os
import sys
import re
import json
import logging
import smtplib
import ssl
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class SkillsMatchFilter:
    """Filter jobs based on skills match percentage."""
    
    def __init__(self):
        # Candidate's skills from config or default
        self.candidate_skills = self._load_candidate_skills()
        
        # Minimum match threshold (70% = high quality applications only)
        self.min_match_threshold = 0.70
    
    def _load_candidate_skills(self) -> set:
        """Load candidate's skills."""
        # Core skills - customize based on your profile
        skills = {
            # Programming
            'python', 'sql', 'r', 'excel', 'vba',
            # Data Analysis
            'data analysis', 'data analytics', 'business analysis',
            'statistical analysis', 'data visualization',
            # Tools
            'tableau', 'power bi', 'looker', 'excel',
            'pandas', 'numpy', 'matplotlib', 'seaborn',
            # Databases
            'mysql', 'postgresql', 'mongodb', 'sql server',
            # Cloud
            'aws', 'azure', 'gcp', 'google cloud',
            # Soft skills
            'communication', 'problem solving', 'analytical',
            'team player', 'stakeholder management',
            # Domain
            'machine learning', 'statistics', 'etl', 'data pipeline',
            'reporting', 'dashboard', 'kpi', 'metrics',
        }
        return skills
    
    def extract_job_skills(self, job_title: str, job_description: str = '') -> set:
        """Extract required skills from job posting."""
        text = f"{job_title} {job_description}".lower()
        
        # Common skill keywords to look for
        skill_keywords = {
            'python', 'sql', 'r', 'java', 'scala', 'spark',
            'tableau', 'power bi', 'looker', 'excel', 'vba',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn',
            'tensorflow', 'pytorch', 'keras', 'machine learning', 'ml',
            'deep learning', 'nlp', 'computer vision',
            'aws', 'azure', 'gcp', 'google cloud', 'cloud',
            'mysql', 'postgresql', 'mongodb', 'oracle', 'sql server',
            'etl', 'data pipeline', 'airflow', 'kafka',
            'data analysis', 'data analytics', 'business intelligence', 'bi',
            'statistics', 'statistical', 'regression', 'hypothesis testing',
            'dashboard', 'reporting', 'visualization',
            'agile', 'scrum', 'jira', 'confluence',
            'communication', 'presentation', 'stakeholder',
        }
        
        found_skills = set()
        for skill in skill_keywords:
            if skill in text:
                found_skills.add(skill)
        
        return found_skills
    
    def calculate_match_score(self, job_title: str, job_description: str = '') -> dict:
        """Calculate how well candidate matches the job."""
        job_skills = self.extract_job_skills(job_title, job_description)
        
        if not job_skills:
            # If no skills detected, assume moderate match
            return {
                'score': 0.6,
                'matching_skills': [],
                'missing_skills': [],
                'recommendation': 'apply'
            }
        
        matching = self.candidate_skills.intersection(job_skills)
        missing = job_skills - self.candidate_skills
        
        score = len(matching) / len(job_skills) if job_skills else 0.5
        
        if score >= 0.8:
            recommendation = 'strong_apply'
        elif score >= 0.7:
            recommendation = 'apply'
        elif score >= 0.5:
            recommendation = 'consider'
        else:
            recommendation = 'skip'
        
        return {
            'score': score,
            'matching_skills': list(matching),
            'missing_skills': list(missing),
            'recommendation': recommendation
        }
    
    def filter_jobs(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter jobs to only include good matches."""
        if jobs_df.empty:
            return jobs_df
        
        filtered_jobs = []
        
        for _, job in jobs_df.iterrows():
            title = job.get('title', '')
            description = job.get('description', job.get('skills', ''))
            
            match = self.calculate_match_score(title, description)
            
            if match['score'] >= self.min_match_threshold:
                job_dict = job.to_dict()
                job_dict['match_score'] = match['score']
                job_dict['matching_skills'] = ', '.join(match['matching_skills'][:5])
                filtered_jobs.append(job_dict)
        
        result_df = pd.DataFrame(filtered_jobs)
        
        # Sort by match score
        if not result_df.empty and 'match_score' in result_df.columns:
            result_df = result_df.sort_values('match_score', ascending=False)
        
        logging.info(f"🎯 Skills Filter: {len(filtered_jobs)}/{len(jobs_df)} jobs match 70%+ skills")
        
        return result_df


class InterviewPrepGenerator:
    """Generate interview preparation materials when interview is detected."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prep_dir = os.path.join(self.base_path, 'interview_prep')
        os.makedirs(self.prep_dir, exist_ok=True)
        
        # Company research data
        self.company_data = {
            'razorpay': {
                'about': 'Leading Indian fintech, payment gateway, unicorn status',
                'founded': '2014',
                'founders': 'Harshil Mathur, Shashank Kumar',
                'culture': 'Fast-paced, innovative, ownership-driven',
                'interview_focus': 'Problem solving, SQL, Python, business cases',
                'glassdoor_rating': '4.1',
            },
            'phonepe': {
                'about': 'Largest UPI player, Walmart-backed, 500M+ users',
                'founded': '2015',
                'founders': 'Sameer Nigam, Rahul Chari, Burzin Engineer',
                'culture': 'Customer-first, data-driven, scale-focused',
                'interview_focus': 'System design, analytics, SQL, product sense',
                'glassdoor_rating': '4.0',
            },
            'swiggy': {
                'about': 'Food delivery + quick commerce leader, Instamart',
                'founded': '2014',
                'founders': 'Sriharsha Majety, Nandan Reddy',
                'culture': 'Fast execution, customer obsession, growth mindset',
                'interview_focus': 'SQL, analytics, case studies, metrics',
                'glassdoor_rating': '3.9',
            },
            'zomato': {
                'about': 'Food tech, public company, Blinkit quick commerce',
                'founded': '2008',
                'founders': 'Deepinder Goyal, Pankaj Chaddah',
                'culture': 'Data-driven, transparent, experimental',
                'interview_focus': 'SQL, Python, product metrics, AB testing',
                'glassdoor_rating': '3.8',
            },
            'flipkart': {
                'about': 'E-commerce leader, Walmart-owned, Big Billion Days',
                'founded': '2007',
                'founders': 'Sachin Bansal, Binny Bansal',
                'culture': 'Customer-first, bold bets, ownership',
                'interview_focus': 'SQL, analytics, case studies, system design',
                'glassdoor_rating': '4.0',
            },
            'google': {
                'about': 'Search, Cloud, AI leader, great culture',
                'founded': '1998',
                'founders': 'Larry Page, Sergey Brin',
                'culture': 'Innovation, 20% time, data-driven decisions',
                'interview_focus': 'Coding, SQL, analytics, behavioral (Googleyness)',
                'glassdoor_rating': '4.4',
            },
            'microsoft': {
                'about': 'Cloud leader, AI with OpenAI, enterprise software',
                'founded': '1975',
                'founders': 'Bill Gates, Paul Allen',
                'culture': 'Growth mindset, inclusive, learn-it-all',
                'interview_focus': 'Coding, system design, behavioral, SQL',
                'glassdoor_rating': '4.3',
            },
            'amazon': {
                'about': 'E-commerce + AWS cloud giant',
                'founded': '1994',
                'founders': 'Jeff Bezos',
                'culture': 'Customer obsession, ownership, bias for action',
                'interview_focus': 'Leadership principles, SQL, coding, system design',
                'glassdoor_rating': '3.9',
            },
        }
    
    def generate_prep_document(self, company: str, job_title: str) -> str:
        """Generate interview prep document for a company."""
        company_lower = company.lower().strip()
        
        # Find matching company data
        company_info = None
        for key, data in self.company_data.items():
            if key in company_lower or company_lower in key:
                company_info = data
                break
        
        prep_content = f"""
================================================================================
🎯 INTERVIEW PREPARATION: {company.upper()} - {job_title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
================================================================================

📋 COMPANY OVERVIEW
-------------------
"""
        
        if company_info:
            prep_content += f"""
• About: {company_info['about']}
• Founded: {company_info['founded']}
• Founders: {company_info['founders']}
• Culture: {company_info['culture']}
• Glassdoor Rating: {company_info['glassdoor_rating']}/5
• Interview Focus: {company_info['interview_focus']}
"""
        else:
            prep_content += f"""
• Research {company} on LinkedIn, Glassdoor, and their website
• Look up recent news and funding announcements
• Understand their products and services
"""
        
        prep_content += f"""

🎤 COMMON INTERVIEW QUESTIONS FOR {job_title.upper()}
-----------------------------------------------------

1. BEHAVIORAL QUESTIONS:
   • Tell me about yourself (2-min pitch focused on relevant experience)
   • Why {company}? (Show you researched the company)
   • Describe a challenging project you worked on
   • How do you handle tight deadlines?
   • Tell me about a time you disagreed with your manager

2. TECHNICAL QUESTIONS (Data/Analytics):
   • SQL: Write a query to find top 5 customers by revenue
   • SQL: Explain window functions (ROW_NUMBER, RANK, LAG, LEAD)
   • Python: How would you clean a dataset with missing values?
   • Statistics: Explain A/B testing and statistical significance
   • Case: How would you measure success of a new feature?

3. PRODUCT/BUSINESS QUESTIONS:
   • What metrics would you track for {company}'s main product?
   • How would you improve {company}'s user experience?
   • Design a dashboard for the leadership team

📊 YOUR TALKING POINTS
----------------------

Based on your profile, emphasize:
• {USER_DETAILS.get('years_experience', '3')}+ years of experience
• Key skills: Python, SQL, Data Visualization
• Quantified achievements (use numbers!)
• Relevant projects and their impact

💡 PRO TIPS
-----------

• Research the interviewer on LinkedIn before the call
• Prepare 3-4 questions to ask the interviewer
• Use STAR method for behavioral answers (Situation, Task, Action, Result)
• Have your resume and portfolio ready to share screen
• Test your video/audio 10 minutes before
• Keep water nearby

📞 LOGISTICS
------------

• Join 5 minutes early
• Have a clean, professional background
• Good lighting on your face
• Mute when not speaking
• Smile and maintain eye contact with camera

================================================================================
Good luck! 🍀
================================================================================
"""
        
        # Save to file
        safe_company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')
        safe_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
        filename = f"interview_prep_{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.join(self.prep_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prep_content)
        
        logging.info(f"📝 Generated interview prep: {filepath}")
        
        return prep_content
    
    def generate_for_all_interviews(self):
        """Generate prep docs for all detected interview requests."""
        interviews_path = os.path.join(
            os.path.dirname(self.prep_dir), 'data', 'interview_requests.csv'
        )
        
        if not os.path.exists(interviews_path):
            logging.info("No interview requests found")
            return
        
        interviews_df = pd.read_csv(interviews_path)
        
        for _, interview in interviews_df.iterrows():
            company = interview.get('company', interview.get('from_email', '').split('@')[1].split('.')[0])
            job_title = interview.get('job_title', 'Data Analyst')
            
            self.generate_prep_document(company, job_title)


class ThankYouEmailSystem:
    """Send thank you emails after interviews."""
    
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = USER_DETAILS.get('email', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.sender_name = USER_DETAILS.get('full_name', '')
        
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.thank_you_log = os.path.join(self.base_path, 'data', 'thank_you_log.csv')
    
    def generate_thank_you_email(self, 
                                 interviewer_name: str,
                                 company: str,
                                 job_title: str,
                                 interview_topic: str = '') -> tuple:
        """Generate a personalized thank you email."""
        
        subject = f"Thank You - {job_title} Interview at {company}"
        
        if interviewer_name and interviewer_name != 'Hiring Manager':
            greeting = f"Dear {interviewer_name},"
        else:
            greeting = "Dear Hiring Team,"
        
        body = f"""{greeting}

Thank you so much for taking the time to speak with me today about the {job_title} position at {company}. I truly enjoyed our conversation and learning more about the role and team.

I'm even more excited about the opportunity after our discussion. {f"Our conversation about {interview_topic} was particularly interesting, and I can see how my experience would be valuable in this area." if interview_topic else "The role aligns perfectly with my skills and career goals."}

I'm confident that my experience in data analysis, along with my passion for deriving actionable insights, would allow me to make meaningful contributions to {company}.

Please don't hesitate to reach out if you need any additional information from my end. I look forward to hearing about the next steps.

Thank you again for the opportunity.

Best regards,
{self.sender_name}
{USER_DETAILS.get('phone', '')}
{USER_DETAILS.get('linkedin_url', '')}"""

        return subject, body
    
    def send_thank_you(self,
                       recipient_email: str,
                       interviewer_name: str,
                       company: str,
                       job_title: str) -> bool:
        """Send thank you email."""
        if not self.sender_password:
            logging.error("SENDER_PASSWORD not configured")
            return False
        
        subject, body = self.generate_thank_you_email(
            interviewer_name, company, job_title
        )
        
        try:
            message = MIMEMultipart()
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = recipient_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            logging.info(f"✅ Thank you email sent to {recipient_email}")
            
            # Log it
            self._log_thank_you(recipient_email, company, job_title)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send thank you email: {e}")
            return False
    
    def _log_thank_you(self, email: str, company: str, job_title: str):
        """Log thank you email."""
        log_entry = {
            'recipient_email': email,
            'company': company,
            'job_title': job_title,
            'sent_at': datetime.now().isoformat()
        }
        
        if os.path.exists(self.thank_you_log):
            df = pd.read_csv(self.thank_you_log)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.thank_you_log, index=False)


class WeeklySummaryDigest:
    """Generate weekly summary of job application activity."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
    
    def generate_summary(self) -> str:
        """Generate a comprehensive weekly summary."""
        
        summary = []
        summary.append("="*60)
        summary.append("📊 WEEKLY JOB APPLICATION SUMMARY")
        summary.append(f"   Week of: {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        summary.append("="*60)
        
        # Sent emails
        sent_path = os.path.join(self.data_path, 'sent_emails_log.csv')
        if os.path.exists(sent_path):
            sent_df = pd.read_csv(sent_path)
            # Filter to last 7 days
            sent_df['sent_at'] = pd.to_datetime(sent_df['sent_at'], errors='coerce')
            # Remove timezone for safe comparison
            sent_df['sent_at'] = sent_df['sent_at'].dt.tz_localize(None)
            week_ago = datetime.now() - timedelta(days=7)
            recent = sent_df[sent_df['sent_at'].notna() & (sent_df['sent_at'] >= week_ago)]
            
            summary.append(f"\n📤 EMAILS SENT THIS WEEK: {len(recent)}")
            if not recent.empty:
                by_company = recent['company'].value_counts().head(5)
                summary.append("   Top companies:")
                for company, count in by_company.items():
                    summary.append(f"   • {company}: {count}")
        
        # Replies received
        replies_path = os.path.join(self.data_path, 'hr_replies.csv')
        if os.path.exists(replies_path):
            replies_df = pd.read_csv(replies_path)
            summary.append(f"\n📬 REPLIES RECEIVED: {len(replies_df)}")
            if 'category' in replies_df.columns:
                by_category = replies_df['category'].value_counts()
                for cat, count in by_category.items():
                    emoji = '🎯' if 'INTERVIEW' in cat else '📧'
                    summary.append(f"   {emoji} {cat}: {count}")
        
        # Interview requests
        interviews_path = os.path.join(self.data_path, 'interview_requests.csv')
        if os.path.exists(interviews_path):
            interviews_df = pd.read_csv(interviews_path)
            summary.append(f"\n🎯 INTERVIEW REQUESTS: {len(interviews_df)}")
            for _, interview in interviews_df.head(5).iterrows():
                company = interview.get('company', 'Unknown')
                summary.append(f"   🏆 {company}")
        
        # Bounced emails
        bounced_path = os.path.join(self.data_path, 'bounced_emails.csv')
        if os.path.exists(bounced_path):
            bounced_df = pd.read_csv(bounced_path)
            summary.append(f"\n❌ BOUNCED EMAILS: {len(bounced_df)}")
        
        # Application tracker status
        tracker_path = os.path.join(self.data_path, 'application_tracker.csv')
        if os.path.exists(tracker_path):
            tracker_df = pd.read_csv(tracker_path)
            summary.append(f"\n📊 APPLICATION STATUS:")
            if 'status' in tracker_df.columns:
                status_counts = tracker_df['status'].value_counts()
                for status, count in status_counts.items():
                    icon = {
                        'applied': '📤',
                        'acknowledged': '📥',
                        'interviewing': '🎯',
                        'offered': '🏆',
                        'rejected': '❌',
                        'no_response': '⏰'
                    }.get(status, '📋')
                    summary.append(f"   {icon} {status}: {count}")
        
        # Response rate calculation
        summary.append(f"\n📈 KEY METRICS:")
        if os.path.exists(sent_path) and os.path.exists(replies_path):
            sent_total = len(pd.read_csv(sent_path))
            replies_total = len(pd.read_csv(replies_path))
            if sent_total > 0:
                response_rate = (replies_total / sent_total) * 100
                summary.append(f"   Response Rate: {response_rate:.1f}%")
        
        # Tips based on performance
        summary.append(f"\n💡 RECOMMENDATIONS:")
        summary.append("   • Follow up on applications older than 3 days")
        summary.append("   • Apply to more 70%+ skill match jobs")
        summary.append("   • Send applications Tue-Thu 9-11 AM for best response")
        
        summary.append("\n" + "="*60)
        
        return '\n'.join(summary)
    
    def save_summary(self) -> str:
        """Save weekly summary to file."""
        summary = self.generate_summary()
        
        summary_path = os.path.join(
            self.data_path, 
            f"weekly_summary_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logging.info(f"📊 Weekly summary saved: {summary_path}")
        
        return summary


def main():
    """Run all interview success suite features."""
    logging.info("="*60)
    logging.info("🎯 INTERVIEW SUCCESS SUITE")
    logging.info("="*60)
    
    # Generate interview prep for any detected interviews
    prep_gen = InterviewPrepGenerator()
    prep_gen.generate_for_all_interviews()
    
    # Generate weekly summary
    digest = WeeklySummaryDigest()
    summary = digest.generate_summary()
    print(summary)
    digest.save_summary()
    
    logging.info("="*60)
    logging.info("✅ Interview Success Suite Complete")
    logging.info("="*60)


if __name__ == "__main__":
    main()
