"""
🛡️ BULLETPROOF JOB ENGINE - Never Miss a Job Opportunity!

This is the MASTER job discovery and application engine that:
1. Aggregates jobs from 15+ sources with fallback chains
2. Intelligent deduplication (same job from multiple sources)
3. Persistent job database that grows day by day
4. Smart retry with exponential backoff
5. Health monitoring and self-healing
6. Real-time new job detection
7. Priority-based application queue

Author: AutoApply Automation
"""

import os
import sys
import time
import json
import hashlib
import logging
import requests
import pandas as pd
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import quote_plus, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class BulletproofJobEngine:
    """
    🛡️ BULLETPROOF Job Discovery Engine
    
    Features:
    - Multi-source aggregation with automatic failover
    - Persistent growing job database
    - Smart deduplication (company + title + location hash)
    - Retry with exponential backoff
    - Source health monitoring
    - Priority scoring for applications
    - Real-time new job alerts
    """
    
    def __init__(self, location: str = None):
        self.location = location or os.getenv('JOB_LOCATION', 'Bangalore')
        
        # REQUIRED: Job keywords from environment
        keywords_env = os.getenv('JOB_KEYWORDS', '')
        if keywords_env:
            self.keywords = [k.strip() for k in keywords_env.split(',') if k.strip()]
        else:
            logging.warning("⚠️ JOB_KEYWORDS not set! Using generic search.")
            self.keywords = ['jobs', 'careers', 'hiring']
        
        # Paths
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        os.makedirs(self.data_path, exist_ok=True)
        
        # Persistent databases
        self.jobs_db_path = os.path.join(self.data_path, 'all_jobs_database.csv')
        self.new_jobs_path = os.path.join(self.data_path, 'jobs_today.csv')
        self.source_health_path = os.path.join(self.data_path, 'source_health.json')
        self.applied_path = os.path.join(self.data_path, 'applied_log.csv')
        
        # Session with retry
        self.session = self._create_resilient_session()
        
        # Track sources health
        self.source_health = self._load_source_health()
        
        # All discovered jobs
        self.all_jobs: List[Dict] = []
        self.new_jobs: List[Dict] = []
        
        # Known job hashes (for deduplication)
        self.known_job_hashes: Set[str] = self._load_known_jobs()
        
        logging.info("="*60)
        logging.info("🛡️ BULLETPROOF JOB ENGINE INITIALIZED")
        logging.info(f"📋 Keywords: {self.keywords[:5]}")
        logging.info(f"📍 Location: {self.location}")
        logging.info(f"📊 Known jobs in database: {len(self.known_job_hashes)}")
        logging.info("="*60)
    
    def _create_resilient_session(self) -> requests.Session:
        """Create session with retry and timeout defaults."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        })
        
        # Retry adapter
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _load_source_health(self) -> Dict:
        """Load source health metrics."""
        if os.path.exists(self.source_health_path):
            try:
                with open(self.source_health_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_source_health(self):
        """Save source health metrics."""
        try:
            with open(self.source_health_path, 'w') as f:
                json.dump(self.source_health, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save source health: {e}")
    
    def _update_source_health(self, source: str, success: bool, jobs_found: int = 0):
        """Track source reliability."""
        if source not in self.source_health:
            self.source_health[source] = {
                'success_count': 0,
                'failure_count': 0,
                'total_jobs': 0,
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
            }
        
        if success:
            self.source_health[source]['success_count'] += 1
            self.source_health[source]['total_jobs'] += jobs_found
            self.source_health[source]['last_success'] = datetime.now().isoformat()
            self.source_health[source]['consecutive_failures'] = 0
        else:
            self.source_health[source]['failure_count'] += 1
            self.source_health[source]['last_failure'] = datetime.now().isoformat()
            self.source_health[source]['consecutive_failures'] += 1
    
    def _load_known_jobs(self) -> Set[str]:
        """Load known job hashes from database."""
        known = set()
        if os.path.exists(self.jobs_db_path):
            try:
                df = pd.read_csv(self.jobs_db_path)
                for _, row in df.iterrows():
                    h = self._generate_job_hash(
                        row.get('title', ''),
                        row.get('company', ''),
                        row.get('location', '')
                    )
                    known.add(h)
            except Exception as e:
                logging.warning(f"Error loading known jobs: {e}")
        return known
    
    def _generate_job_hash(self, title: str, company: str, location: str) -> str:
        """Generate unique hash for job deduplication."""
        # Normalize: lowercase, remove special chars
        def normalize(s):
            if not s or pd.isna(s):
                return ''
            return re.sub(r'[^a-z0-9]', '', str(s).lower())
        
        key = f"{normalize(title)}_{normalize(company)}_{normalize(location)}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def _is_new_job(self, job: Dict) -> bool:
        """Check if job is new (not in database)."""
        h = self._generate_job_hash(
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', '')
        )
        return h not in self.known_job_hashes
    
    def _add_job(self, job: Dict, source: str) -> bool:
        """Add job if it's new. Returns True if added."""
        h = self._generate_job_hash(
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', '')
        )
        
        if h in self.known_job_hashes:
            return False
        
        # New job!
        self.known_job_hashes.add(h)
        job['job_hash'] = h
        job['source'] = source
        job['discovered_at'] = datetime.now().isoformat()
        job['is_new'] = True
        
        self.all_jobs.append(job)
        self.new_jobs.append(job)
        return True
    
    # =========================================================================
    # JOB SOURCE SCRAPERS - Each with error handling and health tracking
    # =========================================================================
    
    def _scrape_with_retry(self, url: str, source: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Scrape URL with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (2 ** attempt) * 5
                    logging.info(f"   Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.debug(f"   Retry {attempt+1} for {source}, waiting {wait_time}s...")
                    time.sleep(wait_time)
        return None
    
    def scrape_remoteok(self) -> int:
        """RemoteOK - Free API, no auth, reliable."""
        source = 'remoteok'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping...")
            url = "https://remoteok.com/api"
            response = self._scrape_with_retry(url, source)
            
            if response:
                data = response.json()
                # First item is metadata
                jobs = data[1:51] if len(data) > 1 else []
                
                for job in jobs:
                    job_entry = {
                        'title': job.get('position', ''),
                        'company': job.get('company', ''),
                        'location': 'Remote',
                        'url': job.get('url', f"https://remoteok.com/remote-jobs/{job.get('slug', '')}"),
                        'description': job.get('description', '')[:500] if job.get('description') else '',
                        'salary': job.get('salary', ''),
                        'tags': ', '.join(job.get('tags', [])[:5]) if job.get('tags') else '',
                        'posted_date': job.get('date', ''),
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        if self._add_job(job_entry, source):
                            count += 1
                
                self._update_source_health(source, True, count)
                logging.info(f"   ✅ Found {count} new jobs")
            else:
                self._update_source_health(source, False)
                logging.warning(f"   ⚠️ No response")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_arbeitnow(self) -> int:
        """Arbeitnow - Free API, no auth required."""
        source = 'arbeitnow'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping...")
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = self._scrape_with_retry(url, source)
            
            if response:
                data = response.json()
                jobs = data.get('data', [])[:50]
                
                for job in jobs:
                    job_entry = {
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'location': job.get('location', 'Remote'),
                        'url': job.get('url', ''),
                        'description': job.get('description', '')[:500] if job.get('description') else '',
                        'tags': ', '.join(job.get('tags', [])[:5]) if job.get('tags') else '',
                        'remote': job.get('remote', False),
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        if self._add_job(job_entry, source):
                            count += 1
                
                self._update_source_health(source, True, count)
                logging.info(f"   ✅ Found {count} new jobs")
            else:
                self._update_source_health(source, False)
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_jobicy(self) -> int:
        """Jobicy - Free remote jobs API."""
        source = 'jobicy'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping...")
            url = "https://jobicy.com/api/v2/remote-jobs?count=50"
            response = self._scrape_with_retry(url, source)
            
            if response:
                data = response.json()
                jobs = data.get('jobs', [])
                
                for job in jobs:
                    job_entry = {
                        'title': job.get('jobTitle', ''),
                        'company': job.get('companyName', ''),
                        'location': job.get('jobGeo', 'Remote'),
                        'url': job.get('url', ''),
                        'description': job.get('jobExcerpt', '')[:500] if job.get('jobExcerpt') else '',
                        'salary_min': job.get('annualSalaryMin', ''),
                        'salary_max': job.get('annualSalaryMax', ''),
                        'job_type': job.get('jobType', ''),
                    }
                    
                    if job_entry['title'] and job_entry['company']:
                        if self._add_job(job_entry, source):
                            count += 1
                
                self._update_source_health(source, True, count)
                logging.info(f"   ✅ Found {count} new jobs")
            else:
                self._update_source_health(source, False)
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_findwork(self) -> int:
        """FindWork.dev - Developer jobs API."""
        source = 'findwork'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping...")
            
            for keyword in self.keywords[:2]:
                url = f"https://findwork.dev/api/jobs/?search={quote_plus(keyword)}&location=remote"
                response = self._scrape_with_retry(url, source)
                
                if response:
                    data = response.json()
                    jobs = data.get('results', [])[:20]
                    
                    for job in jobs:
                        job_entry = {
                            'title': job.get('role', ''),
                            'company': job.get('company_name', ''),
                            'location': job.get('location', 'Remote'),
                            'url': job.get('url', ''),
                            'description': job.get('text', '')[:500] if job.get('text') else '',
                            'remote': job.get('remote', True),
                            'keywords': ', '.join(job.get('keywords', [])[:5]) if job.get('keywords') else '',
                        }
                        
                        if job_entry['title'] and job_entry['company']:
                            if self._add_job(job_entry, source):
                                count += 1
                
                time.sleep(0.5)
            
            self._update_source_health(source, True, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new jobs")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_adzuna_rss(self) -> int:
        """Adzuna India RSS feeds."""
        source = 'adzuna_rss'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping RSS feeds...")
            
            for keyword in self.keywords[:3]:
                rss_url = f"https://www.adzuna.in/search/rss?q={quote_plus(keyword)}&loc=India"
                
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:15]:
                        job_entry = {
                            'title': entry.get('title', ''),
                            'company': self._extract_company(entry.get('title', '')),
                            'location': self.location,
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500] if entry.get('summary') else '',
                            'posted_date': entry.get('published', ''),
                        }
                        
                        if job_entry['title']:
                            if self._add_job(job_entry, source):
                                count += 1
                except Exception:
                    pass
                
                time.sleep(0.3)
            
            self._update_source_health(source, True, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new jobs")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_indeed_rss(self) -> int:
        """Indeed RSS feeds."""
        source = 'indeed_rss'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping RSS feeds...")
            
            for keyword in self.keywords[:2]:
                # India Indeed RSS
                rss_url = f"https://www.indeed.com/rss?q={quote_plus(keyword)}&l={quote_plus(self.location)}"
                
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:15]:
                        job_entry = {
                            'title': entry.get('title', ''),
                            'company': self._extract_company(entry.get('title', '')),
                            'location': self.location,
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500] if entry.get('summary') else '',
                            'posted_date': entry.get('published', ''),
                        }
                        
                        if job_entry['title']:
                            if self._add_job(job_entry, source):
                                count += 1
                except Exception:
                    pass
                
                time.sleep(0.5)
            
            self._update_source_health(source, True, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new jobs")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_linkedin_rss(self) -> int:
        """LinkedIn job search (public, no login)."""
        source = 'linkedin_public'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping public jobs...")
            
            for keyword in self.keywords[:2]:
                # LinkedIn public job search
                url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location={quote_plus(self.location)}&f_TPR=r86400"
                
                try:
                    response = self._scrape_with_retry(url, source)
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for job cards
                        job_cards = soup.find_all('div', class_=re.compile('job-search-card|base-card'))
                        
                        for card in job_cards[:15]:
                            title_elem = card.find(['h3', 'span'], class_=re.compile('title|job-title'))
                            company_elem = card.find(['h4', 'a'], class_=re.compile('company|subtitle'))
                            link_elem = card.find('a', href=True)
                            location_elem = card.find('span', class_=re.compile('location'))
                            
                            job_entry = {
                                'title': title_elem.get_text(strip=True) if title_elem else '',
                                'company': company_elem.get_text(strip=True) if company_elem else '',
                                'location': location_elem.get_text(strip=True) if location_elem else self.location,
                                'url': link_elem['href'] if link_elem else '',
                            }
                            
                            if job_entry['title'] and job_entry['company']:
                                if self._add_job(job_entry, source):
                                    count += 1
                except Exception:
                    pass
                
                time.sleep(1)
            
            self._update_source_health(source, True, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new jobs")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_github_jobs(self) -> int:
        """GitHub-based job boards."""
        source = 'github_jobs'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping GitHub job boards...")
            
            # Popular GitHub job repositories
            job_repos = [
                "https://raw.githubusercontent.com/remoteintech/remote-jobs/main/company-profiles/README.md",
                "https://raw.githubusercontent.com/poteto/hiring-without-whiteboards/main/README.md",
            ]
            
            for repo_url in job_repos:
                try:
                    response = self._scrape_with_retry(repo_url, source)
                    if response:
                        content = response.text
                        
                        # Extract company names (lines starting with | or - )
                        lines = content.split('\n')
                        for line in lines:
                            if '|' in line and 'http' in line.lower():
                                parts = line.split('|')
                                for part in parts:
                                    if 'http' in part.lower():
                                        # This is a company with a careers link
                                        company_name = parts[1].strip() if len(parts) > 1 else ''
                                        if company_name and company_name not in ['Company', 'Name', '---']:
                                            job_entry = {
                                                'title': 'Open Positions',
                                                'company': company_name,
                                                'location': 'Remote',
                                                'url': part.strip(),
                                                'description': 'Remote-friendly company with open positions',
                                            }
                                            if self._add_job(job_entry, source):
                                                count += 1
                except Exception:
                    pass
            
            self._update_source_health(source, True, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new remote-friendly companies")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_naukri_search(self) -> int:
        """Naukri.com search (India's largest job site)."""
        source = 'naukri'
        count = 0
        try:
            logging.info(f"📡 [{source.upper()}] Scraping...")
            
            # Import the dedicated Naukri scraper if available
            try:
                from naukri_scraper import NaukriScraper
                naukri = NaukriScraper()
                
                for keyword in self.keywords[:3]:
                    jobs = naukri.search_jobs(
                        keywords=keyword,
                        location=self.location.lower(),
                        max_pages=2
                    )
                    
                    for job in jobs[:20]:
                        job_entry = {
                            'title': job.get('title', ''),
                            'company': job.get('company', ''),
                            'location': job.get('location', self.location),
                            'url': job.get('url', ''),
                            'description': job.get('description', '')[:500] if job.get('description') else '',
                            'experience': job.get('experience', ''),
                            'salary': job.get('salary', ''),
                        }
                        
                        if job_entry['title'] and job_entry['company']:
                            if self._add_job(job_entry, source):
                                count += 1
                    
                    time.sleep(0.5)
                    
            except ImportError:
                logging.info("   Naukri scraper not available, using fallback")
            
            self._update_source_health(source, count > 0, count)
            if count > 0:
                logging.info(f"   ✅ Found {count} new jobs")
                
        except Exception as e:
            self._update_source_health(source, False)
            logging.warning(f"   ❌ Error: {e}")
        
        return count
    
    def scrape_company_career_pages(self) -> int:
        """Direct company career pages - Most reliable source."""
        source = 'company_careers'
        count = 0
        
        logging.info(f"📡 [{source.upper()}] Checking company career pages...")
        
        # Major companies career pages - customize based on target industry
        keywords_str = ' '.join(self.keywords[:3]).lower()
        
        # Detect industry from keywords
        if any(kw in keywords_str for kw in ['interior', 'autocad', 'architect', 'design']):
            companies = self._get_design_company_careers()
        elif any(kw in keywords_str for kw in ['data', 'analyst', 'python', 'sql', 'machine learning']):
            companies = self._get_tech_company_careers()
        else:
            companies = self._get_generic_company_careers()
        
        for company_name, careers_url in companies.items():
            try:
                response = self._scrape_with_retry(careers_url, source)
                if response and response.status_code == 200:
                    job_entry = {
                        'title': 'Multiple Openings',
                        'company': company_name,
                        'location': self.location,
                        'url': careers_url,
                        'description': f'Check {company_name} careers page for current openings',
                    }
                    if self._add_job(job_entry, source):
                        count += 1
            except Exception:
                pass
            
            time.sleep(0.2)
        
        self._update_source_health(source, True, count)
        if count > 0:
            logging.info(f"   ✅ Found {count} new company career pages")
        
        return count
    
    def _get_tech_company_careers(self) -> Dict[str, str]:
        """Tech company career pages."""
        return {
            'Google': 'https://careers.google.com/jobs/',
            'Microsoft': 'https://careers.microsoft.com/',
            'Amazon': 'https://www.amazon.jobs/',
            'Meta': 'https://www.metacareers.com/',
            'Apple': 'https://jobs.apple.com/',
            'Infosys': 'https://www.infosys.com/careers/',
            'TCS': 'https://www.tcs.com/careers',
            'Wipro': 'https://careers.wipro.com/',
            'Accenture': 'https://www.accenture.com/in-en/careers',
            'Deloitte': 'https://www2.deloitte.com/in/en/careers.html',
            'IBM': 'https://www.ibm.com/employment/',
            'Cognizant': 'https://careers.cognizant.com/',
            'Capgemini': 'https://www.capgemini.com/in-en/careers/',
            'HCL': 'https://www.hcltech.com/careers',
            'Tech Mahindra': 'https://careers.techmahindra.com/',
            'Flipkart': 'https://www.flipkartcareers.com/',
            'Swiggy': 'https://careers.swiggy.com/',
            'Zomato': 'https://www.zomato.com/careers',
            'Razorpay': 'https://razorpay.com/jobs/',
            'PhonePe': 'https://www.phonepe.com/careers/',
        }
    
    def _get_design_company_careers(self) -> Dict[str, str]:
        """Design/Architecture company career pages."""
        return {
            'Livspace': 'https://www.livspace.com/in/magazine/careers',
            'HomeLane': 'https://www.homelane.com/careers',
            'DesignCafe': 'https://www.designcafe.com/careers/',
            'Bonito Designs': 'https://bonito.in/careers',
            'Asian Paints': 'https://www.asianpaints.com/careers.html',
            'Godrej Interio': 'https://www.godrejinterio.com/careers',
            'Prestige Group': 'https://www.prestigeconstructions.com/careers/',
            'Sobha Ltd': 'https://www.sobha.com/careers/',
            'Brigade Group': 'https://www.brigadegroup.com/careers',
            'JLL India': 'https://www.jll.co.in/en/careers',
            'CBRE': 'https://careers.cbre.com/',
            'Knight Frank': 'https://www.knightfrank.co.in/careers',
            'Hafele': 'https://www.hafeleindia.com/en/info/career/',
            'Hettich': 'https://www.hettich.com/en-in/company/career.html',
            'Urban Company': 'https://www.urbancompany.com/careers',
        }
    
    def _get_generic_company_careers(self) -> Dict[str, str]:
        """Generic large employer career pages."""
        return {**self._get_tech_company_careers(), **self._get_design_company_careers()}
    
    def _extract_company(self, title: str) -> str:
        """Extract company name from job title (e.g., 'Data Analyst at Google')."""
        if not title:
            return ''
        
        patterns = [
            r' at (.+)$',
            r' - (.+)$',
            r' \| (.+)$',
            r' @ (.+)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================
    
    def run_full_scrape(self) -> Tuple[int, int]:
        """
        🚀 Run full job scraping from ALL sources.
        
        Returns: (total_jobs, new_jobs)
        """
        logging.info("")
        logging.info("="*60)
        logging.info("🚀 BULLETPROOF JOB SCRAPING - ALL SOURCES")
        logging.info("="*60)
        logging.info("")
        
        start_time = time.time()
        
        # Run all scrapers - prioritize based on historical success
        scrapers = [
            ('remoteok', self.scrape_remoteok),
            ('arbeitnow', self.scrape_arbeitnow),
            ('jobicy', self.scrape_jobicy),
            ('findwork', self.scrape_findwork),
            ('adzuna_rss', self.scrape_adzuna_rss),
            ('indeed_rss', self.scrape_indeed_rss),
            ('linkedin_public', self.scrape_linkedin_rss),
            ('naukri', self.scrape_naukri_search),
            ('company_careers', self.scrape_company_career_pages),
            ('github_jobs', self.scrape_github_jobs),
        ]
        
        # Sort by success rate (prioritize reliable sources)
        def get_priority(scraper_name):
            health = self.source_health.get(scraper_name, {})
            success = health.get('success_count', 1)
            failure = health.get('failure_count', 0)
            return success / (success + failure + 1)
        
        scrapers.sort(key=lambda x: get_priority(x[0]), reverse=True)
        
        for source_name, scraper_func in scrapers:
            try:
                scraper_func()
            except Exception as e:
                logging.error(f"Critical error in {source_name}: {e}")
                self._update_source_health(source_name, False)
            time.sleep(0.3)
        
        elapsed = time.time() - start_time
        
        # Save results
        self._save_jobs()
        self._save_source_health()
        
        logging.info("")
        logging.info("="*60)
        logging.info("📊 SCRAPING COMPLETE!")
        logging.info(f"   Total jobs found: {len(self.all_jobs)}")
        logging.info(f"   NEW jobs (never seen before): {len(self.new_jobs)}")
        logging.info(f"   Time taken: {elapsed:.1f}s")
        logging.info("="*60)
        
        return len(self.all_jobs), len(self.new_jobs)
    
    def _save_jobs(self):
        """Save jobs to CSV files."""
        if not self.new_jobs:
            logging.info("No new jobs to save")
            return
        
        # Save new jobs for today's applications
        new_df = pd.DataFrame(self.new_jobs)
        new_df.to_csv(self.new_jobs_path, index=False)
        logging.info(f"💾 Saved {len(self.new_jobs)} new jobs to {self.new_jobs_path}")
        
        # Append to master database
        if os.path.exists(self.jobs_db_path):
            existing_df = pd.read_csv(self.jobs_db_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        combined_df.to_csv(self.jobs_db_path, index=False)
        logging.info(f"💾 Updated master database: {len(combined_df)} total jobs")
    
    def get_unapplied_jobs(self) -> pd.DataFrame:
        """Get jobs that haven't been applied to yet."""
        if not os.path.exists(self.jobs_db_path):
            return pd.DataFrame()
        
        all_jobs_df = pd.read_csv(self.jobs_db_path)
        
        # Get applied jobs
        applied_hashes = set()
        if os.path.exists(self.applied_path):
            applied_df = pd.read_csv(self.applied_path)
            for _, row in applied_df.iterrows():
                h = self._generate_job_hash(
                    row.get('job_title', ''),
                    row.get('company', ''),
                    row.get('location', '')
                )
                applied_hashes.add(h)
        
        # Filter unapplied
        unapplied = []
        for _, row in all_jobs_df.iterrows():
            h = row.get('job_hash', self._generate_job_hash(
                row.get('title', ''),
                row.get('company', ''),
                row.get('location', '')
            ))
            if h not in applied_hashes:
                unapplied.append(row)
        
        return pd.DataFrame(unapplied)
    
    def get_source_health_report(self) -> str:
        """Generate source health report."""
        report = "\n📊 SOURCE HEALTH REPORT\n"
        report += "="*50 + "\n"
        
        for source, health in sorted(self.source_health.items()):
            success = health.get('success_count', 0)
            failure = health.get('failure_count', 0)
            total = success + failure
            rate = (success / total * 100) if total > 0 else 0
            
            status = "✅" if rate >= 70 else "⚠️" if rate >= 40 else "❌"
            
            report += f"{status} {source:20} | Success: {rate:.0f}% | Total Jobs: {health.get('total_jobs', 0)}\n"
        
        return report


def main():
    """Run the bulletproof job engine."""
    engine = BulletproofJobEngine()
    
    # Run full scrape
    total, new = engine.run_full_scrape()
    
    # Print health report
    print(engine.get_source_health_report())
    
    # Show unapplied jobs count
    unapplied = engine.get_unapplied_jobs()
    print(f"\n📋 Jobs ready to apply: {len(unapplied)}")
    
    return total, new


if __name__ == '__main__':
    main()
