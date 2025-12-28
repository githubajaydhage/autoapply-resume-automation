"""
Personalized Email Sender - Sends customized job application emails to HR contacts
"""

import smtplib
import ssl
import socket
import dns.resolver
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
import re
from datetime import datetime
from string import Template

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS, BASE_RESUME_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class EmailValidator:
    """Validates email addresses before sending."""
    
    # Known invalid/fake email patterns
    INVALID_PATTERNS = [
        r'.*@example\.com$',
        r'.*@test\.com$',
        r'.*@fake\.com$',
        r'.*@email\.com$',
        r'.*@mail\.com$',
        r'noreply@.*',
        r'no-reply@.*',
        r'donotreply@.*',
        r'mailer-daemon@.*',
        r'postmaster@.*',
    ]
    
    # Known valid company domains (verified to exist)
    KNOWN_VALID_DOMAINS = {
        'infosys.com', 'tcs.com', 'wipro.com', 'hcl.com', 'techmahindra.com',
        'mindtree.com', 'mphasis.com', 'ltimindtree.com', 'cognizant.com',
        'capgemini.com', 'accenture.com', 'deloitte.com', 'pwc.com', 'ey.com',
        'kpmg.com', 'razorpay.com', 'zerodha.com', 'phonepe.com', 'swiggy.in',
        'zomato.com', 'cred.club', 'meesho.com', 'groww.in', 'freshworks.com',
        'zohocorp.com', 'flipkart.com', 'olacabs.com', 'paytm.com', 'dream11.com',
        'google.com', 'microsoft.com', 'amazon.com', 'fb.com', 'apple.com',
        'netflix.com', 'uber.com', 'salesforce.com', 'adobe.com', 'oracle.com',
        'ibm.com', 'sap.com', 'vmware.com', 'cisco.com', 'intel.com',
        'qualcomm.com', 'nvidia.com', 'linkedin.com', 'twitter.com', 'stripe.com',
        'hdfcbank.com', 'icicibank.com', 'kotak.com', 'axisbank.com', 'yesbank.in',
        'mckinsey.com', 'bcg.com', 'bain.com', 'mu-sigma.com', 'fractal.ai',
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    }
    
    def __init__(self):
        self.dns_cache = {}  # Cache DNS lookups
        
    def is_valid_format(self, email: str) -> bool:
        """Check if email has valid format."""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Check against invalid patterns
        for invalid in self.INVALID_PATTERNS:
            if re.match(invalid, email, re.IGNORECASE):
                return False
        
        return True
    
    def has_valid_mx_record(self, email: str) -> bool:
        """Check if the email domain has valid MX records (can receive email)."""
        try:
            domain = email.split('@')[1].lower()
            
            # Check cache first
            if domain in self.dns_cache:
                return self.dns_cache[domain]
            
            # Known valid domains - skip DNS check
            if domain in self.KNOWN_VALID_DOMAINS:
                self.dns_cache[domain] = True
                return True
            
            # Try DNS MX lookup
            try:
                mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
                has_mx = len(list(mx_records)) > 0
                self.dns_cache[domain] = has_mx
                return has_mx
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                # Domain doesn't exist or has no MX records
                self.dns_cache[domain] = False
                return False
            except dns.exception.Timeout:
                # Timeout - assume valid (don't block on slow DNS)
                self.dns_cache[domain] = True
                return True
                
        except Exception as e:
            logging.debug(f"MX check error for {email}: {e}")
            return True  # Don't block on errors
    
    def validate_email(self, email: str) -> tuple:
        """
        Validate an email address.
        Returns: (is_valid, reason)
        """
        if not email:
            return False, "Empty email"
        
        email = email.strip().lower()
        
        # Format check
        if not self.is_valid_format(email):
            return False, "Invalid format"
        
        # MX record check
        if not self.has_valid_mx_record(email):
            return False, "Domain cannot receive email"
        
        # Check if it's an HR/recruitment email (not random office emails)
        if not self.is_hr_related_email(email):
            return False, "Not an HR/recruitment email"
        
        return True, "Valid"
    
    def is_hr_related_email(self, email: str) -> bool:
        """Check if the email is HR/recruitment related."""
        email_lower = email.lower()
        local_part = email_lower.split('@')[0]
        
        # HR/recruitment keywords that should be in the email
        hr_keywords = [
            'career', 'careers', 'hr', 'recruit', 'recruiting', 'recruitment',
            'hiring', 'jobs', 'job', 'talent', 'people', 'human', 'staffing',
            'resume', 'resumes', 'apply', 'application', 'applications',
            'india.recruiting', 'indiatalent', 'indiacareers', 'intalent',
            'askhr', 'hrcare', 'in_careers'
        ]
        
        # Check if local part contains HR keywords
        for keyword in hr_keywords:
            if keyword in local_part:
                return True
        
        # Skip generic info/support emails (these are NOT HR)
        non_hr_patterns = [
            'info@', 'support@', 'contact@', 'help@', 'service@',
            'sales@', 'marketing@', 'admin@', 'office@', 'press@',
            'media@', 'legal@', 'finance@', 'billing@', 'accounts@',
            'customer@', 'enquir', 'query', 'feedback@', 'complaints@',
            'ombuds', 'federal@', 'serv', 'gsc@', 'cc@', 'szerviz@',
            '.luxembourg', 'directo@'
        ]
        
        for pattern in non_hr_patterns:
            if pattern in email_lower:
                return False
        
        # Block personal email domains (gmail, yahoo, etc.) - only company emails allowed
        personal_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'rediffmail.com']
        domain = email.split('@')[1].lower()
        
        if domain in personal_domains:
            # Don't send to personal email addresses - not genuine HR
            return False
        
        # If from known valid company domains, accept
        if domain in self.KNOWN_VALID_DOMAINS:
            return True
        
        return False


class PersonalizedEmailSender:
    """Sends personalized job application emails to HR contacts."""
    
    def __init__(self):
        # Email configuration - only password needed from secrets
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Use email from config, password from secrets
        self.sender_email = USER_DETAILS.get('email', 'biradarshweta48@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')  # App password from GitHub Secrets
        self.sender_name = USER_DETAILS.get('full_name', 'Shweta Biradar')
        
        # Applicant details from config.py - no secrets needed!
        self.applicant_name = USER_DETAILS.get('full_name', 'Shweta Biradar')
        self.applicant_phone = USER_DETAILS.get('phone', '+91-7676294009')
        self.applicant_linkedin = USER_DETAILS.get('linkedin_url', '')
        self.applicant_experience = USER_DETAILS.get('years_experience', '3')
        self.applicant_skills = 'Data Analysis, Python, SQL, Excel, Tableau, Power BI'
        
        # Resume path from config
        self.resume_path = BASE_RESUME_PATH
        
        # Email validator
        self.validator = EmailValidator()
        
        # Track sent emails
        self.sent_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'sent_emails_log.csv'
        )
        self.sent_emails = self._load_sent_log()
        
        # Track invalid emails
        self.invalid_log_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'invalid_emails_log.csv'
        )
        
        # Log configuration
        logging.info(f"📧 Email Sender Configuration:")
        logging.info(f"   Sender: {self.sender_name} <{self.sender_email}>")
        logging.info(f"   Phone: {self.applicant_phone}")
        logging.info(f"   Experience: {self.applicant_experience}+ years")
        logging.info(f"   Resume: {self.resume_path}")
        
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
        """Generate a personalized email subject - optimized for high open rates."""
        # Subject lines with higher open rates (data-driven best practices)
        subjects = [
            # Direct and specific (highest open rates)
            f"Application: {job_title} - Bangalore - {self.applicant_experience}+ Years Experience",
            f"{job_title} Application - Bangalore - {self.applicant_name}",
            
            # Creates urgency/interest
            f"Immediate Availability: {job_title} Role in Bangalore",
            f"Bangalore-Based Candidate for {job_title} Opening",
            
            # Personal touch
            f"Interested in {job_title} at {company} Bangalore",
            f"Connecting for {job_title} Opportunity - Bangalore",
        ]
        return random.choice(subjects)
    
    def generate_email_body(self, job_title: str, company: str, job_url: str = None) -> str:
        """Generate a personalized email body."""
        
        # Multiple email templates for variety
        templates = [
            # Template 1 - Professional and direct
            """Dear Hiring Manager,

I am writing to express my strong interest in the ${job_title} position at ${company}'s Bangalore office. With ${experience}+ years of experience in ${skills_area}, I am confident in my ability to contribute effectively to your team.

My key qualifications include:
• Proficient in ${skills}
• Strong analytical and problem-solving abilities
• Excellent communication and collaboration skills
• Proven track record of delivering results
• Currently based in Bangalore and immediately available to join

I am particularly drawn to ${company}'s reputation for innovation and excellence in the industry. I believe my skills and experience align well with the requirements of this role.

I have attached my resume for your review. I would welcome the opportunity to discuss how my background and skills can benefit ${company}.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
${name}
📍 Location: Bangalore, Karnataka
📞 ${phone}
🔗 LinkedIn: ${linkedin}""",

            # Template 2 - Enthusiastic
            """Dear HR Team,

I recently came across the ${job_title} opening at ${company}, and I am excited to submit my application for this role in Bangalore.

As a professional with ${experience}+ years of experience, I have developed strong expertise in ${skills}. I am passionate about leveraging data and technology to drive business insights and decisions.

What excites me about ${company}:
• Your commitment to innovation and excellence
• The opportunity to work on challenging projects
• The collaborative and growth-oriented culture

I am based in Bangalore and immediately available to join. I am confident that my skills and enthusiasm make me a strong candidate for this position.

Please find my resume attached for your consideration.

Warm regards,
${name}
📍 Location: Bangalore, Karnataka
📞 ${phone}
🔗 LinkedIn: ${linkedin}""",

            # Template 3 - Concise
            """Dear Recruitment Team,

I am applying for the ${job_title} position at ${company} (Bangalore).

Profile Summary:
• Experience: ${experience}+ years
• Skills: ${skills}
• Location: Bangalore, Karnataka
• Availability: Immediate

I am currently based in Bangalore and excited about the opportunity to contribute to ${company}'s success.

Please review my attached resume. I look forward to discussing this opportunity with you.

Best regards,
${name}
📍 Location: Bangalore, Karnataka
📞 ${phone}
🔗 LinkedIn: ${linkedin}"""
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
    
    def _log_invalid_email(self, email: str, company: str, reason: str):
        """Log invalid email addresses."""
        log_entry = {
            'email': email,
            'company': company,
            'reason': reason,
            'checked_at': datetime.now().isoformat()
        }
        
        if os.path.exists(self.invalid_log_path):
            df = pd.read_csv(self.invalid_log_path)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.invalid_log_path, index=False)
    
    def send_email(self, recipient_email: str, company: str, job_title: str, job_url: str = None) -> bool:
        """Send a personalized email to a single recipient."""
        
        # Skip if already sent
        if recipient_email.lower() in self.sent_emails:
            logging.info(f"⏭️ Skipping {recipient_email} - already contacted")
            return False
        
        # VALIDATE EMAIL BEFORE SENDING
        is_valid, reason = self.validator.validate_email(recipient_email)
        if not is_valid:
            logging.warning(f"⚠️ Skipping {recipient_email} - {reason}")
            self._log_invalid_email(recipient_email, company, reason)
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
        
        # CRITICAL: Filter to only HR-related emails (skip info@, support@, etc.)
        hr_mask = emails_df['hr_email'].apply(self.validator.is_hr_related_email)
        non_hr_count = len(emails_df) - hr_mask.sum()
        if non_hr_count > 0:
            logging.info(f"🚫 Filtered out {non_hr_count} non-HR emails (info@, support@, cc@, etc.)")
        emails_df = emails_df[hr_mask]
        
        if emails_df.empty:
            logging.info("All emails have already been sent or filtered!")
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
    logging.info("="*60)
    logging.info("📧 PERSONALIZED EMAIL SENDER")
    logging.info("="*60)
    
    sender = PersonalizedEmailSender()
    
    # Try multiple sources for HR emails
    emails_df = pd.DataFrame()
    
    # Source 1: Curated HR database (most reliable)
    curated_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'curated_hr_emails.csv')
    if os.path.exists(curated_path):
        curated_df = pd.read_csv(curated_path)
        # Rename 'email' to 'hr_email' for compatibility
        if 'email' in curated_df.columns:
            curated_df = curated_df.rename(columns={'email': 'hr_email'})
        curated_df['job_title'] = 'Data Analyst / Business Analyst'  # Default
        emails_df = pd.concat([emails_df, curated_df], ignore_index=True)
        logging.info(f"📋 Loaded {len(curated_df)} curated HR emails")
    
    # Source 2: Scraped emails
    scraped_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv')
    if os.path.exists(scraped_path):
        scraped_df = pd.read_csv(scraped_path)
        if 'hr_email' in scraped_df.columns:
            emails_df = pd.concat([emails_df, scraped_df], ignore_index=True)
            logging.info(f"🔍 Loaded {len(scraped_df)} scraped HR emails")
    
    if emails_df.empty:
        logging.error("❌ No HR emails found!")
        logging.info("Run curated_hr_database.py or email_scraper.py first.")
        return
    
    # Clean and dedupe
    emails_df = emails_df[emails_df['hr_email'].notna()]
    emails_df = emails_df.drop_duplicates(subset=['hr_email'], keep='first')
    
    logging.info(f"📊 Total unique HR contacts: {len(emails_df)}")
    
    # Check for password - only thing needed from secrets!
    if not os.getenv('SENDER_PASSWORD'):
        logging.error("\n❌ Gmail App Password not configured!")
        logging.error("Add this ONE secret to GitHub:")
        logging.error("  SENDER_PASSWORD = your-16-char-app-password")
        logging.error("\nHow to create App Password:")
        logging.error("  1. Go to https://myaccount.google.com/security")
        logging.error("  2. Enable 2-Factor Authentication")
        logging.error("  3. Go to https://myaccount.google.com/apppasswords")
        logging.error("  4. Create app password for 'Mail'")
        logging.error("  5. Copy the 16-character password")
        return
    
    # Get max emails from environment variable
    max_emails = int(os.getenv('MAX_EMAILS', '20'))
    
    # Send emails
    stats = sender.send_bulk_emails(
        emails_df,
        max_emails=max_emails,
        delay_range=(45, 90)  # 45-90 seconds between emails
    )
    
    logging.info("="*60)
    logging.info("✅ Email campaign completed!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
