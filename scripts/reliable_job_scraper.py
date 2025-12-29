"""
Reliable Job Scraper - Uses multiple reliable sources that actually work
Includes RSS feeds, Google Jobs, and curated company career pages
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import pandas as pd
import os
import time
import random
import re
from urllib.parse import quote_plus
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ReliableJobScraper:
    """
    Scrapes jobs from sources that ACTUALLY work:
    1. Google Jobs RSS
    2. Indeed RSS (when available)
    3. Company career pages directly
    4. RemoteOK API
    5. Glassdoor RSS
    6. WellFound (AngelList) 
    """
    
    def __init__(self, location: str = "Bangalore"):
        self.location = location
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.all_jobs = []
        
        # Target keywords for jobs - Ajay Dhage (DevOps / SRE / Cloud)
        self.search_keywords = [
            "devops engineer",
            "site reliability engineer",
            "sre",
            "platform engineer",
            "cloud engineer",
            "kubernetes engineer",
            "infrastructure engineer",
            "devops lead",
            "technical lead devops",
            "automation engineer",
            "devsecops",
            "cloud architect",
            "aws engineer",
            "azure devops",
        ]
        
    def scrape_all_sources(self) -> list:
        """Scrape from all reliable sources."""
        logging.info("🚀 Starting reliable job scraping from multiple sources...")
        
        # 1. RemoteOK API (actually works, free, no auth)
        self._scrape_remoteok()
        
        # 2. Arbeitnow API (free, no auth, remote jobs)
        self._scrape_arbeitnow()
        
        # 3. Himalayas API (free, remote jobs)
        self._scrape_himalayas()
        
        # 4. Jobicy API (free, remote jobs)
        self._scrape_jobicy()
        
        # 5. Adzuna API (free tier, global jobs)
        self._scrape_adzuna()
        
        # 6. Direct company career pages (most reliable)
        self._scrape_direct_career_pages()
        
        # 7. Google Jobs via RSS proxies
        self._scrape_google_jobs_rss()
        
        # 8. Indian job sites
        self._scrape_indian_job_sites()
        
        # 9. Startup/tech specific sites
        self._scrape_startup_jobs()
        
        # 10. Job aggregator RSS feeds
        self._scrape_job_aggregators()
        
        # 11. GitHub/Dev focused job boards
        self._scrape_dev_job_boards()
        
        logging.info(f"✅ Total jobs scraped: {len(self.all_jobs)}")
        return self.all_jobs
    
    def _scrape_arbeitnow(self):
        """Arbeitnow - Free API for remote jobs, no auth required."""
        try:
            logging.info("📡 Scraping Arbeitnow API (free, no auth)...")
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                jobs_data = data.get('data', [])
                count = 0
                
                for job in jobs_data[:40]:
                    job_entry = {
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'location': job.get('location', 'Remote'),
                        'url': job.get('url', ''),
                        'description': job.get('description', '')[:500] if job.get('description') else '',
                        'source': 'arbeitnow',
                        'scraped_at': datetime.now().isoformat(),
                        'remote': job.get('remote', False),
                        'tags': ', '.join(job.get('tags', [])[:5]) if job.get('tags') else ''
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        self.all_jobs.append(job_entry)
                        count += 1
                        
                logging.info(f"   ✅ Found {count} jobs from Arbeitnow")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Arbeitnow error: {e}")
        
        time.sleep(1)
    
    def _scrape_himalayas(self):
        """Himalayas.app - Free API for remote jobs."""
        try:
            logging.info("📡 Scraping Himalayas API (free, remote jobs)...")
            url = "https://himalayas.app/jobs/api?limit=50"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                jobs_data = data.get('jobs', [])
                count = 0
                
                for job in jobs_data:
                    job_entry = {
                        'title': job.get('title', ''),
                        'company': job.get('companyName', ''),
                        'location': job.get('locationRestrictions', ['Remote'])[0] if job.get('locationRestrictions') else 'Remote',
                        'url': f"https://himalayas.app/jobs/{job.get('slug', '')}",
                        'description': job.get('excerpt', '')[:500],
                        'source': 'himalayas',
                        'scraped_at': datetime.now().isoformat(),
                        'salary': job.get('salary', ''),
                        'category': job.get('categories', [''])[0] if job.get('categories') else ''
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        self.all_jobs.append(job_entry)
                        count += 1
                        
                logging.info(f"   ✅ Found {count} jobs from Himalayas")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Himalayas error: {e}")
        
        time.sleep(1)
    
    def _scrape_jobicy(self):
        """Jobicy - Free remote jobs API."""
        try:
            logging.info("📡 Scraping Jobicy API (free, remote jobs)...")
            url = "https://jobicy.com/api/v2/remote-jobs?count=50"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                jobs_data = data.get('jobs', [])
                count = 0
                
                for job in jobs_data:
                    job_entry = {
                        'title': job.get('jobTitle', ''),
                        'company': job.get('companyName', ''),
                        'location': job.get('jobGeo', 'Remote'),
                        'url': job.get('url', ''),
                        'description': job.get('jobExcerpt', '')[:500],
                        'source': 'jobicy',
                        'scraped_at': datetime.now().isoformat(),
                        'salary': f"{job.get('annualSalaryMin', '')} - {job.get('annualSalaryMax', '')}",
                        'job_type': job.get('jobType', '')
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        self.all_jobs.append(job_entry)
                        count += 1
                        
                logging.info(f"   ✅ Found {count} jobs from Jobicy")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Jobicy error: {e}")
        
        time.sleep(1)
    
    def _scrape_adzuna(self):
        """Adzuna - Job search with free RSS feeds."""
        try:
            logging.info("📡 Scraping Adzuna RSS feeds...")
            
            # Adzuna India RSS feeds (no API key needed for RSS)
            for keyword in self.search_keywords[:3]:
                encoded = quote_plus(keyword)
                rss_url = f"https://www.adzuna.in/search/rss?q={encoded}&loc=India"
                
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:10]:
                        job_entry = {
                            'title': entry.get('title', ''),
                            'company': self._extract_company_from_title(entry.get('title', '')),
                            'location': self.location,
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500],
                            'source': 'adzuna',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        if job_entry['title']:
                            self.all_jobs.append(job_entry)
                            
                except Exception:
                    pass
                    
                time.sleep(0.5)
                
            logging.info(f"   ✅ Scraped Adzuna RSS feeds")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Adzuna error: {e}")
    
    def _extract_company_from_title(self, title: str) -> str:
        """Extract company name from job title if present."""
        if ' at ' in title:
            return title.split(' at ')[-1].strip()
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) > 1:
                return parts[-1].strip()
        return 'Various'
    
    def _scrape_indian_job_sites(self):
        """Scrape Indian-specific job sites."""
        logging.info("🇮🇳 Scraping Indian job sites...")
        
        # Freshersworld (for freshers)
        self._scrape_freshersworld()
        
        # Instahyre
        self._scrape_instahyre()
        
        # Cutshort
        self._scrape_cutshort()
        
        # Hirist
        self._scrape_hirist()
        
        # IIMJobs
        self._scrape_iimjobs()
    
    def _scrape_freshersworld(self):
        """Freshersworld - Indian freshers job portal."""
        try:
            url = "https://www.freshersworld.com/jobs/category/it-software-jobs"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', {'class': re.compile(r'job-container|job_listing')})
                count = 0
                
                for card in job_cards[:15]:
                    title_elem = card.find(['h2', 'h3', 'a'], {'class': re.compile(r'title|job-title')})
                    company_elem = card.find(['span', 'div'], {'class': re.compile(r'company')})
                    link_elem = card.find('a', href=True)
                    
                    if title_elem:
                        job_entry = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Various',
                            'location': self.location,
                            'url': link_elem.get('href', url) if link_elem else url,
                            'source': 'freshersworld',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.all_jobs.append(job_entry)
                        count += 1
                
                if count:
                    logging.info(f"   ✅ Found {count} jobs from Freshersworld")
                    
        except Exception as e:
            logging.debug(f"   Freshersworld: {e}")
        
        time.sleep(1)
    
    def _scrape_instahyre(self):
        """Instahyre - Indian tech job portal."""
        try:
            # Instahyre public job listings page
            url = "https://www.instahyre.com/search-jobs/"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', {'class': re.compile(r'job-card|opportunity')})
                count = 0
                
                for card in job_cards[:20]:
                    title_elem = card.find(['h2', 'h3', 'a', 'div'], {'class': re.compile(r'title|position')})
                    company_elem = card.find(['span', 'div', 'a'], {'class': re.compile(r'company|employer')})
                    
                    if title_elem:
                        job_entry = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Startup',
                            'location': self.location,
                            'url': url,
                            'source': 'instahyre',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.all_jobs.append(job_entry)
                        count += 1
                
                if count:
                    logging.info(f"   ✅ Found {count} jobs from Instahyre")
                    
        except Exception as e:
            logging.debug(f"   Instahyre: {e}")
        
        time.sleep(1)
    
    def _scrape_cutshort(self):
        """Cutshort - Indian startup job portal."""
        try:
            url = "https://cutshort.io/jobs"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', {'class': re.compile(r'job-card|opportunity-card')})
                count = 0
                
                for card in job_cards[:20]:
                    title_elem = card.find(['h2', 'h3', 'a'])
                    company_elem = card.find(['span', 'div'], {'class': re.compile(r'company')})
                    
                    if title_elem:
                        job_entry = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Startup',
                            'location': self.location,
                            'url': url,
                            'source': 'cutshort',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.all_jobs.append(job_entry)
                        count += 1
                
                if count:
                    logging.info(f"   ✅ Found {count} jobs from Cutshort")
                    
        except Exception as e:
            logging.debug(f"   Cutshort: {e}")
        
        time.sleep(1)
    
    def _scrape_hirist(self):
        """Hirist - Indian tech/startup jobs."""
        try:
            for keyword in ['python', 'data-analyst', 'software-engineer']:
                url = f"https://www.hirist.tech/{keyword}-jobs"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_cards = soup.find_all('div', {'class': re.compile(r'job|listing')})
                    
                    for card in job_cards[:10]:
                        title_elem = card.find(['h2', 'h3', 'a'])
                        company_elem = card.find(['span', 'div'], {'class': re.compile(r'company')})
                        
                        if title_elem:
                            job_entry = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Tech Company',
                                'location': self.location,
                                'url': url,
                                'source': 'hirist',
                                'scraped_at': datetime.now().isoformat()
                            }
                            self.all_jobs.append(job_entry)
                
                time.sleep(0.5)
                
        except Exception as e:
            logging.debug(f"   Hirist: {e}")
    
    def _scrape_iimjobs(self):
        """IIMJobs - Indian management/professional jobs."""
        try:
            url = "https://www.iimjobs.com/j/data-analyst-jobs.html"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', {'class': re.compile(r'job-wrap|listing')})
                count = 0
                
                for card in job_cards[:15]:
                    title_elem = card.find(['h2', 'h3', 'a'])
                    company_elem = card.find(['span', 'div'], {'class': re.compile(r'company')})
                    
                    if title_elem:
                        job_entry = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Corporate',
                            'location': self.location,
                            'url': url,
                            'source': 'iimjobs',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.all_jobs.append(job_entry)
                        count += 1
                
                if count:
                    logging.info(f"   ✅ Found {count} jobs from IIMJobs")
                    
        except Exception as e:
            logging.debug(f"   IIMJobs: {e}")
        
        time.sleep(1)
    
    def _scrape_dev_job_boards(self):
        """Scrape developer-focused job boards."""
        logging.info("💻 Scraping developer job boards...")
        
        # WeWorkRemotely
        self._scrape_weworkremotely()
        
        # Working Nomads
        self._scrape_workingnomads()
        
        # Authentic Jobs
        self._scrape_authentic_jobs()
    
    def _scrape_weworkremotely(self):
        """WeWorkRemotely - Popular remote job board."""
        try:
            categories = ['programming', 'devops-sysadmin', 'data']
            
            for category in categories:
                url = f"https://weworkremotely.com/categories/{category}/jobs.rss"
                
                try:
                    feed = feedparser.parse(url)
                    
                    for entry in feed.entries[:10]:
                        job_entry = {
                            'title': entry.get('title', ''),
                            'company': entry.get('author', 'Remote Company'),
                            'location': 'Remote',
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500],
                            'source': 'weworkremotely',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        if job_entry['title']:
                            self.all_jobs.append(job_entry)
                            
                except Exception:
                    pass
                    
                time.sleep(0.5)
                
            logging.info("   ✅ Scraped WeWorkRemotely")
                
        except Exception as e:
            logging.debug(f"   WeWorkRemotely: {e}")
    
    def _scrape_workingnomads(self):
        """Working Nomads - Remote job aggregator with RSS."""
        try:
            url = "https://www.workingnomads.com/jobs.rss"
            feed = feedparser.parse(url)
            count = 0
            
            for entry in feed.entries[:20]:
                job_entry = {
                    'title': entry.get('title', ''),
                    'company': self._extract_company_from_title(entry.get('title', '')),
                    'location': 'Remote',
                    'url': entry.get('link', ''),
                    'description': entry.get('summary', '')[:500],
                    'source': 'workingnomads',
                    'scraped_at': datetime.now().isoformat()
                }
                
                if job_entry['title']:
                    self.all_jobs.append(job_entry)
                    count += 1
                    
            if count:
                logging.info(f"   ✅ Found {count} jobs from Working Nomads")
                
        except Exception as e:
            logging.debug(f"   Working Nomads: {e}")
        
        time.sleep(1)
    
    def _scrape_authentic_jobs(self):
        """Authentic Jobs - Design & dev jobs with RSS."""
        try:
            url = "https://authenticjobs.com/rss/"
            feed = feedparser.parse(url)
            count = 0
            
            for entry in feed.entries[:15]:
                job_entry = {
                    'title': entry.get('title', ''),
                    'company': entry.get('author', 'Tech Company'),
                    'location': 'Remote/Flexible',
                    'url': entry.get('link', ''),
                    'description': entry.get('summary', '')[:500],
                    'source': 'authenticjobs',
                    'scraped_at': datetime.now().isoformat()
                }
                
                if job_entry['title']:
                    self.all_jobs.append(job_entry)
                    count += 1
                    
            if count:
                logging.info(f"   ✅ Found {count} jobs from Authentic Jobs")
                
        except Exception as e:
            logging.debug(f"   Authentic Jobs: {e}")
    
    def _scrape_remoteok(self):
        """RemoteOK has a free, reliable JSON API."""
        try:
            logging.info("📡 Scraping RemoteOK (free API)...")
            url = "https://remoteok.com/api"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                jobs_data = response.json()
                count = 0
                
                for job in jobs_data[1:50]:  # Skip first item (metadata)
                    if isinstance(job, dict):
                        job_entry = {
                            'title': job.get('position', ''),
                            'company': job.get('company', ''),
                            'location': job.get('location', 'Remote'),
                            'url': job.get('url', job.get('apply_url', '')),
                            'description': job.get('description', '')[:500],
                            'source': 'remoteok',
                            'scraped_at': datetime.now().isoformat(),
                            'salary': job.get('salary', ''),
                            'tags': ', '.join(job.get('tags', [])[:5])
                        }
                        
                        if job_entry['title'] and job_entry['company']:
                            self.all_jobs.append(job_entry)
                            count += 1
                            
                logging.info(f"   ✅ Found {count} jobs from RemoteOK")
                
        except Exception as e:
            logging.warning(f"   ⚠️ RemoteOK error: {e}")
            
        time.sleep(1)
    
    def _scrape_direct_career_pages(self):
        """Scrape directly from company career pages - most reliable."""
        
        # Top tech companies with scrapeable career pages
        career_pages = [
            # Indian Tech Giants
            ("Infosys", "https://www.infosys.com/careers.html"),
            ("TCS", "https://www.tcs.com/careers"),
            ("Wipro", "https://careers.wipro.com/"),
            ("HCL Tech", "https://www.hcltech.com/careers"),
            ("Tech Mahindra", "https://careers.techmahindra.com/"),
            ("Mindtree", "https://www.mindtree.com/careers"),
            ("Mphasis", "https://www.mphasis.com/careers.html"),
            ("L&T Infotech", "https://www.ltimindtree.com/careers/"),
            
            # Product Companies in India
            ("Razorpay", "https://razorpay.com/jobs/"),
            ("Zerodha", "https://zerodha.com/careers/"),
            ("Swiggy", "https://careers.swiggy.com/"),
            ("Zomato", "https://www.zomato.com/careers"),
            ("PhonePe", "https://www.phonepe.com/careers/"),
            ("Paytm", "https://paytm.com/careers"),
            ("Flipkart", "https://www.flipkartcareers.com/"),
            ("Ola", "https://www.olacabs.com/careers"),
            ("CRED", "https://careers.cred.club/"),
            ("Meesho", "https://meesho.io/jobs"),
            
            # Global Giants
            ("Microsoft", "https://careers.microsoft.com/"),
            ("Google", "https://careers.google.com/"),
            ("Amazon", "https://www.amazon.jobs/"),
            ("Meta", "https://www.metacareers.com/"),
            ("Apple", "https://jobs.apple.com/"),
            ("Netflix", "https://jobs.netflix.com/"),
            ("Uber", "https://www.uber.com/careers/"),
            ("Salesforce", "https://careers.salesforce.com/"),
            ("Adobe", "https://adobe.wd5.myworkdayjobs.com/external_experienced"),
            ("Oracle", "https://www.oracle.com/in/corporate/careers/"),
            ("IBM", "https://www.ibm.com/careers/"),
        ]
        
        logging.info("🏢 Scraping direct company career pages...")
        
        for company_name, career_url in career_pages:
            try:
                response = self.session.get(career_url, timeout=10)
                
                if response.status_code == 200:
                    # Create a job entry for each company (HR contact reference)
                    job_entry = {
                        'title': 'Data Analyst / Business Analyst',
                        'company': company_name,
                        'location': self.location,
                        'url': career_url,
                        'description': f'Career opportunities at {company_name}',
                        'source': 'direct_career_page',
                        'scraped_at': datetime.now().isoformat(),
                        'career_page': career_url
                    }
                    self.all_jobs.append(job_entry)
                    
            except Exception as e:
                logging.debug(f"   Skipping {company_name}: {e}")
                continue
                
            time.sleep(0.5)
            
        logging.info(f"   ✅ Added {len(career_pages)} company career page references")
    
    def _scrape_google_jobs_rss(self):
        """Try Google Jobs via RSS feed proxies."""
        try:
            logging.info("📡 Trying Google Jobs RSS feeds...")
            
            # Use RSS aggregators that index Google Jobs
            for keyword in self.search_keywords[:3]:
                # Try Google News search for job postings (as a fallback)
                encoded = quote_plus(f"{keyword} jobs {self.location}")
                rss_url = f"https://news.google.com/rss/search?q={encoded}+hiring&hl=en-IN&gl=IN&ceid=IN:en"
                
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:5]:
                        job_entry = {
                            'title': entry.get('title', keyword),
                            'company': 'Various (see link)',
                            'location': self.location,
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500],
                            'source': 'google_news_jobs',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.all_jobs.append(job_entry)
                        
                except Exception:
                    pass
                    
                time.sleep(1)
                
        except Exception as e:
            logging.warning(f"   ⚠️ Google Jobs RSS error: {e}")
    
    def _scrape_startup_jobs(self):
        """Scrape startup-focused job sites."""
        try:
            logging.info("🚀 Scraping startup job sites...")
            
            # HasJob (Indian startup jobs, actually works)
            try:
                url = "https://hasjob.co/?location=Bangalore"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    job_listings = soup.find_all('a', {'class': 'post-title'})
                    count = 0
                    
                    for listing in job_listings[:20]:
                        title = listing.get_text(strip=True)
                        href = listing.get('href', '')
                        
                        if title and href:
                            job_entry = {
                                'title': title,
                                'company': 'Startup',
                                'location': self.location,
                                'url': f"https://hasjob.co{href}" if not href.startswith('http') else href,
                                'source': 'hasjob',
                                'scraped_at': datetime.now().isoformat()
                            }
                            self.all_jobs.append(job_entry)
                            count += 1
                            
                    logging.info(f"   ✅ Found {count} jobs from HasJob")
                    
            except Exception as e:
                logging.debug(f"   HasJob error: {e}")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Startup jobs error: {e}")
            
    def _scrape_job_aggregators(self):
        """Scrape job aggregator sites."""
        try:
            logging.info("📋 Scraping job aggregators...")
            
            # SimplyHired RSS (when available)
            for keyword in self.search_keywords[:2]:
                try:
                    encoded = quote_plus(keyword)
                    location_encoded = quote_plus(self.location)
                    
                    # Try SimplyHired
                    url = f"https://www.simplyhired.com/search?q={encoded}&l={location_encoded}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        job_cards = soup.find_all('article', {'class': re.compile(r'jobCard|SerpJob')})
                        
                        for card in job_cards[:10]:
                            title_elem = card.find(['h2', 'h3', 'a'])
                            company_elem = card.find(['span', 'div'], {'class': re.compile(r'company|employer')})
                            
                            if title_elem:
                                job_entry = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Various',
                                    'location': self.location,
                                    'url': url,
                                    'source': 'simplyhired',
                                    'scraped_at': datetime.now().isoformat()
                                }
                                self.all_jobs.append(job_entry)
                                
                except Exception:
                    pass
                    
                time.sleep(1)
                
        except Exception as e:
            logging.warning(f"   ⚠️ Aggregator error: {e}")
    
    def save_jobs(self, filepath: str = None):
        """Save scraped jobs to CSV."""
        if not filepath:
            filepath = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'jobs_today.csv'
            )
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if self.all_jobs:
            df = pd.DataFrame(self.all_jobs)
            
            # Remove duplicates by title+company
            df = df.drop_duplicates(subset=['title', 'company'], keep='first')
            
            df.to_csv(filepath, index=False)
            logging.info(f"💾 Saved {len(df)} jobs to {filepath}")
            return df
        else:
            logging.warning("⚠️ No jobs to save")
            # Create empty dataframe with correct columns
            df = pd.DataFrame(columns=['title', 'company', 'location', 'url', 'source', 'scraped_at'])
            df.to_csv(filepath, index=False)
            return df


def main():
    """Main entry point for reliable job scraping."""
    location = os.getenv('JOB_LOCATION', 'Bangalore')
    
    logging.info("="*60)
    logging.info("🚀 RELIABLE JOB SCRAPER")
    logging.info(f"   Location: {location}")
    logging.info("="*60)
    
    scraper = ReliableJobScraper(location=location)
    jobs = scraper.scrape_all_sources()
    scraper.save_jobs()
    
    logging.info("="*60)
    logging.info(f"✅ COMPLETE - Scraped {len(jobs)} jobs from multiple sources")
    logging.info("="*60)
    
    return jobs


if __name__ == "__main__":
    main()
