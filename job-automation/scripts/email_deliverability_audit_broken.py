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
            'email_content': self._audit_email_content(),
            'bounce_rate': self._audit_bounce_rate(),
            'response_rate': self._audit_response_rate()
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(audit_results)
        
        return {
            'audit_results': audit_results,
            'recommendations': recommendations,
            'issues_found': self.issues_found,
            'fixes_applied': self.fixes_applied
        }
    
    def _audit_sent_emails(self) -> Dict:
        """Audit sent emails for common issues."""
        logging.info("📧 Auditing sent emails...")
        
        if not self.sent_emails_file.exists():
            issue = "❌ No sent_emails_log.csv found - emails may not be sending at all!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        df = pd.read_csv(self.sent_emails_file)
        
        results = {
            'total_sent': len(df),
            'last_sent': df['timestamp'].max() if 'timestamp' in df.columns else 'Unknown',
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'unique_recipients': df['recipient_email'].nunique() if 'recipient_email' in df.columns else 0
        }
        
        # Check for issues
        if len(df) == 0:
            self.issues_found.append("❌ Zero emails sent - system not working!")
        elif len(df) < 10:
            self.issues_found.append(f"⚠️ Very few emails sent ({len(df)}) - may not be running regularly")
        
        # Check recent activity
        if 'timestamp' in df.columns:
            recent_emails = df[pd.to_datetime(df['timestamp']) > datetime.now() - timedelta(days=7)]
            if len(recent_emails) == 0:
                self.issues_found.append("❌ No emails sent in last 7 days - cron jobs may be failing")
        
        return results
    
    def _audit_job_discovery(self) -> Dict:
        """Audit job discovery system."""
        logging.info("💼 Auditing job discovery...")
        
        if not self.jobs_file.exists():
            issue = "❌ No jobs_today.csv found - job scraping not working!"
            self.issues_found.append(issue)
            return {'status': 'critical', 'issue': issue}
        
        df = pd.read_csv(self.jobs_file)
        
        results = {
            'jobs_found_today': len(df),
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'has_emails': len(df[df.get('email', '').notna()]) if 'email' in df.columns else 0,
            'recent_jobs': len(df) > 0
        }
        
        if len(df) == 0:
            self.issues_found.append("❌ Zero jobs discovered - scrapers not finding new opportunities!")
        elif results['has_emails'] == 0:
            self.issues_found.append("❌ Jobs found but no HR emails - email discovery failing!")
        elif results['has_emails'] < len(df) * 0.3:  # Less than 30% have emails
            self.issues_found.append(f"⚠️ Only {results['has_emails']}/{len(df)} jobs have HR emails - email discovery needs improvement")
        
        return results
    
    def _audit_hr_email_quality(self) -> Dict:
        """Audit HR email quality and deliverability."""
        logging.info("👤 Auditing HR email quality...")
        
        hr_emails = []
        
        # Collect HR emails from all sources
        if self.hr_emails_file.exists():
            df = pd.read_csv(self.hr_emails_file)
            if 'email' in df.columns:
                hr_emails.extend(df['email'].dropna().tolist())
        
        if self.jobs_file.exists():
            df = pd.read_csv(self.jobs_file)
            if 'email' in df.columns:
                hr_emails.extend(df['email'].dropna().tolist())
        
        if not hr_emails:
            issue = "❌ No HR emails found - cannot send applications!"
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
        
        return results\n    \n    def _audit_bounce_rate(self) -> Dict:\n        \"\"\"Audit email bounce rate.\"\"\"\n        logging.info(\"📉 Auditing bounce rate...\")\n        \n        if not self.sent_emails_file.exists():\n            return {'bounce_rate': 0, 'issue': 'No sent emails to analyze'}\n        \n        df = pd.read_csv(self.sent_emails_file)\n        \n        if len(df) == 0:\n            return {'bounce_rate': 0, 'issue': 'No sent emails'}\n        \n        # Count bounced emails\n        bounced_count = 0\n        if 'status' in df.columns:\n            bounced_count = len(df[df['status'].str.contains('bounce|fail', case=False, na=False)])\n        \n        bounce_rate = (bounced_count / len(df)) * 100\n        \n        results = {\n            'total_sent': len(df),\n            'bounced_count': bounced_count,\n            'bounce_rate': bounce_rate\n        }\n        \n        if bounce_rate > 20:\n            self.issues_found.append(f\"❌ High bounce rate: {bounce_rate:.1f}% - emails not reaching recipients!\")\n        elif bounce_rate > 10:\n            self.issues_found.append(f\"⚠️ Moderate bounce rate: {bounce_rate:.1f}% - some emails failing\")\n        \n        return results\n    \n    def _audit_response_rate(self) -> Dict:\n        \"\"\"Audit response rate from HR.\"\"\"\n        logging.info(\"📊 Auditing response rate...\")\n        \n        if not self.sent_emails_file.exists():\n            return {'response_rate': 0, 'issue': 'No sent emails to analyze'}\n        \n        df = pd.read_csv(self.sent_emails_file)\n        \n        if len(df) == 0:\n            return {'response_rate': 0, 'issue': 'No sent emails'}\n        \n        # Count responses\n        responses = 0\n        if 'replied' in df.columns:\n            responses = len(df[df['replied'].str.contains('true|yes', case=False, na=False)])\n        \n        response_rate = (responses / len(df)) * 100\n        \n        results = {\n            'total_sent': len(df),\n            'responses': responses,\n            'response_rate': response_rate\n        }\n        \n        if response_rate < 2:\n            self.issues_found.append(f\"❌ Very low response rate: {response_rate:.1f}% - emails may not be compelling or reaching right people\")\n        elif response_rate < 5:\n            self.issues_found.append(f\"⚠️ Low response rate: {response_rate:.1f}% - email quality needs improvement\")\n        \n        return results\n    \n    def _audit_email_content(self) -> Dict:\n        \"\"\"Audit email content quality.\"\"\"\n        logging.info(\"📝 Auditing email content quality...\")\n        \n        # This would need to check actual email templates\n        # For now, return basic analysis\n        return {\n            'status': 'info',\n            'message': 'Email content audit requires template analysis'\n        }\n    \n    def _generate_recommendations(self, audit_results: Dict) -> List[str]:\n        \"\"\"Generate specific recommendations based on audit results.\"\"\"\n        recommendations = []\n        \n        # Job discovery recommendations\n        if audit_results['job_discovery'].get('jobs_found_today', 0) == 0:\n            recommendations.append(\"🔧 FIX: Enable job scraping - run: python scripts/enhanced_job_scraper.py\")\n            recommendations.append(\"🔧 FIX: Check scraper credentials and rate limits\")\n        \n        # HR email recommendations\n        hr_quality = audit_results['hr_email_quality'].get('quality_score', 0)\n        if hr_quality < 50:\n            recommendations.append(\"🔧 FIX: Improve HR email discovery - run: python scripts/ai_hr_email_discovery.py\")\n            recommendations.append(\"🔧 FIX: Use LinkedIn email finder for better quality emails\")\n        \n        # Bounce rate recommendations\n        bounce_rate = audit_results['bounce_rate'].get('bounce_rate', 0)\n        if bounce_rate > 10:\n            recommendations.append(\"🔧 FIX: Enable email verification - run: python scripts/email_verifier.py\")\n            recommendations.append(\"🔧 FIX: Check bounce detection - run: python scripts/bounce_checker.py\")\n            recommendations.append(\"🔧 FIX: Create email blacklist for bounced addresses\")\n        \n        # Response rate recommendations\n        response_rate = audit_results['response_rate'].get('response_rate', 0)\n        if response_rate < 5:\n            recommendations.append(\"🔧 FIX: Improve email personalization - use AI cover letters\")\n            recommendations.append(\"🔧 FIX: Check email timing - avoid weekends and late hours\")\n            recommendations.append(\"🔧 FIX: Use professional email templates with clear CTAs\")\n            recommendations.append(\"🔧 FIX: Target specific HR roles, not generic info@ emails\")\n        \n        # General recommendations\n        recommendations.extend([\n            \"📈 OPTIMIZE: Run email open tracking to see if emails are being read\",\n            \"📈 OPTIMIZE: Set up auto-follow-ups for higher response rates\",\n            \"📈 OPTIMIZE: Use AI job matching to apply only to relevant positions\",\n            \"📈 OPTIMIZE: Monitor LinkedIn for warm connections at target companies\"\n        ])\n        \n        return recommendations\n    \n    def apply_fixes(self) -> bool:\n        \"\"\"Apply automated fixes for common issues.\"\"\"\n        logging.info(\"🔧 Applying automated fixes...\")\n        \n        try:\n            # Create bounced emails blacklist\n            self._create_email_blacklist()\n            \n            # Clean invalid emails from HR database\n            self._clean_hr_emails()\n            \n            # Update email verification settings\n            self._update_verification_settings()\n            \n            logging.info(f\"✅ Applied {len(self.fixes_applied)} fixes\")\n            return True\n            \n        except Exception as e:\n            logging.error(f\"❌ Error applying fixes: {e}\")\n            return False\n    \n    def _create_email_blacklist(self):\n        \"\"\"Create blacklist of bounced/invalid emails.\"\"\"\n        blacklist = set()\n        \n        # Add bounced emails\n        if self.bounced_emails_file.exists():\n            df = pd.read_csv(self.bounced_emails_file)\n            if 'email' in df.columns:\n                blacklist.update(df['email'].dropna().str.lower())\n        \n        # Add known bad patterns\n        bad_patterns = [\n            'noreply@', 'no-reply@', 'donotreply@', 'mailer-daemon@',\n            'postmaster@', 'admin@example.com', 'test@test.com'\n        ]\n        \n        if blacklist or bad_patterns:\n            blacklist_df = pd.DataFrame({\n                'email': list(blacklist),\n                'reason': 'bounced',\n                'date_added': datetime.now().strftime('%Y-%m-%d')\n            })\n            blacklist_df.to_csv(self.blacklist_file, index=False)\n            self.fixes_applied.append(f\"Created email blacklist with {len(blacklist)} entries\")\n    \n    def _clean_hr_emails(self):\n        \"\"\"Remove invalid emails from HR database.\"\"\"\n        if self.hr_emails_file.exists():\n            df = pd.read_csv(self.hr_emails_file)\n            original_count = len(df)\n            \n            # Remove invalid emails\n            df = df[df['email'].str.contains('@', na=False)]\n            df = df[df['email'].str.contains('\\.', na=False, regex=True)]\n            \n            if len(df) < original_count:\n                df.to_csv(self.hr_emails_file, index=False)\n                removed = original_count - len(df)\n                self.fixes_applied.append(f\"Removed {removed} invalid emails from HR database\")\n    \n    def _update_verification_settings(self):\n        \"\"\"Update email verification settings for better deliverability.\"\"\"\n        # Create config file with stricter verification settings\n        config = {\n            'min_deliverability_score': 70,\n            'enable_mx_check': True,\n            'enable_bounce_detection': True,\n            'skip_generic_emails': True,\n            'max_bounce_rate': 15\n        }\n        \n        config_file = self.data_dir / \"email_verification_config.json\"\n        import json\n        with open(config_file, 'w') as f:\n            json.dump(config, f, indent=2)\n        \n        self.fixes_applied.append(\"Updated email verification settings for better deliverability\")\n\ndef main():\n    \"\"\"Run email deliverability audit.\"\"\"\n    auditor = EmailDeliverabilityAuditor()\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"🔍 EMAIL DELIVERABILITY AUDIT & DIAGNOSIS\")\n    print(\"=\"*60)\n    \n    results = auditor.audit_email_system()\n    \n    print(\"\\n📊 AUDIT RESULTS:\")\n    print(\"-\" * 30)\n    \n    for category, data in results['audit_results'].items():\n        if isinstance(data, dict) and 'issue' not in data:\n            print(f\"\\n{category.upper()}:\")\n            for key, value in data.items():\n                print(f\"  {key}: {value}\")\n    \n    if results['issues_found']:\n        print(\"\\n❌ ISSUES FOUND:\")\n        print(\"-\" * 30)\n        for issue in results['issues_found']:\n            print(f\"  {issue}\")\n    \n    if results['recommendations']:\n        print(\"\\n💡 RECOMMENDATIONS:\")\n        print(\"-\" * 30)\n        for rec in results['recommendations']:\n            print(f\"  {rec}\")\n    \n    # Apply fixes\n    print(\"\\n🔧 APPLYING FIXES...\")\n    if auditor.apply_fixes():\n        print(\"✅ Fixes applied successfully!\")\n        if auditor.fixes_applied:\n            for fix in auditor.fixes_applied:\n                print(f\"  ✓ {fix}\")\n    else:\n        print(\"❌ Some fixes failed\")\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"✅ AUDIT COMPLETE\")\n    print(\"=\"*60)\n\nif __name__ == \"__main__\":\n    main()\n