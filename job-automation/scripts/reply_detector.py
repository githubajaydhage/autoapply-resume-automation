"""
Reply Detector - Monitors inbox for HR replies and interview requests
Automatically categorizes responses and updates application status
"""

import imaplib
import email
from email.header import decode_header
import re
import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ReplyDetector:
    """Detects and categorizes HR replies from inbox."""
    
    # Keywords indicating positive responses
    POSITIVE_KEYWORDS = [
        'interview', 'schedule', 'meeting', 'call', 'discuss',
        'interested', 'impressive', 'shortlisted', 'selected',
        'next step', 'next round', 'proceed', 'move forward',
        'availability', 'available', 'calendar', 'slot',
        'congratulations', 'pleased', 'happy to', 'delighted',
        'offer', 'position', 'join', 'welcome aboard'
    ]
    
    # Keywords indicating rejection
    REJECTION_KEYWORDS = [
        'unfortunately', 'regret', 'not moving forward',
        'other candidates', 'not a fit', 'not selected',
        'position filled', 'filled the position',
        'not proceed', 'decided not to', 'at this time',
        'keep your resume', 'future opportunities'
    ]
    
    # Keywords indicating acknowledgment (neutral)
    ACKNOWLEDGMENT_KEYWORDS = [
        'received', 'thank you for applying', 'application received',
        'will review', 'reviewing', 'get back to you',
        'under consideration', 'in process'
    ]
    
    # Auto-reply patterns to ignore
    AUTO_REPLY_PATTERNS = [
        r'out of office', r'ooo', r'away from', r'on vacation',
        r'auto.?reply', r'automatic reply', r'auto.?response',
        r'do not reply', r'noreply', r'no-reply'
    ]
    
    def __init__(self):
        self.email_address = USER_DETAILS.get('email', '')
        self.password = os.getenv('SENDER_PASSWORD', '')
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Paths for output files
        self.replies_log_path = os.path.join(self.data_path, 'hr_replies.csv')
        self.interview_requests_path = os.path.join(self.data_path, 'interview_requests.csv')
        
    def connect_to_inbox(self):
        """Connect to email inbox via IMAP."""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.password)
            return mail
        except Exception as e:
            logging.error(f"Failed to connect to inbox: {e}")
            return None
    
    def decode_email_subject(self, msg) -> str:
        """Decode email subject."""
        subject = msg.get('Subject', '')
        if subject:
            decoded_parts = decode_header(subject)
            subject_parts = []
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    subject_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                else:
                    subject_parts.append(part)
            return ' '.join(subject_parts)
        return ''
    
    def decode_email_body(self, msg) -> str:
        """Extract email body text."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except:
                pass
        
        return body
    
    def is_auto_reply(self, subject: str, body: str) -> bool:
        """Check if email is an auto-reply."""
        text = (subject + ' ' + body).lower()
        for pattern in self.AUTO_REPLY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def categorize_reply(self, subject: str, body: str) -> tuple:
        """
        Categorize the reply based on content.
        
        Returns: (category, confidence, details)
        """
        text = (subject + ' ' + body).lower()
        
        # Check for interview/positive response
        positive_matches = [kw for kw in self.POSITIVE_KEYWORDS if kw in text]
        if positive_matches:
            # High confidence if multiple positive keywords
            confidence = min(100, 50 + len(positive_matches) * 15)
            
            # Check for specific interview indicators
            if any(kw in text for kw in ['interview', 'schedule', 'call', 'meeting']):
                return ('INTERVIEW_REQUEST', confidence, positive_matches)
            elif any(kw in text for kw in ['offer', 'join', 'welcome']):
                return ('OFFER', confidence, positive_matches)
            else:
                return ('POSITIVE_RESPONSE', confidence, positive_matches)
        
        # Check for rejection
        rejection_matches = [kw for kw in self.REJECTION_KEYWORDS if kw in text]
        if rejection_matches:
            confidence = min(100, 50 + len(rejection_matches) * 15)
            return ('REJECTION', confidence, rejection_matches)
        
        # Check for acknowledgment
        ack_matches = [kw for kw in self.ACKNOWLEDGMENT_KEYWORDS if kw in text]
        if ack_matches:
            return ('ACKNOWLEDGMENT', 60, ack_matches)
        
        # Unknown - needs manual review
        return ('NEEDS_REVIEW', 30, [])
    
    def load_sent_emails(self) -> set:
        """Load companies we've sent emails to.
        
        Only returns companies that the current user has emailed (multi-user support).
        """
        sent_log_path = os.path.join(self.data_path, 'sent_emails_log.csv')
        companies = set()
        
        if os.path.exists(sent_log_path):
            df = pd.read_csv(sent_log_path)
            # Filter by sender_email for multi-user support
            if 'sender_email' in df.columns and self.email_address:
                df = df[df['sender_email'].str.lower() == self.email_address.lower()]
            if 'company' in df.columns:
                companies = set(df['company'].str.lower().dropna())
            if 'recipient_email' in df.columns:
                # Also track domains we've emailed
                for email in df['recipient_email'].dropna():
                    if '@' in str(email):
                        domain = email.split('@')[1].replace('.com', '').replace('.in', '')
                        companies.add(domain.lower())
        
        return companies
    
    def is_from_company_we_emailed(self, from_address: str, sent_companies: set) -> bool:
        """Check if the reply is from a company we emailed."""
        from_lower = from_address.lower()
        
        # Extract domain
        if '@' in from_lower:
            domain = from_lower.split('@')[1]
            domain_name = domain.split('.')[0]
            
            if domain_name in sent_companies:
                return True
            
            # Check variations
            for company in sent_companies:
                if company in domain_name or domain_name in company:
                    return True
        
        return False
    
    def scan_for_replies(self, days_back: int = 7) -> list:
        """
        Scan inbox for HR replies.
        
        Args:
            days_back: How many days back to scan
            
        Returns:
            List of reply dictionaries
        """
        logging.info("="*60)
        logging.info("📬 REPLY DETECTOR")
        logging.info("="*60)
        
        if not self.password:
            logging.error("❌ SENDER_PASSWORD not set!")
            return []
        
        mail = self.connect_to_inbox()
        if not mail:
            return []
        
        replies = []
        sent_companies = self.load_sent_emails()
        logging.info(f"📋 Tracking replies from {len(sent_companies)} companies")
        
        try:
            mail.select('INBOX')
            
            # Search for emails from last N days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
            _, message_numbers = mail.search(None, f'(SINCE {since_date})')
            
            email_ids = message_numbers[0].split()
            logging.info(f"📧 Scanning {len(email_ids)} emails from last {days_back} days...")
            
            for email_id in email_ids:
                try:
                    _, msg_data = mail.fetch(email_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    # Get sender
                    from_header = msg.get('From', '')
                    from_address = ''
                    if '<' in from_header:
                        from_address = from_header.split('<')[1].split('>')[0]
                    else:
                        from_address = from_header
                    
                    # Skip if not from a company we emailed
                    if not self.is_from_company_we_emailed(from_address, sent_companies):
                        continue
                    
                    # Get email content
                    subject = self.decode_email_subject(msg)
                    body = self.decode_email_body(msg)
                    
                    # Skip auto-replies
                    if self.is_auto_reply(subject, body):
                        continue
                    
                    # Categorize the reply
                    category, confidence, keywords = self.categorize_reply(subject, body)
                    
                    # Get date
                    date_str = msg.get('Date', '')
                    
                    reply_info = {
                        'from_email': from_address,
                        'from_name': from_header.split('<')[0].strip() if '<' in from_header else '',
                        'subject': subject[:200],  # Truncate long subjects
                        'date': date_str,
                        'category': category,
                        'confidence': confidence,
                        'keywords_matched': ', '.join(keywords[:5]),
                        'body_preview': body[:500] if body else '',
                        'detected_at': datetime.now().isoformat()
                    }
                    
                    replies.append(reply_info)
                    
                    # Log based on category
                    if category == 'INTERVIEW_REQUEST':
                        logging.info(f"   🎉 INTERVIEW: {from_address} - {subject[:50]}")
                    elif category == 'OFFER':
                        logging.info(f"   🏆 OFFER: {from_address} - {subject[:50]}")
                    elif category == 'POSITIVE_RESPONSE':
                        logging.info(f"   ✅ POSITIVE: {from_address} - {subject[:50]}")
                    elif category == 'REJECTION':
                        logging.info(f"   ❌ REJECTION: {from_address} - {subject[:50]}")
                    elif category == 'ACKNOWLEDGMENT':
                        logging.info(f"   📥 ACK: {from_address} - {subject[:50]}")
                    else:
                        logging.info(f"   📧 REVIEW: {from_address} - {subject[:50]}")
                        
                except Exception as e:
                    logging.debug(f"Error processing email: {e}")
                    continue
            
            mail.logout()
            
        except Exception as e:
            logging.error(f"Error scanning inbox: {e}")
            return []
        
        logging.info(f"\n📊 Found {len(replies)} relevant replies")
        return replies
    
    def save_replies(self, replies: list):
        """Save detected replies to CSV files."""
        if not replies:
            return
        
        replies_df = pd.DataFrame(replies)
        
        # Save all replies
        if os.path.exists(self.replies_log_path):
            existing = pd.read_csv(self.replies_log_path)
            # Avoid duplicates based on from_email + subject + date
            replies_df = pd.concat([existing, replies_df], ignore_index=True)
            replies_df = replies_df.drop_duplicates(
                subset=['from_email', 'subject', 'date'], 
                keep='last'
            )
        
        replies_df.to_csv(self.replies_log_path, index=False)
        logging.info(f"💾 Saved {len(replies_df)} replies to {self.replies_log_path}")
        
        # Extract interview requests separately
        interview_df = replies_df[
            replies_df['category'].isin(['INTERVIEW_REQUEST', 'OFFER', 'POSITIVE_RESPONSE'])
        ]
        
        if not interview_df.empty:
            interview_df.to_csv(self.interview_requests_path, index=False)
            logging.info(f"🎯 Saved {len(interview_df)} interview/positive responses!")
    
    def get_summary(self) -> dict:
        """Get summary of all detected replies."""
        summary = {
            'total_replies': 0,
            'interview_requests': 0,
            'offers': 0,
            'positive_responses': 0,
            'rejections': 0,
            'acknowledgments': 0,
            'needs_review': 0
        }
        
        if os.path.exists(self.replies_log_path):
            df = pd.read_csv(self.replies_log_path)
            summary['total_replies'] = len(df)
            
            if 'category' in df.columns:
                summary['interview_requests'] = len(df[df['category'] == 'INTERVIEW_REQUEST'])
                summary['offers'] = len(df[df['category'] == 'OFFER'])
                summary['positive_responses'] = len(df[df['category'] == 'POSITIVE_RESPONSE'])
                summary['rejections'] = len(df[df['category'] == 'REJECTION'])
                summary['acknowledgments'] = len(df[df['category'] == 'ACKNOWLEDGMENT'])
                summary['needs_review'] = len(df[df['category'] == 'NEEDS_REVIEW'])
        
        return summary


def main():
    """Main function to detect replies."""
    detector = ReplyDetector()
    
    # Scan for replies
    replies = detector.scan_for_replies(days_back=14)
    
    # Save results
    detector.save_replies(replies)
    
    # Print summary
    summary = detector.get_summary()
    
    logging.info("\n" + "="*60)
    logging.info("📊 REPLY SUMMARY")
    logging.info("="*60)
    logging.info(f"   📬 Total HR Replies: {summary['total_replies']}")
    logging.info(f"   🎉 Interview Requests: {summary['interview_requests']}")
    logging.info(f"   🏆 Offers: {summary['offers']}")
    logging.info(f"   ✅ Positive Responses: {summary['positive_responses']}")
    logging.info(f"   ❌ Rejections: {summary['rejections']}")
    logging.info(f"   📥 Acknowledgments: {summary['acknowledgments']}")
    logging.info(f"   📋 Needs Review: {summary['needs_review']}")
    logging.info("="*60)


if __name__ == "__main__":
    main()
