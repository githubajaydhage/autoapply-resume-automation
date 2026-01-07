"""
Enhanced Job Scraper - Adds more job sources including AngelList, Instahyre, and more
Uses multiple APIs and scraping techniques for comprehensive job coverage
"""

import requests
import pandas as pd
import os
import sys
import logging
import time
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class EnhancedJobScraper:
    """Scrapes jobs from multiple additional sources."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        self.output_path = os.path.join(self.data_path, 'enhanced_jobs.csv')
        
        # Default search parameters
        self.keywords = ['data analyst', 'business analyst', 'data scientist', 'analytics']
        self.locations = ['bangalore', 'india', 'remote']
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        self.all_jobs = []
    
    def scrape_wellfound_api(self) -> list:
        """
        Scrape from Wellfound (formerly AngelList Talent) API.
        Uses public GraphQL API endpoints.
        """
        logging.info("🚀 Scraping Wellfound (AngelList)...")
        jobs = []
        
        # Wellfound uses GraphQL, we'll use their public search endpoint
        base_url = "https://wellfound.com/api/v1/jobs/search"
        
        try:
            for keyword in self.keywords[:2]:  # Limit queries
                params = {
                    'query': keyword,
                    'location': 'india',
                    'remote': 'true',
                    'page': 1,
                    'per_page': 50
                }
                
                response = requests.get(
                    base_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        listings = data.get('jobs', data.get('results', []))
                        
                        for job in listings:
                            parsed = {
                                'title': job.get('title', ''),
                                'company': job.get('company', {}).get('name', job.get('company_name', '')),
                                'location': job.get('location', 'Remote'),
                                'url': job.get('url', f"https://wellfound.com/jobs/{job.get('id', '')}"),
                                'source': 'Wellfound',
                                'scraped_at': datetime.now().isoformat(),
                                'remote': job.get('remote', True),
                                'salary': job.get('salary', '')
                            }
                            
                            if parsed['title'] and parsed['company']:
                                jobs.append(parsed)
                    except json.JSONDecodeError:
                        pass
                
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            logging.warning(f"Wellfound API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Wellfound")
        return jobs
    
    def scrape_instahyre_api(self) -> list:
        """
        Scrape from Instahyre - popular Indian job portal.
        Uses their public API endpoints.
        """
        logging.info("🏢 Scraping Instahyre...")
        jobs = []
        
        base_url = "https://www.instahyre.com/api/v1/job-listings/"
        
        try:
            params = {
                'query': 'data analyst',
                'location': 'bangalore',
                'page': 1,
                'page_size': 50
            }
            
            response = requests.get(
                base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('results', data.get('jobs', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', job.get('job_title', '')),
                            'company': job.get('company', {}).get('name', job.get('company_name', '')),
                            'location': job.get('location', job.get('city', 'India')),
                            'url': job.get('url', f"https://www.instahyre.com/job/{job.get('id', '')}"),
                            'source': 'Instahyre',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': 'remote' in str(job).lower(),
                            'salary': job.get('salary_range', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                
        except Exception as e:
            logging.warning(f"Instahyre API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Instahyre")
        return jobs
    
    def scrape_cutshort(self) -> list:
        """
        Scrape from Cutshort - Indian startup job platform.
        """
        logging.info("✂️ Scraping Cutshort...")
        jobs = []
        
        base_url = "https://cutshort.io/api/jobs/search"
        
        try:
            payload = {
                'query': 'data analyst',
                'location': 'bangalore',
                'experience': {'min': 0, 'max': 5}
            }
            
            response = requests.post(
                base_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('jobs', data.get('results', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', ''),
                            'company': job.get('company', {}).get('name', job.get('company_name', '')),
                            'location': job.get('location', 'India'),
                            'url': job.get('url', f"https://cutshort.io/job/{job.get('id', '')}"),
                            'source': 'Cutshort',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': job.get('remote', False),
                            'salary': job.get('salary', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logging.warning(f"Cutshort API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Cutshort")
        return jobs
    
    def scrape_linkedin_rss(self) -> list:
        """
        Scrape from LinkedIn RSS feeds (publicly available).
        Note: Limited data but legitimate access.
        """
        logging.info("🔗 Scraping LinkedIn RSS...")
        jobs = []
        
        # LinkedIn provides RSS feeds for job searches
        rss_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        
        try:
            params = {
                'keywords': 'data analyst',
                'location': 'India',
                'geoId': '102713980',  # India
                'start': 0
            }
            
            response = requests.get(
                rss_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for card in soup.find_all('div', class_='base-card'):
                    try:
                        title_elem = card.find('h3', class_='base-search-card__title')
                        company_elem = card.find('h4', class_='base-search-card__subtitle')
                        location_elem = card.find('span', class_='job-search-card__location')
                        link_elem = card.find('a', class_='base-card__full-link')
                        
                        parsed = {
                            'title': title_elem.get_text(strip=True) if title_elem else '',
                            'company': company_elem.get_text(strip=True) if company_elem else '',
                            'location': location_elem.get_text(strip=True) if location_elem else 'India',
                            'url': link_elem['href'] if link_elem and link_elem.get('href') else '',
                            'source': 'LinkedIn',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': False,
                            'salary': ''
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"LinkedIn RSS error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from LinkedIn")
        return jobs
    
    def scrape_glassdoor_api(self) -> list:
        """
        Scrape from Glassdoor public listings.
        """
        logging.info("🪟 Scraping Glassdoor...")
        jobs = []
        
        # Glassdoor's public API endpoint
        base_url = "https://www.glassdoor.co.in/Job/jobs.htm"
        
        try:
            params = {
                'sc.keyword': 'data analyst',
                'locT': 'C',
                'locId': '2906753',  # Bangalore
                'jobType': 'all',
            }
            
            response = requests.get(
                base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find job cards
                for card in soup.find_all(['li', 'div'], class_=re.compile(r'job.*card|react-job')):
                    try:
                        title_elem = card.find(['a', 'span'], class_=re.compile(r'job.*title'))
                        company_elem = card.find(['a', 'span'], class_=re.compile(r'employer'))
                        location_elem = card.find(['span'], class_=re.compile(r'location'))
                        
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        company = company_elem.get_text(strip=True) if company_elem else ''
                        
                        if title and company:
                            parsed = {
                                'title': title,
                                'company': company,
                                'location': location_elem.get_text(strip=True) if location_elem else 'India',
                                'url': title_elem.get('href', '') if title_elem and title_elem.name == 'a' else '',
                                'source': 'Glassdoor',
                                'scraped_at': datetime.now().isoformat(),
                                'remote': False,
                                'salary': ''
                            }
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"Glassdoor error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Glassdoor")
        return jobs
    
    def scrape_indeed_rss(self) -> list:
        """
        Scrape from Indeed RSS feeds.
        """
        logging.info("📋 Scraping Indeed...")
        jobs = []
        
        rss_url = "https://www.indeed.co.in/rss"
        
        try:
            params = {
                'q': 'data analyst',
                'l': 'bangalore',
                'sort': 'date'
            }
            
            response = requests.get(
                rss_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                
                for item in soup.find_all('item'):
                    try:
                        title = item.find('title')
                        link = item.find('link')
                        
                        # Parse company from title (format: "Title - Company")
                        title_text = title.get_text() if title else ''
                        parts = title_text.split(' - ')
                        job_title = parts[0] if parts else title_text
                        company = parts[1] if len(parts) > 1 else ''
                        
                        parsed = {
                            'title': job_title.strip(),
                            'company': company.strip(),
                            'location': 'Bangalore',
                            'url': link.get_text() if link else '',
                            'source': 'Indeed',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': 'remote' in title_text.lower(),
                            'salary': ''
                        }
                        
                        if parsed['title']:
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"Indeed RSS error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Indeed")
        return jobs
    
    def scrape_foundit(self) -> list:
        """
        Scrape from Foundit (formerly Monster India).
        """
        logging.info("👹 Scraping Foundit (Monster)...")
        jobs = []
        
        api_url = "https://www.foundit.in/middleware/jobsearch"
        
        try:
            payload = {
                'query': 'data analyst',
                'locations': ['bangalore'],
                'experience': {'min': 0, 'max': 5},
                'page': 1,
                'limit': 50
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('jobs', data.get('jobDetails', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', job.get('designationName', '')),
                            'company': job.get('companyName', job.get('company', {}).get('name', '')),
                            'location': job.get('locations', job.get('location', 'India')),
                            'url': job.get('url', f"https://www.foundit.in/job/{job.get('jobId', '')}"),
                            'source': 'Foundit',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': job.get('isRemote', False),
                            'salary': job.get('salary', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logging.warning(f"Foundit API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Foundit")
        return jobs
    
    def scrape_all(self) -> pd.DataFrame:
        """Scrape from all enhanced sources."""
        logging.info("="*60)
        logging.info("🔍 ENHANCED JOB SCRAPER")
        logging.info("="*60)
        
        all_jobs = []
        
        # Scrape from all sources
        scrapers = [
            self.scrape_wellfound_api,
            self.scrape_instahyre_api,
            self.scrape_cutshort,
            self.scrape_linkedin_rss,
            self.scrape_glassdoor_api,
            self.scrape_indeed_rss,
            self.scrape_foundit,
        ]
        
        for scraper in scrapers:
            try:
                jobs = scraper()
                all_jobs.extend(jobs)
            except Exception as e:
                logging.warning(f"Scraper error: {e}")
            time.sleep(2)  # Be polite between scrapers
        
        # Create DataFrame
        df = pd.DataFrame(all_jobs)
        
        if not df.empty:
            # Clean data
            df['title'] = df['title'].str.strip()
            df['company'] = df['company'].str.strip()
            df = df[df['title'] != '']
            df = df[df['company'] != '']
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['title', 'company'], keep='first')
            
            # Save
            df.to_csv(self.output_path, index=False)
            
            logging.info("="*60)
            logging.info(f"✅ ENHANCED SCRAPING COMPLETE")
            logging.info(f"   Total jobs: {len(df)}")
            logging.info(f"   Sources: {df['source'].nunique()}")
            logging.info(f"   Saved to: {self.output_path}")
            logging.info("="*60)
        else:
            logging.warning("No jobs scraped from enhanced sources")
        
        return df
    
    def merge_with_existing(self) -> pd.DataFrame:
        """Merge enhanced jobs with existing jobs_today.csv."""
        existing_path = os.path.join(self.data_path, 'jobs_today.csv')
        
        enhanced_df = self.scrape_all()
        
        if os.path.exists(existing_path):
            existing_df = pd.read_csv(existing_path)
            
            # Ensure same columns
            for col in ['source', 'scraped_at', 'remote', 'salary']:
                if col not in existing_df.columns:
                    existing_df[col] = ''
            
            # Merge - handle empty DataFrames
            if existing_df.empty:
                merged = enhanced_df
            elif enhanced_df.empty:
                merged = existing_df
            else:
                merged = pd.concat([existing_df, enhanced_df], ignore_index=True)
            merged = merged.drop_duplicates(subset=['title', 'company'], keep='first')
            
            # Save back
            merged.to_csv(existing_path, index=False)
            logging.info(f"📊 Merged: {len(existing_df)} existing + {len(enhanced_df)} enhanced = {len(merged)} total")
            
            return merged
        
        # No existing file, save enhanced as jobs_today
        enhanced_df.to_csv(existing_path, index=False)
        return enhanced_df


def main():
    """Main function to run enhanced job scraping."""
    scraper = EnhancedJobScraper()
    jobs_df = scraper.merge_with_existing()
    
    if not jobs_df.empty:
        print(f"\n📊 Job Sources Summary:")
        print(jobs_df['source'].value_counts())


if __name__ == "__main__":
    main()
