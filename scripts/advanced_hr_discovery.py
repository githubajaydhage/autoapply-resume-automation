"""
Advanced HR/Recruiter Discovery System
Implements comprehensive web search patterns to grow HR database over time.

Features:
1. HR/Recruiter Profile Discovery (LinkedIn indexed profiles)
2. Company Website HR Email Discovery
3. Email Pattern Extraction from company domains
4. HR Leads from Public Documents (PDF, XLSX, CSV, DOCX)
5. Startup/Hiring Announcements
6. Job Portal Public Profiles
7. Noise Filtering & Email Validation
8. Persistent Database Growth (cumulative data)

Sources:
- DuckDuckGo (bot-friendly)
- Bing (backup search)
- Naukri, Indeed, Wellfound career pages
- Company career pages
"""

import os
import re
import time
import random
import logging
import hashlib
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse
from typing import Dict, List, Optional, Set, Tuple
import json

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AdvancedHRDiscovery:
    """
    Advanced HR/Recruiter discovery system with persistent database growth.
    Implements comprehensive search patterns and stores discovered data.
    """
    
    # Email regex pattern
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Noise filtering - skip these patterns
    NOISE_PATTERNS = [
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'support@', 'sales@', 'admin@', 'info@', 'contact@',
        'newsletter', 'notification', 'unsubscribe', 'feedback',
        'mailer', 'alert@', 'test@', 'example@', 'demo@',
        'webmaster', 'postmaster', 'hostmaster', 'abuse@'
    ]
    
    # HR/Recruiter keywords for filtering
    HR_KEYWORDS = [
        'hr', 'career', 'careers', 'recruit', 'recruiting', 'recruitment',
        'hiring', 'talent', 'jobs', 'job', 'resume', 'apply', 'staffing',
        'people', 'human resources', 'talent acquisition', 'hrbp'
    ]
    
    # Common HR email prefixes
    HR_EMAIL_PREFIXES = [
        'hr', 'careers', 'career', 'recruitment', 'recruiting', 'jobs',
        'job', 'talent', 'hiring', 'people', 'talentacquisition',
        'humanresources', 'staffing', 'resume', 'apply'
    ]
    
    # LinkedIn role patterns for HR discovery
    HR_ROLES = [
        'HR Manager', 'Talent Acquisition', 'Recruiter', 'People Operations',
        'HR Business Partner', 'Human Resources', 'Technical Recruiter',
        'Hiring Manager', 'Recruitment Manager', 'HR Lead', 'HR Director',
        'Campus Recruiter', 'Sourcer', 'People Partner', 'HR Generalist'
    ]
    
    def __init__(self, data_dir: str = 'data'):
        """Initialize the advanced HR discovery system."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Persistent database files
        self.hr_db_file = os.path.join(data_dir, 'discovered_hr_emails.csv')
        self.employees_db_file = os.path.join(data_dir, 'discovered_employees.csv')
        self.companies_db_file = os.path.join(data_dir, 'discovered_companies.csv')
        
        # Load existing data
        self.hr_emails = self._load_hr_database()
        self.employees = self._load_employees_database()
        self.companies = self._load_companies_database()
        
        # Session for requests
        self.session = requests.Session()
        self._update_headers()
        
        # DNS cache for MX validation
        self.dns_cache = {}
        
        # Statistics
        self.stats = {
            'new_hr_emails': 0,
            'new_employees': 0,
            'new_companies': 0,
            'searches_performed': 0
        }
        
        logging.info(f"🔍 Advanced HR Discovery initialized")
        logging.info(f"   📧 Existing HR emails: {len(self.hr_emails)}")
        logging.info(f"   👥 Existing employees: {len(self.employees)}")
        logging.info(f"   🏢 Existing companies: {len(self.companies)}")
    
    def _update_headers(self):
        """Update session headers with random User-Agent."""
        self.session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
        })
    
    def _load_hr_database(self) -> pd.DataFrame:
        """Load existing HR email database."""
        if os.path.exists(self.hr_db_file):
            try:
                return pd.read_csv(self.hr_db_file)
            except Exception as e:
                logging.warning(f"Could not load HR database: {e}")
        
        return pd.DataFrame(columns=[
            'email', 'company', 'domain', 'source', 'search_query',
            'email_type', 'discovered_at', 'verified', 'last_used'
        ])
    
    def _load_employees_database(self) -> pd.DataFrame:
        """Load existing employees database."""
        if os.path.exists(self.employees_db_file):
            try:
                return pd.read_csv(self.employees_db_file)
            except Exception as e:
                logging.warning(f"Could not load employees database: {e}")
        
        return pd.DataFrame(columns=[
            'name', 'company', 'role', 'email', 'linkedin_url',
            'source', 'discovered_at', 'contacted', 'last_contacted'
        ])
    
    def _load_companies_database(self) -> pd.DataFrame:
        """Load existing companies database."""
        if os.path.exists(self.companies_db_file):
            try:
                return pd.read_csv(self.companies_db_file)
            except Exception as e:
                logging.warning(f"Could not load companies database: {e}")
        
        return pd.DataFrame(columns=[
            'company', 'domain', 'career_page', 'email_pattern',
            'hr_emails_found', 'employees_found', 'discovered_at', 'last_updated'
        ])
    
    def _save_databases(self):
        """Save all databases to disk."""
        try:
            self.hr_emails.to_csv(self.hr_db_file, index=False)
            self.employees.to_csv(self.employees_db_file, index=False)
            self.companies.to_csv(self.companies_db_file, index=False)
            logging.info(f"💾 Databases saved - HR: {len(self.hr_emails)}, Employees: {len(self.employees)}, Companies: {len(self.companies)}")
        except Exception as e:
            logging.error(f"Failed to save databases: {e}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format and check against noise patterns."""
        email = email.lower().strip()
        
        # Basic format check
        if not self.EMAIL_REGEX.match(email):
            return False
        
        # Skip noise patterns
        if any(noise in email for noise in self.NOISE_PATTERNS):
            return False
        
        # Skip very long emails (likely errors)
        if len(email) > 60:
            return False
        
        # Skip emails with too many dots
        if email.count('.') > 4:
            return False
        
        return True
    
    def _is_hr_email(self, email: str) -> bool:
        """Check if email is likely an HR/recruitment email."""
        email = email.lower()
        prefix = email.split('@')[0]
        
        return any(kw in prefix for kw in self.HR_EMAIL_PREFIXES)
    
    def _validate_domain_mx(self, domain: str) -> bool:
        """Validate domain has MX records (can receive email)."""
        if not HAS_DNS:
            return True  # Assume valid if no DNS library
        
        if domain in self.dns_cache:
            return self.dns_cache[domain]
        
        try:
            dns.resolver.resolve(domain, 'MX')
            self.dns_cache[domain] = True
            return True
        except Exception:
            self.dns_cache[domain] = False
            return False
    
    def _add_hr_email(self, email: str, company: str, source: str, 
                      query: str = '', email_type: str = 'general'):
        """Add HR email to database if not already present."""
        email = email.lower().strip()
        
        if not self._is_valid_email(email):
            return False
        
        # Check if already exists
        if len(self.hr_emails) > 0 and email in self.hr_emails['email'].values:
            return False
        
        domain = email.split('@')[1] if '@' in email else ''
        
        # Validate domain
        if not self._validate_domain_mx(domain):
            return False
        
        # Add to database
        new_row = pd.DataFrame([{
            'email': email,
            'company': company,
            'domain': domain,
            'source': source,
            'search_query': query,
            'email_type': email_type,
            'discovered_at': datetime.now().isoformat(),
            'verified': False,
            'last_used': ''
        }])
        
        self.hr_emails = pd.concat([self.hr_emails, new_row], ignore_index=True)
        self.stats['new_hr_emails'] += 1
        logging.debug(f"✅ Added HR email: {email} ({company})")
        return True
    
    def _add_employee(self, name: str, company: str, role: str, 
                      email: str = '', linkedin_url: str = '', source: str = ''):
        """Add employee to database if not already present."""
        # Check for duplicates
        if len(self.employees) > 0:
            if email and email in self.employees['email'].values:
                return False
            if linkedin_url and linkedin_url in self.employees['linkedin_url'].values:
                return False
        
        new_row = pd.DataFrame([{
            'name': name,
            'company': company,
            'role': role,
            'email': email,
            'linkedin_url': linkedin_url,
            'source': source,
            'discovered_at': datetime.now().isoformat(),
            'contacted': False,
            'last_contacted': ''
        }])
        
        self.employees = pd.concat([self.employees, new_row], ignore_index=True)
        self.stats['new_employees'] += 1
        logging.debug(f"✅ Added employee: {name} at {company}")
        return True
    
    def _add_company(self, company: str, domain: str = '', career_page: str = '',
                     email_pattern: str = ''):
        """Add company to database if not already present."""
        company_clean = company.lower().strip()
        
        if len(self.companies) > 0:
            if company_clean in self.companies['company'].str.lower().values:
                return False
        
        new_row = pd.DataFrame([{
            'company': company,
            'domain': domain,
            'career_page': career_page,
            'email_pattern': email_pattern,
            'hr_emails_found': 0,
            'employees_found': 0,
            'discovered_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }])
        
        self.companies = pd.concat([self.companies, new_row], ignore_index=True)
        self.stats['new_companies'] += 1
        return True
    
    def _search_duckduckgo(self, query: str) -> str:
        """Perform DuckDuckGo search and return HTML content."""
        try:
            self._update_headers()
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = self.session.get(url, timeout=15)
            time.sleep(random.uniform(1, 2))
            self.stats['searches_performed'] += 1
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logging.debug(f"DuckDuckGo search error: {e}")
        
        return ''
    
    def _search_bing(self, query: str) -> str:
        """Perform Bing search and return HTML content."""
        try:
            self._update_headers()
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            response = self.session.get(url, timeout=15)
            time.sleep(random.uniform(1, 2))
            self.stats['searches_performed'] += 1
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logging.debug(f"Bing search error: {e}")
        
        return ''
    
    # ================================================================
    # SEARCH PATTERN IMPLEMENTATIONS
    # ================================================================
    
    def discover_hr_profiles_linkedin(self, company: str):
        """
        1. HR/Recruiter Profile Discovery (LinkedIn indexed)
        site:linkedin.com/in "HR Manager" "COMPANY_NAME"
        """
        logging.info(f"🔍 Discovering HR profiles at {company} via LinkedIn...")
        
        for role in self.HR_ROLES[:5]:  # Limit to 5 roles per company
            query = f'site:linkedin.com/in "{role}" "{company}" -"no-reply"'
            
            html = self._search_duckduckgo(query)
            if not html:
                html = self._search_bing(query)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract LinkedIn profile URLs and names
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'linkedin.com/in/' in href:
                        # Extract name from link text
                        name = link.get_text().strip()
                        if name and len(name) > 3 and len(name) < 50:
                            self._add_employee(
                                name=name,
                                company=company,
                                role=role,
                                linkedin_url=href,
                                source='linkedin_profile_search'
                            )
                
                # Also extract emails from page
                emails = self.EMAIL_REGEX.findall(soup.get_text())
                for email in emails:
                    if self._is_valid_email(email):
                        self._add_hr_email(email, company, 'linkedin_search', query)
    
    def discover_company_hr_emails(self, company: str, domain: str):
        """
        2. Company Website HR Email Discovery
        site:COMPANY_DOMAIN "hr@" / "careers@" / "recruitment@"
        """
        logging.info(f"🔍 Discovering HR emails from {domain}...")
        
        prefixes = ['hr@', 'careers@', 'recruitment@', 'jobs@', 
                    'talent acquisition', 'people operations']
        
        for prefix in prefixes:
            query = f'site:{domain} "{prefix}" -"no-reply" -"support@" -"sales@"'
            
            html = self._search_duckduckgo(query)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                emails = self.EMAIL_REGEX.findall(soup.get_text())
                
                for email in emails:
                    if self._is_valid_email(email) and domain in email.lower():
                        email_type = 'hr' if self._is_hr_email(email) else 'general'
                        self._add_hr_email(email, company, 'company_site_search', query, email_type)
    
    def discover_email_patterns(self, company: str, domain: str):
        """
        3. HR Email Pattern Extraction
        site:COMPANY_DOMAIN "@COMPANY_DOMAIN" "HR"
        """
        logging.info(f"🔍 Extracting email patterns for {domain}...")
        
        keywords = ['HR', 'Recruiter', 'Talent', 'Hiring', 'Careers']
        
        for keyword in keywords:
            query = f'site:{domain} "@{domain}" "{keyword}"'
            
            html = self._search_duckduckgo(query)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                emails = self.EMAIL_REGEX.findall(soup.get_text())
                
                for email in emails:
                    if self._is_valid_email(email) and domain in email.lower():
                        self._add_hr_email(email, company, 'pattern_extraction', query)
    
    def discover_hr_from_documents(self, company: str, domain: str):
        """
        4. HR Leads from Public Documents
        filetype:pdf "@COMPANY_DOMAIN" "HR"
        """
        logging.info(f"🔍 Searching public documents for {company} HR...")
        
        file_types = ['pdf', 'xlsx', 'docx']
        keywords = ['HR', 'Recruiter', 'Human Resources', 'Talent Acquisition']
        
        for ftype in file_types:
            for keyword in keywords[:2]:  # Limit queries
                query = f'filetype:{ftype} "@{domain}" "{keyword}"'
                
                html = self._search_bing(query)  # Bing is better for filetype search
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    emails = self.EMAIL_REGEX.findall(soup.get_text())
                    
                    for email in emails:
                        if self._is_valid_email(email):
                            self._add_hr_email(email, company, 'document_search', query)
    
    def discover_hiring_announcements(self, company: str):
        """
        5. Startup/Hiring Announcements
        "we are hiring" "HR Manager" "COMPANY_NAME"
        """
        logging.info(f"🔍 Searching hiring announcements for {company}...")
        
        queries = [
            f'"we are hiring" "HR" "{company}"',
            f'"join our team" "recruiter" "{company}"',
            f'"careers at" "{company}" email',
            f'"hiring for" "{company}" contact'
        ]
        
        for query in queries:
            query += ' -"no-reply" -"support@"'
            
            html = self._search_duckduckgo(query)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                emails = self.EMAIL_REGEX.findall(soup.get_text())
                
                for email in emails:
                    if self._is_valid_email(email):
                        self._add_hr_email(email, company, 'hiring_announcement', query)
    
    def discover_job_portal_profiles(self, company: str):
        """
        6. Job Portal Public Profiles
        site:indeed.com "HR Manager" "COMPANY_NAME"
        """
        logging.info(f"🔍 Searching job portals for {company} HR...")
        
        portals = ['indeed.com', 'naukri.com', 'linkedin.com/jobs']
        roles = ['HR Manager', 'Talent Acquisition', 'Recruiter']
        
        for portal in portals:
            for role in roles:
                query = f'site:{portal} "{role}" "{company}"'
                
                html = self._search_duckduckgo(query)
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    emails = self.EMAIL_REGEX.findall(soup.get_text())
                    
                    for email in emails:
                        if self._is_valid_email(email):
                            self._add_hr_email(email, company, 'job_portal_search', query)
    
    def generate_email_patterns(self, company: str, domain: str, first_name: str = '', last_name: str = ''):
        """
        8. Email Pattern Generation (Post-Domain Discovery)
        Generate potential HR email patterns for a known domain.
        """
        patterns = []
        
        # Generic HR patterns (always try these)
        generic_patterns = [
            f'hr@{domain}',
            f'careers@{domain}',
            f'jobs@{domain}',
            f'recruitment@{domain}',
            f'hiring@{domain}',
            f'talent@{domain}',
            f'talentacquisition@{domain}',
            f'humanresources@{domain}',
            f'people@{domain}'
        ]
        
        patterns.extend(generic_patterns)
        
        # Person-specific patterns (if name provided)
        if first_name and last_name:
            first = first_name.lower()
            last = last_name.lower()
            first_initial = first[0] if first else ''
            
            person_patterns = [
                f'{first}.{last}@{domain}',
                f'{first}{last}@{domain}',
                f'{first}@{domain}',
                f'{first_initial}{last}@{domain}',
                f'{first}_{last}@{domain}',
                f'{first}.{last[0]}@{domain}',
                f'{last}.{first}@{domain}'
            ]
            patterns.extend(person_patterns)
        
        # Add patterns to database for validation
        for email in patterns:
            if self._validate_domain_mx(domain):
                self._add_hr_email(email, company, 'pattern_generation', 
                                   f'generated_{domain}', 'generated')
        
        return patterns
    
    # ================================================================
    # MAIN DISCOVERY WORKFLOW
    # ================================================================
    
    def discover_for_company(self, company: str, domain: str = None):
        """Run full discovery workflow for a single company."""
        logging.info(f"\n{'='*60}")
        logging.info(f"🏢 FULL DISCOVERY: {company}")
        logging.info(f"{'='*60}")
        
        # Infer domain if not provided
        if not domain:
            domain = self._infer_domain(company)
        
        if domain:
            self._add_company(company, domain)
        
        # Run all discovery methods
        self.discover_hr_profiles_linkedin(company)
        
        if domain:
            self.discover_company_hr_emails(company, domain)
            self.discover_email_patterns(company, domain)
            self.discover_hr_from_documents(company, domain)
            self.generate_email_patterns(company, domain)
        
        self.discover_hiring_announcements(company)
        self.discover_job_portal_profiles(company)
        
        # Save after each company
        self._save_databases()
    
    def discover_for_job_list(self, jobs_df: pd.DataFrame, max_companies: int = None):
        """Run discovery for companies in a job list.
        
        Args:
            jobs_df: DataFrame with job listings
            max_companies: Max NEW companies to discover (default: from env or 10)
        """
        if 'company' not in jobs_df.columns:
            logging.error("No 'company' column in jobs dataframe")
            return
        
        # Get limit from env or parameter
        if max_companies is None:
            max_companies = int(os.getenv('MAX_DISCOVERY_COMPANIES', '10'))
        
        all_companies = jobs_df['company'].dropna().unique().tolist()
        
        # Get already discovered companies
        already_discovered = set()
        if len(self.companies) > 0:
            already_discovered = set(self.companies['company'].str.lower().tolist())
        
        # Filter to only NEW companies
        new_companies = [c for c in all_companies if c.lower() not in already_discovered]
        
        if len(new_companies) == 0:
            logging.info(f"✅ All {len(all_companies)} companies already in database! Using cached data.")
            return
        
        # Limit to max_companies
        companies_to_discover = new_companies[:max_companies]
        
        logging.info(f"🔍 Discovering {len(companies_to_discover)} NEW companies (of {len(all_companies)} total, {len(already_discovered)} already cached)")
        logging.info(f"⏱️ Estimated time: ~{len(companies_to_discover) * 5} minutes")
        
        for i, company in enumerate(companies_to_discover, 1):
            logging.info(f"[{i}/{len(companies_to_discover)}] Processing {company}...")
            try:
                self.discover_for_company(company)
            except Exception as e:
                logging.error(f"Error discovering {company}: {e}")
                continue
        
        self._print_summary()
    
    def discover_from_keywords(self, keywords: List[str], location: str = 'Bangalore'):
        """Run discovery based on job keywords."""
        logging.info(f"🔍 Keyword-based discovery: {keywords}")
        
        for keyword in keywords[:5]:  # Limit to 5 keywords
            # Search for companies hiring for this role
            query = f'"{keyword}" "{location}" hiring careers email'
            
            html = self._search_duckduckgo(query)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract emails
                emails = self.EMAIL_REGEX.findall(soup.get_text())
                for email in emails:
                    if self._is_valid_email(email):
                        domain = email.split('@')[1]
                        company = domain.split('.')[0].title()
                        self._add_hr_email(email, company, 'keyword_search', query)
        
        self._save_databases()
        self._print_summary()
    
    def _infer_domain(self, company: str) -> Optional[str]:
        """Try to infer company domain from company name."""
        company_clean = re.sub(r'[^a-z0-9\s]', '', company.lower())
        company_slug = company_clean.replace(' ', '')
        
        # Check if we already know this company's domain
        if len(self.companies) > 0:
            match = self.companies[self.companies['company'].str.lower() == company.lower()]
            if len(match) > 0 and match.iloc[0]['domain']:
                return match.iloc[0]['domain']
        
        # Common domain patterns
        potential_domains = [
            f'{company_slug}.com',
            f'{company_slug}.in',
            f'{company_slug}.co.in',
            f'{company_slug}.io'
        ]
        
        # Validate each potential domain
        for domain in potential_domains:
            if self._validate_domain_mx(domain):
                return domain
        
        return None
    
    def _print_summary(self):
        """Print discovery summary."""
        logging.info("\n" + "="*60)
        logging.info("📊 DISCOVERY SUMMARY")
        logging.info("="*60)
        logging.info(f"   🆕 New HR emails discovered: {self.stats['new_hr_emails']}")
        logging.info(f"   🆕 New employees discovered: {self.stats['new_employees']}")
        logging.info(f"   🆕 New companies discovered: {self.stats['new_companies']}")
        logging.info(f"   🔍 Searches performed: {self.stats['searches_performed']}")
        logging.info("="*60)
        logging.info(f"   📧 Total HR emails in DB: {len(self.hr_emails)}")
        logging.info(f"   👥 Total employees in DB: {len(self.employees)}")
        logging.info(f"   🏢 Total companies in DB: {len(self.companies)}")
        logging.info("="*60 + "\n")
    
    def get_hr_emails_df(self) -> pd.DataFrame:
        """Get all discovered HR emails as DataFrame."""
        return self.hr_emails.copy()
    
    def get_employees_df(self) -> pd.DataFrame:
        """Get all discovered employees as DataFrame."""
        return self.employees.copy()
    
    def get_fresh_emails(self, days: int = 7) -> pd.DataFrame:
        """Get recently discovered emails (for prioritization)."""
        if len(self.hr_emails) == 0:
            return pd.DataFrame()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return self.hr_emails[self.hr_emails['discovered_at'] >= cutoff].copy()
    
    def get_unused_emails(self) -> pd.DataFrame:
        """Get emails that haven't been used yet."""
        if len(self.hr_emails) == 0:
            return pd.DataFrame()
        
        return self.hr_emails[self.hr_emails['last_used'] == ''].copy()


def main():
    """Main entry point for HR discovery."""
    logging.info("="*60)
    logging.info("🔍 ADVANCED HR DISCOVERY SYSTEM")
    logging.info("   Growing the HR database with fresh data")
    logging.info("="*60)
    
    discovery = AdvancedHRDiscovery()
    
    # Get job keywords from environment
    keywords_env = os.getenv('JOB_KEYWORDS', '')
    location = os.getenv('TARGET_LOCATION', 'Bangalore')
    
    if keywords_env:
        keywords = [k.strip() for k in keywords_env.split(',')]
        logging.info(f"📋 Keywords from env: {keywords}")
        discovery.discover_from_keywords(keywords, location)
    
    # Load jobs and discover for each company
    jobs_file = os.path.join('data', 'jobs_today.csv')
    if os.path.exists(jobs_file):
        try:
            jobs_df = pd.read_csv(jobs_file)
            if len(jobs_df) > 0:
                discovery.discover_for_job_list(jobs_df)
        except Exception as e:
            logging.error(f"Error loading jobs: {e}")
    
    # Print final stats
    discovery._print_summary()
    
    # Return discovered data for other scripts to use
    return discovery.get_hr_emails_df()


if __name__ == "__main__":
    main()
