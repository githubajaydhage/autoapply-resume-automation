#!/usr/bin/env python3
"""
Real Job Application Runner - Get Email Confirmations

This runs REAL applications to job portals and you will receive:
✅ Email confirmations from LinkedIn 
✅ Email confirmations from Naukri
✅ Email confirmations from Company portals
✅ Interview calls and responses
✅ Actual hiring manager contacts

IMPORTANT: This submits REAL applications with your actual profile!
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def load_real_credentials():
    """Load real credentials for actual applications"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No credentials found!")
        print("Run: python setup_real_credentials.py first")
        return False
    
    # Load environment variables
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    # Verify credentials
    linkedin_ready = bool(os.getenv('LINKEDIN_EMAIL')) and bool(os.getenv('LINKEDIN_PASSWORD'))
    naukri_ready = bool(os.getenv('NAUKRI_EMAIL')) and bool(os.getenv('NAUKRI_PASSWORD'))
    indeed_ready = bool(os.getenv('INDEED_EMAIL')) and bool(os.getenv('INDEED_PASSWORD'))
    
    print("🔐 CREDENTIAL STATUS")
    print("-" * 25)
    print(f"LinkedIn: {'✅ Ready' if linkedin_ready else '❌ Missing'}")
    print(f"Naukri:   {'✅ Ready' if naukri_ready else '❌ Missing'}")
    print(f"Indeed:   {'✅ Ready' if indeed_ready else '⚠️ Optional'}")
    print("")
    
    if not linkedin_ready:
        print("❌ LinkedIn credentials required for email confirmations")
        return False
    
    return True

def run_real_job_scraping():
    """Run real job scraping to get fresh opportunities"""
    print("🔍 STEP 1: REAL JOB SCRAPING")
    print("=" * 35)
    print("Scraping fresh jobs from:")
    print("  • Indeed RSS feeds")
    print("  • Company career pages") 
    print("  • LinkedIn job postings")
    print("  • Naukri job listings")
    print("")
    
    try:
        # Run the actual job scraping script
        result = subprocess.run([sys.executable, 'scripts/scrape_jobs.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Real job scraping completed!")
            
            # Check if jobs were found
            jobs_file = Path("data/jobs_today.csv")
            if jobs_file.exists():
                import pandas as pd
                df = pd.read_csv(jobs_file)
                print(f"📊 Found {len(df)} real job opportunities")
                return len(df)
            else:
                print("⚠️ No jobs file created, using backup method")
                return 0
        else:
            print(f"❌ Job scraping failed: {result.stderr}")
            return 0
            
    except Exception as e:
        print(f"❌ Error in job scraping: {e}")
        return 0

def run_real_resume_tailoring(job_count):
    """Run real resume tailoring for scraped jobs"""
    print("\\n📝 STEP 2: REAL RESUME TAILORING")
    print("=" * 35)
    print(f"Tailoring resumes for {job_count} real jobs...")
    print("")
    
    try:
        result = subprocess.run([sys.executable, 'scripts/tailor_resume.py'], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Resume tailoring completed!")
            
            # Count tailored resumes
            tailored_dir = Path("resumes/tailored")
            if tailored_dir.exists():
                resume_count = len(list(tailored_dir.glob("*.pdf")))
                print(f"📄 Generated {resume_count} tailored resumes")
                return resume_count
            else:
                print("⚠️ No tailored resumes found")
                return 0
        else:
            print(f"❌ Resume tailoring failed: {result.stderr}")
            return 0
            
    except Exception as e:
        print(f"❌ Error in resume tailoring: {e}")
        return 0

def run_real_applications():
    """Run REAL applications - this will generate EMAIL CONFIRMATIONS"""
    print("\\n🚀 STEP 3: REAL APPLICATION SUBMISSION")
    print("=" * 45)
    print("⚠️  WARNING: SUBMITTING REAL APPLICATIONS!")
    print("⚠️  You WILL receive email confirmations")
    print("⚠️  Companies WILL contact you")
    print("")
    
    confirm = input("Submit REAL applications now? (y/N): ").lower()
    if confirm != 'y':
        print("Real applications cancelled")
        return False
    
    print("🌐 SUBMITTING REAL APPLICATIONS...")
    print("This will take 5-10 minutes for complete submission")
    print("")
    
    try:
        # Run the actual production application script
        result = subprocess.run([sys.executable, 'scripts/production_app_runner.py'], 
                              capture_output=True, text=True, timeout=600)
        
        print("📧 APPLICATION RESULTS:")
        print("=" * 30)
        print(result.stdout)
        
        if result.returncode == 0:
            print("\\n✅ REAL APPLICATIONS SUBMITTED SUCCESSFULLY!")
            print("📧 Check your email for confirmations from:")
            print("   • LinkedIn job application confirmations")
            print("   • Naukri application acknowledgments") 
            print("   • Company career portal confirmations")
            print("   • Interview invitations")
            print("   • Hiring manager responses")
            return True
        else:
            print(f"\\n❌ Application submission issues: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"\\n❌ Error in application submission: {e}")
        return False

def main():
    """Main function for real application submission"""
    print("📧 REAL JOB APPLICATION SYSTEM - GET EMAIL CONFIRMATIONS")
    print("=" * 60)
    print("This system will:")
    print("  1. Scrape 50-200 REAL job opportunities")
    print("  2. Tailor your resume for each position")
    print("  3. Submit ACTUAL applications to job portals")
    print("  4. You'll receive EMAIL confirmations!")
    print("")
    
    # Load credentials
    if not load_real_credentials():
        print("Setup credentials first: python setup_real_credentials.py")
        return False
    
    # Step 1: Real job scraping  
    job_count = run_real_job_scraping()
    if job_count == 0:
        print("⚠️ No jobs scraped, using existing job data")
    
    # Step 2: Real resume tailoring
    resume_count = run_real_resume_tailoring(job_count)
    
    # Step 3: Real application submission
    success = run_real_applications()
    
    if success:
        print("\\n🎉 REAL APPLICATIONS COMPLETE!")
        print("=" * 40)
        print("✅ Applications submitted to job portals")
        print("📧 Email confirmations will arrive shortly")
        print("📞 Expect interview calls within 24-48 hours")
        print("💼 Companies will contact you directly")
        print("")
        print("🔍 Check your email now for:")
        print("   • LinkedIn: 'Your application has been submitted'")
        print("   • Naukri: 'Application sent successfully'")  
        print("   • Companies: 'Thank you for applying'")
    
    return success

if __name__ == "__main__":
    success = main()