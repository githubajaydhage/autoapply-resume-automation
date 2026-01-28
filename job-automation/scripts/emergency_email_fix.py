#!/usr/bin/env python3
"""
URGENT EMAIL SYSTEM FIXES
Addresses critical issues preventing HR responses and job applications
"""

import pandas as pd
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def diagnose_email_issues():
    """Diagnose and fix email system issues."""
    
    print("🔍 DIAGNOSING EMAIL SYSTEM ISSUES...")
    print("=" * 50)
    
    data_dir = Path("data")
    issues = []
    fixes = []
    
    # 1. Check sent emails
    sent_file = data_dir / "sent_emails_log.csv"
    if sent_file.exists():
        df = pd.read_csv(sent_file)
        print(f"📧 Total emails attempted: {len(df)}")
        
        # Check statuses
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            print("📊 Email Status Breakdown:")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
            
            # Check auth failures
            auth_failed = len(df[df['status'] == 'auth_failed'])
            if auth_failed > 0:
                issues.append(f"❌ CRITICAL: {auth_failed} emails failed authentication - EMAIL CREDENTIALS WRONG!")
                fixes.append("🔧 FIX: Set correct SENDER_EMAIL and SENDER_PASSWORD (Gmail App Password)")
            
            # Check sent emails
            sent_count = len(df[df['status'] == 'sent'])
            if sent_count == 0:
                issues.append("❌ CRITICAL: Zero emails actually sent!")
            
            # Check for responses
            if 'replied' in df.columns:
                responses = len(df[df['replied'].str.contains('true|yes', case=False, na=False)])
            else:
                responses = 0
            response_rate = (responses / len(df)) * 100 if len(df) > 0 else 0
            print(f"📈 Response rate: {response_rate:.1f}% ({responses}/{len(df)})")
            
            if response_rate == 0:
                issues.append("❌ ZERO responses from HR - emails not compelling or reaching wrong people")
                fixes.extend([
                    "🔧 FIX: Use specific HR email addresses, not generic careers@ emails",
                    "🔧 FIX: Improve email subject lines and personalization",
                    "🔧 FIX: Send to actual hiring managers, not general inboxes"
                ])
    else:
        issues.append("❌ CRITICAL: No sent_emails_log.csv - email system not running!")
    
    # 2. Check job discovery
    jobs_file = data_dir / "jobs_today.csv"
    if jobs_file.exists():
        df = pd.read_csv(jobs_file)
        print(f"💼 Jobs found today: {len(df)}")
        
        if len(df) == 0:
            issues.append("❌ CRITICAL: Zero jobs discovered - job scrapers failing!")
            fixes.append("🔧 FIX: Check job scraper credentials and run manually")
        else:
            # Check if jobs have HR emails
            if 'email' in df.columns:
                has_emails = len(df[df['email'].notna()])
                print(f"📧 Jobs with HR emails: {has_emails}/{len(df)}")
                if has_emails == 0:
                    issues.append("❌ CRITICAL: Jobs found but NO HR emails - cannot apply!")
                    fixes.append("🔧 FIX: Enable HR email discovery system")
    else:
        issues.append("❌ CRITICAL: No jobs_today.csv - job discovery not working!")
    
    # 3. Check HR email quality
    hr_file = data_dir / "discovered_hr_emails.csv"
    if hr_file.exists():
        df = pd.read_csv(hr_file)
        print(f"👤 HR emails discovered: {len(df)}")
        
        if 'email' in df.columns:
            # Check email quality
            generic_emails = df[df['email'].str.contains('careers@|info@|contact@|support@', case=False, na=False)]
            generic_count = len(generic_emails)
            print(f"⚠️ Generic emails: {generic_count}/{len(df)} ({(generic_count/len(df)*100):.1f}%)")
            
            if generic_count > len(df) * 0.7:  # More than 70% generic
                issues.append("❌ Too many generic emails - low response rates expected")
                fixes.append("🔧 FIX: Find specific hiring manager emails using LinkedIn")
    
    # Print issues and fixes
    print("\n❌ CRITICAL ISSUES IDENTIFIED:")
    print("-" * 40)
    for issue in issues:
        print(issue)
    
    print("\n🔧 REQUIRED FIXES:")
    print("-" * 40)
    for fix in fixes:
        print(fix)
    
    return issues, fixes

def create_emergency_fixes():
    """Create emergency fixes for immediate problems."""
    
    print("\n🚨 APPLYING EMERGENCY FIXES...")
    print("=" * 50)
    
    # 1. Create improved email verification
    create_email_blacklist()
    
    # 2. Create better HR email discovery
    create_hr_email_finder()
    
    # 3. Create email credential checker
    create_credential_checker()
    
    print("✅ Emergency fixes created!")

def create_email_blacklist():
    """Create blacklist of ineffective email addresses."""
    
    blacklist_emails = [
        # Generic company emails (rarely monitored by HR)
        'careers@', 'jobs@', 'info@', 'contact@', 'support@',
        'admin@', 'office@', 'hello@', 'mail@', 'enquiry@',
        'sales@', 'marketing@', 'help@', 'service@', 'feedback@',
        
        # Auto-reply emails
        'noreply@', 'no-reply@', 'donotreply@', 'mailer-daemon@',
        'postmaster@', 'bounce@', 'return@'
    ]
    
    # Save blacklist
    data_dir = Path("data")
    blacklist_file = data_dir / "email_blacklist.txt"
    
    with open(blacklist_file, 'w') as f:
        f.write("# Email patterns to avoid (low response rate)\n")
        for pattern in blacklist_emails:
            f.write(f"{pattern}\n")
    
    print(f"📝 Created email blacklist: {blacklist_file}")

def create_hr_email_finder():
    """Create HR-specific email discovery script."""
    
    hr_finder_script = '''#!/usr/bin/env python3
"""
Smart HR Email Finder - Finds specific HR professional emails
"""

import requests
import re
from typing import List

def find_hr_emails(company_name: str) -> List[str]:
    """Find HR-specific emails for a company."""
    
    # Common HR email patterns
    hr_patterns = [
        f"hr@{company_name.lower().replace(' ', '')}.com",
        f"talent@{company_name.lower().replace(' ', '')}.com", 
        f"recruiting@{company_name.lower().replace(' ', '')}.com",
        f"careers@{company_name.lower().replace(' ', '')}.com",
        f"jobs@{company_name.lower().replace(' ', '')}.com"
    ]
    
    # Try to find hiring manager names from LinkedIn
    # This would require LinkedIn API or scraping
    
    return hr_patterns

def verify_email_deliverability(email: str) -> bool:
    """Quick check if email is likely deliverable."""
    
    # Skip obviously bad emails
    bad_patterns = ['careers@', 'info@', 'contact@']
    if any(pattern in email.lower() for pattern in bad_patterns):
        return False
    
    # Check domain exists
    domain = email.split('@')[-1]
    try:
        import dns.resolver
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False

if __name__ == "__main__":
    # Test with sample companies
    companies = ["Microsoft", "Google", "Amazon"]
    for company in companies:
        emails = find_hr_emails(company)
        print(f"{company}: {emails}")
'''
    
    # Save HR finder script
    scripts_dir = Path("scripts")
    hr_finder_file = scripts_dir / "smart_hr_finder.py"
    
    with open(hr_finder_file, 'w') as f:
        f.write(hr_finder_script)
    
    print(f"📝 Created HR email finder: {hr_finder_file}")

def create_credential_checker():
    """Create email credential checker."""
    
    checker_script = '''#!/usr/bin/env python3
"""
Email Credential Checker - Test if email credentials work
"""

import smtplib
import ssl
import os

def test_email_credentials():
    """Test if email credentials are working."""
    
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD') 
    
    if not sender_email or not sender_password:
        print("❌ SENDER_EMAIL or SENDER_PASSWORD not set!")
        print("Set these environment variables:")
        print("  SENDER_EMAIL=your-gmail@gmail.com")
        print("  SENDER_PASSWORD=your-app-password")
        return False
    
    try:
        print(f"🔍 Testing credentials for: {sender_email}")
        
        # Create secure connection
        context = ssl.create_default_context()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls(context=context)
        
        # Test login
        server.login(sender_email, sender_password)
        server.quit()
        
        print("✅ Email credentials are working!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed!")
        print("💡 For Gmail, use App Password:")
        print("   1. Enable 2-factor authentication")
        print("   2. Go to: https://myaccount.google.com/apppasswords")
        print("   3. Generate app password for 'Mail'")
        print("   4. Use that password, not your regular password")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_email_credentials()
'''
    
    # Save credential checker
    scripts_dir = Path("scripts")
    checker_file = scripts_dir / "test_email_credentials.py"
    
    with open(checker_file, 'w') as f:
        f.write(checker_script)
    
    print(f"📝 Created credential checker: {checker_file}")

def main():
    """Main diagnosis and fix function."""
    
    print("🚨 EMAIL SYSTEM EMERGENCY DIAGNOSIS")
    print("=" * 60)
    
    # Diagnose issues
    issues, fixes = diagnose_email_issues()
    
    if not issues:
        print("\n✅ No critical issues found - system appears healthy!")
        return
    
    # Apply emergency fixes
    create_emergency_fixes()
    
    print("\n🎯 IMMEDIATE ACTION REQUIRED:")
    print("-" * 40)
    print("1. Run: python scripts/test_email_credentials.py")
    print("2. Fix email credentials if authentication failing")
    print("3. Run job scrapers to get fresh jobs with HR emails")
    print("4. Use specific HR emails, not generic careers@ emails")
    print("5. Monitor sent_emails_log.csv for delivery status")
    
    print("\n📞 WHY NO CALLS/RESPONSES?")
    print("-" * 40)
    print("• Authentication failures = emails never sent")
    print("• Generic emails (careers@) = low response rates")
    print("• No personalization = emails look like spam")
    print("• Wrong timing = emails buried in inbox")
    print("• No follow-up = single email gets ignored")
    
    print("\n🎯 HOW TO GET RESPONSES:")
    print("-" * 40)
    print("• Find specific hiring manager emails on LinkedIn")
    print("• Personalize each email with company research")
    print("• Send Tuesday-Thursday, 9-11 AM IST")
    print("• Follow up after 3-5 days with different angle")
    print("• Apply to fewer, higher-quality opportunities")

if __name__ == "__main__":
    main()