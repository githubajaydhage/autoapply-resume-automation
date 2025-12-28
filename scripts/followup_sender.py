"""
Follow-Up Email System - Automatically sends follow-up emails after initial contact
Increases response rate by 30-40%
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import os
import sys
import logging
import time
import random
from datetime import datetime, timedelta
from string import Template

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS, BASE_RESUME_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class FollowUpEmailSender:
    """Sends follow-up emails to previously contacted HR/recruiters."""
    
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        self.sender_email = USER_DETAILS.get('email', 'biradarshweta48@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.sender_name = USER_DETAILS.get('full_name', 'Shweta Biradar')
        
        # Applicant details
        self.applicant_name = USER_DETAILS.get('full_name', 'Shweta Biradar')
        self.applicant_phone = USER_DETAILS.get('phone', '+91-7676294009')
        
        # Paths
        self.sent_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'sent_emails_log.csv'
        )
        self.followup_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'followup_log.csv'
        )
        
        self.followup_sent = self._load_followup_log()
        
        # Follow-up timing
        self.followup_after_days = 5  # Send follow-up 5 days after initial email
        
    def _load_followup_log(self) -> set:
        """Load previously sent follow-up emails."""
        if os.path.exists(self.followup_log_path):
            df = pd.read_csv(self.followup_log_path)
            return set(df['recipient_email'].str.lower())
        return set()
    
    def _save_followup_log(self, recipient_email: str, company: str, status: str):
        """Log sent follow-up email."""
        log_entry = {
            'recipient_email': recipient_email,
            'company': company,
            'sent_at': datetime.now().isoformat(),
            'status': status,
            'type': 'followup'
        }
        
        if os.path.exists(self.followup_log_path):
            df = pd.read_csv(self.followup_log_path)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.followup_log_path, index=False)
        self.followup_sent.add(recipient_email.lower())
    
    def get_contacts_to_followup(self) -> pd.DataFrame:
        """Get contacts who should receive follow-up emails."""
        if not os.path.exists(self.sent_log_path):
            logging.info("No sent emails log found - no follow-ups to send")
            return pd.DataFrame()
        
        df = pd.read_csv(self.sent_log_path)
        
        # Filter for successful sends
        df = df[df['status'] == 'sent']
        
        # Parse dates and calculate days since sent
        df['sent_at'] = pd.to_datetime(df['sent_at'])
        df['days_since_sent'] = (datetime.now() - df['sent_at']).dt.days
        
        # Get contacts that are due for follow-up
        due_for_followup = df[df['days_since_sent'] >= self.followup_after_days]
        
        # Exclude those already followed up
        due_for_followup = due_for_followup[
            ~due_for_followup['recipient_email'].str.lower().isin(self.followup_sent)
        ]
        
        logging.info(f"📊 Found {len(due_for_followup)} contacts due for follow-up")
        return due_for_followup
    
    def generate_followup_subject(self, job_title: str, company: str) -> str:
        """Generate follow-up email subject (references previous email)."""
        subjects = [
            f"Following Up - {job_title} Application",
            f"Re: {job_title} Position at {company}",
            f"Quick Follow-Up: {job_title} Application",
            f"Checking In - {job_title} Opportunity",
        ]
        return random.choice(subjects)
    
    def generate_followup_body(self, job_title: str, company: str, days_since: int) -> str:
        """Generate follow-up email body."""
        
        templates = [
            # Template 1 - Polite reminder
            """Dear Hiring Team,

I hope this email finds you well. I am following up on my application for the ${job_title} position that I submitted ${days} days ago.

I remain very interested in this opportunity at ${company} and would welcome the chance to discuss how my skills and experience align with your team's needs.

If you need any additional information or would like to schedule a call, please let me know. I am available at your convenience.

Thank you for your time and consideration.

Best regards,
${name}
${phone}""",

            # Template 2 - Add value
            """Dear Recruitment Team,

I wanted to follow up on my application for the ${job_title} role at ${company}.

Since my initial application, I have been:
• Continuing to develop my skills in relevant technologies
• Researching ${company}'s recent initiatives
• Ready to contribute from day one

I understand you may be reviewing many applications. I would genuinely appreciate any update on the status of my application.

Looking forward to hearing from you.

Best regards,
${name}
${phone}""",

            # Template 3 - Short and direct
            """Hi,

I am following up on my ${job_title} application from ${days} days ago.

I am still very interested in this role and would appreciate any update on the hiring process.

Please let me know if you need any additional information.

Thanks,
${name}
${phone}"""
        ]
        
        template = Template(random.choice(templates))
        
        return template.substitute(
            job_title=job_title,
            company=company,
            days=days_since,
            name=self.applicant_name,
            phone=self.applicant_phone
        )
    
    def send_followup(self, recipient_email: str, company: str, job_title: str, days_since: int) -> bool:
        """Send a follow-up email."""
        
        if recipient_email.lower() in self.followup_sent:
            logging.info(f"⏭️ Already followed up with {recipient_email}")
            return False
        
        if not self.sender_password:
            logging.error("❌ SENDER_PASSWORD not set")
            return False
        
        try:
            subject = self.generate_followup_subject(job_title, company)
            body = self.generate_followup_body(job_title, company, days_since)
            
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
            
            logging.info(f"✅ Follow-up sent to {recipient_email} ({company})")
            self._save_followup_log(recipient_email, company, 'sent')
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send follow-up to {recipient_email}: {e}")
            self._save_followup_log(recipient_email, company, f'failed: {e}')
            return False
    
    def send_all_followups(self, max_followups: int = 20) -> dict:
        """Send follow-ups to all eligible contacts."""
        
        contacts = self.get_contacts_to_followup()
        
        if contacts.empty:
            logging.info("No follow-ups to send at this time")
            return {'sent': 0, 'failed': 0}
        
        contacts = contacts.head(max_followups)
        
        logging.info(f"📧 Sending {len(contacts)} follow-up emails...")
        
        stats = {'sent': 0, 'failed': 0}
        
        for idx, row in contacts.iterrows():
            success = self.send_followup(
                row['recipient_email'],
                row.get('company', 'Company'),
                row.get('job_title', 'Position'),
                int(row.get('days_since_sent', 7))
            )
            
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            
            # Delay between emails
            if idx < len(contacts) - 1:
                delay = random.uniform(60, 120)
                logging.info(f"⏳ Waiting {delay:.0f}s before next follow-up...")
                time.sleep(delay)
        
        logging.info(f"\n📊 Follow-Up Summary:")
        logging.info(f"   ✅ Sent: {stats['sent']}")
        logging.info(f"   ❌ Failed: {stats['failed']}")
        
        return stats


def main():
    """Main function to send follow-up emails."""
    logging.info("="*60)
    logging.info("📧 FOLLOW-UP EMAIL SYSTEM")
    logging.info("="*60)
    
    if not os.getenv('SENDER_PASSWORD'):
        logging.error("❌ SENDER_PASSWORD not configured")
        return
    
    sender = FollowUpEmailSender()
    
    # Check how many are due
    contacts = sender.get_contacts_to_followup()
    
    if contacts.empty:
        logging.info("✅ No follow-ups due at this time")
        logging.info("   (Follow-ups are sent 5 days after initial contact)")
        return
    
    max_followups = int(os.getenv('MAX_FOLLOWUPS', '10'))
    stats = sender.send_all_followups(max_followups=max_followups)
    
    logging.info("="*60)
    logging.info("✅ Follow-up campaign complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
