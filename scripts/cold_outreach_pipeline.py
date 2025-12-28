"""
Cold Outreach Pipeline - Complete pipeline for HR email scraping and personalized outreach
This replaces browser automation with email-based job applications.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.email_scraper import HREmailScraper, TARGET_COMPANIES
from scripts.email_sender import PersonalizedEmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'data', 'cold_outreach.log'))
    ]
)


def run_scraping_phase() -> pd.DataFrame:
    """Phase 1: Scrape HR emails from various sources."""
    logging.info("=" * 60)
    logging.info("🔍 PHASE 1: HR EMAIL SCRAPING")
    logging.info("=" * 60)
    
    scraper = HREmailScraper()
    all_emails = pd.DataFrame()
    
    # 1. Scrape from existing jobs CSV
    jobs_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs_today.csv')
    if os.path.exists(jobs_csv):
        logging.info("\n📋 Scraping emails from jobs CSV...")
        jobs_emails = scraper.scrape_from_jobs_csv(jobs_csv)
        if not jobs_emails.empty:
            all_emails = pd.concat([all_emails, jobs_emails], ignore_index=True)
            logging.info(f"   Found {len(jobs_emails)} email entries from jobs")
    
    # 2. Scrape from target company career pages
    logging.info("\n🏢 Scraping emails from target companies...")
    company_emails = scraper.scrape_from_company_list(TARGET_COMPANIES)
    if not company_emails.empty:
        all_emails = pd.concat([all_emails, company_emails], ignore_index=True)
        logging.info(f"   Found {len(company_emails)} email entries from companies")
    
    # 3. Clean and deduplicate
    if not all_emails.empty:
        # Remove entries without emails
        all_emails = all_emails[all_emails['hr_email'].notna()]
        
        # Deduplicate by email
        all_emails = all_emails.drop_duplicates(subset=['hr_email'], keep='first')
        
        # Save consolidated list
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv')
        all_emails.to_csv(output_path, index=False)
        
        logging.info(f"\n✅ Phase 1 Complete: {len(all_emails)} unique HR emails collected")
        logging.info(f"   Saved to: {output_path}")
    else:
        logging.warning("\n⚠️ No HR emails found during scraping phase")
    
    return all_emails


def run_email_phase(emails_df: pd.DataFrame, max_emails: int = 20) -> dict:
    """Phase 2: Send personalized emails to HR contacts."""
    logging.info("\n" + "=" * 60)
    logging.info("📧 PHASE 2: PERSONALIZED EMAIL OUTREACH")
    logging.info("=" * 60)
    
    if emails_df.empty:
        logging.warning("No emails to send - skipping email phase")
        return {'sent': 0, 'failed': 0, 'skipped': 0}
    
    sender = PersonalizedEmailSender()
    
    # Check credentials
    if not os.getenv('SENDER_EMAIL') or not os.getenv('SENDER_PASSWORD'):
        logging.error("\n❌ Email credentials not configured!")
        logging.error("Set these environment variables (or GitHub Secrets):")
        logging.error("  SENDER_EMAIL - Your Gmail address")
        logging.error("  SENDER_PASSWORD - Gmail App Password")
        logging.error("\nTo create an App Password:")
        logging.error("  1. Enable 2-Factor Authentication on your Google Account")
        logging.error("  2. Go to https://myaccount.google.com/apppasswords")
        logging.error("  3. Generate a new app password for 'Mail'")
        return {'sent': 0, 'failed': 0, 'skipped': 0, 'error': 'no_credentials'}
    
    # Check applicant details
    logging.info("\n👤 Applicant Configuration:")
    logging.info(f"   Name: {os.getenv('APPLICANT_NAME', 'Not Set')}")
    logging.info(f"   Email: {os.getenv('SENDER_EMAIL', 'Not Set')}")
    logging.info(f"   Phone: {os.getenv('APPLICANT_PHONE', 'Not Set')}")
    logging.info(f"   Experience: {os.getenv('APPLICANT_EXPERIENCE', '3')}+ years")
    
    # Send emails
    logging.info(f"\n📤 Sending up to {max_emails} personalized emails...")
    stats = sender.send_bulk_emails(
        emails_df,
        max_emails=max_emails,
        delay_range=(45, 90)  # 45-90 seconds between emails
    )
    
    return stats


def generate_report(emails_df: pd.DataFrame, email_stats: dict):
    """Generate a summary report."""
    logging.info("\n" + "=" * 60)
    logging.info("📊 COLD OUTREACH REPORT")
    logging.info("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_emails_scraped': len(emails_df) if not emails_df.empty else 0,
        'emails_sent': email_stats.get('sent', 0),
        'emails_failed': email_stats.get('failed', 0),
        'emails_skipped': email_stats.get('skipped', 0),
    }
    
    if not emails_df.empty:
        # Count by company
        company_counts = emails_df.groupby('company').size().to_dict()
        report['companies_contacted'] = len(company_counts)
        report['top_companies'] = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    logging.info(f"\n📈 Summary:")
    logging.info(f"   Total HR emails found: {report['total_emails_scraped']}")
    logging.info(f"   Emails sent: {report['emails_sent']}")
    logging.info(f"   Emails failed: {report['emails_failed']}")
    logging.info(f"   Emails skipped: {report['emails_skipped']}")
    
    if 'companies_contacted' in report:
        logging.info(f"   Companies with emails: {report['companies_contacted']}")
    
    # Save report
    import json
    report_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cold_outreach_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"\n📄 Report saved to: {report_path}")
    
    return report


def main():
    """Main pipeline execution."""
    logging.info("🚀 COLD OUTREACH PIPELINE STARTED")
    logging.info(f"   Timestamp: {datetime.now().isoformat()}")
    logging.info("=" * 60)
    
    # Phase 1: Scrape emails
    emails_df = run_scraping_phase()
    
    # Phase 2: Send emails
    email_stats = run_email_phase(emails_df, max_emails=20)
    
    # Generate report
    report = generate_report(emails_df, email_stats)
    
    logging.info("\n" + "=" * 60)
    logging.info("✅ COLD OUTREACH PIPELINE COMPLETED")
    logging.info("=" * 60)
    
    # Exit with error if no emails sent and credentials were missing
    if email_stats.get('error') == 'no_credentials':
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
