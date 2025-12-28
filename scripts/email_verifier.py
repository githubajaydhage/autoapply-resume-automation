"""
Email Verifier - Validates email addresses before sending using multiple methods
"""

import socket
import smtplib
import dns.resolver
import re
import os
import sys
import logging
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class EmailVerifier:
    """
    Comprehensive email verification with multiple validation levels:
    1. Syntax validation
    2. Domain/MX record check
    3. SMTP verification (check if mailbox exists)
    4. Known bad email patterns
    5. Reputation scoring
    """
    
    # Known invalid/fake email patterns
    INVALID_PATTERNS = [
        r'.*@example\.com$',
        r'.*@test\.com$',
        r'.*@fake\.com$',
        r'noreply@.*',
        r'no-reply@.*',
        r'donotreply@.*',
        r'mailer-daemon@.*',
        r'postmaster@.*',
    ]
    
    # Non-HR patterns (should not email these)
    NON_HR_PATTERNS = [
        'info@', 'support@', 'contact@', 'help@', 'service@',
        'sales@', 'marketing@', 'admin@', 'office@', 'press@',
        'media@', 'legal@', 'finance@', 'billing@', 'accounts@',
        'customer@', 'enquir', 'query', 'feedback@', 'complaints@',
        'ombuds', 'federal@', 'gsc@', 'cc@', 'webmaster@'
    ]
    
    # Known high-risk domains (likely to bounce) - domain -> list of bad prefixes
    HIGH_RISK_DOMAINS = {
        # Companies that ONLY accept applications via portal
        'google.com': ['jobs@', 'careers@', 'recruiting@'],
        'microsoft.com': ['jobs@', 'careers@', 'recruiting@'],
        'amazon.com': ['jobs@', 'careers@', 'amazon-hiring@'],
        'apple.com': ['jobs@', 'careers@', 'recruiting@'],
        'meta.com': ['jobs@', 'careers@', 'recruiting@'],
        'fb.com': ['jobs@', 'careers@', 'recruiting@'],
        'netflix.com': ['jobs@', 'careers@', 'recruiting@'],
        'uber.com': ['jobs@', 'careers@', 'recruiting@'],
    }
    
    # Known GOOD company HR emails (verified to work)
    VERIFIED_HR_EMAILS = {
        # Indian IT Companies
        'helpdesk.recruitment@wipro.com': 'Wipro',
        'career@razorpay.com': 'Razorpay',
        'recrops@ca.ibm.com': 'IBM',
        # Add more verified emails here as you confirm them
    }
    
    # Known BAD emails (don't waste time on these)
    KNOWN_BAD_EMAILS = {
        'jobs@google.com': 'Google does not accept direct applications',
        'careers@microsoft.com': 'Microsoft uses ATS only',
        'amazon-hiring@amazon.com': 'Not a valid Amazon email',
        'recruiting@fb.com': 'Meta does not accept direct applications',
        'careers@apple.com': 'Apple uses ATS only',
    }
    
    def __init__(self):
        self.mx_cache = {}  # Cache MX lookups
        self.smtp_cache = {}  # Cache SMTP verification results
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.verification_log_path = os.path.join(self.data_dir, 'email_verification_log.csv')
        
    def validate_syntax(self, email: str) -> tuple:
        """Check if email has valid syntax."""
        if not email or not isinstance(email, str):
            return False, "Empty or invalid email"
        
        email = email.strip().lower()
        
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check against invalid patterns
        for invalid in self.INVALID_PATTERNS:
            if re.match(invalid, email, re.IGNORECASE):
                return False, "Matches invalid pattern"
        
        return True, "Valid syntax"
    
    def check_known_status(self, email: str) -> tuple:
        """Check if email is in known good/bad lists."""
        email_lower = email.lower()
        
        # Check known bad emails
        if email_lower in self.KNOWN_BAD_EMAILS:
            return False, self.KNOWN_BAD_EMAILS[email_lower]
        
        # Check known good emails
        if email_lower in self.VERIFIED_HR_EMAILS:
            return True, f"Verified HR email for {self.VERIFIED_HR_EMAILS[email_lower]}"
        
        # Check high-risk domains
        domain = email_lower.split('@')[1]
        local_part = email_lower.split('@')[0]
        
        if domain in self.HIGH_RISK_DOMAINS:
            risk_prefixes = self.HIGH_RISK_DOMAINS[domain]
            if isinstance(risk_prefixes, list):
                for prefix in risk_prefixes:
                    if email_lower.startswith(prefix):
                        return False, f"High-risk generic email for {domain}"
        
        return None, "Unknown status"  # None means need to check further
    
    def is_hr_related(self, email: str) -> tuple:
        """Check if email is HR/recruitment related."""
        email_lower = email.lower()
        local_part = email_lower.split('@')[0]
        
        # Check if it matches non-HR patterns
        for pattern in self.NON_HR_PATTERNS:
            if pattern in email_lower:
                return False, f"Non-HR email (matches {pattern})"
        
        # HR keywords
        hr_keywords = [
            'career', 'careers', 'hr', 'recruit', 'recruiting', 'recruitment',
            'hiring', 'jobs', 'job', 'talent', 'people', 'human', 'staffing'
        ]
        
        for keyword in hr_keywords:
            if keyword in local_part:
                return True, "Contains HR keyword"
        
        # If no HR keyword but from valid company domain, might still be valid
        return None, "No HR keywords found"
    
    def check_mx_record(self, email: str) -> tuple:
        """Check if domain has valid MX records."""
        try:
            domain = email.split('@')[1].lower()
            
            # Check cache
            if domain in self.mx_cache:
                return self.mx_cache[domain]
            
            # Try MX lookup
            try:
                mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
                mx_hosts = [str(r.exchange) for r in mx_records]
                self.mx_cache[domain] = (True, f"MX records found: {mx_hosts[0]}")
                return True, f"MX records found"
            except dns.resolver.NXDOMAIN:
                self.mx_cache[domain] = (False, "Domain does not exist")
                return False, "Domain does not exist"
            except dns.resolver.NoAnswer:
                self.mx_cache[domain] = (False, "No MX records")
                return False, "No MX records"
            except dns.resolver.NoNameservers:
                self.mx_cache[domain] = (False, "No nameservers")
                return False, "No nameservers"
            except dns.exception.Timeout:
                self.mx_cache[domain] = (True, "DNS timeout (assumed valid)")
                return True, "DNS timeout (assumed valid)"
                
        except Exception as e:
            return True, f"MX check error: {e}"
    
    def smtp_verify(self, email: str, timeout: int = 10) -> tuple:
        """
        Verify email exists using SMTP RCPT TO command.
        Note: Many servers don't allow this or give false positives.
        """
        try:
            domain = email.split('@')[1].lower()
            
            # Check cache
            cache_key = email.lower()
            if cache_key in self.smtp_cache:
                return self.smtp_cache[cache_key]
            
            # Get MX record
            try:
                mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
                mx_host = str(mx_records[0].exchange).rstrip('.')
            except:
                return None, "Could not get MX record for SMTP check"
            
            # Try SMTP verification
            try:
                smtp = smtplib.SMTP(timeout=timeout)
                smtp.connect(mx_host)
                smtp.helo('verify.local')
                smtp.mail('test@verify.local')
                code, message = smtp.rcpt(email)
                smtp.quit()
                
                if code == 250:
                    self.smtp_cache[cache_key] = (True, "SMTP verified - mailbox exists")
                    return True, "SMTP verified - mailbox exists"
                elif code == 550:
                    self.smtp_cache[cache_key] = (False, "Mailbox does not exist")
                    return False, "Mailbox does not exist"
                else:
                    self.smtp_cache[cache_key] = (None, f"SMTP response: {code}")
                    return None, f"SMTP response: {code}"
                    
            except smtplib.SMTPServerDisconnected:
                return None, "Server disconnected"
            except smtplib.SMTPConnectError:
                return None, "Could not connect to mail server"
            except socket.timeout:
                return None, "Connection timeout"
            except Exception as e:
                return None, f"SMTP error: {str(e)[:50]}"
                
        except Exception as e:
            return None, f"Verification error: {e}"
    
    def calculate_deliverability_score(self, email: str) -> dict:
        """
        Calculate a deliverability score (0-100) for an email.
        Returns dict with score and details.
        """
        result = {
            'email': email,
            'score': 0,
            'is_deliverable': False,
            'checks': {},
            'recommendation': ''
        }
        
        score = 0
        
        # 1. Syntax check (20 points)
        syntax_valid, syntax_msg = self.validate_syntax(email)
        result['checks']['syntax'] = {'valid': syntax_valid, 'message': syntax_msg}
        if syntax_valid:
            score += 20
        else:
            result['score'] = 0
            result['recommendation'] = 'Invalid email format - do not send'
            return result
        
        # 2. Known status check (can be +30 or -100)
        known_status, known_msg = self.check_known_status(email)
        result['checks']['known_status'] = {'status': known_status, 'message': known_msg}
        if known_status is True:
            score += 30
        elif known_status is False:
            result['score'] = 0
            result['is_deliverable'] = False
            result['recommendation'] = f'Known bad email: {known_msg}'
            return result
        
        # 3. HR relevance check (20 points)
        is_hr, hr_msg = self.is_hr_related(email)
        result['checks']['hr_relevance'] = {'is_hr': is_hr, 'message': hr_msg}
        if is_hr is True:
            score += 20
        elif is_hr is False:
            result['score'] = score
            result['recommendation'] = f'Not an HR email: {hr_msg}'
            return result
        
        # 4. MX record check (20 points)
        mx_valid, mx_msg = self.check_mx_record(email)
        result['checks']['mx_record'] = {'valid': mx_valid, 'message': mx_msg}
        if mx_valid:
            score += 20
        else:
            result['score'] = score
            result['recommendation'] = f'Domain cannot receive email: {mx_msg}'
            return result
        
        # 5. SMTP verification (10 points) - optional, can fail silently
        smtp_valid, smtp_msg = self.smtp_verify(email, timeout=5)
        result['checks']['smtp_verify'] = {'valid': smtp_valid, 'message': smtp_msg}
        if smtp_valid is True:
            score += 10
        elif smtp_valid is False:
            # Definitive failure
            result['score'] = 0
            result['recommendation'] = f'Mailbox does not exist: {smtp_msg}'
            return result
        # If None, we can't determine, don't penalize
        
        result['score'] = score
        result['is_deliverable'] = score >= 50
        
        if score >= 80:
            result['recommendation'] = 'High confidence - safe to send'
        elif score >= 60:
            result['recommendation'] = 'Medium confidence - likely deliverable'
        elif score >= 40:
            result['recommendation'] = 'Low confidence - may bounce'
        else:
            result['recommendation'] = 'Very low confidence - do not send'
        
        return result
    
    def verify_email_list(self, emails: list, max_workers: int = 5) -> pd.DataFrame:
        """Verify a list of emails in parallel."""
        results = []
        
        logging.info(f"🔍 Verifying {len(emails)} emails...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_email = {
                executor.submit(self.calculate_deliverability_score, email): email 
                for email in emails
            }
            
            for i, future in enumerate(as_completed(future_to_email)):
                email = future_to_email[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    status = "✅" if result['is_deliverable'] else "❌"
                    logging.info(f"   {status} [{i+1}/{len(emails)}] {email}: {result['score']}/100 - {result['recommendation']}")
                    
                except Exception as e:
                    results.append({
                        'email': email,
                        'score': 0,
                        'is_deliverable': False,
                        'recommendation': f'Verification error: {e}'
                    })
        
        df = pd.DataFrame(results)
        
        # Save verification log
        df['verified_at'] = datetime.now().isoformat()
        if os.path.exists(self.verification_log_path):
            df_existing = pd.read_csv(self.verification_log_path)
            df_combined = pd.concat([df_existing, df], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['email'], keep='last')
            df_combined.to_csv(self.verification_log_path, index=False)
        else:
            df.to_csv(self.verification_log_path, index=False)
        
        logging.info(f"💾 Verification results saved to {self.verification_log_path}")
        
        return df
    
    def get_deliverable_emails(self, emails: list, min_score: int = 50) -> list:
        """Get list of emails that meet minimum deliverability score."""
        df = self.verify_email_list(emails)
        deliverable = df[df['score'] >= min_score]['email'].tolist()
        
        logging.info(f"\n📊 VERIFICATION SUMMARY:")
        logging.info(f"   Total checked: {len(emails)}")
        logging.info(f"   Deliverable (score >= {min_score}): {len(deliverable)}")
        logging.info(f"   Filtered out: {len(emails) - len(deliverable)}")
        
        return deliverable


def main():
    """Test email verification."""
    logging.info("="*60)
    logging.info("📧 EMAIL VERIFIER")
    logging.info("="*60)
    
    verifier = EmailVerifier()
    
    # Test emails
    test_emails = [
        'careers@phonepe.com',
        'careers@swiggy.in',
        'jobs@google.com',
        'careers@microsoft.com',
        'helpdesk.recruitment@wipro.com',
        'career@razorpay.com',
        'info@somecompany.com',
        'invalid-email-format',
        'nonexistent@thisdoesnotexist12345.com',
    ]
    
    logging.info(f"\n🔍 Testing {len(test_emails)} emails:\n")
    
    for email in test_emails:
        result = verifier.calculate_deliverability_score(email)
        status = "✅" if result['is_deliverable'] else "❌"
        logging.info(f"{status} {email}")
        logging.info(f"   Score: {result['score']}/100")
        logging.info(f"   Recommendation: {result['recommendation']}")
        logging.info("")
    
    logging.info("="*60)


if __name__ == "__main__":
    main()
