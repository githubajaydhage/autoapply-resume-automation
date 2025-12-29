"""
HR Email Finder - Extracts REAL HR emails from actual job postings
NO guessing or pattern generation - only genuine emails found in job listings

Sources:
1. Job posting pages (mailto: links)
2. Company career pages (contact emails)
3. Job boards that show recruiter emails
4. Naukri/LinkedIn public job posts with emails
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin, quote_plus

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class RealHREmailFinder:
    """Finds REAL HR emails from actual job postings - NO guessing."""
    
    # Rotating User-Agents to avoid detection
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    ]
    
    # Email pattern to find in HTML
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # Keywords that indicate HR/recruitment emails
    HR_KEYWORDS = ['hr', 'career', 'careers', 'recruit', 'hiring', 'talent', 'jobs', 'job', 'resume', 'apply', 'staffing']
    
    # Skip these generic emails
    SKIP_PATTERNS = ['noreply', 'no-reply', 'donotreply', 'mailer', 'notification', 'alert', 
                     'newsletter', 'unsubscribe', 'feedback', 'example.com', 'test@']
    
    def __init__(self):
        self.session = requests.Session()
        self._update_headers()
        self.found_emails = []
        self.dns_cache = {}
    
    def _update_headers(self):
        """Update session headers with a random User-Agent for anti-detection."""
        ua = random.choice(self.USER_AGENTS)
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
    def find_real_hr_emails(self) -> pd.DataFrame:
        """Find real HR emails from multiple sources."""
        logging.info("="*60)
        logging.info("🔍 REAL HR EMAIL FINDER")
        logging.info("   Only genuine emails from actual job postings")
        logging.info("="*60)
        
        # Source 1: Naukri job listings (has real recruiter emails)
        self._scrape_naukri_emails()
        
        # Source 2: Indeed job postings
        self._scrape_indeed_emails()
        
        # Source 3: Company career pages - DISABLED (too many 404/403 errors)
        # Career page scraping is unreliable - most sites block bots or have changed URLs
        # Using curated_hr_database.py instead which has verified emails
        # self._scrape_career_pages()
        logging.info("📡 Skipping career page scraping (using curated HR database instead)")
        
        # Source 4: LinkedIn public job posts
        self._scrape_linkedin_jobs()
        
        # Source 5: Glassdoor job listings - DISABLED (403 Forbidden)
        # self._scrape_glassdoor_emails()
        
        # Source 6: Internshala (for fresher jobs)
        self._scrape_internshala_emails()
        
        # Deduplicate and validate
        df = self._process_results()
        
        return df
    
    def _scrape_naukri_emails(self):
        """Scrape real recruiter emails from Naukri job listings with anti-detection."""
        logging.info("📡 Scraping Naukri for recruiter emails...")
        
        keywords = ["data analyst bangalore", "business analyst bangalore", "python developer bangalore"]
        
        for keyword in keywords:
            try:
                # Rotate headers for each request
                self._update_headers()
                
                # Add random delay
                time.sleep(random.uniform(2, 4))
                
                # Naukri search URL
                url = f"https://www.naukri.com/{keyword.replace(' ', '-')}-jobs"
                
                response = self.session.get(url, timeout=15)
                
                # Handle 403 - retry with fresh session
                if response.status_code == 403:
                    logging.debug(f"Naukri 403, retrying with fresh session...")
                    time.sleep(random.uniform(3, 6))
                    self.session = requests.Session()
                    self._update_headers()
                    response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all job cards
                    job_cards = soup.find_all(['article', 'div'], class_=lambda x: x and 'job' in str(x).lower())
                    
                    for card in job_cards[:20]:
                        # Look for mailto links
                        mailto_links = card.find_all('a', href=lambda x: x and 'mailto:' in str(x).lower())
                        for link in mailto_links:
                            email = link['href'].replace('mailto:', '').split('?')[0].strip()
                            if self._is_valid_hr_email(email):
                                company = self._extract_company(card)
                                self._add_email(email, company, 'naukri', keyword)
                        
                        # Also search for emails in text
                        text = card.get_text()
                        emails = self.EMAIL_REGEX.findall(text)
                        for email in emails:
                            if self._is_valid_hr_email(email):
                                company = self._extract_company(card)
                                self._add_email(email, company, 'naukri', keyword)
                
            except Exception as e:
                logging.debug(f"Naukri error for {keyword}: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'naukri'])} emails from Naukri")
    
    def _scrape_indeed_emails(self):
        """Scrape recruiter emails from Indeed job listings."""
        logging.info("📡 Scraping Indeed for recruiter emails...")
        
        keywords = ["data+analyst", "business+analyst", "python"]
        
        for keyword in keywords:
            try:
                url = f"https://in.indeed.com/jobs?q={keyword}&l=Bangalore"
                
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find email patterns in the page
                    page_text = soup.get_text()
                    emails = self.EMAIL_REGEX.findall(page_text)
                    
                    for email in emails:
                        if self._is_valid_hr_email(email):
                            self._add_email(email, 'Unknown', 'indeed', keyword)
                    
                    # Check mailto links
                    mailto_links = soup.find_all('a', href=lambda x: x and 'mailto:' in str(x).lower())
                    for link in mailto_links:
                        email = link['href'].replace('mailto:', '').split('?')[0].strip()
                        if self._is_valid_hr_email(email):
                            self._add_email(email, 'Unknown', 'indeed', keyword)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logging.debug(f"Indeed error: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'indeed'])} emails from Indeed")
    
    def _scrape_career_pages(self):
        """Scrape emails from company career pages with anti-detection."""
        logging.info("📡 Scraping company career pages...")
        
        # Real career page URLs with known HR emails
        career_pages = [
            ("Infosys", "https://www.infosys.com/careers/"),
            ("TCS", "https://www.tcs.com/careers"),
            ("Wipro", "https://careers.wipro.com/"),
            ("HCL", "https://www.hcltech.com/careers"),
            ("Tech Mahindra", "https://careers.techmahindra.com/"),
            ("Mindtree", "https://www.ltimindtree.com/careers/"),
            ("Mphasis", "https://careers.mphasis.com/"),
            ("Cognizant", "https://careers.cognizant.com/"),
            ("Capgemini", "https://www.capgemini.com/in-en/careers/"),
            ("Accenture", "https://www.accenture.com/in-en/careers"),
            ("Deloitte", "https://www2.deloitte.com/in/en/careers.html"),
            ("Razorpay", "https://razorpay.com/jobs/"),
            ("Swiggy", "https://careers.swiggy.com/"),
            ("Zomato", "https://www.zomato.com/careers"),
            ("PhonePe", "https://www.phonepe.com/careers/"),
            ("Meesho", "https://www.meesho.com/careers"),
            ("Groww", "https://groww.in/careers"),
        ]
        
        for company, url in career_pages:
            try:
                # Rotate headers before each request
                self._update_headers()
                
                # Add random delay to appear more human-like
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(url, timeout=10)
                
                # Handle 403 - retry with fresh headers
                if response.status_code == 403:
                    logging.debug(f"403 from {company}, retrying with fresh headers...")
                    time.sleep(random.uniform(2, 5))
                    self._update_headers()
                    self.session = requests.Session()  # Fresh session
                    self._update_headers()
                    response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all mailto links
                    mailto_links = soup.find_all('a', href=lambda x: x and 'mailto:' in str(x).lower())
                    for link in mailto_links:
                        email = link['href'].replace('mailto:', '').split('?')[0].strip()
                        if self._is_valid_hr_email(email):
                            self._add_email(email, company, 'career_page', 'direct')
                    
                    # Search for emails in contact sections
                    contact_sections = soup.find_all(['div', 'section', 'footer'], 
                                                     class_=lambda x: x and any(k in str(x).lower() for k in ['contact', 'footer', 'connect']))
                    for section in contact_sections:
                        emails = self.EMAIL_REGEX.findall(section.get_text())
                        for email in emails:
                            if self._is_valid_hr_email(email):
                                self._add_email(email, company, 'career_page', 'direct')
                
            except Exception as e:
                logging.debug(f"Career page error for {company}: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'career_page'])} emails from career pages")
    
    def _scrape_linkedin_jobs(self):
        """Scrape emails from LinkedIn public job listings."""
        logging.info("📡 Checking LinkedIn public job pages...")
        
        # LinkedIn public job search (no login needed)
        keywords = ["data analyst india", "business analyst bangalore"]
        
        for keyword in keywords:
            try:
                url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(keyword)}&location=India"
                
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find emails in the page
                    page_text = soup.get_text()
                    emails = self.EMAIL_REGEX.findall(page_text)
                    
                    for email in emails:
                        if self._is_valid_hr_email(email):
                            self._add_email(email, 'Unknown', 'linkedin_jobs', keyword)
                
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                logging.debug(f"LinkedIn error: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'linkedin_jobs'])} emails from LinkedIn")
    
    def _scrape_glassdoor_emails(self):
        """Scrape emails from Glassdoor job listings."""
        logging.info("📡 Checking Glassdoor job listings...")
        
        try:
            url = "https://www.glassdoor.co.in/Job/bangalore-data-analyst-jobs-SRCH_IL.0,9_IC2940587_KO10,22.htm"
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find emails
                page_text = soup.get_text()
                emails = self.EMAIL_REGEX.findall(page_text)
                
                for email in emails:
                    if self._is_valid_hr_email(email):
                        self._add_email(email, 'Unknown', 'glassdoor', 'data analyst')
            
        except Exception as e:
            logging.debug(f"Glassdoor error: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'glassdoor'])} emails from Glassdoor")
    
    def _scrape_internshala_emails(self):
        """Scrape emails from Internshala (fresher jobs)."""
        logging.info("📡 Checking Internshala job listings...")
        
        try:
            urls = [
                "https://internshala.com/jobs/data-analyst-jobs-in-bangalore/",
                "https://internshala.com/jobs/business-analyst-jobs/",
                "https://internshala.com/jobs/python-jobs-in-bangalore/",
            ]
            
            for url in urls:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find emails in job cards
                    page_text = soup.get_text()
                    emails = self.EMAIL_REGEX.findall(page_text)
                    
                    for email in emails:
                        if self._is_valid_hr_email(email):
                            self._add_email(email, 'Unknown', 'internshala', 'fresher')
                    
                    # Check mailto links
                    mailto_links = soup.find_all('a', href=lambda x: x and 'mailto:' in str(x).lower())
                    for link in mailto_links:
                        email = link['href'].replace('mailto:', '').split('?')[0].strip()
                        if self._is_valid_hr_email(email):
                            self._add_email(email, 'Unknown', 'internshala', 'fresher')
                
                time.sleep(random.uniform(2, 3))
            
        except Exception as e:
            logging.debug(f"Internshala error: {e}")
        
        logging.info(f"   Found {len([e for e in self.found_emails if e['source'] == 'internshala'])} emails from Internshala")
    
    def _is_valid_hr_email(self, email: str) -> bool:
        """Check if email is a valid HR/recruitment email."""
        if not email:
            return False
        
        email = email.lower().strip()
        
        # Basic format check
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False
        
        # Skip invalid patterns
        for pattern in self.SKIP_PATTERNS:
            if pattern in email:
                return False
        
        # Must contain HR keywords OR be from a known company domain
        local_part = email.split('@')[0]
        domain = email.split('@')[1]
        
        # Check for HR keywords in local part
        has_hr_keyword = any(kw in local_part for kw in self.HR_KEYWORDS)
        
        # Check if from company domain (not personal email like gmail)
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'rediffmail.com']
        is_company_domain = domain not in personal_domains
        
        # Accept if has HR keyword, OR if it's from company domain
        if has_hr_keyword:
            return True
        
        # For company domains, accept even without HR keyword (might be recruiter name)
        if is_company_domain and len(local_part) > 2:
            return True
        
        # For personal domains, only accept if has HR keyword
        return False
    
    def _extract_company(self, element) -> str:
        """Extract company name from HTML element."""
        try:
            # Try common class patterns
            company_elem = element.find(['a', 'span', 'div'], class_=lambda x: x and 'company' in str(x).lower())
            if company_elem:
                return company_elem.get_text(strip=True)
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _add_email(self, email: str, company: str, source: str, job_keyword: str):
        """Add email to found list."""
        email = email.lower().strip()
        
        # Check if already exists
        if any(e['email'] == email for e in self.found_emails):
            return
        
        self.found_emails.append({
            'email': email,
            'company': company,
            'source': source,
            'job_keyword': job_keyword,
            'found_at': datetime.now().isoformat()
        })
    
    def _verify_mx_record(self, domain: str) -> bool:
        """Verify domain has MX records."""
        if not HAS_DNS:
            return True  # Skip if dns module not available
        
        if domain in self.dns_cache:
            return self.dns_cache[domain]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
            has_mx = len(list(mx_records)) > 0
            self.dns_cache[domain] = has_mx
            return has_mx
        except:
            self.dns_cache[domain] = False
            return False
    
    def _process_results(self) -> pd.DataFrame:
        """Process and save results."""
        if not self.found_emails:
            logging.warning("⚠️ No genuine HR emails found from job postings")
            logging.info("   This is normal - most job sites hide recruiter emails")
            logging.info("   System will use curated database (130+ verified emails)")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.found_emails)
        
        # Verify MX records
        if HAS_DNS:
            logging.info("🔍 Verifying email domains...")
            valid_mask = df['email'].apply(lambda x: self._verify_mx_record(x.split('@')[1]))
            invalid_count = (~valid_mask).sum()
            if invalid_count > 0:
                logging.info(f"   Removed {invalid_count} emails with invalid domains")
            df = df[valid_mask]
        
        # Rename for compatibility
        df = df.rename(columns={'email': 'hr_email'})
        df['job_title'] = df['job_keyword'].apply(lambda x: x.title() if x else 'Various')
        
        # Deduplicate
        df = df.drop_duplicates(subset=['hr_email'], keep='first')
        
        # Save results
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        output_path = os.path.join(data_dir, 'scraped_hr_emails.csv')
        df.to_csv(output_path, index=False)
        logging.info(f"💾 Saved {len(df)} genuine HR emails to {output_path}")
        
        # Merge with all_hr_emails.csv
        all_hr_path = os.path.join(data_dir, 'all_hr_emails.csv')
        if os.path.exists(all_hr_path):
            existing = pd.read_csv(all_hr_path)
            combined = pd.concat([existing, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=['hr_email'], keep='first')
        else:
            combined = df
        
        combined.to_csv(all_hr_path, index=False)
        logging.info(f"📊 Total HR emails in database: {len(combined)}")
        
        return df


def main():
    """Find real HR emails from job postings."""
    logging.info("="*60)
    logging.info("🔍 REAL HR EMAIL FINDER")
    logging.info("   Only genuine emails - NO pattern guessing")
    logging.info("="*60)
    
    finder = RealHREmailFinder()
    df = finder.find_real_hr_emails()
    
    if not df.empty:
        logging.info("\n📊 GENUINE EMAILS FOUND:")
        for _, row in df.head(15).iterrows():
            logging.info(f"   ✅ {row['company']}: {row['hr_email']} (from {row['source']})")
    else:
        logging.info("\n⚠️ No emails scraped - this is normal!")
        logging.info("   Most job sites hide recruiter emails.")
        logging.info("   System will use curated database (130+ verified emails)")
    
    logging.info("="*60)
    return df


if __name__ == "__main__":
    main()
