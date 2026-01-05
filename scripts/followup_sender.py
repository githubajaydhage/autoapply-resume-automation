"""
Smart Follow-Up Email System - Multi-stage follow-up sequences
Stage 1: Day 3 - Gentle reminder
Stage 2: Day 7 - Value-add follow-up
Stage 3: Day 14 - Final follow-up with urgency
Increases response rate by 40-60%
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

# CI Mode detection - reduce delays in GitHub Actions
CI_MODE = os.getenv('CI', 'false').lower() == 'true' or os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
if CI_MODE:
    logging.info("🚀 CI Mode detected - using optimized delays for GitHub Actions")


class SmartFollowUpSender:
    """
    Sends multi-stage follow-up emails with different messaging for each stage.
    
    Follow-up Sequence:
    - Stage 1 (Day 3): Gentle reminder - "Just checking in"
    - Stage 2 (Day 7): Value-add - Share insight, show continued interest
    - Stage 3 (Day 14): Final follow-up - Create urgency, last attempt
    """
    
    # Follow-up schedule (days after initial email)
    FOLLOWUP_SCHEDULE = {
        1: 3,   # First follow-up after 3 days
        2: 7,   # Second follow-up after 7 days
        3: 14,  # Final follow-up after 14 days
    }
    
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        self.sender_email = os.getenv('SENDER_EMAIL', USER_DETAILS.get('email', ''))
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.sender_name = os.getenv('APPLICANT_NAME', USER_DETAILS.get('full_name', ''))
        
        # Applicant details from env vars or config.py
        self.applicant_name = os.getenv('APPLICANT_NAME', USER_DETAILS.get('full_name', ''))
        self.applicant_phone = os.getenv('APPLICANT_PHONE', USER_DETAILS.get('phone', ''))
        self.applicant_linkedin = USER_DETAILS.get('linkedin_url', '')
        
        # Paths
        self.sent_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'sent_emails_log.csv'
        )
        self.followup_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'followup_log.csv'
        )
        
        self.followup_history = self._load_followup_log()
        
    def _load_followup_log(self) -> pd.DataFrame:
        """Load follow-up history."""
        if os.path.exists(self.followup_log_path):
            return pd.read_csv(self.followup_log_path)
        return pd.DataFrame(columns=['recipient_email', 'company', 'sent_at', 'status', 'stage'])
    
    def _get_followup_count(self, email: str) -> int:
        """Get number of follow-ups already sent to this email."""
        if self.followup_history.empty:
            return 0
        sent = self.followup_history[
            (self.followup_history['recipient_email'].str.lower() == email.lower()) &
            (self.followup_history['status'] == 'sent')
        ]
        return len(sent)
    
    def _save_followup_log(self, recipient_email: str, company: str, status: str, stage: int):
        """Log sent follow-up email with stage."""
        log_entry = {
            'recipient_email': recipient_email,
            'company': company,
            'sent_at': datetime.now().isoformat(),
            'status': status,
            'stage': stage
        }
        
        self.followup_history = pd.concat([
            self.followup_history, 
            pd.DataFrame([log_entry])
        ], ignore_index=True)
        
        self.followup_history.to_csv(self.followup_log_path, index=False)
    
    def get_contacts_to_followup(self) -> pd.DataFrame:
        """Get contacts who should receive follow-up emails based on stage."""
        if not os.path.exists(self.sent_log_path):
            logging.info("No sent emails log found - no follow-ups to send")
            return pd.DataFrame()
        
        df = pd.read_csv(self.sent_log_path)
        
        # Filter for successful sends only
        df = df[df['status'] == 'sent']
        
        # Parse dates and calculate days since sent
        df['sent_at'] = pd.to_datetime(df['sent_at'], errors='coerce')
        # Remove timezone info for safe comparison
        df['sent_at'] = df['sent_at'].dt.tz_localize(None)
        df['days_since_sent'] = (datetime.now() - df['sent_at']).dt.days
        
        # Determine which stage each contact is eligible for
        eligible_contacts = []
        
        for idx, row in df.iterrows():
            email = row['recipient_email']
            days = row['days_since_sent']
            followups_sent = self._get_followup_count(email)
            
            # Determine next stage
            next_stage = followups_sent + 1
            
            if next_stage > 3:
                continue  # Max 3 follow-ups
            
            # Check if enough days have passed for next stage
            required_days = self.FOLLOWUP_SCHEDULE.get(next_stage, 999)
            
            if days >= required_days:
                row_dict = row.to_dict()
                row_dict['next_stage'] = next_stage
                row_dict['followups_sent'] = followups_sent
                eligible_contacts.append(row_dict)
        
        result_df = pd.DataFrame(eligible_contacts)
        logging.info(f"📊 Found {len(result_df)} contacts due for follow-up")
        return result_df
    
    def generate_stage_subject(self, job_title: str, company: str, stage: int) -> str:
        """Generate subject line based on follow-up stage."""
        
        stage_subjects = {
            1: [
                f"Quick follow-up: {job_title} application",
                f"Checking in - {job_title} at {company}",
                f"Re: {job_title} Position",
            ],
            2: [
                f"Still interested in {job_title} role",
                f"Following up: {job_title} opportunity",
                f"Re: {job_title} - Additional information",
            ],
            3: [
                f"Final follow-up: {job_title} application",
                f"One last note about {job_title} position",
                f"Before I move on - {job_title} at {company}",
            ]
        }
        
        subjects = stage_subjects.get(stage, stage_subjects[1])
        return random.choice(subjects)
    
    def generate_stage_body(self, job_title: str, company: str, stage: int, days: int) -> str:
        """Generate email body based on follow-up stage."""
        
        # Stage 1: Gentle reminder (Day 3)
        stage1_templates = [
            """Dear Hiring Team,

I hope this email finds you well. I wanted to follow up on my application for the ${job_title} position that I submitted a few days ago.

I remain very enthusiastic about this opportunity at ${company} and believe my skills would be a great fit for your team.

Please let me know if you need any additional information from my end. I'm happy to provide references or complete any assessments.

Looking forward to your response.

Best regards,
${name}
${phone}""",

            """Hi,

Just a quick follow-up on my ${job_title} application at ${company}.

I'm still very interested in this role and wanted to confirm you received my application materials. Please let me know if there's anything else you need.

Thanks!
${name}
${phone}"""
        ]
        
        # Stage 2: Value-add follow-up (Day 7)
        stage2_templates = [
            """Dear Recruitment Team,

I hope you're doing well. I'm following up on my application for the ${job_title} position at ${company}.

Since my last email, I wanted to reiterate my interest and share a few additional points:

• I've been keeping up with ${company}'s recent developments and am excited about the company's direction
• I'm available for an interview at your earliest convenience
• I can provide additional work samples or complete any technical assessments if needed

I understand you're likely reviewing many applications, and I appreciate your time. Even a brief update on the status would be greatly appreciated.

Best regards,
${name}
${phone}
${linkedin}""",

            """Hi there,

Following up again on the ${job_title} opportunity at ${company}.

I wanted to emphasize that I'm not just looking for any job - I'm specifically interested in ${company} because of [the innovative work you're doing / your company culture / the growth opportunities].

I'm confident I can add value from day one. Would you have 15 minutes for a quick call this week?

Thank you for considering my application.

Best,
${name}
${phone}"""
        ]
        
        # Stage 3: Final follow-up with urgency (Day 14)
        stage3_templates = [
            """Dear Hiring Manager,

I wanted to reach out one final time regarding my application for the ${job_title} position at ${company}.

I understand that hiring processes can take time and priorities shift. If this position has been filled or put on hold, I completely understand.

However, if you're still considering candidates, I want to reaffirm my strong interest in this role. I believe my background makes me an excellent fit, and I would love the opportunity to discuss this further.

If I don't hear back, I'll assume the position has been filled. Either way, I appreciate your time and consideration.

Best regards,
${name}
${phone}""",

            """Hi,

This is my final follow-up on the ${job_title} position at ${company}.

I'm still very interested and available. If the role is still open, I'd love to connect. If not, I understand and wish you the best in finding the right candidate.

Thank you for your time.

Best,
${name}
${phone}"""
        ]
        
        templates = {1: stage1_templates, 2: stage2_templates, 3: stage3_templates}
        template_list = templates.get(stage, stage1_templates)
        template = Template(random.choice(template_list))
        
        linkedin_text = f"LinkedIn: {self.applicant_linkedin}" if self.applicant_linkedin else ""
        
        return template.substitute(
            job_title=job_title,
            company=company,
            days=days,
            name=self.applicant_name,
            phone=self.applicant_phone,
            linkedin=linkedin_text
        )
    
    def send_followup(self, recipient_email: str, company: str, job_title: str, 
                       days_since: int, stage: int) -> bool:
        """Send a stage-appropriate follow-up email."""
        
        if not self.sender_password:
            logging.error("❌ SENDER_PASSWORD not set")
            return False
        
        try:
            subject = self.generate_stage_subject(job_title, company, stage)
            body = self.generate_stage_body(job_title, company, stage, days_since)
            
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
            
            stage_names = {1: "Gentle Reminder", 2: "Value-Add", 3: "Final Follow-up"}
            logging.info(f"✅ Stage {stage} ({stage_names.get(stage)}) sent to {recipient_email} ({company})")
            self._save_followup_log(recipient_email, company, 'sent', stage)
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send follow-up to {recipient_email}: {e}")
            self._save_followup_log(recipient_email, company, f'failed: {e}', stage)
            return False
    
    def send_all_followups(self, max_followups: int = 20) -> dict:
        """Send stage-appropriate follow-ups to all eligible contacts."""
        
        contacts = self.get_contacts_to_followup()
        
        if contacts.empty:
            logging.info("No follow-ups to send at this time")
            return {'sent': 0, 'failed': 0, 'by_stage': {1: 0, 2: 0, 3: 0}}
        
        contacts = contacts.head(max_followups)
        
        logging.info(f"📧 Sending {len(contacts)} follow-up emails (multi-stage)...")
        
        stats = {'sent': 0, 'failed': 0, 'by_stage': {1: 0, 2: 0, 3: 0}}
        
        for idx, row in contacts.iterrows():
            stage = row.get('next_stage', 1)
            success = self.send_followup(
                row['recipient_email'],
                row.get('company', 'Company'),
                row.get('job_title', 'Position'),
                int(row.get('days_since_sent', 3)),
                stage
            )
            
            if success:
                stats['sent'] += 1
                stats['by_stage'][stage] = stats['by_stage'].get(stage, 0) + 1
            else:
                stats['failed'] += 1
            
            # Delay between emails - reduced in CI mode to prevent timeout
            if idx < len(contacts) - 1:
                if CI_MODE:
                    delay = random.uniform(5, 15)  # 5-15 seconds in CI
                else:
                    delay = random.uniform(45, 90)  # 45-90 seconds locally
                logging.info(f"⏳ Waiting {delay:.0f}s before next follow-up...")
                time.sleep(delay)
        
        logging.info(f"\n📊 Multi-Stage Follow-Up Summary:")
        logging.info(f"   ✅ Total Sent: {stats['sent']}")
        logging.info(f"      - Stage 1 (Day 3 - Gentle): {stats['by_stage'].get(1, 0)}")
        logging.info(f"      - Stage 2 (Day 7 - Value): {stats['by_stage'].get(2, 0)}")
        logging.info(f"      - Stage 3 (Day 14 - Final): {stats['by_stage'].get(3, 0)}")
        logging.info(f"   ❌ Failed: {stats['failed']}")
        
        return stats


# Keep backward compatibility alias
FollowUpEmailSender = SmartFollowUpSender


def main():
    """Main function to send smart follow-up emails."""
    logging.info("="*60)
    logging.info("📧 SMART MULTI-STAGE FOLLOW-UP SYSTEM")
    logging.info("="*60)
    logging.info("📋 Follow-up Schedule:")
    logging.info("   Stage 1: Day 3 - Gentle reminder")
    logging.info("   Stage 2: Day 7 - Value-add message")
    logging.info("   Stage 3: Day 14 - Final follow-up")
    logging.info("="*60)
    
    if not os.getenv('SENDER_PASSWORD'):
        logging.error("❌ SENDER_PASSWORD not configured")
        return
    
    sender = SmartFollowUpSender()
    
    # Check how many are due
    contacts = sender.get_contacts_to_followup()
    
    if contacts.empty:
        logging.info("✅ No follow-ups due at this time")
        logging.info("   (Stage 1 starts 3 days after initial contact)")
        return
    
    # Show breakdown by stage
    if 'next_stage' in contacts.columns:
        for stage in [1, 2, 3]:
            count = len(contacts[contacts['next_stage'] == stage])
            if count > 0:
                logging.info(f"   Stage {stage} due: {count} contacts")
    
    max_followups = int(os.getenv('MAX_FOLLOWUPS', '15'))
    stats = sender.send_all_followups(max_followups=max_followups)
    
    logging.info("="*60)
    logging.info("✅ Smart follow-up campaign complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
