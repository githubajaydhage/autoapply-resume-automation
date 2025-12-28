"""
Naukri.com Job Scraper
Scrapes job listings from Naukri.com - India's leading job portal.
"""

import os
import re
import time
import random
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class NaukriScraper:
    """Scrape job listings from Naukri.com."""
    
    BASE_URL = "https://www.naukri.com"
    
    # Headers to mimic browser
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Popular job locations in India
    LOCATIONS = {
        'bangalore': 'bangalore-jobs',
        'mumbai': 'mumbai-jobs',
        'delhi': 'delhi-ncr-jobs',
        'hyderabad': 'hyderabad-jobs',
        'chennai': 'chennai-jobs',
        'pune': 'pune-jobs',
        'kolkata': 'kolkata-jobs',
        'noida': 'noida-jobs',
        'gurgaon': 'gurgaon-jobs',
        'remote': 'work-from-home-jobs',
    }
    
    # Experience levels
    EXPERIENCE_MAPPING = {
        'fresher': '0to1',
        'junior': '1to3',
        'mid': '3to5',
        'senior': '5to10',
        'lead': '10to15',
    }
    
    def __init__(self, output_dir: str = 'data'):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        logging.info("🔍 Naukri.com Job Scraper initialized")
    
    def build_search_url(self, 
                         keywords: List[str],
                         location: str = None,
                         experience: str = None,
                         page: int = 1) -> str:
        """Build Naukri search URL."""
        
        # Format keywords for URL
        keyword_str = '-'.join(keywords).lower().replace(' ', '-')
        
        # Base search URL
        url = f"{self.BASE_URL}/{keyword_str}-jobs"
        
        # Add location
        if location and location.lower() in self.LOCATIONS:
            url = f"{self.BASE_URL}/{keyword_str}-jobs-in-{location.lower()}"
        
        # Add query parameters
        params = []
        
        if experience and experience.lower() in self.EXPERIENCE_MAPPING:
            exp_code = self.EXPERIENCE_MAPPING[experience.lower()]
            params.append(f"experience={exp_code}")
        
        if page > 1:
            params.append(f"page={page}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def extract_job_details(self, job_element) -> Optional[Dict]:
        """Extract job details from a job card element."""
        try:
            # Try different selectors as Naukri changes their HTML structure
            job = {}
            
            # Job title
            title_elem = job_element.select_one('a.title, .jobTupleHeader a, .title')
            if title_elem:
                job['title'] = title_elem.get_text(strip=True)
                job['link'] = title_elem.get('href', '')
                if job['link'] and not job['link'].startswith('http'):
                    job['link'] = self.BASE_URL + job['link']
            
            # Company name
            company_elem = job_element.select_one('.companyInfo a, .subTitle, .companyname')
            if company_elem:
                job['company'] = company_elem.get_text(strip=True)
            
            # Experience required
            exp_elem = job_element.select_one('.experience .ellipsis, .expwdth')
            if exp_elem:
                job['experience'] = exp_elem.get_text(strip=True)
            
            # Salary
            salary_elem = job_element.select_one('.salary .ellipsis, .salary')
            if salary_elem:
                job['salary'] = salary_elem.get_text(strip=True)
            
            # Location
            loc_elem = job_element.select_one('.location .ellipsis, .location')
            if loc_elem:
                job['location'] = loc_elem.get_text(strip=True)
            
            # Job description snippet
            desc_elem = job_element.select_one('.job-description, .jobDescription, .row6')
            if desc_elem:
                job['description'] = desc_elem.get_text(strip=True)[:500]
            
            # Skills/Tags
            tags_elems = job_element.select('.tag-li, .skillName, .dot-gt')
            if tags_elems:
                job['skills'] = ', '.join([t.get_text(strip=True) for t in tags_elems[:10]])
            
            # Posted date
            date_elem = job_element.select_one('.date, .postedDate')
            if date_elem:
                job['posted'] = date_elem.get_text(strip=True)
            
            # Validate we have minimum required fields
            if job.get('title') and job.get('company'):
                job['source'] = 'naukri.com'
                job['scraped_at'] = datetime.now().isoformat()
                return job
            
            return None
            
        except Exception as e:
            logging.debug(f"Error extracting job: {e}")
            return None
    
    def scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single page of job listings."""
        jobs = []
        
        try:
            logging.info(f"🌐 Fetching: {url[:80]}...")
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                logging.warning(f"⚠️ Got status {response.status_code}")
                return jobs
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different job card selectors
            job_cards = (
                soup.select('.jobTuple, .srp-jobtuple, article.job') or
                soup.select('[type="tuple"], .list-item') or
                soup.select('.job-card, .cust-job-tuple')
            )
            
            logging.info(f"📋 Found {len(job_cards)} job cards on page")
            
            for card in job_cards:
                job = self.extract_job_details(card)
                if job:
                    jobs.append(job)
            
        except requests.RequestException as e:
            logging.error(f"❌ Request failed: {e}")
        except Exception as e:
            logging.error(f"❌ Scraping error: {e}")
        
        return jobs
    
    def search_jobs(self,
                    keywords: List[str],
                    location: str = None,
                    experience: str = None,
                    max_pages: int = 3,
                    max_jobs: int = 50) -> List[Dict]:
        """Search for jobs with given criteria."""
        
        all_jobs = []
        
        logging.info(f"🔍 Searching: {', '.join(keywords)}")
        if location:
            logging.info(f"📍 Location: {location}")
        if experience:
            logging.info(f"👤 Experience: {experience}")
        
        for page in range(1, max_pages + 1):
            url = self.build_search_url(keywords, location, experience, page)
            
            jobs = self.scrape_page(url)
            all_jobs.extend(jobs)
            
            logging.info(f"📊 Page {page}: Got {len(jobs)} jobs (Total: {len(all_jobs)})")
            
            if len(all_jobs) >= max_jobs:
                all_jobs = all_jobs[:max_jobs]
                break
            
            if not jobs:
                break
            
            # Be polite - random delay between pages
            delay = random.uniform(2, 4)
            time.sleep(delay)
        
        return all_jobs
    
    def scrape_multiple_searches(self, searches: List[Dict]) -> List[Dict]:
        """Run multiple search queries and combine results."""
        all_jobs = []
        seen_links = set()
        
        for search in searches:
            keywords = search.get('keywords', [])
            location = search.get('location')
            experience = search.get('experience')
            
            jobs = self.search_jobs(
                keywords=keywords,
                location=location,
                experience=experience,
                max_pages=search.get('max_pages', 2),
                max_jobs=search.get('max_jobs', 30)
            )
            
            # Deduplicate
            for job in jobs:
                link = job.get('link', '')
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_jobs.append(job)
            
            # Delay between searches
            time.sleep(random.uniform(3, 5))
        
        return all_jobs
    
    def save_results(self, jobs: List[Dict], filename: str = 'naukri_jobs.csv') -> str:
        """Save scraped jobs to CSV."""
        if not jobs:
            logging.warning("⚠️ No jobs to save")
            return None
        
        df = pd.DataFrame(jobs)
        
        # Reorder columns
        column_order = ['title', 'company', 'location', 'experience', 'salary', 
                        'skills', 'description', 'link', 'posted', 'source', 'scraped_at']
        
        existing_cols = [c for c in column_order if c in df.columns]
        extra_cols = [c for c in df.columns if c not in column_order]
        df = df[existing_cols + extra_cols]
        
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        
        logging.info(f"💾 Saved {len(jobs)} jobs to {filepath}")
        return filepath
    
    def merge_with_existing(self, new_jobs: List[Dict], existing_file: str = 'jobs_today.csv') -> pd.DataFrame:
        """Merge new jobs with existing jobs file."""
        filepath = os.path.join(self.output_dir, existing_file)
        
        new_df = pd.DataFrame(new_jobs)
        
        if os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            
            # Add source column if missing
            if 'source' not in existing_df.columns:
                existing_df['source'] = 'other'
            
            # Combine and deduplicate
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Deduplicate by link or by title+company
            if 'link' in combined.columns:
                combined = combined.drop_duplicates(subset=['link'], keep='first')
            else:
                combined = combined.drop_duplicates(subset=['title', 'company'], keep='first')
            
            combined.to_csv(filepath, index=False)
            logging.info(f"📊 Merged: {len(new_jobs)} new + {len(existing_df)} existing = {len(combined)} total jobs")
            
            return combined
        else:
            new_df.to_csv(filepath, index=False)
            logging.info(f"💾 Created new jobs file with {len(new_jobs)} jobs")
            return new_df


def main():
    """Main function to scrape Naukri jobs."""
    logging.info("="*60)
    logging.info("🔍 NAUKRI.COM JOB SCRAPER")
    logging.info("="*60)
    
    scraper = NaukriScraper()
    
    # Get search keywords from environment or use defaults
    keywords_env = os.getenv('NAUKRI_KEYWORDS', 'python developer, data scientist, software engineer')
    keywords_list = [k.strip() for k in keywords_env.split(',')]
    
    location = os.getenv('NAUKRI_LOCATION', 'bangalore')
    experience = os.getenv('NAUKRI_EXPERIENCE', 'mid')
    
    # Build search queries
    searches = []
    for keyword in keywords_list:
        searches.append({
            'keywords': [keyword],
            'location': location,
            'experience': experience,
            'max_pages': 2,
            'max_jobs': 20
        })
    
    logging.info(f"📋 Running {len(searches)} search queries...")
    
    # Run searches
    all_jobs = scraper.scrape_multiple_searches(searches)
    
    if all_jobs:
        # Save to separate file
        scraper.save_results(all_jobs, 'naukri_jobs.csv')
        
        # Merge with main jobs file
        scraper.merge_with_existing(all_jobs, 'jobs_today.csv')
        
        logging.info(f"\n📊 Summary:")
        logging.info(f"   Total jobs scraped: {len(all_jobs)}")
        
        # Show top companies
        companies = {}
        for job in all_jobs:
            company = job.get('company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
        
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
        logging.info(f"   Top companies: {', '.join([c[0] for c in top_companies])}")
    else:
        logging.warning("⚠️ No jobs found. Naukri might be blocking automated access.")
        logging.info("💡 Try using the RSS feed alternative in reliable_job_scraper.py")
    
    logging.info("="*60)
    logging.info("✅ Naukri scraping complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
