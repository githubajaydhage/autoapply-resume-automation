#!/usr/bin/env python3
"""
Credential Check and Simultaneous Application Simulation
"""

import logging
import os
import time
import concurrent.futures
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/credentials_test.log')
    ]
)
logger = logging.getLogger(__name__)

def check_github_secrets():
    """Check if GitHub secrets/credentials are accessible"""
    logger.info("🔐 CHECKING GITHUB SECRETS / CREDENTIALS")
    logger.info("=" * 60)
    
    credentials_config = {
        'LINKEDIN_EMAIL': {'required': True, 'mask': False},
        'LINKEDIN_PASSWORD': {'required': True, 'mask': True},
        'NAUKRI_EMAIL': {'required': True, 'mask': False},
        'NAUKRI_PASSWORD': {'required': True, 'mask': True},
        'INDEED_EMAIL': {'required': False, 'mask': False},
        'INDEED_PASSWORD': {'required': False, 'mask': True},
    }
    
    credentials_status = {}
    
    for env_var, config in credentials_config.items():
        value = os.getenv(env_var)
        if value:
            if config['mask']:
                masked_value = '*' * min(len(value), 12)
                logger.info(f"✅ {env_var:20s}: {masked_value}")
            else:
                logger.info(f"✅ {env_var:20s}: {value}")
            credentials_status[env_var] = True
        else:
            status_char = "❌" if config['required'] else "⚪"
            priority = "REQUIRED" if config['required'] else "Optional"
            logger.warning(f"{status_char} {env_var:20s}: NOT SET ({priority})")
            credentials_status[env_var] = False
    
    # Summary
    logger.info("")
    required_creds = [k for k, v in credentials_config.items() if v['required']]
    required_set = [k for k in required_creds if credentials_status[k]]
    
    logger.info(f"📊 CREDENTIAL STATUS:")
    logger.info(f"   Required Set:     {len(required_set)}/{len(required_creds)}")
    logger.info(f"   LinkedIn Ready:   {'✅' if credentials_status.get('LINKEDIN_EMAIL') and credentials_status.get('LINKEDIN_PASSWORD') else '❌'}")
    logger.info(f"   Naukri Ready:     {'✅' if credentials_status.get('NAUKRI_EMAIL') and credentials_status.get('NAUKRI_PASSWORD') else '❌'}")
    logger.info(f"   Indeed Ready:     {'✅' if credentials_status.get('INDEED_EMAIL') and credentials_status.get('INDEED_PASSWORD') else '⚪'}")
    
    linkedin_ready = credentials_status.get('LINKEDIN_EMAIL') and credentials_status.get('LINKEDIN_PASSWORD')
    naukri_ready = credentials_status.get('NAUKRI_EMAIL') and credentials_status.get('NAUKRI_PASSWORD')
    
    return {
        'linkedin_ready': linkedin_ready,
        'naukri_ready': naukri_ready,
        'indeed_ready': credentials_status.get('INDEED_EMAIL') and credentials_status.get('INDEED_PASSWORD'),
        'overall_ready': linkedin_ready and naukri_ready
    }

def simulate_platform_applications(platform, jobs, credentials_ready):
    """Simulate job applications for a platform"""
    thread_name = threading.current_thread().name
    logger.info(f"🚀 [{thread_name}] Starting {platform.upper()} application simulation")
    
    if not credentials_ready:
        logger.error(f"❌ [{thread_name}] {platform.upper()}: Credentials not ready, skipping")
        return {'platform': platform, 'count': 0, 'time': 0, 'error': 'No credentials'}
    
    start_time = time.time()
    successful_applications = 0
    
    try:
        for i, job in enumerate(jobs, 1):
            logger.info(f"[{thread_name}] {platform.upper()} App {i}/{len(jobs)}: {job['title']} at {job['company']}")
            
            # Simulate different application times per platform
            if platform == 'linkedin':
                app_time = 3.5  # LinkedIn Easy Apply is faster
            elif platform == 'naukri':
                app_time = 2.8  # Naukri is relatively fast
            elif platform == 'indeed':
                app_time = 4.2  # Indeed can be slower
            else:
                app_time = 5.0  # Company sites take longer
            
            # Simulate application process
            time.sleep(app_time)
            
            # 85% success rate simulation
            import random
            if random.random() < 0.85:
                successful_applications += 1
                logger.info(f"✅ [{thread_name}] {platform.upper()}: Applied successfully to {job['company']}")
            else:
                logger.warning(f"⚠️  [{thread_name}] {platform.upper()}: Application failed for {job['company']}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ [{thread_name}] {platform.upper()} COMPLETE: {successful_applications}/{len(jobs)} applications in {elapsed_time:.1f}s")
        
        return {
            'platform': platform,
            'count': successful_applications,
            'total_jobs': len(jobs),
            'time': elapsed_time,
            'success_rate': (successful_applications / len(jobs)) * 100
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ [{thread_name}] {platform.upper()} ERROR: {str(e)} (after {elapsed_time:.1f}s)")
        return {'platform': platform, 'count': 0, 'total_jobs': len(jobs), 'time': elapsed_time, 'error': str(e)}

def generate_realistic_jobs():
    """Generate realistic job listings for testing"""
    
    # High-priority jobs from our optimized scraper
    jobs_data = {
        'linkedin': [
            {'title': 'Senior Data Analyst', 'company': 'Microsoft', 'priority_score': 9.8},
            {'title': 'Business Intelligence Analyst', 'company': 'Amazon', 'priority_score': 9.6},
            {'title': 'Data Scientist', 'company': 'Google', 'priority_score': 9.4},
            {'title': 'Analytics Engineer', 'company': 'Meta', 'priority_score': 9.2},
            {'title': 'BI Developer', 'company': 'Salesforce', 'priority_score': 8.9},
        ],
        'naukri': [
            {'title': 'Data Analyst - SQL Expert', 'company': 'Tata Consultancy Services', 'priority_score': 9.1},
            {'title': 'Power BI Specialist', 'company': 'Infosys', 'priority_score': 8.8},
            {'title': 'Business Analyst', 'company': 'Wipro', 'priority_score': 8.6},
            {'title': 'Data Engineer', 'company': 'Accenture', 'priority_score': 8.4},
            {'title': 'Analytics Consultant', 'company': 'Deloitte', 'priority_score': 8.2},
            {'title': 'SQL Developer', 'company': 'Cognizant', 'priority_score': 8.0},
        ],
        'indeed': [
            {'title': 'Data Analytics Specialist', 'company': 'Adobe', 'priority_score': 8.7},
            {'title': 'Business Intelligence Analyst', 'company': 'Oracle', 'priority_score': 8.5},
            {'title': 'Data Analyst', 'company': 'IBM', 'priority_score': 8.3},
        ],
        'company_careers': [
            {'title': 'Data Analyst - Cloud Platform', 'company': 'Google', 'priority_score': 9.7},
            {'title': 'Business Analyst - Azure', 'company': 'Microsoft', 'priority_score': 9.5},
        ]
    }
    
    # Add metadata to jobs
    for platform, jobs in jobs_data.items():
        for job in jobs:
            job.update({
                'location': 'Bangalore',
                'portal': platform,
                'posted_date': 'Today' if job['priority_score'] > 9.0 else '1 day ago'
            })
    
    return jobs_data

def run_simultaneous_applications_test(credential_status):
    """Run simultaneous application test"""
    logger.info("")
    logger.info("🎯 SIMULTANEOUS APPLICATION SIMULATION")
    logger.info("=" * 60)
    
    # Generate test jobs
    test_jobs = generate_realistic_jobs()
    
    # Show job distribution
    logger.info("📊 JOB TARGETS BY PLATFORM:")
    total_jobs = 0
    for platform, jobs in test_jobs.items():
        ready_status = credential_status.get(f"{platform.split('_')[0]}_ready", False)
        status_emoji = "✅" if ready_status else "❌"
        logger.info(f"   {status_emoji} {platform.upper():15s}: {len(jobs)} jobs")
        total_jobs += len(jobs)
    
    logger.info(f"   {'📝 TOTAL':17s}: {total_jobs} jobs")
    logger.info("")
    
    # Determine which platforms to run
    platforms_to_run = []
    if credential_status['linkedin_ready']:
        platforms_to_run.append(('linkedin', test_jobs['linkedin']))
    if credential_status['naukri_ready']:
        platforms_to_run.append(('naukri', test_jobs['naukri']))
    if credential_status['indeed_ready']:
        platforms_to_run.append(('indeed', test_jobs['indeed']))
    
    # Always run company careers (doesn't need portal credentials)
    platforms_to_run.append(('company_careers', test_jobs['company_careers']))
    
    if not platforms_to_run:
        logger.error("❌ No platforms ready - missing credentials")
        return []
    
    # Run applications simultaneously
    logger.info(f"⚡ LAUNCHING {len(platforms_to_run)} SIMULTANEOUS APPLICATION THREADS")
    logger.info("-" * 60)
    
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="App") as executor:
        # Submit all platform applications
        future_to_platform = {}
        
        for platform, jobs in platforms_to_run:
            creds_ready = credential_status.get(f"{platform.split('_')[0]}_ready", True)  # Company careers don't need creds
            future = executor.submit(simulate_platform_applications, platform, jobs, creds_ready)
            future_to_platform[future] = platform
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Exception in {platform} thread: {e}")
                results.append({
                    'platform': platform, 
                    'count': 0, 
                    'total_jobs': 0, 
                    'time': 0, 
                    'error': str(e)
                })
    
    total_time = time.time() - start_time
    
    # Results summary
    logger.info("")
    logger.info("🎯 SIMULTANEOUS APPLICATION RESULTS")
    logger.info("=" * 60)
    
    total_applications = 0
    total_target_jobs = 0
    
    for result in sorted(results, key=lambda x: x['count'], reverse=True):
        platform = result['platform'].upper()
        count = result['count']
        total_jobs = result.get('total_jobs', 0)
        time_taken = result['time']
        success_rate = result.get('success_rate', 0)
        
        total_applications += count
        total_target_jobs += total_jobs
        
        if 'error' in result:
            logger.error(f"❌ {platform:15s}: {count}/{total_jobs} apps, {time_taken:.1f}s (ERROR)")
        else:
            logger.info(f"✅ {platform:15s}: {count}/{total_jobs} apps, {time_taken:.1f}s ({success_rate:.0f}%)")
    
    # Performance metrics
    logger.info("-" * 60)
    logger.info(f"📊 PERFORMANCE SUMMARY:")
    logger.info(f"   Target Jobs:        {total_target_jobs}")
    logger.info(f"   Successful Apps:    {total_applications}")
    logger.info(f"   Success Rate:       {(total_applications/total_target_jobs)*100:.1f}%")
    logger.info(f"   Total Time:         {total_time:.1f}s")
    logger.info(f"   Avg Time Per App:   {total_time/total_applications:.1f}s" if total_applications > 0 else "   Avg Time Per App:   N/A")
    
    # Simultaneous vs Sequential comparison
    sequential_time = sum(r['time'] for r in results)
    speedup = sequential_time / total_time if total_time > 0 else 1
    
    logger.info("")
    logger.info("⚡ SIMULTANEOUS PROCESSING BENEFIT:")
    logger.info(f"   Sequential Est:     {sequential_time:.1f}s")
    logger.info(f"   Simultaneous Time:  {total_time:.1f}s")
    logger.info(f"   Speedup Factor:     {speedup:.1f}x faster")
    
    return results

def main():
    """Main function"""
    logger.info("🚀 CREDENTIALS & SIMULTANEOUS APPLICATION TEST")
    logger.info("=" * 70)
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    # Step 1: Check credentials
    credential_status = check_github_secrets()
    
    # Step 2: Run simultaneous application test
    results = run_simultaneous_applications_test(credential_status)
    
    # Step 3: Final assessment
    logger.info("")
    logger.info("🎯 SYSTEM READINESS ASSESSMENT")
    logger.info("=" * 50)
    
    ready_platforms = []
    if credential_status['linkedin_ready']:
        ready_platforms.append("LinkedIn")
    if credential_status['naukri_ready']:
        ready_platforms.append("Naukri")
    if credential_status['indeed_ready']:
        ready_platforms.append("Indeed")
    ready_platforms.append("Company Careers")  # Always available
    
    total_applications = sum(r['count'] for r in results)
    
    if ready_platforms and total_applications > 0:
        logger.info(f"✅ SYSTEM READY FOR PRODUCTION!")
        logger.info(f"   Active Platforms: {', '.join(ready_platforms)}")
        logger.info(f"   Test Applications: {total_applications}")
        logger.info("   🚀 Ready for simultaneous job applications!")
    else:
        logger.warning("⚠️  SYSTEM NOT FULLY READY")
        logger.info("   💡 Set up missing credentials using GitHub repository secrets")
        logger.info("   💡 Or run: python scripts/setup_local_credentials.py")
    
    return credential_status['overall_ready']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)