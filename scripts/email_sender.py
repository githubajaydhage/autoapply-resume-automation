"""
Personalized Email Sender - Sends customized job application emails to HR contacts
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import os
import logging
import time
import random
from datetime import datetime
from string import Template

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class PersonalizedEmailSender:
    """Sends personalized job application emails to HR contacts."""
    
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')  # App password for Gmail
        self.sender_name = os.getenv('SENDER_NAME', 'Job Applicant')
        
        # Applicant details
        self.applicant_name = os.getenv('APPLICANT_NAME', 'Your Name')
        self.applicant_phone = os.getenv('APPLICANT_PHONE', '+91-XXXXXXXXXX')
        self.applicant_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        self.applicant_experience = os.getenv('APPLICANT_EXPERIENCE', '3')
        self.applicant_skills = os.getenv('APPLICANT_SKILLS', 'Data Analysis, Python, SQL, Excel, Tableau')
        
        # Resume path
        self.resume_path = os.getenv('RESUME_PATH', os.path.join(
            os.path.dirname(__file__), '..', 'resumes', 'base_resume.pdf'
        ))
        
        # Track sent emails
        self.sent_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'sent_emails_log.csv'
        )
        self.sent_emails = self._load_sent_log()
        
    def _load_sent_log(self) -> set:
        """Load previously sent emails to avoid duplicates."""
        if os.path.exists(self.sent_log_path):
            df = pd.read_csv(self.sent_log_path)
            return set(df['recipient_email'].str.lower())
        return set()
    
    def _save_sent_log(self, recipient_email: str, company: str, job_title: str, status: str):
        """Log sent email."""
        log_entry = {
            'recipient_email': recipient_email,
            'company': company,
            'job_title': job_title,
            'sent_at': datetime.now().isoformat(),
            'status': status
        }
        
        if os.path.exists(self.sent_log_path):
            df = pd.read_csv(self.sent_log_path)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.sent_log_path, index=False)
        self.sent_emails.add(recipient_email.lower())
    
    def generate_email_subject(self, job_title: str, company: str) -> str:
        """Generate a personalized email subject."""
        subjects = [
            f"Application for {job_title} Position at {company}",
            f"Experienced Professional Seeking {job_title} Role at {company}",
            f"{job_title} Opportunity at {company} - {self.applicant_name}",
            f"Interest in {job_title} Position - {self.applicant_experience}+ Years Experience",
            f"Application: {job_title} at {company}",
        ]
        return random.choice(subjects)
    
    def generate_email_body(self, job_title: str, company: str, job_url: str = None) -> str:
        """Generate a personalized email body."""
        
        # Multiple email templates for variety
        templates = [
            # Template 1 - Professional and direct
            """Dear Hiring Manager,

I am writing to express my strong interest in the ${job_title} position at ${company}. With ${experience}+ years of experience in ${skills_area}, I am confident in my ability to contribute effectively to your team.

My key qualifications include:
• Proficient in ${skills}
• Strong analytical and problem-solving abilities
• Excellent communication and collaboration skills
• Proven track record of delivering results

I am particularly drawn to ${company}'s reputation for innovation and excellence in the industry. I believe my skills and experience align well with the requirements of this role.

I have attached my resume for your review. I would welcome the opportunity to discuss how my background and skills can benefit ${company}.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
${name}
${phone}
${linkedin}""",

            # Template 2 - Enthusiastic
            """Dear HR Team,

I recently came across the ${job_title} opening at ${company}, and I am excited to submit my application for this role.

As a professional with ${experience}+ years of experience, I have developed strong expertise in ${skills}. I am passionate about leveraging data and technology to drive business insights and decisions.

What excites me about ${company}:
• Your commitment to innovation and excellence
• The opportunity to work on challenging projects
• The collaborative and growth-oriented culture

I am confident that my skills and enthusiasm make me a strong candidate for this position. Please find my resume attached for your consideration.

I would appreciate the opportunity to discuss how I can contribute to your team's success.

Warm regards,
${name}
Contact: ${phone}
LinkedIn: ${linkedin}""",

            # Template 3 - Concise
            """Dear Recruitment Team,

I am applying for the ${job_title} position at ${company}.

Profile Summary:
• Experience: ${experience}+ years
• Skills: ${skills}
• Education: Relevant degree with continuous learning

I am immediately available and excited about the opportunity to contribute to ${company}'s success.

Please review my attached resume. I look forward to discussing this opportunity with you.

Best regards,
${name}
${phone}"""
        ]
        
        template = Template(random.choice(templates))
        
        # Determine skills area from skills
        skills_list = self.applicant_skills.split(',')
        skills_area = "data analysis and business intelligence" if any('data' in s.lower() or 'analyst' in s.lower() for s in skills_list) else "technology and analytics"
        
        body = template.substitute(
            job_title=job_title,
            company=company,
            experience=self.applicant_experience,
            skills=self.applicant_skills,
            skills_area=skills_area,
            name=self.applicant_name,
            phone=self.applicant_phone,
            linkedin=self.applicant_linkedin if self.applicant_linkedin else "(LinkedIn profile available upon request)"
        )
        
        return body
    
    def create_email_message(self, recipient_email: str, subject: str, body: str, attach_resume: bool = True) -> MIMEMultipart:
        """Create email message with optional resume attachment."""
        message = MIMEMultipart()
        message['From'] = f"{self.sender_name} <{self.sender_email}>"
        message['To'] = recipient_email
        message['Subject'] = subject
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Attach resume if requested and file exists
        if attach_resume and os.path.exists(self.resume_path):
            try:
                with open(self.resume_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                
                filename = os.path.basename(self.resume_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                message.attach(part)
                logging.info(f"📎 Attached resume: {filename}")
            except Exception as e:
                logging.warning(f"Could not attach resume: {e}")
        
        return message
    
    def send_email(self, recipient_email: str, company: str, job_title: str, job_url: str = None) -> bool:
        """Send a personalized email to a single recipient."""
        
        # Skip if already sent
        if recipient_email.lower() in self.sent_emails:
            logging.info(f"⏭️ Skipping {recipient_email} - already contacted")
            return False
        
        # Validate configuration
        if not self.sender_email or not self.sender_password:
            logging.error("❌ SENDER_EMAIL and SENDER_PASSWORD environment variables must be set!")
            logging.error("For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
            return False
        
        try:
            # Generate personalized content
            subject = self.generate_email_subject(job_title, company)
            body = self.generate_email_body(job_title, company, job_url)
            message = self.create_email_message(recipient_email, subject, body)
            
            # Connect and send
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            logging.info(f"✅ Email sent successfully to {recipient_email} ({company})")
            self._save_sent_log(recipient_email, company, job_title, 'sent')
            return True
            
        except smtplib.SMTPAuthenticationError:
            logging.error("❌ SMTP Authentication failed! Check your email and app password.")
            logging.error("For Gmail, enable 2FA and create an App Password.")
            self._save_sent_log(recipient_email, company, job_title, 'auth_failed')
            return False
            
        except Exception as e:
            logging.error(f"❌ Failed to send email to {recipient_email}: {e}")
            self._save_sent_log(recipient_email, company, job_title, f'failed: {str(e)}')
            return False
    
    def send_bulk_emails(self, emails_df: pd.DataFrame, max_emails: int = 50, delay_range: tuple = (30, 60)) -> dict:
        """Send emails to multiple recipients from a DataFrame."""
        
        if emails_df.empty:
            logging.warning("No emails to send!")
            return {'sent': 0, 'failed': 0, 'skipped': 0}
        
        # Filter out already sent
        emails_df = emails_df[~emails_df['hr_email'].str.lower().isin(self.sent_emails)]
        emails_df = emails_df[emails_df['hr_email'].notna()]
        
        if emails_df.empty:
            logging.info("All emails have already been sent!")
            return {'sent': 0, 'failed': 0, 'skipped': 0}
        
        # Limit to max_emails
        emails_to_send = emails_df.head(max_emails)
        
        logging.info(f"📧 Preparing to send {len(emails_to_send)} emails...")
        
        stats = {'sent': 0, 'failed': 0, 'skipped': 0}
        
        for idx, row in emails_to_send.iterrows():
            recipient = row['hr_email']
            company = row.get('company', 'Your Company')
            job_title = row.get('job_title', 'Open Position')
            job_url = row.get('job_url', '')
            
            logging.info(f"📤 Sending email {stats['sent'] + stats['failed'] + 1}/{len(emails_to_send)} to {recipient}")
            
            success = self.send_email(recipient, company, job_title, job_url)
            
            if success:
                stats['sent'] += 1
            else:
                if recipient.lower() in self.sent_emails:
                    stats['skipped'] += 1
                else:
                    stats['failed'] += 1
            
            # Random delay between emails to avoid spam detection
            if idx < len(emails_to_send) - 1:
                delay = random.uniform(*delay_range)
                logging.info(f"⏳ Waiting {delay:.0f} seconds before next email...")
                time.sleep(delay)
        
        logging.info(f"\n📊 Email Campaign Summary:")
        logging.info(f"   ✅ Sent: {stats['sent']}")
        logging.info(f"   ❌ Failed: {stats['failed']}")
        logging.info(f"   ⏭️ Skipped: {stats['skipped']}")
        
        return stats


def main():
    """Main function to send personalized emails."""
    sender = PersonalizedEmailSender()
    
    # Load HR emails
    emails_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv')
    
    if not os.path.exists(emails_path):
        logging.error(f"❌ HR emails file not found: {emails_path}")
        logging.info("Run email_scraper.py first to collect HR emails.")
        return
    
    emails_df = pd.read_csv(emails_path)
    emails_df = emails_df[emails_df['hr_email'].notna()]
    
    logging.info(f"📊 Loaded {len(emails_df)} HR email contacts")
    
    # Check for credentials
    if not os.getenv('SENDER_EMAIL') or not os.getenv('SENDER_PASSWORD'):
        logging.error("\n❌ Email credentials not configured!")
        logging.error("Set these environment variables:")
        logging.error("  SENDER_EMAIL=your.email@gmail.com")
        logging.error("  SENDER_PASSWORD=your-app-password")
        logging.error("\nFor Gmail, create an App Password:")
        logging.error("  1. Enable 2-Factor Authentication")
        logging.error("  2. Go to https://myaccount.google.com/apppasswords")
        logging.error("  3. Create a new app password")
        return
    
    # Get max emails from environment variable
    max_emails = int(os.getenv('MAX_EMAILS', '20'))
    
    # Send emails
    stats = sender.send_bulk_emails(
        emails_df,
        max_emails=max_emails,  # Limit per run to avoid spam flags
        delay_range=(45, 90)  # 45-90 seconds between emails
    )
    
    logging.info("\n✅ Email campaign completed!")


if __name__ == "__main__":
    main()
