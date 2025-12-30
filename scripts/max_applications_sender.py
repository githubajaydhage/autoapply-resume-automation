#!/usr/bin/env python3
"""
⚡ MAXIMUM APPLICATIONS SENDER
Send as many applications as possible, as fast as possible.

This is the AGGRESSIVE mode - use when you need interviews ASAP!
"""

import os
import sys
import csv
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MaxApplicationsSender:
    """Send maximum applications quickly"""
    
    def __init__(self):
        # Email config
        self.sender_email = os.getenv('SENDER_EMAIL') or os.getenv('GMAIL_USER')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Applicant info
        self.applicant_name = os.getenv('APPLICANT_NAME', 'Job Seeker')
        self.applicant_email = os.getenv('APPLICANT_EMAIL', self.sender_email)
        self.applicant_phone = os.getenv('APPLICANT_PHONE', '')
        self.applicant_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        self.years_experience = os.getenv('YEARS_EXPERIENCE', '3')
        self.skills = os.getenv('APPLICANT_SKILLS', '')
        self.target_role = os.getenv('APPLICANT_TARGET_ROLE', 'Professional')
        
        # Resume
        self.resume_path = os.getenv('RESUME_PATH', 'resumes/resume.pdf')
        
        # Files
        self.jobs_file = Path("data/jobs_today.csv")
        self.applied_file = Path("data/applied_log.csv")
        self.hr_emails_file = Path("data/hr_emails_master.csv")
        
        # Stats
        self.sent = 0
        self.failed = 0
        self.skipped = 0
        
        # AI provider
        self.ai = None
        try:
            from scripts.free_ai_providers import FreeAIManager
            self.ai = FreeAIManager()
        except:
            pass
    
    def get_all_hr_emails(self) -> List[Dict]:
        """Get all HR emails from all sources"""
        
        emails = []
        seen = set()
        
        # 1. From jobs_today.csv
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = row.get('email', '').strip()
                        if email and email not in seen and '@' in email:
                            seen.add(email)
                            emails.append({
                                'email': email,
                                'company': row.get('company', ''),
                                'title': row.get('title', self.target_role),
                                'source': 'jobs_today'
                            })
            except:
                pass
        
        # 2. From curated HR database
        try:
            from scripts.curated_hr_database import get_all_hr_emails
            for email in get_all_hr_emails():
                if email not in seen:
                    seen.add(email)
                    company = email.split('@')[1].split('.')[0].title()
                    emails.append({
                        'email': email,
                        'company': company,
                        'title': self.target_role,
                        'source': 'curated'
                    })
        except:
            pass
        
        # 3. From advanced HR discovery
        try:
            from scripts.advanced_hr_discovery import AdvancedHRDiscovery
            discovery = AdvancedHRDiscovery()
            for email in discovery.get_all_emails():
                if email not in seen:
                    seen.add(email)
                    company = email.split('@')[1].split('.')[0].title()
                    emails.append({
                        'email': email,
                        'company': company,
                        'title': self.target_role,
                        'source': 'advanced'
                    })
        except:
            pass
        
        # 4. From master HR emails file
        if self.hr_emails_file.exists():
            try:
                with open(self.hr_emails_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = row.get('email', '').strip()
                        if email and email not in seen and '@' in email:
                            seen.add(email)
                            emails.append({
                                'email': email,
                                'company': row.get('company', ''),
                                'title': self.target_role,
                                'source': 'master_db'
                            })
            except:
                pass
        
        print(f"📧 Found {len(emails)} unique HR emails")
        return emails
    
    def get_already_applied(self) -> set:
        """Get emails we've already applied to"""
        
        applied = set()
        
        if self.applied_file.exists():
            try:
                with open(self.applied_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = row.get('email', '').strip().lower()
                        if email:
                            applied.add(email)
            except:
                pass
        
        print(f"📋 Already applied to {len(applied)} emails")
        return applied
    
    def generate_subject(self, job: Dict) -> str:
        """Generate compelling email subject"""
        
        title = job.get('title', self.target_role)
        company = job.get('company', '')
        
        subjects = [
            f"Application for {title} - {self.applicant_name}",
            f"{self.applicant_name} - {self.years_experience}+ Years {title}",
            f"Experienced {title} Available - {self.applicant_name}",
            f"{title} Position - {self.applicant_name} | {self.years_experience} Years Exp",
        ]
        
        # Use AI if available
        if self.ai and random.random() > 0.5:
            try:
                prompt = f"Write ONE compelling email subject line (max 10 words) for {title} job application at {company}. Just the subject, no quotes."
                ai_subject = self.ai.generate(prompt, max_tokens=30)
                if ai_subject and len(ai_subject) < 100:
                    return ai_subject.strip().strip('"').strip("'")
            except:
                pass
        
        return random.choice(subjects)
    
    def generate_email_body(self, job: Dict) -> str:
        """Generate personalized email body"""
        
        title = job.get('title', self.target_role)
        company = job.get('company', 'your esteemed organization')
        
        # Use AI if available
        if self.ai:
            try:
                prompt = f"""Write a brief, professional job application email (80-100 words):
- Position: {title}
- Company: {company}  
- Applicant: {self.applicant_name}
- Experience: {self.years_experience} years
- Key Skills: {self.skills[:100] if self.skills else 'relevant domain expertise'}

Be enthusiastic, specific, professional. Include a call to action.
End with applicant name only, no regards/best wishes.
"""
                body = self.ai.generate(prompt, max_tokens=250)
                if body and len(body) > 50:
                    return body.strip()
            except:
                pass
        
        # Fallback template
        skill_list = self.skills.split(',')[0] if self.skills else 'this domain'
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}.

With {self.years_experience} years of experience in {skill_list}, I have developed expertise that I believe would be valuable to your team. I am passionate about delivering results and would welcome the opportunity to contribute to {company}'s success.

I have attached my resume for your review. I would be grateful for the opportunity to discuss how my background aligns with your requirements.

Thank you for considering my application.

{self.applicant_name}
{self.applicant_phone}
{self.applicant_linkedin}"""
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   attach_resume: bool = True) -> bool:
        """Send a single email"""
        
        if not self.sender_email or not self.sender_password:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.applicant_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Reply-To'] = self.applicant_email
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach resume
            if attach_resume and os.path.exists(self.resume_path):
                with open(self.resume_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    
                    filename = os.path.basename(self.resume_path)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"  ❌ Send failed: {str(e)[:50]}")
            return False
    
    def log_application(self, job: Dict, status: str = 'sent'):
        """Log application to file"""
        
        self.applied_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ['date', 'email', 'company', 'title', 'status', 'followup_date', 'source']
        
        file_exists = self.applied_file.exists()
        
        with open(self.applied_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'email': job.get('email', ''),
                'company': job.get('company', ''),
                'title': job.get('title', ''),
                'status': status,
                'followup_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'source': job.get('source', 'direct')
            })
    
    def run(self, max_emails: int = 50, delay_min: int = 20, delay_max: int = 45):
        """Send applications to all HR emails"""
        
        print("\n" + "="*60)
        print("⚡ MAXIMUM APPLICATIONS SENDER")
        print("="*60)
        
        if not self.sender_email or not self.sender_password:
            print("\n❌ ERROR: Email credentials not configured!")
            print("Set environment variables:")
            print("  - GMAIL_USER (or SENDER_EMAIL)")
            print("  - GMAIL_APP_PASSWORD")
            return
        
        print(f"\n👤 From: {self.applicant_name} <{self.sender_email}>")
        print(f"🎯 Target Role: {self.target_role}")
        print(f"📄 Resume: {self.resume_path}")
        print(f"⏱️ Delay: {delay_min}-{delay_max}s between emails")
        
        # Get all HR emails
        all_emails = self.get_all_hr_emails()
        
        # Get already applied
        applied = self.get_already_applied()
        
        # Filter out already applied
        to_send = [e for e in all_emails if e['email'].lower() not in applied]
        
        print(f"\n📤 Will send to {min(len(to_send), max_emails)} emails (max: {max_emails})")
        
        if not to_send:
            print("⚠️ No new emails to send to!")
            return
        
        # Confirm
        print(f"\n{'─'*60}")
        input("Press ENTER to start sending (Ctrl+C to cancel)...")
        print(f"{'─'*60}\n")
        
        # Send emails
        for i, job in enumerate(to_send[:max_emails], 1):
            email = job['email']
            company = job.get('company', 'Unknown')
            
            print(f"[{i}/{min(len(to_send), max_emails)}] {email[:40]}...", end=" ")
            
            # Generate email
            subject = self.generate_subject(job)
            body = self.generate_email_body(job)
            
            # Send
            success = self.send_email(email, subject, body)
            
            if success:
                self.sent += 1
                self.log_application(job, 'sent')
                print("✅ Sent")
            else:
                self.failed += 1
                self.log_application(job, 'failed')
            
            # Rate limiting - be nice to email servers
            if i < len(to_send[:max_emails]):
                delay = random.uniform(delay_min, delay_max)
                print(f"    ⏳ Waiting {delay:.0f}s...")
                time.sleep(delay)
        
        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"  ✅ Sent: {self.sent}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  📋 Total processed: {self.sent + self.failed}")
        print(f"\n  📁 Log: {self.applied_file}")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    sender = MaxApplicationsSender()
    
    # Get max emails from environment or default
    max_emails = int(os.getenv('MAX_EMAILS_PER_RUN', '30'))
    
    sender.run(max_emails=max_emails)


if __name__ == "__main__":
    main()
