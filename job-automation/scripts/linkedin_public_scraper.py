"""
LinkedIn Job Scraper - Scrapes job postings from LinkedIn public pages
Uses public RSS/API approaches that don't require authentication
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
import pandas as pd
import os
import time
import random
from urllib.parse import quote_plus
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class LinkedInPublicScraper:
    """Scrapes LinkedIn jobs from public pages without authentication."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def search_jobs(self, keywords: str, location: str = "India", num_jobs: int = 25) -> list:
        """Search for jobs on LinkedIn public job listings."""
        jobs = []
        
        # LinkedIn public job search URL
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        
        # Try LinkedIn's public job listing page
        urls_to_try = [
            f"https://www.linkedin.com/jobs/search/?keywords={encoded_keywords}&location={encoded_location}",
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_keywords}&location={encoded_location}&start=0",
        ]
        
        for url in urls_to_try:
            try:
                logging.info(f"🔍 Searching: {url[:80]}...")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job cards
                    job_cards = soup.find_all('div', {'class': re.compile(r'job-search-card|base-card')})
                    
                    for card in job_cards[:num_jobs]:
                        try:
                            job = self._parse_job_card(card)
                            if job:
                                jobs.append(job)
                        except Exception as e:
                            logging.debug(f"Error parsing job card: {e}")
                            continue
                    
                    if jobs:
                        logging.info(f"✅ Found {len(jobs)} jobs for '{keywords}'")
                        break
                else:
                    logging.warning(f"Got status {response.status_code} from LinkedIn")
                    
            except Exception as e:
                logging.warning(f"Error searching LinkedIn: {e}")
                continue
            
            time.sleep(random.uniform(2, 4))
        
        return jobs
    
    def _parse_job_card(self, card) -> dict:
        """Parse a LinkedIn job card element."""
        job = {}
        
        # Job title
        title_elem = card.find(['h3', 'h4'], {'class': re.compile(r'title|job-title')})
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
        
        # Company name
        company_elem = card.find(['h4', 'a'], {'class': re.compile(r'company|subtitle')})
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Location
        location_elem = card.find(['span', 'div'], {'class': re.compile(r'location|job-search-card__location')})
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # Job URL
        link_elem = card.find('a', href=True)
        if link_elem:
            href = link_elem.get('href', '')
            if '/jobs/' in href:
                job['url'] = href if href.startswith('http') else f"https://www.linkedin.com{href}"
        
        # Job ID
        if 'url' in job:
            job_id_match = re.search(r'/jobs/view/(\d+)', job.get('url', ''))
            if job_id_match:
                job['job_id'] = job_id_match.group(1)
        
        job['source'] = 'linkedin'
        job['scraped_at'] = pd.Timestamp.now().isoformat()
        
        return job if job.get('title') and job.get('company') else None
    
    def get_job_details(self, job_url: str) -> dict:
        """Get detailed job information from a job page."""
        try:
            response = self.session.get(job_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'url': job_url,
                'description': '',
                'poster_info': None,
                'emails': []
            }
            
            # Job description
            desc_elem = soup.find('div', {'class': re.compile(r'description|show-more-less-html')})
            if desc_elem:
                details['description'] = desc_elem.get_text(separator=' ', strip=True)[:2000]
            
            # Look for recruiter/poster info
            poster_elem = soup.find('div', {'class': re.compile(r'job-poster|posted-by')})
            if poster_elem:
                details['poster_info'] = poster_elem.get_text(strip=True)
            
            # Extract any emails from description
            email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
            emails = email_pattern.findall(details['description'])
            details['emails'] = list(set(emails))
            
            return details
            
        except Exception as e:
            logging.warning(f"Error getting job details: {e}")
            return None


class NaukriPublicScraper:
    """Scrapes Naukri jobs from public pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def search_jobs(self, keywords: str, location: str = "bangalore", num_jobs: int = 25) -> list:
        """Search for jobs on Naukri public listings."""
        jobs = []
        
        # Format keywords for URL
        formatted_keywords = keywords.lower().replace(' ', '-')
        formatted_location = location.lower().replace(' ', '-')
        
        # Naukri public search URL
        url = f"https://www.naukri.com/{formatted_keywords}-jobs-in-{formatted_location}"
        
        try:
            logging.info(f"🔍 Searching Naukri: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find job cards
                job_cards = soup.find_all('article', {'class': re.compile(r'jobTuple|srp-jobtuple')})
                if not job_cards:
                    job_cards = soup.find_all('div', {'class': re.compile(r'jobTuple|cust-job-tuple')})
                
                for card in job_cards[:num_jobs]:
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logging.debug(f"Error parsing Naukri job: {e}")
                        continue
                
                logging.info(f"✅ Found {len(jobs)} jobs on Naukri")
            else:
                logging.warning(f"Got status {response.status_code} from Naukri")
                
        except Exception as e:
            logging.warning(f"Error searching Naukri: {e}")
        
        return jobs
    
    def _parse_job_card(self, card) -> dict:
        """Parse a Naukri job card."""
        job = {}
        
        # Job title
        title_elem = card.find('a', {'class': re.compile(r'title|jobTitle')})
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
            job['url'] = title_elem.get('href', '')
        
        # Company
        company_elem = card.find('a', {'class': re.compile(r'comp-name|subTitle')})
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Location
        loc_elem = card.find('span', {'class': re.compile(r'loc|locWdth')})
        if loc_elem:
            job['location'] = loc_elem.get_text(strip=True)
        
        # Experience
        exp_elem = card.find('span', {'class': re.compile(r'exp|expwdth')})
        if exp_elem:
            job['experience'] = exp_elem.get_text(strip=True)
        
        job['source'] = 'naukri'
        job['scraped_at'] = pd.Timestamp.now().isoformat()
        
        return job if job.get('title') and job.get('company') else None


def scrape_jobs_public(keywords_list: list = None, location: str = "Bangalore") -> pd.DataFrame:
    """Scrape jobs from public pages of LinkedIn and Naukri."""
    
    if keywords_list is None:
        # Get keywords from JOB_KEYWORDS environment variable - NO HARDCODED DEFAULTS
        job_keywords = os.getenv('JOB_KEYWORDS', '')
        if job_keywords:
            keywords_list = [k.strip() for k in job_keywords.split(',') if k.strip()]
        else:
            logging.warning("⚠️ JOB_KEYWORDS not set in environment, using empty list")
            keywords_list = []
    
    all_jobs = []
    
    # LinkedIn scraper
    linkedin_scraper = LinkedInPublicScraper()
    for keyword in keywords_list:
        jobs = linkedin_scraper.search_jobs(keyword, location, num_jobs=10)
        all_jobs.extend(jobs)
        time.sleep(random.uniform(3, 6))
    
    # Naukri scraper
    naukri_scraper = NaukriPublicScraper()
    for keyword in keywords_list:
        jobs = naukri_scraper.search_jobs(keyword, location, num_jobs=10)
        all_jobs.extend(jobs)
        time.sleep(random.uniform(3, 6))
    
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        # Remove duplicates by job URL
        df = df.drop_duplicates(subset=['url'], keep='first')
        logging.info(f"📊 Total unique jobs found: {len(df)}")
        return df
    
    return pd.DataFrame()


def main():
    """Main function to run public job scraping."""
    logging.info("🚀 Starting public job scraping...")
    
    location = os.getenv('JOB_LOCATION', 'Bangalore')
    
    jobs_df = scrape_jobs_public(location=location)
    
    if not jobs_df.empty:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs_today.csv')
        jobs_df.to_csv(output_path, index=False)
        logging.info(f"✅ Saved {len(jobs_df)} jobs to {output_path}")
        
        # Print summary
        logging.info("\n📊 Jobs by source:")
        for source, count in jobs_df['source'].value_counts().items():
            logging.info(f"   {source}: {count} jobs")
        
        logging.info("\n📊 Jobs by company (top 10):")
        for company, count in jobs_df['company'].value_counts().head(10).items():
            logging.info(f"   {company}: {count} jobs")
    else:
        logging.warning("⚠️ No jobs found!")


if __name__ == "__main__":
    main()
