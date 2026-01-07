"""
HR Email Scraper - Extracts recruiter/HR emails from job postings and company pages
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
import pandas as pd
import os
import time
import random
from urllib.parse import urljoin, urlparse
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class HREmailScraper:
    """Scrapes HR/recruiter emails from job postings and company websites."""
    
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
    
    def __init__(self):
        self.session = requests.Session()
        self._update_headers()
        
        # Email pattern
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            re.IGNORECASE
        )
        
        # HR-related keywords to identify relevant emails
        self.hr_keywords = [
            'hr', 'human', 'resource', 'recruit', 'talent', 'career', 'job', 
            'hiring', 'people', 'staffing', 'employment', 'acquisition'
        ]
        
        # Domains to skip (generic email providers)
        self.skip_domains = [
            'example.com', 'gmail.com', 'yahoo.com', 'hotmail.com', 
            'outlook.com', 'test.com', 'email.com', 'mail.com',
            'sentry.io', 'w3.org', 'schema.org', 'googleapis.com'
        ]
        
        self.scraped_emails = []
    
    def _update_headers(self):
        """Update session with fresh randomized headers."""
        self.session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0',
        })
        
    def is_valid_hr_email(self, email: str, company_domain: str = None) -> bool:
        """Check if email looks like an HR/recruiter email."""
        email_lower = email.lower()
        domain = email.split('@')[-1].lower()
        
        # Skip generic domains
        if domain in self.skip_domains:
            return False
            
        # Skip image/file extensions mistakenly captured
        if any(ext in email_lower for ext in ['.png', '.jpg', '.gif', '.svg', '.css', '.js']):
            return False
            
        # Prefer emails with HR keywords
        local_part = email.split('@')[0].lower()
        has_hr_keyword = any(kw in local_part or kw in domain for kw in self.hr_keywords)
        
        # If company domain provided, prefer matching emails
        if company_domain and company_domain.lower() in domain:
            return True
            
        # Accept if has HR keyword
        if has_hr_keyword:
            return True
            
        # Accept corporate emails (not personal domains)
        if domain not in self.skip_domains and '.' in domain:
            return True
            
        return False
    
    def extract_emails_from_text(self, text: str, company_domain: str = None) -> list:
        """Extract valid emails from text."""
        if not text:
            return []
            
        emails = self.email_pattern.findall(text)
        valid_emails = []
        
        for email in emails:
            if self.is_valid_hr_email(email, company_domain):
                valid_emails.append(email.lower())
                
        return list(set(valid_emails))
    
    def scrape_page(self, url: str, company_name: str = None) -> list:
        """Scrape a single page for emails with anti-detection measures."""
        try:
            # Rotate headers before each request
            self._update_headers()
            
            # Add small random delay to appear more human-like
            time.sleep(random.uniform(0.5, 2))
            
            response = self.session.get(url, timeout=15)
            
            # Handle 403 Forbidden - retry with fresh session
            if response.status_code == 403:
                logging.debug(f"Got 403 for {url}, retrying with fresh session...")
                self.session = requests.Session()
                self._update_headers()
                time.sleep(random.uniform(2, 4))
                response = self.session.get(url, timeout=15)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get company domain from URL
            parsed_url = urlparse(url)
            company_domain = parsed_url.netloc.replace('www.', '')
            
            # Extract text content
            text = soup.get_text(separator=' ')
            
            # Also check href attributes for mailto links
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            mailto_emails = []
            for link in mailto_links:
                href = link.get('href', '')
                email_match = self.email_pattern.search(href)
                if email_match:
                    mailto_emails.append(email_match.group())
            
            # Combine all emails
            all_emails = self.extract_emails_from_text(text, company_domain)
            all_emails.extend([e.lower() for e in mailto_emails if self.is_valid_hr_email(e, company_domain)])
            
            return list(set(all_emails))
            
        except Exception as e:
            logging.warning(f"Error scraping {url}: {e}")
            return []
    
    def scrape_company_careers_page(self, company_name: str, careers_url: str) -> dict:
        """Scrape a company's careers page for HR emails."""
        logging.info(f"🔍 Scraping {company_name} careers page: {careers_url}")
        
        emails = self.scrape_page(careers_url, company_name)
        
        # DISABLED: Additional path scraping generates too many 404 errors
        # Most company websites block bots or have non-standard URL structures
        # Using curated_hr_database.py for reliable email sources
        
        emails = list(set(emails))
        
        return {
            'company': company_name,
            'careers_url': careers_url,
            'emails': emails,
            'email_count': len(emails)
        }
    
    def scrape_linkedin_jobs_page(self, job_url: str) -> dict:
        """Scrape LinkedIn job posting for contact info."""
        # LinkedIn blocks scraping, but we can try to get company info
        logging.info(f"🔍 Checking LinkedIn job: {job_url}")
        
        try:
            response = self.session.get(job_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract company name
            company_elem = soup.find('a', {'class': re.compile(r'company', re.I)})
            company_name = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Extract job title
            title_elem = soup.find('h1') or soup.find('h2', {'class': re.compile(r'title', re.I)})
            job_title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
            
            # LinkedIn rarely shows emails directly, but capture any found
            text = soup.get_text()
            emails = self.extract_emails_from_text(text)
            
            return {
                'source': 'linkedin',
                'job_url': job_url,
                'company': company_name,
                'job_title': job_title,
                'emails': emails
            }
        except Exception as e:
            logging.warning(f"Error scraping LinkedIn job: {e}")
            return None
    
    def search_company_emails(self, company_name: str) -> list:
        """Search for company HR emails using various methods."""
        emails = []
        
        # Common HR email patterns to try
        common_patterns = [
            f"hr@{company_name.lower().replace(' ', '')}.com",
            f"careers@{company_name.lower().replace(' ', '')}.com",
            f"jobs@{company_name.lower().replace(' ', '')}.com",
            f"recruitment@{company_name.lower().replace(' ', '')}.com",
            f"hiring@{company_name.lower().replace(' ', '')}.com",
            f"talent@{company_name.lower().replace(' ', '')}.com",
        ]
        
        # Try to find company website
        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+careers+contact+email"
        
        try:
            response = self.session.get(search_url, timeout=10)
            found_emails = self.extract_emails_from_text(response.text)
            emails.extend(found_emails)
        except:
            pass
        
        return list(set(emails))
    
    def scrape_from_jobs_csv(self, jobs_csv_path: str) -> pd.DataFrame:
        """Scrape emails from jobs listed in the jobs CSV."""
        if not os.path.exists(jobs_csv_path):
            logging.error(f"Jobs CSV not found: {jobs_csv_path}")
            return pd.DataFrame()
        
        jobs_df = pd.read_csv(jobs_csv_path)
        logging.info(f"📊 Processing {len(jobs_df)} jobs from CSV")
        
        results = []
        
        for idx, job in jobs_df.iterrows():
            company = job.get('company', 'Unknown')
            job_title = job.get('title', 'Unknown Position')
            job_url = job.get('url') or job.get('link', '')
            source = job.get('source', 'unknown')
            
            logging.info(f"Processing {idx+1}/{len(jobs_df)}: {job_title} at {company}")
            
            emails = []
            
            # Scrape job URL if available
            if job_url and job_url.startswith('http'):
                page_emails = self.scrape_page(job_url, company)
                emails.extend(page_emails)
            
            # Search for company emails
            company_emails = self.search_company_emails(company)
            emails.extend(company_emails)
            
            emails = list(set(emails))
            
            if emails:
                for email in emails:
                    results.append({
                        'company': company,
                        'job_title': job_title,
                        'job_url': job_url,
                        'source': source,
                        'hr_email': email,
                        'scraped_at': pd.Timestamp.now().isoformat()
                    })
                logging.info(f"  ✅ Found {len(emails)} emails: {emails}")
            else:
                # Add entry with no email found
                results.append({
                    'company': company,
                    'job_title': job_title,
                    'job_url': job_url,
                    'source': source,
                    'hr_email': None,
                    'scraped_at': pd.Timestamp.now().isoformat()
                })
                logging.info(f"  ⚠️ No emails found")
            
            # Be respectful with rate limiting
            time.sleep(random.uniform(2, 5))
        
        return pd.DataFrame(results)
    
    def scrape_from_company_list(self, companies: list) -> pd.DataFrame:
        """Scrape emails from a list of companies with their career URLs."""
        results = []
        
        for company_info in companies:
            if isinstance(company_info, dict):
                company_name = company_info.get('name', 'Unknown')
                careers_url = company_info.get('careers_url', '')
            else:
                company_name = str(company_info)
                careers_url = ''
            
            if careers_url:
                data = self.scrape_company_careers_page(company_name, careers_url)
                for email in data.get('emails', []):
                    results.append({
                        'company': company_name,
                        'careers_url': careers_url,
                        'hr_email': email,
                        'scraped_at': pd.Timestamp.now().isoformat()
                    })
            
            time.sleep(random.uniform(2, 4))
        
        return pd.DataFrame(results)


# Target companies with career pages
TARGET_COMPANIES = [
    {"name": "Infosys", "careers_url": "https://www.infosys.com/careers.html"},
    {"name": "TCS", "careers_url": "https://www.tcs.com/careers"},
    {"name": "Wipro", "careers_url": "https://careers.wipro.com/"},
    {"name": "HCL Technologies", "careers_url": "https://www.hcltech.com/careers"},
    {"name": "Tech Mahindra", "careers_url": "https://careers.techmahindra.com/"},
    {"name": "Cognizant", "careers_url": "https://careers.cognizant.com/"},
    {"name": "Capgemini", "careers_url": "https://www.capgemini.com/in-en/careers/"},
    {"name": "Accenture", "careers_url": "https://www.accenture.com/in-en/careers"},
    {"name": "IBM", "careers_url": "https://www.ibm.com/careers/"},
    {"name": "Oracle", "careers_url": "https://www.oracle.com/in/careers/"},
    {"name": "SAP", "careers_url": "https://jobs.sap.com/"},
    {"name": "Microsoft", "careers_url": "https://careers.microsoft.com/"},
    {"name": "Google", "careers_url": "https://careers.google.com/"},
    {"name": "Amazon", "careers_url": "https://www.amazon.jobs/"},
    {"name": "Deloitte", "careers_url": "https://www2.deloitte.com/in/en/careers.html"},
    {"name": "KPMG", "careers_url": "https://kpmg.com/in/en/home/careers.html"},
    {"name": "EY", "careers_url": "https://www.ey.com/en_in/careers"},
    {"name": "PwC", "careers_url": "https://www.pwc.in/careers.html"},
    {"name": "Mindtree", "careers_url": "https://www.mindtree.com/careers"},
    {"name": "Mphasis", "careers_url": "https://www.mphasis.com/home/careers.html"},
]


def search_emails_duckduckgo(scraper, search_terms: list) -> pd.DataFrame:
    """Search for HR emails using DuckDuckGo (bot-friendly alternative to direct scraping)."""
    logging.info("🔍 Searching for HR emails via DuckDuckGo (bot-friendly)...")
    
    results = []
    
    for term in search_terms[:5]:  # Limit to 5 terms
        try:
            scraper._update_headers()
            
            # DuckDuckGo HTML search (bot-friendly, no API key needed)
            search_query = f'{term} bangalore careers hr email contact'
            search_url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
            
            response = scraper.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract emails from search results
                page_text = soup.get_text()
                emails = scraper.email_pattern.findall(page_text)
                
                for email in emails:
                    if scraper.is_valid_hr_email(email):
                        results.append({
                            'company': 'Unknown',
                            'hr_email': email.lower(),
                            'source': 'duckduckgo_search',
                            'search_term': term,
                            'scraped_at': pd.Timestamp.now().isoformat()
                        })
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logging.debug(f"DuckDuckGo search error for '{term}': {e}")
    
    logging.info(f"   Found {len(results)} emails from DuckDuckGo")
    return pd.DataFrame(results)


def main():
    """Main function to run the email scraper."""
    scraper = HREmailScraper()
    
    # First, try to scrape from existing jobs CSV
    jobs_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs_today.csv')
    
    if os.path.exists(jobs_csv):
        logging.info("📧 Scraping HR emails from jobs CSV...")
        jobs_emails_df = scraper.scrape_from_jobs_csv(jobs_csv)
        
        if not jobs_emails_df.empty:
            output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hr_emails_from_jobs.csv')
            jobs_emails_df.to_csv(output_path, index=False)
            logging.info(f"✅ Saved {len(jobs_emails_df)} records to {output_path}")
    else:
        jobs_emails_df = pd.DataFrame()
    
    # Use bot-friendly search engines instead of direct career page scraping
    # Get search terms from JOB_KEYWORDS environment variable
    keywords_env = os.getenv('JOB_KEYWORDS', '')
    if keywords_env:
        search_terms = [k.strip() for k in keywords_env.split(',')]
    else:
        search_terms = ["interior designer", "autocad designer", "civil engineer"]
    
    logging.info("🏢 Searching for company HR emails via bot-friendly engines...")
    companies_emails_df = search_emails_duckduckgo(scraper, search_terms)
    
    if not companies_emails_df.empty:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hr_emails_from_companies.csv')
        companies_emails_df.to_csv(output_path, index=False)
        logging.info(f"✅ Saved {len(companies_emails_df)} records to {output_path}")
    
    # Combine all emails
    all_emails = pd.concat([
        jobs_emails_df if not jobs_emails_df.empty else pd.DataFrame(),
        companies_emails_df if not companies_emails_df.empty else pd.DataFrame()
    ], ignore_index=True)
    
    if not all_emails.empty:
        # Remove duplicates
        all_emails = all_emails.drop_duplicates(subset=['hr_email'], keep='first')
        all_emails = all_emails[all_emails['hr_email'].notna()]
        
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv')
        all_emails.to_csv(output_path, index=False)
        logging.info(f"📊 Total unique HR emails found: {len(all_emails)}")
        logging.info(f"✅ Saved to {output_path}")
    else:
        logging.warning("⚠️ No HR emails found")


if __name__ == "__main__":
    main()
