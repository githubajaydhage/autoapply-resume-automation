#!/usr/bin/env python3
"""
Production Job Application System - REAL Applications
Scrapes jobs and applies using Playwright browser automation
"""

import logging
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from applicators.linkedin import LinkedInApplicator
from applicators.naukri import NaukriApplicator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/production_applications.log')
    ]
)
logger = logging.getLogger(__name__)


def load_jobs():
    """Load jobs from scraped CSV file."""
    jobs_files = [
        Path("data/jobs_today.csv"),
        Path("data/prioritized_jobs_today.csv"),
    ]
    
    for jobs_file in jobs_files:
        if jobs_file.exists():
            try:
                df = pd.read_csv(jobs_file)
                jobs = df.to_dict('records')
                logger.info(f"✅ Loaded {len(jobs)} jobs from {jobs_file}")
                return jobs
            except Exception as e:
                logger.warning(f"Could not load {jobs_file}: {e}")
    
    logger.warning("No job files found")
    return []


def filter_jobs_by_platform(jobs, platform):
    """Filter jobs by platform/portal."""
    platform_jobs = []
    for job in jobs:
        portal = job.get('portal', '').lower()
        if platform == 'linkedin' and portal == 'linkedin':
            platform_jobs.append(job)
        elif platform == 'naukri' and portal == 'naukri':
            platform_jobs.append(job)
        elif platform == 'company' and portal in ['company', 'careers']:
            platform_jobs.append(job)
    return platform_jobs


def run_linkedin_applications(jobs):
    """Run LinkedIn Easy Apply applications."""
    linkedin_jobs = filter_jobs_by_platform(jobs, 'linkedin')
    
    if not linkedin_jobs:
        logger.info("No LinkedIn jobs to apply to")
        return 0
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if not email or not password:
        logger.warning("LinkedIn credentials not set - skipping LinkedIn applications")
        return 0
    
    logger.info(f"🔗 Starting LinkedIn applications for {len(linkedin_jobs)} jobs")
    
    try:
        applicator = LinkedInApplicator()
        applicator.run(linkedin_jobs)
        # Return actual applied count from tracker
        return applicator.applied_count if hasattr(applicator, 'applied_count') else 0
    except Exception as e:
        logger.error(f"LinkedIn application error: {e}")
        return 0


def run_naukri_applications(jobs):
    """Run Naukri applications."""
    naukri_jobs = filter_jobs_by_platform(jobs, 'naukri')
    
    if not naukri_jobs:
        logger.info("No Naukri jobs to apply to")
        return 0
    
    email = os.getenv('NAUKRI_EMAIL')
    password = os.getenv('NAUKRI_PASSWORD')
    
    if not email or not password:
        logger.warning("Naukri credentials not set - skipping Naukri applications")
        return 0
    
    logger.info(f"📋 Starting Naukri applications for {len(naukri_jobs)} jobs")
    
    try:
        applicator = NaukriApplicator()
        applicator.run(naukri_jobs)
        # Return actual applied count from tracker
        return applicator.applied_count if hasattr(applicator, 'applied_count') else 0
    except Exception as e:
        logger.error(f"Naukri application error: {e}")
        return 0


def run_company_applications(jobs):
    """Run company career site applications - log only for now."""
    company_jobs = filter_jobs_by_platform(jobs, 'company')
    
    if not company_jobs:
        logger.info("No company career jobs to apply to")
        return 0
    
    logger.info(f"🏢 Company career jobs found: {len(company_jobs)}")
    logger.info("   Note: Company career sites require manual application")
    
    for job in company_jobs:
        url = job.get('url', job.get('link', 'N/A'))
        logger.info(f"   → {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        logger.info(f"     URL: {url}")
    
    return 0  # Company sites need manual application


def save_application_summary(results):
    """Save application summary to JSON."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "total_applications": sum(r.get('count', 0) for r in results)
    }
    
    summary_file = Path("data/application_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"📄 Summary saved to {summary_file}")


def main():
    """Main entry point for production job applications."""
    logger.info("=" * 60)
    logger.info("🚀 PRODUCTION JOB APPLICATION SYSTEM")
    logger.info("=" * 60)
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Load jobs
    jobs = load_jobs()
    if not jobs:
        logger.error("No jobs found to apply to. Run scrape_jobs.py first.")
        return False
    
    logger.info(f"📊 Found {len(jobs)} total jobs")
    
    # Count jobs by platform
    linkedin_count = len(filter_jobs_by_platform(jobs, 'linkedin'))
    naukri_count = len(filter_jobs_by_platform(jobs, 'naukri'))
    company_count = len(filter_jobs_by_platform(jobs, 'company'))
    
    logger.info(f"   LinkedIn: {linkedin_count} jobs")
    logger.info(f"   Naukri:   {naukri_count} jobs")
    logger.info(f"   Company:  {company_count} jobs")
    logger.info("")
    
    results = []
    
    # Run applications for each platform
    if linkedin_count > 0:
        count = run_linkedin_applications(jobs)
        results.append({'platform': 'linkedin', 'count': count, 'total': linkedin_count})
    
    if naukri_count > 0:
        count = run_naukri_applications(jobs)
        results.append({'platform': 'naukri', 'count': count, 'total': naukri_count})
    
    if company_count > 0:
        count = run_company_applications(jobs)
        results.append({'platform': 'company', 'count': count, 'total': company_count})
    
    # Summary
    total_applied = sum(r['count'] for r in results)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 APPLICATION SUMMARY")
    logger.info("=" * 60)
    
    for r in results:
        logger.info(f"   {r['platform'].upper():12s}: {r['count']}/{r['total']} applications")
    
    logger.info(f"   {'TOTAL':12s}: {total_applied} applications submitted")
    logger.info("=" * 60)
    
    # Save summary
    save_application_summary(results)
    
    if total_applied > 0:
        logger.info("✅ Job applications completed successfully!")
        return True
    else:
        logger.warning("⚠️ No applications were submitted")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
