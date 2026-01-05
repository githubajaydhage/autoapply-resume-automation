"""
Fresh Job Hunter - Monitors and prioritizes LATEST job openings
Focuses on jobs posted within last 24-48 hours for maximum response rate

Key Features:
1. Real-time job scraping from multiple sources
2. Date-based prioritization (newest first)
3. Hiring manager email discovery
4. Urgent application flagging
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import pandas as pd
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class FreshJobHunter:
    """
    Hunts for the FRESHEST job openings and prioritizes them.
    
    Priority Tiers:
    - HOT (posted today): Apply immediately
    - FRESH (1-3 days): Apply within hours
    - RECENT (4-7 days): Apply same day
    - OLDER (7+ days): Lower priority
    """
    
    # Job freshness tiers (in hours)
    FRESHNESS_TIERS = {
        'hot': 24,        # Posted within 24 hours
        'fresh': 72,      # Posted within 3 days
        'recent': 168,    # Posted within 7 days
        'older': 999999   # Everything else
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.fresh_jobs = []
        
        # Get job keywords from environment
        keywords_env = os.getenv('JOB_KEYWORDS', 'data analyst, sql developer, business analyst')
        self.keywords = [k.strip() for k in keywords_env.split(',') if k.strip()]
        logging.info(f"🎯 Hunting fresh jobs for: {self.keywords}")
        
    def hunt_fresh_jobs(self) -> pd.DataFrame:
        """Hunt for fresh jobs from all real-time sources."""
        logging.info("="*60)
        logging.info("🔥 FRESH JOB HUNTER - Finding Latest Openings")
        logging.info("="*60)
        
        # 1. LinkedIn Jobs (via RSS/scraping)
        self._hunt_linkedin_fresh()
        
        # 2. Naukri Fresh Jobs (posted today)
        self._hunt_naukri_fresh()
        
        # 3. Indeed Fresh Jobs (last 24 hours)
        self._hunt_indeed_fresh()
        
        # 4. Glassdoor New Listings
        self._hunt_glassdoor_fresh()
        
        # 5. Google Jobs API
        self._hunt_google_jobs()
        
        # 6. AngelList/Wellfound Startups
        self._hunt_startup_fresh()
        
        # 7. Company Career Pages (hot companies)
        self._hunt_hot_companies()
        
        # 8. Remote Job Boards (updated hourly)
        self._hunt_remote_fresh()
        
        # 9. Indian Startup Job Boards
        self._hunt_indian_startups()
        
        # Create DataFrame and prioritize by freshness
        df = pd.DataFrame(self.fresh_jobs)
        
        if not df.empty:
            df = self._calculate_freshness_score(df)
            df = df.sort_values('freshness_score', ascending=False)
            
            # Log summary
            hot_count = len(df[df['freshness_tier'] == 'hot'])
            fresh_count = len(df[df['freshness_tier'] == 'fresh'])
            logging.info(f"\n🔥 FRESHNESS SUMMARY:")
            logging.info(f"   🔴 HOT (today): {hot_count} jobs - APPLY NOW!")
            logging.info(f"   🟠 FRESH (1-3 days): {fresh_count} jobs")
            logging.info(f"   📊 Total fresh jobs: {len(df)}")
        
        return df
    
    def _calculate_freshness_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate freshness score for prioritization."""
        now = datetime.now()
        
        def get_freshness(row):
            posted_date = row.get('date_posted', '')
            hours_ago = self._parse_posted_date(posted_date)
            
            # Determine tier
            if hours_ago <= self.FRESHNESS_TIERS['hot']:
                tier = 'hot'
                score = 100
            elif hours_ago <= self.FRESHNESS_TIERS['fresh']:
                tier = 'fresh'
                score = 80
            elif hours_ago <= self.FRESHNESS_TIERS['recent']:
                tier = 'recent'
                score = 60
            else:
                tier = 'older'
                score = 40
            
            return pd.Series({'freshness_tier': tier, 'freshness_score': score, 'hours_ago': hours_ago})
        
        freshness_data = df.apply(get_freshness, axis=1)
        df = pd.concat([df, freshness_data], axis=1)
        
        return df
    
    def _parse_posted_date(self, date_str: str) -> int:
        """Parse date string and return hours ago."""
        if not date_str:
            return 999  # Unknown = assume older
        
        date_str = str(date_str).lower()
        
        # Common patterns
        if 'just now' in date_str or 'just posted' in date_str:
            return 0
        if 'hour' in date_str:
            match = re.search(r'(\d+)\s*hour', date_str)
            return int(match.group(1)) if match else 1
        if 'today' in date_str or '0 day' in date_str:
            return 12
        if 'yesterday' in date_str or '1 day' in date_str:
            return 36
        if 'day' in date_str:
            match = re.search(r'(\d+)\s*day', date_str)
            days = int(match.group(1)) if match else 7
            return days * 24
        if 'week' in date_str:
            match = re.search(r'(\d+)\s*week', date_str)
            weeks = int(match.group(1)) if match else 1
            return weeks * 168
        if 'month' in date_str:
            return 720  # ~30 days
        
        # Try parsing as date
        try:
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%B %d, %Y', '%d %B %Y']:
                try:
                    posted = datetime.strptime(date_str, fmt)
                    hours = (datetime.now() - posted).total_seconds() / 3600
                    return int(hours)
                except:
                    continue
        except:
            pass
        
        return 168  # Default to 1 week if can't parse
    
    def _hunt_linkedin_fresh(self):
        """Hunt LinkedIn for jobs posted today."""
        logging.info("📡 Hunting LinkedIn fresh jobs...")
        try:
            for keyword in self.keywords[:2]:  # Top 2 keywords
                # LinkedIn jobs RSS/API (public listings)
                encoded = quote_plus(keyword)
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded}&location=India&f_TPR=r86400&start=0"
                
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for card in soup.select('.job-search-card')[:10]:
                        title = card.select_one('.base-search-card__title')
                        company = card.select_one('.base-search-card__subtitle')
                        link = card.select_one('a.base-card__full-link')
                        time_posted = card.select_one('time')
                        
                        if title and company:
                            self.fresh_jobs.append({
                                'title': title.get_text(strip=True),
                                'company': company.get_text(strip=True),
                                'url': link.get('href', '') if link else '',
                                'date_posted': time_posted.get('datetime', 'today') if time_posted else 'today',
                                'source': 'linkedin_fresh',
                                'priority': 'high'
                            })
                    logging.info(f"   Found {len(soup.select('.job-search-card'))} fresh LinkedIn jobs for '{keyword}'")
        except Exception as e:
            logging.debug(f"   LinkedIn: {e}")
    
    def _hunt_naukri_fresh(self):
        """Hunt Naukri for jobs posted today (freshness=1)."""
        logging.info("📡 Hunting Naukri fresh jobs (today)...")
        try:
            for keyword in self.keywords[:2]:
                encoded = keyword.replace(' ', '-')
                # freshness=1 means posted today
                url = f"https://www.naukri.com/{encoded}-jobs?freshness=1"
                
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for card in soup.select('.srp-jobtuple-wrapper, .jobTuple')[:15]:
                        title_elem = card.select_one('.title, .desig')
                        company_elem = card.select_one('.comp-name, .companyInfo a')
                        
                        if title_elem:
                            self.fresh_jobs.append({
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': card.get('href', '') or (title_elem.get('href', '') if title_elem else ''),
                                'date_posted': 'today',
                                'source': 'naukri_fresh',
                                'priority': 'high'
                            })
                    logging.info(f"   Found Naukri jobs posted today for '{keyword}'")
        except Exception as e:
            logging.debug(f"   Naukri: {e}")
    
    def _hunt_indeed_fresh(self):
        """Hunt Indeed for jobs posted in last 24 hours."""
        logging.info("📡 Hunting Indeed fresh jobs (last 24h)...")
        try:
            for keyword in self.keywords[:2]:
                encoded = quote_plus(keyword)
                # fromage=1 means last 24 hours
                url = f"https://in.indeed.com/jobs?q={encoded}&l=India&fromage=1"
                
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for card in soup.select('.job_seen_beacon, .resultContent')[:10]:
                        title_elem = card.select_one('.jobTitle span, h2 a')
                        company_elem = card.select_one('.companyName, .company')
                        
                        if title_elem:
                            self.fresh_jobs.append({
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': '',
                                'date_posted': 'today',
                                'source': 'indeed_fresh',
                                'priority': 'high'
                            })
                    logging.info(f"   Found Indeed jobs from last 24 hours for '{keyword}'")
        except Exception as e:
            logging.debug(f"   Indeed: {e}")
    
    def _hunt_glassdoor_fresh(self):
        """Hunt Glassdoor for new listings."""
        logging.info("📡 Hunting Glassdoor fresh jobs...")
        # Glassdoor requires authentication, skip for now
        pass
    
    def _hunt_google_jobs(self):
        """Hunt Google Jobs for fresh listings."""
        logging.info("📡 Hunting Google Jobs...")
        try:
            for keyword in self.keywords[:2]:
                encoded = quote_plus(f"{keyword} India")
                url = f"https://www.google.com/search?q={encoded}+jobs&ibp=htl;jobs"
                
                resp = self.session.get(url, timeout=10)
                # Google Jobs requires JS rendering, but we can get some metadata
                if resp.status_code == 200 and 'job' in resp.text.lower():
                    logging.info(f"   Google Jobs available for '{keyword}'")
        except Exception as e:
            logging.debug(f"   Google Jobs: {e}")
    
    def _hunt_startup_fresh(self):
        """Hunt AngelList/Wellfound for fresh startup jobs."""
        logging.info("📡 Hunting startup job boards...")
        try:
            # Wellfound API
            url = "https://wellfound.com/role/data-analyst"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for card in soup.select('[data-test="StartupResult"]')[:10]:
                    name = card.select_one('.styles_component__DzUj0')
                    if name:
                        self.fresh_jobs.append({
                            'title': 'Data Analyst',
                            'company': name.get_text(strip=True),
                            'url': '',
                            'date_posted': 'recent',
                            'source': 'wellfound',
                            'priority': 'medium'
                        })
                logging.info(f"   Found startup jobs on Wellfound")
        except Exception as e:
            logging.debug(f"   Wellfound: {e}")
    
    def _hunt_hot_companies(self):
        """Hunt career pages of actively hiring companies."""
        logging.info("📡 Checking hot company career pages...")
        
        # Companies known to post frequently
        hot_companies = [
            ('Razorpay', 'https://razorpay.com/careers/'),
            ('Swiggy', 'https://careers.swiggy.com/'),
            ('Zomato', 'https://www.zomato.com/careers'),
            ('PhonePe', 'https://www.phonepe.com/careers/'),
            ('Flipkart', 'https://www.flipkartcareers.com/'),
            ('Paytm', 'https://paytm.com/careers/'),
            ('CRED', 'https://cred.club/careers'),
            ('Groww', 'https://groww.in/careers'),
            ('Zerodha', 'https://zerodha.com/careers/'),
            ('Meesho', 'https://www.meesho.com/careers'),
        ]
        
        for company, url in hot_companies[:5]:
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    # Check if any of our keywords are mentioned
                    page_text = resp.text.lower()
                    for keyword in self.keywords:
                        if keyword.lower() in page_text:
                            self.fresh_jobs.append({
                                'title': f'{keyword.title()} Openings',
                                'company': company,
                                'url': url,
                                'date_posted': 'recent',
                                'source': 'career_page',
                                'priority': 'medium'
                            })
                            break
            except:
                pass
    
    def _hunt_remote_fresh(self):
        """Hunt remote job boards that update hourly."""
        logging.info("📡 Hunting remote job boards...")
        try:
            # RemoteOK - updates frequently
            resp = self.session.get('https://remoteok.com/api', timeout=10)
            if resp.status_code == 200:
                jobs = resp.json()
                for job in jobs[1:15]:  # Skip first (legal notice)
                    if isinstance(job, dict):
                        title = job.get('position', '')
                        # Check if relevant
                        if any(kw.lower() in title.lower() for kw in self.keywords):
                            self.fresh_jobs.append({
                                'title': title,
                                'company': job.get('company', 'Remote Company'),
                                'url': job.get('url', ''),
                                'date_posted': job.get('date', 'recent'),
                                'source': 'remoteok',
                                'priority': 'medium'
                            })
                logging.info(f"   Found jobs on RemoteOK")
        except Exception as e:
            logging.debug(f"   RemoteOK: {e}")
    
    def _hunt_indian_startups(self):
        """Hunt Indian startup job boards."""
        logging.info("📡 Hunting Indian startup jobs...")
        
        # Cutshort, Instahyre, etc.
        startup_sources = [
            ('Cutshort', 'https://cutshort.io/jobs'),
            ('Instahyre', 'https://www.instahyre.com/jobs/'),
            ('Hirist', 'https://www.hirist.tech/jobs'),
        ]
        
        for name, url in startup_sources:
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    logging.info(f"   {name} job board accessible")
            except:
                pass
    
    def get_hiring_managers(self, companies: list) -> pd.DataFrame:
        """Try to find hiring managers for companies with fresh openings."""
        logging.info("\n🎯 Finding hiring managers for fresh openings...")
        
        hiring_managers = []
        
        for company in companies[:10]:
            # Generate potential HR/hiring email patterns
            domain = self._extract_domain(company)
            if domain:
                patterns = [
                    f"hr@{domain}",
                    f"careers@{domain}",
                    f"hiring@{domain}",
                    f"recruitment@{domain}",
                    f"jobs@{domain}",
                    f"talent@{domain}",
                    f"people@{domain}",
                ]
                
                # Add first pattern as primary
                hiring_managers.append({
                    'company': company,
                    'email': patterns[0],
                    'type': 'hr',
                    'all_patterns': patterns[:3]
                })
        
        return pd.DataFrame(hiring_managers)
    
    def _extract_domain(self, company: str) -> str:
        """Extract likely email domain from company name."""
        # Clean company name
        name = company.lower().strip()
        name = re.sub(r'[^a-z0-9]', '', name)
        
        # Known company domains
        known_domains = {
            'razorpay': 'razorpay.com',
            'swiggy': 'swiggy.in',
            'zomato': 'zomato.com',
            'phonepe': 'phonepe.com',
            'flipkart': 'flipkart.com',
            'paytm': 'paytm.com',
            'cred': 'cred.club',
            'groww': 'groww.in',
            'meesho': 'meesho.com',
            'zerodha': 'zerodha.com',
        }
        
        if name in known_domains:
            return known_domains[name]
        
        # Generic pattern
        return f"{name}.com"
    
    def save_fresh_jobs(self, df: pd.DataFrame):
        """Save fresh jobs to CSV with priority tags."""
        if df.empty:
            logging.warning("No fresh jobs to save")
            return
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save all fresh jobs
        output_path = os.path.join(output_dir, 'fresh_jobs.csv')
        df.to_csv(output_path, index=False)
        logging.info(f"💾 Saved {len(df)} fresh jobs to {output_path}")
        
        # Save HOT jobs separately for urgent attention
        hot_jobs = df[df['freshness_tier'] == 'hot']
        if not hot_jobs.empty:
            hot_path = os.path.join(output_dir, 'hot_jobs_urgent.csv')
            hot_jobs.to_csv(hot_path, index=False)
            logging.info(f"🔥 Saved {len(hot_jobs)} HOT jobs (apply immediately!) to {hot_path}")


def main():
    """Hunt for fresh jobs and prioritize them."""
    logging.info("="*60)
    logging.info("🔥 FRESH JOB HUNTER")
    logging.info("   Finding the LATEST job openings")
    logging.info("   Priority: Posted TODAY > Last 3 days > Last week")
    logging.info("="*60)
    
    hunter = FreshJobHunter()
    fresh_jobs = hunter.hunt_fresh_jobs()
    
    if not fresh_jobs.empty:
        hunter.save_fresh_jobs(fresh_jobs)
        
        # Get hiring managers for top companies
        top_companies = fresh_jobs['company'].unique()[:10]
        hiring_managers = hunter.get_hiring_managers(list(top_companies))
        
        if not hiring_managers.empty:
            logging.info(f"\n📧 Found potential hiring contacts for {len(hiring_managers)} companies")
    else:
        logging.warning("No fresh jobs found - try different keywords")
    
    logging.info("="*60)
    return fresh_jobs


if __name__ == "__main__":
    main()
