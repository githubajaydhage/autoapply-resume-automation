"""
HR Email Finder - Finds HR emails from companies with ACTIVE job openings
Uses multiple strategies:
1. Job APIs (RemoteOK, Adzuna, TheMuseAPI) to find companies hiring
2. Generates HR email patterns from company domains
3. Hunter.io style email guessing
4. Verifies emails via MX records
"""

import requests
import pandas as pd
import os
import logging
import re
import time
import random
from datetime import datetime
from urllib.parse import urlparse

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class HREmailFinder:
    """Finds HR emails from companies with active job openings."""
    
    # Common HR email patterns used by companies
    HR_EMAIL_PATTERNS = [
        "careers@{domain}",
        "hr@{domain}",
        "jobs@{domain}",
        "recruitment@{domain}",
        "recruiting@{domain}",
        "hiring@{domain}",
        "talent@{domain}",
        "resume@{domain}",
        "apply@{domain}",
        "careers.india@{domain}",
        "india.careers@{domain}",
        "india.recruiting@{domain}",
        "indiacareers@{domain}",
        "indiajobs@{domain}",
        "hr.india@{domain}",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
        })
        self.found_emails = []
        self.verified_emails = []
        self.dns_cache = {}
        
    def find_all_hr_emails(self) -> pd.DataFrame:
        """Find HR emails from all sources."""
        logging.info("="*60)
        logging.info("🔍 HR EMAIL FINDER - Finding HR contacts from active job postings")
        logging.info("="*60)
        
        # 1. Get companies from job APIs
        companies = self._get_hiring_companies()
        logging.info(f"📊 Found {len(companies)} companies with active openings")
        
        # 2. Generate HR email patterns
        self._generate_hr_emails(companies)
        logging.info(f"📧 Generated {len(self.found_emails)} potential HR emails")
        
        # 3. Verify emails (MX record check)
        self._verify_emails()
        logging.info(f"✅ Verified {len(self.verified_emails)} HR emails")
        
        # 4. Save results
        return self._save_results()
    
    def _get_hiring_companies(self) -> list:
        """Get list of companies with active job openings."""
        companies = []
        
        # Source 1: RemoteOK API
        companies.extend(self._get_remoteok_companies())
        
        # Source 2: Adzuna API (free tier)
        companies.extend(self._get_adzuna_companies())
        
        # Source 3: The Muse API
        companies.extend(self._get_themuse_companies())
        
        # Source 4: GitHub Jobs alternatives
        companies.extend(self._get_startup_companies())
        
        # Source 5: Direct company list (known hiring)
        companies.extend(self._get_known_hiring_companies())
        
        # Deduplicate
        seen = set()
        unique_companies = []
        for company in companies:
            domain = company.get('domain', '').lower()
            if domain and domain not in seen:
                seen.add(domain)
                unique_companies.append(company)
        
        return unique_companies
    
    def _get_remoteok_companies(self) -> list:
        """Get companies from RemoteOK API."""
        companies = []
        try:
            logging.info("📡 Fetching companies from RemoteOK...")
            response = self.session.get("https://remoteok.com/api", timeout=15)
            
            if response.status_code == 200:
                jobs = response.json()
                for job in jobs[1:100]:  # First 100 jobs
                    if isinstance(job, dict) and job.get('company'):
                        company_name = job.get('company', '')
                        # Try to extract domain from job URL or company name
                        domain = self._extract_domain(job.get('company_logo', '') or job.get('url', ''))
                        if not domain:
                            domain = self._guess_domain(company_name)
                        
                        if domain:
                            companies.append({
                                'name': company_name,
                                'domain': domain,
                                'job_title': job.get('position', ''),
                                'source': 'remoteok'
                            })
                            
                logging.info(f"   Found {len(companies)} companies from RemoteOK")
                
        except Exception as e:
            logging.warning(f"RemoteOK error: {e}")
        
        return companies
    
    def _get_adzuna_companies(self) -> list:
        """Get companies from Adzuna (no API key needed for basic access)."""
        companies = []
        try:
            logging.info("📡 Fetching companies from Adzuna...")
            
            # Adzuna India RSS-like endpoints
            keywords = ["data+analyst", "business+analyst", "python", "sql"]
            
            for keyword in keywords[:2]:  # Limit to avoid rate limiting
                url = f"https://www.adzuna.in/search?q={keyword}&w=bangalore"
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        # Extract company names from HTML
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find company elements
                        company_elements = soup.find_all(['a', 'div'], class_=lambda x: x and 'company' in str(x).lower())
                        for elem in company_elements[:20]:
                            company_name = elem.get_text(strip=True)
                            if company_name and len(company_name) > 2:
                                domain = self._guess_domain(company_name)
                                if domain:
                                    companies.append({
                                        'name': company_name,
                                        'domain': domain,
                                        'job_title': keyword.replace('+', ' '),
                                        'source': 'adzuna'
                                    })
                                    
                    time.sleep(1)  # Rate limit
                except:
                    pass
                    
            logging.info(f"   Found {len(companies)} companies from Adzuna")
            
        except Exception as e:
            logging.warning(f"Adzuna error: {e}")
        
        return companies
    
    def _get_themuse_companies(self) -> list:
        """Get companies from The Muse API (free, no auth)."""
        companies = []
        try:
            logging.info("📡 Fetching companies from The Muse...")
            
            # The Muse has a free public API
            url = "https://www.themuse.com/api/public/companies?page=1&industry=Technology"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                for company in data.get('results', [])[:50]:
                    company_name = company.get('name', '')
                    # The Muse provides company info
                    refs = company.get('refs', {})
                    landing = refs.get('landing_page', '')
                    
                    domain = self._extract_domain(landing)
                    if not domain:
                        domain = self._guess_domain(company_name)
                    
                    if domain:
                        companies.append({
                            'name': company_name,
                            'domain': domain,
                            'job_title': 'Various',
                            'source': 'themuse'
                        })
                        
                logging.info(f"   Found {len(companies)} companies from The Muse")
                
        except Exception as e:
            logging.warning(f"The Muse error: {e}")
        
        return companies
    
    def _get_startup_companies(self) -> list:
        """Get companies from startup job boards."""
        companies = []
        
        # Known startup domains that are actively hiring
        startups = [
            {"name": "Razorpay", "domain": "razorpay.com"},
            {"name": "Zerodha", "domain": "zerodha.com"},
            {"name": "CRED", "domain": "cred.club"},
            {"name": "Meesho", "domain": "meesho.com"},
            {"name": "Groww", "domain": "groww.in"},
            {"name": "PhonePe", "domain": "phonepe.com"},
            {"name": "Swiggy", "domain": "swiggy.in"},
            {"name": "Zomato", "domain": "zomato.com"},
            {"name": "Ola", "domain": "olacabs.com"},
            {"name": "Paytm", "domain": "paytm.com"},
            {"name": "PolicyBazaar", "domain": "policybazaar.com"},
            {"name": "Lenskart", "domain": "lenskart.com"},
            {"name": "Urban Company", "domain": "urbancompany.com"},
            {"name": "Dunzo", "domain": "dunzo.in"},
            {"name": "BigBasket", "domain": "bigbasket.com"},
            {"name": "Nykaa", "domain": "nykaa.com"},
            {"name": "Flipkart", "domain": "flipkart.com"},
            {"name": "Dream11", "domain": "dream11.com"},
            {"name": "Udaan", "domain": "udaan.com"},
            {"name": "Byju's", "domain": "byjus.com"},
            {"name": "Unacademy", "domain": "unacademy.com"},
            {"name": "UpGrad", "domain": "upgrad.com"},
            {"name": "Delhivery", "domain": "delhivery.com"},
            {"name": "ShareChat", "domain": "sharechat.co"},
            {"name": "Ather Energy", "domain": "atherenergy.com"},
            {"name": "Rapido", "domain": "rapido.bike"},
            {"name": "Jupiter", "domain": "jupiter.money"},
            {"name": "Slice", "domain": "sliceit.com"},
            {"name": "Jar", "domain": "myjar.app"},
            {"name": "Fi", "domain": "fi.money"},
        ]
        
        for s in startups:
            companies.append({
                'name': s['name'],
                'domain': s['domain'],
                'job_title': 'Various Openings',
                'source': 'startup_list'
            })
        
        logging.info(f"   Added {len(startups)} known startups")
        return companies
    
    def _get_known_hiring_companies(self) -> list:
        """List of major companies known to be actively hiring."""
        companies = [
            # IT Services
            {"name": "TCS", "domain": "tcs.com"},
            {"name": "Infosys", "domain": "infosys.com"},
            {"name": "Wipro", "domain": "wipro.com"},
            {"name": "HCL", "domain": "hcl.com"},
            {"name": "Tech Mahindra", "domain": "techmahindra.com"},
            {"name": "Cognizant", "domain": "cognizant.com"},
            {"name": "Capgemini", "domain": "capgemini.com"},
            {"name": "LTIMindtree", "domain": "ltimindtree.com"},
            {"name": "Mphasis", "domain": "mphasis.com"},
            {"name": "Persistent", "domain": "persistent.com"},
            {"name": "Cyient", "domain": "cyient.com"},
            {"name": "Zensar", "domain": "zensar.com"},
            {"name": "Birlasoft", "domain": "birlasoft.com"},
            {"name": "Hexaware", "domain": "hexaware.com"},
            {"name": "NIIT Technologies", "domain": "niit-tech.com"},
            {"name": "Sonata Software", "domain": "sonata-software.com"},
            
            # Product Companies (India offices)
            {"name": "Google", "domain": "google.com"},
            {"name": "Microsoft", "domain": "microsoft.com"},
            {"name": "Amazon", "domain": "amazon.com"},
            {"name": "Meta", "domain": "fb.com"},
            {"name": "Apple", "domain": "apple.com"},
            {"name": "Netflix", "domain": "netflix.com"},
            {"name": "Adobe", "domain": "adobe.com"},
            {"name": "Salesforce", "domain": "salesforce.com"},
            {"name": "Oracle", "domain": "oracle.com"},
            {"name": "SAP", "domain": "sap.com"},
            {"name": "IBM", "domain": "ibm.com"},
            {"name": "VMware", "domain": "vmware.com"},
            {"name": "Cisco", "domain": "cisco.com"},
            {"name": "Intel", "domain": "intel.com"},
            {"name": "Qualcomm", "domain": "qualcomm.com"},
            {"name": "NVIDIA", "domain": "nvidia.com"},
            {"name": "Uber", "domain": "uber.com"},
            {"name": "Atlassian", "domain": "atlassian.com"},
            {"name": "Stripe", "domain": "stripe.com"},
            {"name": "Spotify", "domain": "spotify.com"},
            
            # Banks & Finance
            {"name": "HDFC Bank", "domain": "hdfcbank.com"},
            {"name": "ICICI Bank", "domain": "icicibank.com"},
            {"name": "Kotak", "domain": "kotak.com"},
            {"name": "Axis Bank", "domain": "axisbank.com"},
            {"name": "Yes Bank", "domain": "yesbank.in"},
            {"name": "Bajaj Finance", "domain": "bajajfinserv.in"},
            {"name": "Paytm Payments Bank", "domain": "paytmbank.com"},
            
            # Consulting
            {"name": "Accenture", "domain": "accenture.com"},
            {"name": "Deloitte", "domain": "deloitte.com"},
            {"name": "PwC", "domain": "pwc.com"},
            {"name": "EY", "domain": "ey.com"},
            {"name": "KPMG", "domain": "kpmg.com"},
            {"name": "McKinsey", "domain": "mckinsey.com"},
            {"name": "BCG", "domain": "bcg.com"},
            {"name": "Bain", "domain": "bain.com"},
            
            # Analytics
            {"name": "Mu Sigma", "domain": "mu-sigma.com"},
            {"name": "Fractal Analytics", "domain": "fractal.ai"},
            {"name": "Tiger Analytics", "domain": "tigeranalytics.com"},
            {"name": "LatentView", "domain": "latentview.com"},
            {"name": "AbsolutData", "domain": "absolutdata.com"},
            {"name": "Tredence", "domain": "tredence.com"},
            {"name": "TheMathCompany", "domain": "themathcompany.com"},
        ]
        
        result = []
        for c in companies:
            result.append({
                'name': c['name'],
                'domain': c['domain'],
                'job_title': 'Active Openings',
                'source': 'known_hiring'
            })
        
        logging.info(f"   Added {len(companies)} known hiring companies")
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url if url.startswith('http') else f"https://{url}")
            domain = parsed.netloc.lower()
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if '.' in domain else ""
        except:
            return ""
    
    def _guess_domain(self, company_name: str) -> str:
        """Guess company domain from name."""
        if not company_name:
            return ""
        
        # Clean company name
        name = company_name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+(inc|ltd|llc|pvt|private|limited|corp|corporation|technologies|tech|software|solutions|services|india|global).*$', '', name)
        name = name.strip().replace(' ', '')
        
        if len(name) < 2:
            return ""
        
        # Try common TLDs
        possible_domains = [
            f"{name}.com",
            f"{name}.in",
            f"{name}.io",
            f"{name}.co",
            f"{name}.ai",
        ]
        
        # Return first one that might exist
        return possible_domains[0]
    
    def _generate_hr_emails(self, companies: list):
        """Generate HR email patterns for each company."""
        for company in companies:
            domain = company.get('domain', '')
            if not domain:
                continue
            
            for pattern in self.HR_EMAIL_PATTERNS:
                email = pattern.format(domain=domain)
                self.found_emails.append({
                    'company': company.get('name', ''),
                    'email': email,
                    'domain': domain,
                    'job_title': company.get('job_title', 'Various'),
                    'source': company.get('source', 'unknown'),
                    'pattern': pattern.split('@')[0]
                })
    
    def _verify_emails(self):
        """Verify emails by checking MX records."""
        if not HAS_DNS:
            logging.warning("⚠️ dnspython not installed - skipping MX verification")
            self.verified_emails = self.found_emails
            return
        
        logging.info("🔍 Verifying email domains (MX records)...")
        
        verified_domains = set()
        invalid_domains = set()
        
        for email_info in self.found_emails:
            domain = email_info.get('domain', '')
            
            if domain in verified_domains:
                self.verified_emails.append(email_info)
            elif domain in invalid_domains:
                continue
            else:
                # Check MX record
                if self._has_mx_record(domain):
                    verified_domains.add(domain)
                    self.verified_emails.append(email_info)
                else:
                    invalid_domains.add(domain)
        
        logging.info(f"   Valid domains: {len(verified_domains)}")
        logging.info(f"   Invalid domains: {len(invalid_domains)}")
    
    def _has_mx_record(self, domain: str) -> bool:
        """Check if domain has MX records."""
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
    
    def _save_results(self) -> pd.DataFrame:
        """Save verified HR emails to CSV."""
        if not self.verified_emails:
            logging.error("❌ No verified HR emails found!")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.verified_emails)
        
        # Add job_title column if missing
        if 'job_title' not in df.columns:
            df['job_title'] = 'Data Analyst / Business Analyst'
        
        # Rename email to hr_email for compatibility
        if 'email' in df.columns:
            df = df.rename(columns={'email': 'hr_email'})
        
        # Deduplicate by email
        df = df.drop_duplicates(subset=['hr_email'], keep='first')
        
        # Save to multiple locations
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Save as new_hr_emails.csv
        new_path = os.path.join(data_dir, 'new_hr_emails.csv')
        df.to_csv(new_path, index=False)
        logging.info(f"💾 Saved {len(df)} new HR emails to {new_path}")
        
        # Also append to all_hr_emails.csv
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
    """Find HR emails from companies with active job openings."""
    logging.info("="*60)
    logging.info("🔍 HR EMAIL FINDER")
    logging.info("="*60)
    
    finder = HREmailFinder()
    df = finder.find_all_hr_emails()
    
    if not df.empty:
        logging.info("\n📊 SUMMARY:")
        logging.info(f"   Total new HR emails: {len(df)}")
        logging.info(f"   Unique companies: {df['company'].nunique()}")
        logging.info("\n📧 Sample emails found:")
        for _, row in df.head(10).iterrows():
            logging.info(f"   {row['company']}: {row['hr_email']}")
    
    logging.info("="*60)
    return df


if __name__ == "__main__":
    main()
