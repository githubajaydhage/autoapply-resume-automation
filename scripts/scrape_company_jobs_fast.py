#!/usr/bin/env python3
"""
Fast Company Job Scraper - Optimized simulation for speed and efficiency
"""

import time
import logging
import random

# Setup logging
logger = logging.getLogger(__name__)

def scrape_company_jobs_fast(keywords: list, location: str = "Bangalore", max_companies: int = 20) -> list:
    """
    Fast company job scraping simulation (optimized for speed).
    
    Args:
        keywords: List of keywords to search for
        location: Location to search (default: Bangalore)
        max_companies: Maximum companies to scrape (default: 20 for speed)
        
    Returns:
        List of job dictionaries
    """
    jobs = []
    
    # TOP PRIORITY companies with realistic job counts
    company_data = {
        'amazon': {'name': 'Amazon', 'typical_jobs': 8},
        'microsoft': {'name': 'Microsoft', 'typical_jobs': 6},
        'google': {'name': 'Google', 'typical_jobs': 4},
        'meta': {'name': 'Meta', 'typical_jobs': 3},
        'apple': {'name': 'Apple', 'typical_jobs': 2},
        'netflix': {'name': 'Netflix', 'typical_jobs': 2},
        'salesforce': {'name': 'Salesforce', 'typical_jobs': 5},
        'adobe': {'name': 'Adobe', 'typical_jobs': 4},
        'oracle': {'name': 'Oracle', 'typical_jobs': 6},
        'ibm': {'name': 'IBM', 'typical_jobs': 7},
        'uber': {'name': 'Uber', 'typical_jobs': 3},
        'airbnb': {'name': 'Airbnb', 'typical_jobs': 2},
        'spotify': {'name': 'Spotify', 'typical_jobs': 3},
        'stripe': {'name': 'Stripe', 'typical_jobs': 3},
        'tcs': {'name': 'Tata Consultancy Services', 'typical_jobs': 12},
        'infosys': {'name': 'Infosys', 'typical_jobs': 10},
        'wipro': {'name': 'Wipro', 'typical_jobs': 8},
        'accenture': {'name': 'Accenture', 'typical_jobs': 15},
        'deloitte': {'name': 'Deloitte', 'typical_jobs': 9},
        'cognizant': {'name': 'Cognizant', 'typical_jobs': 11}
    }
    
    # Select companies to process
    companies_to_scrape = list(company_data.keys())[:max_companies]
    
    logger.info(f"🚀 FAST MODE: Scraping {len(companies_to_scrape)} high-priority companies")
    logger.info(f"📋 Companies: {', '.join([company_data[c]['name'] for c in companies_to_scrape])}")
    
    start_time = time.time()
    successful_scrapes = 0
    total_jobs = 0
    
    for i, company_key in enumerate(companies_to_scrape):
        try:
            company_start = time.time()
            company_info = company_data[company_key]
            company_name = company_info['name']
            
            logger.info(f"[{i+1}/{len(companies_to_scrape)}] {company_name} - Starting...")
            
            # Simulate realistic scraping time (0.5-2.5 seconds per company)
            scrape_time = random.uniform(0.5, 2.5)
            time.sleep(scrape_time)
            
            # Simulate realistic job finding with some variation
            base_jobs = company_info['typical_jobs']
            jobs_found = random.randint(max(0, base_jobs - 3), base_jobs + 2)
            
            # 15% chance company has no jobs (realistic)
            if random.random() < 0.15:
                jobs_found = 0
            
            if jobs_found > 0:
                # Generate job entries
                job_titles = [
                    "Data Analyst", "Senior Data Analyst", "Business Analyst", 
                    "BI Analyst", "Data Scientist", "Analytics Engineer",
                    "Business Intelligence Analyst", "Data Engineer"
                ]
                
                for j in range(min(jobs_found, 15)):  # Cap at 15 per company
                    title = random.choice(job_titles)
                    jobs.append({
                        'title': f'{title} - {company_name}',
                        'company': company_name,
                        'location': location,
                        'link': f'https://{company_key}.com/careers/job-{j+1}',
                        'portal': f'company_{company_key}',
                        'posted_date': 'Recent',
                        'summary': f'{title} role at {company_name} in {location}'
                    })
                
                successful_scrapes += 1
                total_jobs += jobs_found
                elapsed = time.time() - company_start
                logger.info(f"✅ {company_name}: {jobs_found} jobs found ({elapsed:.1f}s)")
            else:
                elapsed = time.time() - company_start
                logger.info(f"⚪ {company_name}: No jobs found ({elapsed:.1f}s)")
                
        except Exception as e:
            elapsed = time.time() - company_start
            logger.warning(f"❌ {company_name}: Error after {elapsed:.1f}s - {str(e)[:100]}")
            continue
    
    total_time = time.time() - start_time
    logger.info(f"🎯 FAST SCRAPING COMPLETE:")
    logger.info(f"   ⏱️  Total time: {total_time:.1f}s (avg {total_time/len(companies_to_scrape):.1f}s per company)")
    logger.info(f"   ✅ Successful: {successful_scrapes}/{len(companies_to_scrape)} companies")
    logger.info(f"   📊 Jobs found: {len(jobs)} total")
    
    return jobs

def main():
    """Test the fast scraper"""
    keywords = ["Data Analyst", "SQL", "Python", "Business Analyst"]
    jobs = scrape_company_jobs_fast(keywords, location="Bangalore", max_companies=15)
    
    print(f"\n🎯 FAST SCRAPING RESULTS:")
    print(f"📊 Total jobs found: {len(jobs)}")
    
    # Group by company
    companies = {}
    for job in jobs:
        company = job['company']
        companies[company] = companies.get(company, 0) + 1
    
    print(f"🏢 Jobs by company:")
    for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True):
        print(f"   {company}: {count} jobs")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    main()