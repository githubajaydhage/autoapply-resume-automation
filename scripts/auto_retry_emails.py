#!/usr/bin/env python3
"""
Auto-Retry Failed Emails - Smart retry system with verification
Only retries with valid, verified alternate email addresses
"""

import os
import re
import json
import logging
import smtplib
import pandas as pd
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Tuple
import dns.resolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class EmailVerifier:
    """Verify email addresses before retrying."""
    
    def __init__(self):
        self.verified_cache = {}
        self.cache_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'email_verification_cache.json'
        )
        self._load_cache()
    
    def _load_cache(self):
        """Load verification cache."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.verified_cache = json.load(f)
        except:
            self.verified_cache = {}
    
    def _save_cache(self):
        """Save verification cache."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.verified_cache, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving cache: {e}")
    
    def verify_email(self, email: str) -> Tuple[bool, int, str]:
        """
        Verify email address exists and is deliverable.
        
        Returns: (is_valid, score, reason)
        Score: 0-100 (100 = definitely valid)
        """
        email = email.lower().strip()
        
        # Check cache first
        if email in self.verified_cache:
            cached = self.verified_cache[email]
            return cached['valid'], cached['score'], cached['reason']
        
        score = 0
        reasons = []
        
        # 1. Basic format validation (20 points)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            result = (False, 0, "Invalid email format")
            self._cache_result(email, result)
            return result
        score += 20
        
        # 2. Check for disposable/temporary email domains (reject)
        disposable_domains = [
            'tempmail', 'guerrillamail', '10minutemail', 'mailinator',
            'throwaway', 'fakeinbox', 'temp-mail', 'discard.email'
        ]
        domain = email.split('@')[1].lower()
        if any(d in domain for d in disposable_domains):
            result = (False, 0, "Disposable email domain")
            self._cache_result(email, result)
            return result
        
        # 3. Check for generic/invalid patterns (reduce score)
        invalid_prefixes = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon', 
                          'postmaster', 'abuse', 'spam', 'test', 'example']
        prefix = email.split('@')[0].lower()
        if any(prefix.startswith(p) for p in invalid_prefixes):
            reasons.append("Generic/system email address")
            score -= 30
        
        # 4. DNS MX record check (30 points)
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                score += 30
                reasons.append("Valid MX records")
            else:
                reasons.append("No MX records found")
        except dns.resolver.NXDOMAIN:
            result = (False, 0, "Domain does not exist")
            self._cache_result(email, result)
            return result
        except dns.resolver.NoAnswer:
            reasons.append("No MX records")
        except Exception as e:
            reasons.append(f"DNS check failed: {str(e)[:30]}")
        
        # 5. Check for HR-related patterns (bonus points)
        hr_patterns = ['hr', 'recruit', 'career', 'talent', 'hiring', 'jobs', 
                      'people', 'human.resource', 'staffing']
        if any(p in email.lower() for p in hr_patterns):
            score += 20
            reasons.append("HR-related email pattern")
        
        # 6. Check for company domain (not free email)
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                       'aol.com', 'icloud.com', 'mail.com', 'protonmail.com']
        if domain not in free_domains:
            score += 15
            reasons.append("Corporate domain")
        
        # 7. SMTP verification (15 points) - Optional, can be slow
        # Disabled by default to avoid being blocked
        # smtp_valid = self._smtp_verify(email)
        # if smtp_valid:
        #     score += 15
        
        # Cap score at 100
        score = min(100, max(0, score))
        
        is_valid = score >= 50
        reason = "; ".join(reasons) if reasons else "Basic validation passed"
        
        result = (is_valid, score, reason)
        self._cache_result(email, result)
        
        return result
    
    def _cache_result(self, email: str, result: Tuple[bool, int, str]):
        """Cache verification result."""
        self.verified_cache[email] = {
            'valid': result[0],
            'score': result[1],
            'reason': result[2],
            'checked_at': datetime.now().isoformat()
        }
        self._save_cache()
    
    def _smtp_verify(self, email: str) -> bool:
        """
        SMTP verification - checks if mailbox exists.
        Note: Many servers block this, use with caution.
        """
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host)
            server.helo('gmail.com')
            server.mail('test@gmail.com')
            code, _ = server.rcpt(email)
            server.quit()
            
            return code == 250
            
        except Exception:
            return False


class AutoRetryEmails:
    """
    Smart retry system for failed emails.
    
    Features:
    1. Identifies bounced/failed emails
    2. Finds alternate email addresses for same company
    3. Verifies alternates before retry
    4. Tracks retry attempts to avoid spam
    """
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.retry_log = os.path.join(self.data_dir, 'retry_log.csv')
        self.verifier = EmailVerifier()
        
        # Email config
        self.sender_email = os.environ.get('SENDER_EMAIL', 'biradarshweta48@gmail.com')
        self.sender_password = os.environ.get('SENDER_PASSWORD', '')
        self.sender_name = os.environ.get('SENDER_NAME', 'Shweta Biradar')
        
        self.max_retries_per_company = 2
        self.retry_delay_days = 3  # Wait before retry
        
        self._init_retry_log()
    
    def _init_retry_log(self):
        """Initialize retry log."""
        if not os.path.exists(self.retry_log):
            df = pd.DataFrame(columns=[
                'original_email', 'company', 'job_title', 'failed_at',
                'failure_reason', 'retry_email', 'retry_status',
                'retry_at', 'retry_count'
            ])
            os.makedirs(self.data_dir, exist_ok=True)
            df.to_csv(self.retry_log, index=False)
    
    def get_failed_emails(self) -> pd.DataFrame:
        """Get list of failed/bounced emails that need retry."""
        bounced_file = os.path.join(self.data_dir, 'bounced_emails.csv')
        sent_log = os.path.join(self.data_dir, 'sent_emails_log.csv')
        
        failed_emails = []
        
        # Get bounced emails
        if os.path.exists(bounced_file):
            try:
                bounced = pd.read_csv(bounced_file)
                for _, row in bounced.iterrows():
                    failed_emails.append({
                        'email': row.get('email', row.get('bounced_email', '')),
                        'company': row.get('company', 'Unknown'),
                        'job_title': row.get('job_title', ''),
                        'reason': row.get('bounce_reason', row.get('reason', 'bounced'))
                    })
            except Exception as e:
                logging.error(f"Error reading bounced: {e}")
        
        # Check sent log for failures
        if os.path.exists(sent_log):
            try:
                sent = pd.read_csv(sent_log)
                if 'status' in sent.columns:
                    failed = sent[sent['status'].str.contains('failed|error|bounced', case=False, na=False)]
                    for _, row in failed.iterrows():
                        failed_emails.append({
                            'email': row.get('recipient_email', ''),
                            'company': row.get('company', 'Unknown'),
                            'job_title': row.get('job_title', ''),
                            'reason': row.get('status', 'failed')
                        })
            except Exception as e:
                logging.error(f"Error reading sent log: {e}")
        
        return pd.DataFrame(failed_emails).drop_duplicates(subset=['email'])
    
    def find_alternate_emails(self, company: str, failed_email: str) -> List[Dict]:
        """Find alternate email addresses for the same company."""
        alternates = []
        
        # Search in HR database
        hr_files = [
            'curated_hr_emails.csv',
            'all_hr_emails.csv',
            'verified_hr_emails.csv',
            'scraped_hr_emails.csv'
        ]
        
        company_lower = company.lower()
        failed_domain = failed_email.split('@')[1].lower() if '@' in failed_email else ''
        
        for hr_file in hr_files:
            filepath = os.path.join(self.data_dir, hr_file)
            if not os.path.exists(filepath):
                continue
            
            try:
                df = pd.read_csv(filepath)
                email_col = 'email' if 'email' in df.columns else 'hr_email'
                
                for _, row in df.iterrows():
                    email = str(row.get(email_col, '')).lower()
                    row_company = str(row.get('company', '')).lower()
                    
                    if not email or email == failed_email.lower():
                        continue
                    
                    # Match by company name or domain
                    email_domain = email.split('@')[1] if '@' in email else ''
                    
                    if (company_lower in row_company or 
                        row_company in company_lower or
                        (failed_domain and email_domain == failed_domain)):
                        
                        # Verify before adding
                        is_valid, score, reason = self.verifier.verify_email(email)
                        
                        if is_valid and score >= 60:
                            alternates.append({
                                'email': email,
                                'company': row.get('company', company),
                                'score': score,
                                'source': hr_file
                            })
                            
            except Exception as e:
                logging.error(f"Error reading {hr_file}: {e}")
        
        # Sort by verification score
        alternates.sort(key=lambda x: x['score'], reverse=True)
        
        return alternates[:3]  # Return top 3 alternates
    
    def should_retry(self, company: str) -> bool:
        """Check if we should retry for this company."""
        try:
            df = pd.read_csv(self.retry_log)
            company_retries = df[df['company'].str.lower() == company.lower()]
            
            # Check retry count
            if len(company_retries) >= self.max_retries_per_company:
                return False
            
            # Check if last retry was recent
            if not company_retries.empty:
                last_retry = pd.to_datetime(company_retries['retry_at'].max())
                # Remove timezone for safe comparison
                if last_retry.tzinfo is not None:
                    last_retry = last_retry.tz_localize(None)
                if datetime.now() - last_retry < timedelta(days=self.retry_delay_days):
                    return False
            
            return True
            
        except Exception:
            return True
    
    def retry_email(self, original_email: str, company: str, job_title: str,
                   alternate_email: str, alternate_score: int) -> bool:
        """Retry sending email to alternate address."""
        
        logging.info(f"🔄 Retrying email for {company}")
        logging.info(f"   Original: {original_email} (failed)")
        logging.info(f"   Alternate: {alternate_email} (score: {alternate_score})")
        
        if not self.sender_password:
            logging.warning("No SENDER_PASSWORD set, cannot send")
            return False
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = alternate_email
            msg['Subject'] = f"Application for {job_title or 'Open Position'} - {company}"
            
            body = f"""Dear Hiring Manager,

I previously reached out regarding opportunities at {company} but my email may not have been delivered. 

I am writing to express my interest in {job_title or 'open positions'} at {company}. With my background in software development and data analysis, I believe I would be a strong addition to your team.

I have attached my resume for your review. I would welcome the opportunity to discuss how I can contribute to {company}.

Thank you for your time and consideration.

Best regards,
{self.sender_name}
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach resume
            resume_path = os.path.join(os.path.dirname(__file__), '..', 'resumes')
            for filename in os.listdir(resume_path):
                if filename.endswith('.pdf') and 'resume' in filename.lower():
                    with open(os.path.join(resume_path, filename), 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)
                    break
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            # Log retry
            self._log_retry(original_email, company, job_title, alternate_email, 'success')
            
            logging.info(f"✅ Retry successful: {alternate_email}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Retry failed: {e}")
            self._log_retry(original_email, company, job_title, alternate_email, f'failed: {str(e)[:50]}')
            return False
    
    def _log_retry(self, original_email: str, company: str, job_title: str,
                   retry_email: str, status: str):
        """Log retry attempt."""
        try:
            df = pd.read_csv(self.retry_log)
            
            new_entry = {
                'original_email': original_email,
                'company': company,
                'job_title': job_title,
                'failed_at': datetime.now().isoformat(),
                'failure_reason': 'bounced',
                'retry_email': retry_email,
                'retry_status': status,
                'retry_at': datetime.now().isoformat(),
                'retry_count': len(df[df['company'] == company]) + 1
            }
            
            new_row = pd.DataFrame([new_entry])
            if df.empty:
                df = new_row
            else:
                df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.retry_log, index=False)
            
        except Exception as e:
            logging.error(f"Error logging retry: {e}")
    
    def process_retries(self) -> Dict:
        """Process all failed emails and attempt retries."""
        stats = {'processed': 0, 'retried': 0, 'success': 0, 'skipped': 0}
        
        failed = self.get_failed_emails()
        logging.info(f"📊 Found {len(failed)} failed emails to process")
        
        for _, row in failed.iterrows():
            email = row['email']
            company = row['company']
            job_title = row.get('job_title', '')
            
            stats['processed'] += 1
            
            if not self.should_retry(company):
                logging.info(f"⏭️ Skipping {company} - max retries reached or recent retry")
                stats['skipped'] += 1
                continue
            
            # Find alternates
            alternates = self.find_alternate_emails(company, email)
            
            if not alternates:
                logging.info(f"❌ No valid alternates found for {company}")
                continue
            
            # Try best alternate
            best = alternates[0]
            stats['retried'] += 1
            
            if self.retry_email(email, company, job_title, best['email'], best['score']):
                stats['success'] += 1
        
        return stats


def main():
    """Main function - process email retries."""
    logging.info("=" * 60)
    logging.info("🔄 AUTO-RETRY FAILED EMAILS")
    logging.info("=" * 60)
    
    retrier = AutoRetryEmails()
    
    # Process retries
    stats = retrier.process_retries()
    
    logging.info("")
    logging.info("📊 RETRY SUMMARY:")
    logging.info(f"   Processed: {stats['processed']}")
    logging.info(f"   Retried: {stats['retried']}")
    logging.info(f"   Success: {stats['success']}")
    logging.info(f"   Skipped: {stats['skipped']}")
    
    logging.info("=" * 60)
    logging.info("✅ Auto-retry complete!")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
