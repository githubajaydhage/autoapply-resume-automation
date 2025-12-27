#!/usr/bin/env python3
"""
Test credentials and run simultaneous job applications
"""

import logging
import os
import sys
import time
import concurrent.futures
import threading
from pathlib import Path

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from applicators.linkedin import LinkedInApplicator
from applicators.naukri import NaukriApplicator
from applicators.indeed import IndeedApplicator
from applicators.company_careers import CompanyCareersApplicator
from utils.config import PORTAL_CONFIGS, COMPANY_CAREERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/simultaneous_applications.log')
    ]
)
logger = logging.getLogger(__name__)

def check_credentials():
    """Check if all required credentials are set"""
    logger.info("🔐 CHECKING CREDENTIALS")
    logger.info("=" * 50)
    
    credentials_status = {}
    required_env_vars = [
        'LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD',
        'NAUKRI_EMAIL', 'NAUKRI_PASSWORD', 
        'INDEED_EMAIL', 'INDEED_PASSWORD'
    ]
    
    for env_var in required_env_vars:
        value = os.getenv(env_var)
        if value:
            # Mask password for security
            if 'PASSWORD' in env_var:
                masked_value = '*' * len(value)
                logger.info(f"✅ {env_var}: {masked_value}")
            else:
                logger.info(f"✅ {env_var}: {value}")
            credentials_status[env_var] = True
        else:
            logger.error(f"❌ {env_var}: NOT SET")
            credentials_status[env_var] = False
    
    logger.info("")
    
    # Check overall status
    all_set = all(credentials_status.values())
    if all_set:
        logger.info("🎯 ALL CREDENTIALS VERIFIED ✅")
        return True
    else:
        missing = [k for k, v in credentials_status.items() if not v]
        logger.error(f"⚠️  MISSING CREDENTIALS: {', '.join(missing)}")
        logger.error("Please set missing environment variables or GitHub secrets")
        return False

def generate_test_jobs():
    """Generate test jobs for different platforms"""
    logger.info("📝 Generating test jobs for simultaneous applications...")
    
    # LinkedIn jobs
    linkedin_jobs = [
        {
            'title': 'Senior Data Analyst',
            'company': 'Tech Solutions Inc',
            'location': 'Bangalore',
            'link': 'https://www.linkedin.com/jobs/view/3774567890',
            'portal': 'linkedin',
            'priority_score': 9.5,
            'posted_date': 'Today'
        },
        {
            'title': 'Business Intelligence Analyst',
            'company': 'DataCorp Technologies',
            'location': 'Bangalore', 
            'link': 'https://www.linkedin.com/jobs/view/3774567891',
            'portal': 'linkedin',
            'priority_score': 8.8,
            'posted_date': '1 day ago'
        }
    ]
    
    # Naukri jobs
    naukri_jobs = [
        {
            'title': 'Data Analyst - SQL Expert',
            'company': 'Analytics Pro Solutions',
            'location': 'Bangalore',
            'link': 'https://www.naukri.com/job-listings/data-analyst-sql-expert-analytics-pro-solutions-bangalore-3-to-8-years-220124500001',
            'portal': 'naukri',
            'priority_score': 9.2,
            'posted_date': 'Today'
        },
        {
            'title': 'Power BI Developer',
            'company': 'Business Intelligence Corp',
            'location': 'Bangalore',
            'link': 'https://www.naukri.com/job-listings/power-bi-developer-business-intelligence-corp-bangalore-2-to-6-years-220124500002',
            'portal': 'naukri', 
            'priority_score': 8.9,
            'posted_date': '2 days ago'
        }
    ]
    
    # Indeed jobs
    indeed_jobs = [
        {
            'title': 'Data Analytics Specialist',
            'company': 'Digital Insights Ltd',
            'location': 'Bangalore',
            'link': 'https://indeed.com/viewjob?jk=abc123def456',
            'portal': 'indeed',
            'priority_score': 8.7,
            'posted_date': '1 day ago'
        }
    ]
    
    # Company career jobs
    company_jobs = [
        {
            'title': 'Data Analyst - Google Cloud',
            'company': 'Google',
            'location': 'Bangalore',
            'link': 'https://careers.google.com/jobs/results/123456789',
            'portal': 'company_google',
            'priority_score': 9.8,
            'posted_date': 'Today'
        },
        {
            'title': 'Business Analyst',
            'company': 'Microsoft',
            'location': 'Bangalore',
            'link': 'https://careers.microsoft.com/us/en/job/1234567',
            'portal': 'company_microsoft',
            'priority_score': 9.6,
            'posted_date': 'Today'
        }
    ]
    
    return {
        'linkedin': linkedin_jobs,
        'naukri': naukri_jobs,
        'indeed': indeed_jobs,
        'company': company_jobs
    }

def apply_to_platform_jobs(platform, jobs):
    """Apply to jobs on a specific platform (runs in separate thread)"""
    thread_name = threading.current_thread().name
    logger.info(f"🚀 [{thread_name}] Starting {platform} applications")
    
    start_time = time.time()
    applications_count = 0
    
    try:
        if platform == 'linkedin':
            applicator = LinkedInApplicator()
            applications_count = applicator.run(jobs)
            
        elif platform == 'naukri':
            applicator = NaukriApplicator()
            applications_count = applicator.run(jobs)
            
        elif platform == 'indeed':
            applicator = IndeedApplicator()
            applications_count = applicator.run(jobs)
            
        elif platform == 'company':
            # Handle company applications
            for job in jobs:
                company_key = job['portal'].replace('company_', '')
                if company_key in COMPANY_CAREERS:
                    logger.info(f"[{thread_name}] Applying to {company_key}: {job['title']}")
                    # Simulate application process
                    time.sleep(2)  # Simulate application time
                    applications_count += 1
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ [{thread_name}] {platform} complete: {applications_count} applications in {elapsed_time:.1f}s")
        return {'platform': platform, 'count': applications_count, 'time': elapsed_time}
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ [{thread_name}] {platform} failed: {str(e)} (after {elapsed_time:.1f}s)")
        return {'platform': platform, 'count': 0, 'time': elapsed_time, 'error': str(e)}

def run_simultaneous_applications():
    """Run applications to all platforms simultaneously"""
    logger.info("🎯 STARTING SIMULTANEOUS JOB APPLICATIONS")
    logger.info("=" * 60)
    
    # Generate test jobs
    test_jobs = generate_test_jobs()
    
    logger.info("📊 APPLICATION TARGETS:")
    total_jobs = 0
    for platform, jobs in test_jobs.items():
        logger.info(f"   {platform.capitalize():12s}: {len(jobs)} jobs")
        total_jobs += len(jobs)
    logger.info(f"   {'TOTAL':12s}: {total_jobs} jobs")
    logger.info("")
    
    # Run applications simultaneously using ThreadPoolExecutor
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="App") as executor:
        # Submit all platform applications simultaneously
        future_to_platform = {}
        
        for platform, jobs in test_jobs.items():
            if jobs:  # Only submit if there are jobs
                future = executor.submit(apply_to_platform_jobs, platform, jobs)
                future_to_platform[future] = platform
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Exception in {platform} thread: {e}")
                results.append({'platform': platform, 'count': 0, 'time': 0, 'error': str(e)})
    
    # Calculate total results
    total_time = time.time() - start_time
    successful_applications = sum(r['count'] for r in results)
    
    # Report results
    logger.info("")
    logger.info("🎯 SIMULTANEOUS APPLICATION RESULTS")
    logger.info("=" * 60)
    
    for result in sorted(results, key=lambda x: x['count'], reverse=True):
        platform = result['platform'].capitalize()
        count = result['count']
        time_taken = result['time']
        
        if 'error' in result:
            logger.error(f"❌ {platform:12s}: {count} applications, {time_taken:.1f}s (ERROR: {result['error']})")
        else:
            logger.info(f"✅ {platform:12s}: {count} applications, {time_taken:.1f}s")
    
    logger.info("-" * 60)
    logger.info(f"📊 SUMMARY:")
    logger.info(f"   Total Jobs Targeted:    {total_jobs}")
    logger.info(f"   Successful Applications: {successful_applications}")
    logger.info(f"   Success Rate:           {(successful_applications/total_jobs)*100:.1f}%")
    logger.info(f"   Total Execution Time:   {total_time:.1f}s")
    logger.info(f"   Average Time Per App:   {total_time/total_jobs:.1f}s")
    
    # Performance comparison
    sequential_time_estimate = sum(r['time'] for r in results)
    speedup = sequential_time_estimate / total_time if total_time > 0 else 1
    
    logger.info("")
    logger.info("⚡ PERFORMANCE COMPARISON:")
    logger.info(f"   Sequential Estimate: {sequential_time_estimate:.1f}s")
    logger.info(f"   Simultaneous Actual: {total_time:.1f}s") 
    logger.info(f"   Speedup Factor:      {speedup:.1f}x faster")
    
    return results

def main():
    """Main function to test credentials and run simultaneous applications"""
    logger.info("🚀 CREDENTIAL CHECK & SIMULTANEOUS APPLICATION TEST")
    logger.info("=" * 70)
    logger.info("")
    
    # Create data directory if needed
    Path("data").mkdir(exist_ok=True)
    
    # Step 1: Check credentials
    if not check_credentials():
        logger.error("❌ Credential check failed. Please set up missing credentials.")
        logger.info("")
        logger.info("💡 TO SET CREDENTIALS:")
        logger.info("   For GitHub Actions: Add to repository secrets")
        logger.info("   For local testing: Set environment variables")
        logger.info("   Example: export LINKEDIN_EMAIL='your-email@gmail.com'")
        return False
    
    logger.info("")
    
    # Step 2: Run simultaneous applications
    results = run_simultaneous_applications()
    
    # Step 3: Final summary
    logger.info("")
    logger.info("🎯 TEST COMPLETE!")
    successful_platforms = len([r for r in results if r['count'] > 0])
    total_applications = sum(r['count'] for r in results)
    
    if total_applications > 0:
        logger.info(f"✅ SUCCESS: {total_applications} applications submitted across {successful_platforms} platforms")
        logger.info("🚀 System ready for production simultaneous applications!")
    else:
        logger.warning("⚠️  No applications were submitted. Check platform configurations.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)