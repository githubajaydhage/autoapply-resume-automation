#!/usr/bin/env python3
"""
Enhanced Email Deliverability Checker
Identifies and fixes common issues preventing HR responses and job applications
"""

import pandas as pd
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import dns.resolver
import re
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class EmailDeliverabilityAuditor:
    """
    Comprehensive email deliverability audit and fixes
    Addresses issues preventing HR responses and calls
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.sent_emails_file = self.data_dir / "sent_emails_log.csv"
        self.bounced_emails_file = self.data_dir / "bounced_emails.csv"
        self.hr_emails_file = self.data_dir / "discovered_hr_emails.csv" 
        self.jobs_file = self.data_dir / "jobs_today.csv"
        self.applied_file = self.data_dir / "applied_log.csv"
        self.blacklist_file = self.data_dir / "email_blacklist.csv"
        
        # Issues tracking
        self.issues_found = []
        self.fixes_applied = []
        
    def audit_email_system(self) -> Dict:
        """Run comprehensive audit of email system."""
        logging.info("🔍 Starting Email Deliverability Audit...")
        
        audit_results = {
            'sent_emails': self._audit_sent_emails(),
            'job_discovery': self._audit_job_discovery(),
            'hr_email_quality': self._audit_hr_email_quality(),
            'bounce_rate': self._audit_bounce_rate(),
            'response_rate': self._audit_response_rate(),
            'email_content': self._audit_email_content()
        }
        
        recommendations = self._generate_recommendations(audit_results)
        
        return {
            'audit_results': audit_results,
            'issues_found': self.issues_found,
            'recommendations': recommendations,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _audit_sent_emails(self) -> Dict:
        """Audit sent emails and authentication status."""
        logging.info("📧 Auditing sent emails...")
        
        if not self.sent_emails_file.exists():
            issue = "❌ No sent emails log found - emails may not be sending!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        df = pd.read_csv(self.sent_emails_file)
        
        if len(df) == 0:
            issue = "❌ Sent emails log is empty - no emails being sent!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        # Check authentication failures
        auth_failures = 0
        if 'status' in df.columns:
            auth_failed_df = df[df['status'].str.contains('auth_failed|authentication|535', case=False, na=False)]
            auth_failures = len(auth_failed_df)
        
        results = {
            'total_sent': len(df),
            'auth_failures': auth_failures,
            'auth_failure_rate': (auth_failures / len(df)) * 100,
            'last_sent': df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else 'Unknown'
        }
        
        if auth_failures > 0:
            self.issues_found.append(f"❌ {auth_failures} emails failed authentication - check Gmail app password!")
        
        return results
    
    def _audit_job_discovery(self) -> Dict:
        """Audit job discovery and targeting."""
        logging.info("🎯 Auditing job discovery...")
        
        if not self.jobs_file.exists():
            issue = "❌ No jobs file found - job scraping not working!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        df = pd.read_csv(self.jobs_file)
        
        if len(df) == 0:
            issue = "❌ No jobs found today - scraper may be broken!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        # Check job quality
        today = datetime.now().strftime('%Y-%m-%d')
        jobs_today = 0
        if 'date_posted' in df.columns:
            jobs_today = len(df[df['date_posted'].str.contains(today, na=False)])
        
        # Check if jobs have HR emails attached
        jobs_with_hr = 0
        if 'hr_email' in df.columns or 'primary_hr_email' in df.columns:
            hr_col = 'hr_email' if 'hr_email' in df.columns else 'primary_hr_email'
            jobs_with_hr = len(df[df[hr_col].notna()])
        
        results = {
            'total_jobs': len(df),
            'jobs_found_today': jobs_today,
            'jobs_with_hr_emails': jobs_with_hr,
            'hr_coverage_rate': (jobs_with_hr / len(df)) * 100 if len(df) > 0 else 0
        }
        
        if jobs_today == 0:
            self.issues_found.append("❌ No new jobs found today - check job scrapers")
        
        if results['hr_coverage_rate'] < 50:
            self.issues_found.append(f"❌ Only {results['hr_coverage_rate']:.1f}% of jobs have HR emails attached!")
        
        return results
    
    def _audit_hr_email_quality(self) -> Dict:
        """Audit quality of discovered HR emails."""
        logging.info("👤 Auditing HR email quality...")
        
        # Check discovered HR emails
        hr_emails = []
        if self.hr_emails_file.exists():
            df = pd.read_csv(self.hr_emails_file)
            if 'email' in df.columns:
                hr_emails = df['email'].dropna().tolist()
        
        # Also check job file for HR emails
        if self.jobs_file.exists():
            jobs_df = pd.read_csv(self.jobs_file)
            if 'hr_email' in jobs_df.columns:
                hr_emails.extend(jobs_df['hr_email'].dropna().tolist())
            if 'primary_hr_email' in jobs_df.columns:
                hr_emails.extend(jobs_df['primary_hr_email'].dropna().tolist())
        
        if len(hr_emails) == 0:
            issue = "❌ No HR emails found - HR discovery not working!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        # Analyze email quality
        valid_emails = []
        invalid_emails = []
        generic_emails = []
        
        generic_patterns = ['info@', 'contact@', 'support@', 'admin@', 'sales@', 'hello@']
        
        for email in hr_emails:
            if not email or pd.isna(email):
                continue
                
            email = str(email).lower().strip()
            
            if '@' not in email or '.' not in email:
                invalid_emails.append(email)
            elif any(pattern in email for pattern in generic_patterns):
                generic_emails.append(email)
            else:
                valid_emails.append(email)
        
        results = {
            'total_emails': len(hr_emails),
            'valid_emails': len(valid_emails),
            'invalid_emails': len(invalid_emails),
            'generic_emails': len(generic_emails),
            'quality_score': (len(valid_emails) / len(hr_emails)) * 100 if hr_emails else 0
        }
        
        if results['quality_score'] < 50:
            self.issues_found.append(f"❌ Poor email quality: {results['quality_score']:.1f}% valid emails")
        elif results['quality_score'] < 80:
            self.issues_found.append(f"⚠️ Moderate email quality: {results['quality_score']:.1f}% valid emails")
        
        return results
    
    def _audit_bounce_rate(self) -> Dict:
        """Audit email bounce rate."""
        logging.info("📉 Auditing bounce rate...")
        
        if not self.sent_emails_file.exists():
            return {'bounce_rate': 0, 'issue': 'No sent emails to analyze'}
        
        df = pd.read_csv(self.sent_emails_file)
        
        if len(df) == 0:
            return {'bounce_rate': 0, 'issue': 'No sent emails'}
        
        # Count bounced emails
        bounced_count = 0
        if 'status' in df.columns:
            bounced_count = len(df[df['status'].str.contains('bounce|fail', case=False, na=False)])
        
        bounce_rate = (bounced_count / len(df)) * 100
        
        results = {
            'total_sent': len(df),
            'bounced_count': bounced_count,
            'bounce_rate': bounce_rate
        }
        
        if bounce_rate > 20:
            self.issues_found.append(f"❌ High bounce rate: {bounce_rate:.1f}% - emails not reaching recipients!")
        elif bounce_rate > 10:
            self.issues_found.append(f"⚠️ Moderate bounce rate: {bounce_rate:.1f}% - some emails failing")
        
        return results
    
    def _audit_response_rate(self) -> Dict:
        """Audit response rate from HR."""
        logging.info("📊 Auditing response rate...")
        
        if not self.sent_emails_file.exists():
            return {'response_rate': 0, 'issue': 'No sent emails to analyze'}
        
        df = pd.read_csv(self.sent_emails_file)
        
        if len(df) == 0:
            return {'response_rate': 0, 'issue': 'No sent emails'}
        
        # Count responses
        responses = 0
        if 'replied' in df.columns:
            responses = len(df[df['replied'].str.contains('true|yes', case=False, na=False)])
        
        response_rate = (responses / len(df)) * 100
        
        results = {
            'total_sent': len(df),
            'responses': responses,
            'response_rate': response_rate
        }
        
        if response_rate < 2:
            self.issues_found.append(f"❌ Very low response rate: {response_rate:.1f}% - emails may not be compelling or reaching right people")
        elif response_rate < 5:
            self.issues_found.append(f"⚠️ Low response rate: {response_rate:.1f}% - email quality needs improvement")
        
        return results
    
    def _audit_email_content(self) -> Dict:
        """Audit email content quality."""
        logging.info("📝 Auditing email content quality...")
        
        # This would need to check actual email templates
        # For now, return basic analysis
        return {
            'status': 'info',
            'message': 'Email content audit requires template analysis'
        }
    
    def _generate_recommendations(self, audit_results: Dict) -> List[str]:
        """Generate specific recommendations based on audit results."""
        recommendations = []
        
        # Job discovery recommendations
        if audit_results['job_discovery'].get('jobs_found_today', 0) == 0:
            recommendations.append("🔧 FIX: Enable job scraping - run: python scripts/enhanced_job_scraper.py")
            recommendations.append("🔧 FIX: Check scraper credentials and rate limits")
        
        # HR email recommendations
        hr_quality = audit_results['hr_email_quality'].get('quality_score', 0)
        if hr_quality < 50:
            recommendations.append("🔧 FIX: Improve HR email discovery - run: python scripts/ai_hr_email_discovery.py")
            recommendations.append("🔧 FIX: Use LinkedIn email finder for better quality emails")
        
        # Bounce rate recommendations
        bounce_rate = audit_results['bounce_rate'].get('bounce_rate', 0)
        if bounce_rate > 10:
            recommendations.append("🔧 FIX: Enable email verification - run: python scripts/email_verifier.py")
            recommendations.append("🔧 FIX: Check bounce detection - run: python scripts/bounce_checker.py")
            recommendations.append("🔧 FIX: Create email blacklist for bounced addresses")
        
        # Response rate recommendations
        response_rate = audit_results['response_rate'].get('response_rate', 0)
        if response_rate < 5:
            recommendations.append("🔧 FIX: Improve email personalization - use AI cover letters")
            recommendations.append("🔧 FIX: Check email timing - avoid weekends and late hours")
            recommendations.append("🔧 FIX: Use professional email templates with clear CTAs")
            recommendations.append("🔧 FIX: Target specific HR roles, not generic info@ emails")
        
        # General recommendations
        recommendations.extend([
            "📈 OPTIMIZE: Run email open tracking to see if emails are being read",
            "📈 OPTIMIZE: Set up auto-follow-ups for higher response rates",
            "📈 OPTIMIZE: Use AI job matching to apply only to relevant positions",
            "📈 OPTIMIZE: Monitor LinkedIn for warm connections at target companies"
        ])
        
        return recommendations
    
    def apply_fixes(self) -> bool:
        """Apply automated fixes for common issues."""
        logging.info("🔧 Applying automated fixes...")
        
        try:
            # Create bounced emails blacklist
            self._create_email_blacklist()
            
            # Clean invalid emails from HR database
            self._clean_hr_emails()
            
            # Update email verification settings
            self._update_verification_settings()
            
            logging.info(f"✅ Applied {len(self.fixes_applied)} fixes")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error applying fixes: {e}")
            return False
    
    def _create_email_blacklist(self):
        """Create blacklist of bounced/invalid emails."""
        blacklist = set()
        
        # Add bounced emails
        if self.bounced_emails_file.exists():
            df = pd.read_csv(self.bounced_emails_file)
            if 'email' in df.columns:
                blacklist.update(df['email'].dropna().str.lower())
        
        # Add known bad patterns
        bad_patterns = [
            'noreply@', 'no-reply@', 'donotreply@', 'mailer-daemon@',
            'postmaster@', 'admin@example.com', 'test@test.com'
        ]
        
        if blacklist or bad_patterns:
            blacklist_df = pd.DataFrame({
                'email': list(blacklist),
                'reason': 'bounced',
                'date_added': datetime.now().strftime('%Y-%m-%d')
            })
            blacklist_df.to_csv(self.blacklist_file, index=False)
            self.fixes_applied.append(f"Created email blacklist with {len(blacklist)} entries")
    
    def _clean_hr_emails(self):
        """Remove invalid emails from HR database."""
        if self.hr_emails_file.exists():
            df = pd.read_csv(self.hr_emails_file)
            original_count = len(df)
            
            # Remove invalid emails
            df = df[df['email'].str.contains('@', na=False)]
            df = df[df['email'].str.contains('\\.', na=False, regex=True)]
            
            if len(df) < original_count:
                df.to_csv(self.hr_emails_file, index=False)
                removed = original_count - len(df)
                self.fixes_applied.append(f"Removed {removed} invalid emails from HR database")
    
    def _update_verification_settings(self):
        """Update email verification settings for better deliverability."""
        # Create config file with stricter verification settings
        config = {
            'min_deliverability_score': 70,
            'enable_mx_check': True,
            'enable_bounce_detection': True,
            'skip_generic_emails': True,
            'max_bounce_rate': 15
        }
        
        config_file = self.data_dir / "email_verification_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.fixes_applied.append("Updated email verification settings for better deliverability")

def main():
    """Run email deliverability audit."""
    auditor = EmailDeliverabilityAuditor()
    
    print("\n" + "="*60)
    print("🔍 EMAIL DELIVERABILITY AUDIT & DIAGNOSIS")
    print("="*60)
    
    results = auditor.audit_email_system()
    
    print("\n📊 AUDIT RESULTS:")
    print("-" * 30)
    
    for category, data in results['audit_results'].items():
        if isinstance(data, dict) and 'issue' not in data:
            print(f"\n{category.upper()}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    if results['issues_found']:
        print("\n❌ ISSUES FOUND:")
        print("-" * 30)
        for issue in results['issues_found']:
            print(f"  {issue}")
    
    if results['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 30)
        for rec in results['recommendations']:
            print(f"  {rec}")
    
    # Apply fixes
    print("\n🔧 APPLYING FIXES...")
    if auditor.apply_fixes():
        print("✅ Fixes applied successfully!")
        if auditor.fixes_applied:
            for fix in auditor.fixes_applied:
                print(f"  ✓ {fix}")
    else:
        print("❌ Some fixes failed")
    
    print("\n" + "="*60)
    print("✅ AUDIT COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()