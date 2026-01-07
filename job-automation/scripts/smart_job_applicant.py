#!/usr/bin/env python3
"""
Smart Job Application System
Uses specific HR emails and applies to jobs correctly
Fixes: Generic email targeting and low response rates
"""

import csv
import os
import sys
import smtplib
import ssl
import time
import logging
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class SmartJobApplicant:
    """
    Smart job application system that:
    1. Uses specific HR emails (not generic)
    2. Personalizes each application
    3. Tracks application status
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Input/Output files
        self.jobs_file = self.data_dir / "jobs_today.csv"
        self.sent_emails_file = self.data_dir / "sent_emails_log.csv"
        self.applications_file = self.data_dir / "applications_sent_today.csv"
        
        # Email configuration
        self.sender_email = os.getenv('SENDER_EMAIL') or os.getenv('GMAIL_USER')
        self.sender_password = os.getenv('SENDER_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Applicant details
        self.applicant_name = os.getenv('APPLICANT_NAME', 'Job Seeker')
        self.applicant_email = os.getenv('APPLICANT_EMAIL', self.sender_email)
        self.years_experience = os.getenv('YEARS_EXPERIENCE', '3')
        self.skills = os.getenv('APPLICANT_SKILLS', 'Python, Data Analysis, Machine Learning')
        
        # Application tracking
        self.sent_today = []
        self.successful_applications = []
        self.failed_applications = []
        
        # Load previously sent emails to avoid duplicates
        self.previously_sent = self.load_previously_sent()
        
    def load_previously_sent(self) -> set:
        """Load previously sent emails to avoid duplicates."""
        sent_emails = set()
        
        if self.sent_emails_file.exists():
            with open(self.sent_emails_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row.get('recipient_email', '').strip().lower()
                    if email:
                        sent_emails.add(email)
        
        logging.info(f"📧 Loaded {len(sent_emails)} previously sent emails (will skip duplicates)")
        return sent_emails
    
    def apply_to_jobs(self, max_applications: int = 5) -> bool:
        """Apply to jobs with specific HR emails."""
        
        if not self.jobs_file.exists():
            logging.error("❌ No jobs file found!")
            return False
        
        # Validate email credentials
        if not self.validate_email_credentials():
            return False
        
        # Load jobs with HR emails
        with open(self.jobs_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_jobs = list(reader)
        
        # Filter jobs that have HR emails and haven't been applied to
        applicable_jobs = []
        for job in all_jobs:
            hr_email = job.get('primary_hr_email', '').strip().lower()
            if hr_email and hr_email not in self.previously_sent:
                applicable_jobs.append(job)
        
        if not applicable_jobs:
            logging.warning("⚠️ No new jobs to apply to (all already sent or no HR emails)")
            return False
        
        logging.info(f"🎯 Found {len(applicable_jobs)} jobs ready for application")
        
        # Limit applications per run
        jobs_to_apply = applicable_jobs[:max_applications]
        logging.info(f"📨 Applying to {len(jobs_to_apply)} jobs this run")
        
        # Apply to each job
        for i, job in enumerate(jobs_to_apply, 1):
            logging.info(f"\\n📧 Application {i}/{len(jobs_to_apply)}: {job.get('company', '')}")
            
            success = self.send_application_email(job)
            
            if success:
                self.successful_applications.append(job)
                logging.info(f"✅ Successfully applied to {job.get('company', '')}")
            else:
                self.failed_applications.append(job)
                logging.error(f"❌ Failed to apply to {job.get('company', '')}")
            
            # Rate limiting between emails
            if i < len(jobs_to_apply):
                time.sleep(2)
        
        # Save application results
        self.save_application_results()
        
        # Print summary
        self.print_application_summary()
        
        return len(self.successful_applications) > 0
    
    def validate_email_credentials(self) -> bool:
        """Validate email credentials before sending."""
        
        if not self.sender_email or not self.sender_password:
            logging.error("❌ Email credentials not set!")
            logging.error("Set SENDER_EMAIL and SENDER_PASSWORD environment variables")
            return False
        
        try:
            logging.info("🔍 Validating email credentials...")
            
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls(context=context)
            server.login(self.sender_email, self.sender_password)
            server.quit()
            
            logging.info("✅ Email credentials validated successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Email credential validation failed: {e}")
            return False
    
    def send_application_email(self, job: Dict) -> bool:
        """Send personalized application email for a specific job."""
        
        company = job.get('company', 'Company')
        job_title = job.get('title', 'Position')
        hr_email = job.get('primary_hr_email', '').strip()
        
        if not hr_email:
            logging.error(f"❌ No HR email for {company}")
            return False
        
        try:
            # Create personalized email
            subject = self.generate_email_subject(job_title, company)
            body = self.generate_email_body(job, hr_email)
            
            # Create email message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = hr_email
            message["Subject"] = subject
            
            # Add body
            message.attach(MIMEText(body, "plain"))
            
            # Send email
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls(context=context)
            server.login(self.sender_email, self.sender_password)
            
            text = message.as_string()
            server.sendmail(self.sender_email, hr_email, text)
            server.quit()
            
            # Log successful send
            self.log_sent_email(hr_email, company, job_title, 'sent')
            
            logging.info(f"📧 Email sent to {hr_email} for {company} - {job_title}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send email to {hr_email}: {e}")
            self.log_sent_email(hr_email, company, job_title, f'failed: {str(e)[:100]}')
            return False
    
    def generate_email_subject(self, job_title: str, company: str) -> str:
        """Generate personalized email subject."""
        
        subjects = [
            f"Application for {job_title} Position at {company}",
            f"Experienced {job_title} - Application for {company}",
            f"Interest in {job_title} Role - {self.applicant_name}",
            f"Application: {job_title} Position - {self.years_experience}+ Years Experience"
        ]
        
        # Use first subject for now (can be randomized later)
        return subjects[0]
    
    def generate_email_body(self, job: Dict, hr_email: str) -> str:
        """Generate personalized email body."""
        
        company = job.get('company', 'Company')
        job_title = job.get('title', 'Position')
        
        # Determine greeting based on email
        if 'university' in hr_email or 'campus' in hr_email or 'college' in hr_email:
            greeting = "Dear University Recruiting Team"
            context = "I am excited to apply for campus recruitment opportunities"
        elif 'careers' in hr_email:
            greeting = "Dear Careers Team"
            context = "I am writing to express my interest in career opportunities"
        elif 'recruiting' in hr_email or 'talent' in hr_email:
            greeting = "Dear Recruiting Team"
            context = "I am interested in exploring opportunities"
        else:
            greeting = "Dear Hiring Manager"
            context = "I am writing to express my interest in the available position"
        
        body = f'''
{greeting},

{context} at {company}, specifically for the {job_title} position.

With {self.years_experience}+ years of experience in {self.skills}, I am confident in my ability to contribute effectively to your team. I have hands-on experience in data analysis, problem-solving, and delivering results in fast-paced environments.

Key qualifications:
• {self.years_experience}+ years of professional experience
• Strong technical skills in {self.skills}
• Proven track record of delivering quality work
• Excellent communication and teamwork abilities

I would welcome the opportunity to discuss how my background and enthusiasm can contribute to {company}'s continued success. I am available for an interview at your convenience and can start immediately.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{self.applicant_name}
Email: {self.applicant_email}
Experience: {self.years_experience}+ years

Note: This email was sent to {hr_email} as the designated contact for {company} opportunities.
'''.strip()
        
        return body
    
    def log_sent_email(self, recipient: str, company: str, job_title: str, status: str) -> None:
        """Log sent email to tracking file."""
        
        log_entry = {
            'recipient_email': recipient,
            'company': company,
            'job_title': job_title,
            'sent_at': datetime.now().isoformat(),
            'status': status
        }
        
        # Append to sent emails log
        file_exists = self.sent_emails_file.exists()
        
        with open(self.sent_emails_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['recipient_email', 'company', 'job_title', 'sent_at', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(log_entry)
    
    def save_application_results(self) -> None:
        """Save today's application results."""
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        all_applications = self.successful_applications + self.failed_applications
        
        if not all_applications:
            return
        
        # Save applications sent today
        with open(self.applications_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['company', 'job_title', 'hr_email', 'status', 'applied_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in self.successful_applications:
                writer.writerow({
                    'company': job.get('company', ''),
                    'job_title': job.get('title', ''),
                    'hr_email': job.get('primary_hr_email', ''),
                    'status': 'sent',
                    'applied_at': today
                })
            
            for job in self.failed_applications:
                writer.writerow({
                    'company': job.get('company', ''),
                    'job_title': job.get('title', ''),
                    'hr_email': job.get('primary_hr_email', ''),
                    'status': 'failed',
                    'applied_at': today
                })
    
    def print_application_summary(self) -> None:
        """Print application summary."""
        
        total = len(self.successful_applications) + len(self.failed_applications)
        success_count = len(self.successful_applications)
        
        print("\\n" + "="*50)
        print("📊 APPLICATION SUMMARY")
        print("="*50)
        print(f"Total applications attempted: {total}")
        print(f"Successful applications: {success_count}")
        print(f"Failed applications: {len(self.failed_applications)}")
        print(f"Success rate: {(success_count/total*100):.1f}%" if total > 0 else "Success rate: 0%")
        
        if self.successful_applications:
            print("\\n✅ SUCCESSFUL APPLICATIONS:")
            for job in self.successful_applications:
                print(f"  • {job.get('company', '')} - {job.get('title', '')}")
        
        if self.failed_applications:
            print("\\n❌ FAILED APPLICATIONS:")
            for job in self.failed_applications:
                print(f"  • {job.get('company', '')} - {job.get('title', '')}")
        
        print("="*50)

def main():
    """Main function to run smart job applications."""
    
    print("🚀 SMART JOB APPLICATION SYSTEM")
    print("="*50)
    print("Uses specific HR emails and personalized applications")
    print()
    
    applicant = SmartJobApplicant()
    
    # Apply to jobs (limit to 3 per run to avoid overwhelming)
    max_apps = 3
    success = applicant.apply_to_jobs(max_applications=max_apps)
    
    if success:
        print(f"\\n🎯 Applications completed! Check sent_emails_log.csv for details.")
        print("💡 TIP: Run this script again later to apply to more jobs")
        print("📊 Monitor dashboard for response tracking")
    else:
        print("\\n⚠️ No applications sent. Check logs for issues.")

if __name__ == "__main__":
    main()