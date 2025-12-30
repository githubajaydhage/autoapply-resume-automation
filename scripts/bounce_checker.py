"""
Bounce Checker - Monitors inbox for bounced emails and updates email status
"""

import imaplib
import email
from email.header import decode_header
import pandas as pd
import os
import sys
import logging
import re
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class BounceChecker:
    """Checks inbox for bounced emails and tracks delivery status."""
    
    # Common bounce indicators in email subjects and bodies
    BOUNCE_SUBJECT_PATTERNS = [
        r'delivery.*fail',
        r'undeliverable',
        r'mail.*delivery.*failed',
        r'returned.*mail',
        r'delivery.*status.*notification',
        r'message.*not.*delivered',
        r'failed.*delivery',
        r'could.*not.*deliver',
        r'recipient.*rejected',
        r'address.*rejected',
        r'user.*unknown',
        r'mailbox.*not.*found',
        r'no.*such.*user',
        r'invalid.*recipient',
        r'bounce',
        r'mailer-daemon',
        r'postmaster',
    ]
    
    # Patterns to extract the bounced email address
    BOUNCED_EMAIL_PATTERNS = [
        r'delivery to the following recipient failed.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'failed to deliver to.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'recipient.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*?rejected',
        r'<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>.*?fail',
        r'original.*?to:.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'final.*?recipient.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    # Common bounce reasons
    BOUNCE_REASONS = {
        'user unknown': 'Email address does not exist',
        'mailbox not found': 'Mailbox does not exist',
        'address rejected': 'Email address rejected by server',
        'domain not found': 'Domain does not exist',
        'no such user': 'User does not exist',
        'mailbox full': 'Recipient mailbox is full',
        'blocked': 'Email was blocked by recipient',
        'spam': 'Email marked as spam',
        'quota exceeded': 'Mailbox quota exceeded',
        'temporarily rejected': 'Temporary delivery failure',
    }
    
    def __init__(self):
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        # Email must be configured via environment or USER_DETAILS
        self.email_address = os.getenv('SENDER_EMAIL') or USER_DETAILS.get('email', '')
        if not self.email_address:
            logging.warning("⚠️ SENDER_EMAIL not set! Bounce checking may fail.")
        self.email_password = os.getenv('SENDER_PASSWORD', '')
        
        # Paths for data files
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.bounce_log_path = os.path.join(self.data_dir, 'bounced_emails.csv')
        self.sent_log_path = os.path.join(self.data_dir, 'sent_emails_log.csv')
        self.verified_emails_path = os.path.join(self.data_dir, 'verified_emails.csv')
        self.problematic_emails_path = os.path.join(self.data_dir, 'problematic_emails.csv')
        
    def connect_to_inbox(self):
        """Connect to email inbox via IMAP."""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            return mail
        except Exception as e:
            logging.error(f"❌ Failed to connect to inbox: {e}")
            return None
    
    def is_bounce_email(self, subject: str, from_addr: str) -> bool:
        """Check if an email is a bounce notification."""
        subject_lower = subject.lower()
        from_lower = from_addr.lower()
        
        # Check from address
        if any(x in from_lower for x in ['mailer-daemon', 'postmaster', 'mail-daemon']):
            return True
        
        # Check subject patterns
        for pattern in self.BOUNCE_SUBJECT_PATTERNS:
            if re.search(pattern, subject_lower, re.IGNORECASE):
                return True
        
        return False
    
    def extract_bounced_email(self, body: str, subject: str) -> str:
        """Extract the bounced email address from the message."""
        text = f"{subject}\n{body}".lower()
        
        for pattern in self.BOUNCED_EMAIL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).lower()
        
        # Fallback: find any email in the body
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails_found = re.findall(email_pattern, body)
        
        # Filter out our own email and common system emails
        for found_email in emails_found:
            found_lower = found_email.lower()
            if (found_lower != self.email_address.lower() and
                'mailer-daemon' not in found_lower and
                'postmaster' not in found_lower):
                return found_lower
        
        return None
    
    def extract_bounce_reason(self, body: str) -> str:
        """Extract the reason for bounce from the message body."""
        body_lower = body.lower()
        
        for keyword, reason in self.BOUNCE_REASONS.items():
            if keyword in body_lower:
                return reason
        
        return "Unknown delivery failure"
    
    def get_email_body(self, msg) -> str:
        """Extract body from email message."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def check_for_bounces(self, days_back: int = 7) -> list:
        """Check inbox for bounce notifications."""
        logging.info(f"🔍 Checking inbox for bounce notifications (last {days_back} days)...")
        
        if not self.email_password:
            logging.error("❌ SENDER_PASSWORD not set. Cannot check inbox.")
            return []
        
        mail = self.connect_to_inbox()
        if not mail:
            return []
        
        bounces = []
        
        try:
            mail.select('INBOX')
            
            # Search for emails from the last N days
            date_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search for potential bounce emails
            search_criteria = f'(SINCE {date_since})'
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logging.warning("Failed to search inbox")
                return []
            
            email_ids = messages[0].split()
            logging.info(f"📬 Found {len(email_ids)} emails to check")
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject
                    subject = ""
                    if msg['Subject']:
                        decoded = decode_header(msg['Subject'])
                        subject = decoded[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode('utf-8', errors='ignore')
                    
                    # Get from address
                    from_addr = msg.get('From', '')
                    
                    # Check if this is a bounce
                    if self.is_bounce_email(subject, from_addr):
                        body = self.get_email_body(msg)
                        bounced_email = self.extract_bounced_email(body, subject)
                        
                        if bounced_email:
                            reason = self.extract_bounce_reason(body)
                            bounce_info = {
                                'bounced_email': bounced_email,
                                'reason': reason,
                                'bounce_date': msg.get('Date', ''),
                                'subject': subject[:100],
                            }
                            bounces.append(bounce_info)
                            logging.info(f"   ❌ Bounce detected: {bounced_email} - {reason}")
                
                except Exception as e:
                    logging.debug(f"Error processing email: {e}")
                    continue
            
            mail.logout()
            
        except Exception as e:
            logging.error(f"Error checking bounces: {e}")
        
        logging.info(f"📊 Found {len(bounces)} bounced emails")
        return bounces
    
    def save_bounces(self, bounces: list):
        """Save bounced emails to CSV."""
        if not bounces:
            return
        
        df_new = pd.DataFrame(bounces)
        df_new['detected_at'] = datetime.now().isoformat()
        
        if os.path.exists(self.bounce_log_path):
            df_existing = pd.read_csv(self.bounce_log_path)
            if df_existing.empty:
                df_combined = df_new
            else:
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['bounced_email'], keep='last')
        else:
            df_combined = df_new
        
        df_combined.to_csv(self.bounce_log_path, index=False)
        logging.info(f"💾 Saved {len(bounces)} bounces to {self.bounce_log_path}")
    
    def update_sent_log_with_bounces(self, bounces: list):
        """Update sent_emails_log.csv with bounce status."""
        if not bounces or not os.path.exists(self.sent_log_path):
            return
        
        df = pd.read_csv(self.sent_log_path)
        bounced_emails = {b['bounced_email'].lower(): b['reason'] for b in bounces}
        
        updated_count = 0
        for idx, row in df.iterrows():
            email_lower = row['recipient_email'].lower()
            if email_lower in bounced_emails:
                df.at[idx, 'status'] = f"bounced: {bounced_emails[email_lower]}"
                updated_count += 1
        
        if updated_count > 0:
            df.to_csv(self.sent_log_path, index=False)
            logging.info(f"📝 Updated {updated_count} entries in sent log with bounce status")
    
    def generate_email_quality_report(self):
        """Generate a report of verified vs problematic emails."""
        if not os.path.exists(self.sent_log_path):
            logging.warning("No sent emails log found")
            return
        
        df = pd.read_csv(self.sent_log_path)
        
        # Categorize emails
        verified = []
        problematic = []
        
        for _, row in df.iterrows():
            email_info = {
                'email': row['recipient_email'],
                'company': row.get('company', 'Unknown'),
                'status': row['status'],
                'sent_at': row.get('sent_at', '')
            }
            
            status_lower = str(row['status']).lower()
            if 'bounced' in status_lower or 'failed' in status_lower:
                email_info['reason'] = status_lower
                problematic.append(email_info)
            elif 'sent' in status_lower:
                verified.append(email_info)
        
        # Save verified emails
        if verified:
            df_verified = pd.DataFrame(verified)
            df_verified.to_csv(self.verified_emails_path, index=False)
            logging.info(f"✅ {len(verified)} verified emails saved to {self.verified_emails_path}")
        
        # Save problematic emails
        if problematic:
            df_problematic = pd.DataFrame(problematic)
            df_problematic.to_csv(self.problematic_emails_path, index=False)
            logging.info(f"⚠️ {len(problematic)} problematic emails saved to {self.problematic_emails_path}")
        
        # Print summary
        logging.info("\n📊 EMAIL QUALITY REPORT:")
        logging.info(f"   ✅ Verified/Delivered: {len(verified)}")
        logging.info(f"   ❌ Bounced/Failed: {len(problematic)}")
        
        if problematic:
            logging.info("\n⚠️ PROBLEMATIC EMAILS:")
            for p in problematic[:10]:  # Show first 10
                logging.info(f"   - {p['email']} ({p['company']}): {p['reason']}")


def main():
    """Main function to check for bounces."""
    logging.info("="*60)
    logging.info("📬 EMAIL BOUNCE CHECKER")
    logging.info("="*60)
    
    if not os.getenv('SENDER_PASSWORD'):
        logging.error("❌ SENDER_PASSWORD environment variable not set!")
        logging.info("Set this to check your inbox for bounces.")
        return
    
    checker = BounceChecker()
    
    # Check for bounces in the last 7 days
    bounces = checker.check_for_bounces(days_back=7)
    
    # Save bounces
    if bounces:
        checker.save_bounces(bounces)
        checker.update_sent_log_with_bounces(bounces)
    
    # Generate quality report
    checker.generate_email_quality_report()
    
    logging.info("="*60)
    logging.info("✅ Bounce check completed!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
