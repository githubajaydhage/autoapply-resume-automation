"""
Lead Scraper - Comprehensive HR Lead Generation System
=======================================================
Features:
1. Google Custom Search API / Bing Web Search API integration
2. LinkedIn profile discovery for HR managers
3. Hunter.io API for email pattern detection
4. NeverBounce / ZeroBounce email validation
5. Industry-specific filtering (exclude IT for design roles)
6. Saves validated leads to leads.csv

Required API Keys (set as environment variables):
- GOOGLE_API_KEY & GOOGLE_CSE_ID  (for Google Custom Search)
- BING_API_KEY                    (for Bing Web Search)
- HUNTER_API_KEY                  (for Hunter.io email finder)
- NEVERBOUNCE_API_KEY             (for email validation)
- ZEROBOUNCE_API_KEY              (alternative email validation)
"""

import os
import sys
import re
import json
import time
import random
import logging
import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, quote_plus, urlparse
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class IndustryFilter:
    """Filter companies by industry to target relevant companies only."""
    
    # IT Companies to EXCLUDE for design/non-IT roles
    IT_COMPANIES = {
        'infosys', 'tcs', 'wipro', 'hcl', 'techmahindra', 'tech mahindra',
        'cognizant', 'capgemini', 'accenture', 'mindtree', 'mphasis',
        'ltimindtree', 'hexaware', 'cyient', 'persistent', 'l&t infotech',
        'zensar', 'coforge', 'birlasoft', 'mastek', 'happiest minds',
        'google', 'microsoft', 'amazon', 'meta', 'facebook', 'apple',
        'netflix', 'oracle', 'sap', 'salesforce', 'adobe', 'vmware',
        'cisco', 'intel', 'qualcomm', 'nvidia', 'ibm', 'dell',
        'hp', 'lenovo', 'samsung', 'asus', 'acer',
        'razorpay', 'phonepe', 'paytm', 'cred', 'zerodha', 'groww',
        'swiggy', 'zomato', 'ola', 'uber', 'flipkart', 'myntra',
        'freshworks', 'zoho', 'atlassian', 'github', 'gitlab',
    }
    
    # Interior Design / Architecture related companies - PRIORITIZE these
    DESIGN_COMPANIES = {
        'livspace', 'homelane', 'designcafe', 'design cafe', 'bonito',
        'interior company', 'godrej interio', 'pepperfry', 'urban ladder',
        'wooden street', 'hometown', 'ikea', 'ashley furniture',
        'havells', 'crompton', 'orient electric', 'asian paints',
        'berger paints', 'nippon paint', 'dulux', 'kansai nerolac',
        'sobha', 'brigade', 'prestige', 'godrej properties', 'dlf',
        'lodha', 'oberoi realty', 'mahindra lifespaces', 'tata housing',
        'embassy', 'puravankara', 'salarpuria', 'total environment',
        'shapoorji pallonji', 'hiranandani', 'runwal', 'kalpataru',
        'modular kitchen', 'hafele', 'hettich', 'blum', 'ebco',
        'greenlaminate', 'century ply', 'kitply', 'virgo',
        'kohler', 'jaquar', 'hindware', 'parryware', 'cera',
        'sleek', 'wurfel', 'aristo', 'hacker', 'schmidt',
    }
    
    # Architecture firms
    ARCHITECTURE_FIRMS = {
        'dsa', 'hafeez contractor', 'morphogenesis', 'studio lotus',
        'anagram architects', 'khosla associates', 'mindspackle',
        'sanjay puri architects', 'spasm design', 'malik architecture',
        'edifice consultants', 'cma', 'hundredhands', 'venkataramanan',
        'larsen & toubro', 'jacobs', 'aecom', 'gensler', 'hok',
        'perkins&will', 'som', 'foster', 'zaha hadid', 'bjarke ingels',
    }
    
    def __init__(self, exclude_it: bool = True, target_industry: str = 'interior_design'):
        self.exclude_it = exclude_it
        self.target_industry = target_industry
    
    def should_include(self, company_name: str) -> Tuple[bool, str]:
        """Check if company should be included based on industry filters."""
        if not company_name:
            return True, "unknown"
        
        company_lower = company_name.lower().strip()
        
        # Always include design/architecture companies
        for design_co in self.DESIGN_COMPANIES | self.ARCHITECTURE_FIRMS:
            if design_co in company_lower or company_lower in design_co:
                return True, "design_company"
        
        # Exclude IT companies if flag is set
        if self.exclude_it:
            for it_co in self.IT_COMPANIES:
                if it_co in company_lower or company_lower in it_co:
                    return False, "it_company_excluded"
        
        return True, "general"


class GoogleSearchAPI:
    """Google Custom Search API for finding HR contacts using bot-friendly query templates."""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY', '')
        self.cse_id = os.getenv('GOOGLE_CSE_ID', '')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Job opening discovery templates - to find companies actively hiring
        self.job_opening_templates = [
            '"hiring {role}" "{location}" -"no longer" -"closed"',
            '"we are hiring" "{role}" "{location}"',
            '"job opening" "{role}" "{location}"',
            '"now hiring" "{role}" "{location}"',
            '"careers" "{role}" "apply now" "{location}"',
            'site:naukri.com "{role}" "{location}"',
            'site:indeed.com "{role}" "{location}"',
            'site:linkedin.com/jobs "{role}" "{location}"',
        ]
        
        # Company extraction from job postings
        self.company_discovery_templates = [
            '"{role}" jobs "{location}" company',
            '"{role}" opportunities "{location}" "join our team"',
            '"{role}" vacancy "{location}" "company name"',
        ]
        
        # HR/Recruiter Profile Discovery (Open Web Indexed)
        self.hr_profile_templates = [
            'site:linkedin.com/in "HR Manager" "{company}"',
            'site:linkedin.com/in "Talent Acquisition" "{company}"',
            'site:linkedin.com/in "Recruiter" "{company}"',
            'site:linkedin.com/in "People Operations" "{company}"',
            'site:linkedin.com/in "HR Business Partner" "{company}"',
        ]
        
        self.company_email_templates = [
            'site:{domain} "hr@"',
            'site:{domain} "careers@"',
            'site:{domain} "recruitment@"',
            'site:{domain} "jobs@"',
            'site:{domain} "talent acquisition"',
            'site:{domain} "people operations"',
        ]
        
        self.email_pattern_templates = [
            'site:{domain} "@{domain}" "HR"',
            'site:{domain} "@{domain}" "Recruiter"',
            'site:{domain} "@{domain}" "Talent"',
        ]
        
        self.document_templates = [
            'filetype:pdf "@{domain}" "HR"',
            'filetype:xlsx "@{domain}" "Recruiter"',
            'filetype:csv "@{domain}" "Human Resources"',
            'filetype:docx "@{domain}" "Talent Acquisition"',
        ]
        
        self.hiring_announcement_templates = [
            '"we are hiring" "HR Manager" "{company}"',
            '"join our team" "Recruiter" "{company}"',
            '"careers at" "{company}" email',
        ]
        
        self.job_portal_templates = [
            'site:indeed.com "HR Manager" "{company}"',
            'site:naukri.com "Talent Acquisition" "{company}"',
            'site:wellfound.com "Recruiter" "{company}"',
        ]
        
        # Noise filtering suffix
        self.noise_filter = ' -"no-reply" -"support@" -"sales@" -"admin@"'
        
    def is_configured(self) -> bool:
        return bool(self.api_key and self.cse_id)
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Execute Google Custom Search and return results."""
        if not self.is_configured():
            logging.warning("Google Custom Search API not configured")
            return []
        
        try:
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': min(num_results, 10)  # API max is 10 per request
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                logging.error(f"Google API error: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Google search error: {e}")
            return []
    
    def discover_hiring_companies(self, role: str, location: str = "Bangalore") -> List[Dict]:
        """Discover companies that are actively hiring for a specific role."""
        results = []
        
        # Search for job openings
        for template in self.job_opening_templates:
            query = template.format(role=role, location=location) + self.noise_filter
            search_results = self.search(query, num_results=10)
            results.extend(search_results)
            time.sleep(0.5)
        
        # Search for company-specific hiring announcements
        for template in self.company_discovery_templates:
            query = template.format(role=role, location=location) + self.noise_filter
            search_results = self.search(query, num_results=10)
            results.extend(search_results)
            time.sleep(0.5)
        
        return results
    
    def search_hr_profiles(self, company: str) -> List[Dict]:
        """Search for HR Manager LinkedIn profiles at a company using dynamic templates."""
        results = []
        
        for template in self.hr_profile_templates:
            query = template.format(company=company) + self.noise_filter
            search_results = self.search(query, num_results=5)
            results.extend(search_results)
            time.sleep(0.5)  # Rate limiting
        
        return results
    
    def search_company_emails_by_domain(self, domain: str) -> List[Dict]:
        """Search for company HR emails by domain using multiple query patterns."""
        results = []
        
        # Company website email discovery
        for template in self.company_email_templates:
            query = template.format(domain=domain) + self.noise_filter
            search_results = self.search(query, num_results=5)
            results.extend(search_results)
            time.sleep(0.5)
        
        # Email pattern extraction
        for template in self.email_pattern_templates:
            query = template.format(domain=domain) + self.noise_filter
            search_results = self.search(query, num_results=5)
            results.extend(search_results)
            time.sleep(0.5)
        
        # Document-based email discovery
        for template in self.document_templates[:2]:  # Limit to avoid quota
            query = template.format(domain=domain) + self.noise_filter
            search_results = self.search(query, num_results=3)
            results.extend(search_results)
            time.sleep(0.5)
        
        return results
    
    def search_hiring_announcements(self, company: str) -> List[Dict]:
        """Search for hiring announcements that might contain HR contact info."""
        results = []
        
        for template in self.hiring_announcement_templates:
            query = template.format(company=company) + self.noise_filter
            search_results = self.search(query, num_results=5)
            results.extend(search_results)
            time.sleep(0.5)
        
        return results
    
    def search_job_portal_profiles(self, company: str) -> List[Dict]:
        """Search for HR profiles on job portals."""
        results = []
        
        for template in self.job_portal_templates:
            query = template.format(company=company) + self.noise_filter
            search_results = self.search(query, num_results=3)
            results.extend(search_results)
            time.sleep(0.5)
        
        return results
    
    def search_company_emails(self, company: str, domain: str = None) -> List[Dict]:
        """Search for company career/HR email addresses using dynamic templates."""
        results = []
        
        if domain:
            # Use domain-specific searches
            results.extend(self.search_company_emails_by_domain(domain))
        else:
            # Use company name searches
            queries = [
                f'"{company}" careers email contact hr' + self.noise_filter,
                f'"{company}" recruitment email apply' + self.noise_filter,
                f'"{company}" "hr@" OR "careers@"' + self.noise_filter,
            ]
            
            for query in queries:
                search_results = self.search(query, num_results=5)
                results.extend(search_results)
                time.sleep(0.5)
        
        return results


class BingSearchAPI:
    """Bing Web Search API for finding HR contacts using bot-friendly query templates."""
    
    def __init__(self):
        self.api_key = os.getenv('BING_API_KEY', '')
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        
        # Job opening discovery templates
        self.job_opening_templates = [
            '"hiring {role}" "{location}" -"no longer" -"closed"',
            '"we are hiring" "{role}" "{location}"',
            '"job opening" "{role}" "{location}"',
            '"now hiring" "{role}" "{location}"',
            'site:naukri.com "{role}" "{location}"',
            'site:indeed.com "{role}" "{location}"',
        ]
        
        # Bot-friendly search query templates (same as Google)
        self.hr_profile_templates = [
            'site:linkedin.com/in "HR Manager" "{company}"',
            'site:linkedin.com/in "Talent Acquisition" "{company}"',
            'site:linkedin.com/in "Recruiter" "{company}"',
            'site:linkedin.com/in "People Operations" "{company}"',
        ]
        
        self.company_search_templates = [
            '"{company}" "hr@" OR "careers@" OR "recruitment@"',
            '"{company}" hiring email contact',
            '"{company}" "join our team" email',
            'site:{domain} "@{domain}" "HR"' if '{domain}' in '{company}' else '"{company}" email HR',
        ]
        
        # Noise filtering suffix
        self.noise_filter = ' -"no-reply" -"support@" -"sales@" -"admin@"'
        
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def search(self, query: str, count: int = 10) -> List[Dict]:
        """Execute Bing search and return results."""
        if not self.is_configured():
            logging.warning("Bing Search API not configured")
            return []
        
        try:
            headers = {'Ocp-Apim-Subscription-Key': self.api_key}
            params = {'q': query, 'count': count, 'mkt': 'en-IN'}
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('webPages', {}).get('value', [])
            else:
                logging.error(f"Bing API error: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Bing search error: {e}")
            return []
    
    def discover_hiring_companies_bing(self, role: str, location: str = "Bangalore") -> List[Dict]:
        """Discover companies hiring for a role using Bing search."""
        results = []
        
        for template in self.job_opening_templates:
            query = template.format(role=role, location=location) + self.noise_filter
            search_results = self.search(query, count=8)
            results.extend(search_results)
            time.sleep(0.3)
        
        return results
    
    def search_hr_emails(self, keywords: List[str], location: str = "Bangalore") -> List[Dict]:
        """Search for HR contacts based on job keywords using dynamic templates."""
        results = []
        
        for keyword in keywords[:3]:  # Limit queries
            # Company-focused searches
            company_queries = [
                f'"{keyword}" company "{location}" careers email' + self.noise_filter,
                f'"{keyword}" hiring email contact bangalore' + self.noise_filter,
                f'"{keyword}" "we are hiring" HR Manager' + self.noise_filter,
            ]
            
            # LinkedIn HR profile searches
            for template in self.hr_profile_templates:
                linkedin_query = template.format(company=f'{keyword} {location}') + self.noise_filter
                company_queries.append(linkedin_query)
            
            for query in company_queries:
                search_results = self.search(query, count=5)
                results.extend(search_results)
                time.sleep(0.3)
        
        return results
    
    def search_company_by_domain(self, domain: str) -> List[Dict]:
        """Search for HR emails by company domain using multiple query patterns."""
        results = []
        
        domain_queries = [
            f'site:{domain} "hr@" OR "careers@" OR "recruitment@"' + self.noise_filter,
            f'site:{domain} "@{domain}" "HR" OR "Talent"' + self.noise_filter,
            f'"@{domain}" "Human Resources" OR "Recruiter"' + self.noise_filter,
        ]
        
        for query in domain_queries:
            search_results = self.search(query, count=5)
            results.extend(search_results)
            time.sleep(0.3)
        
        return results


class HunterIOAPI:
    """Hunter.io API for finding and verifying email patterns."""
    
    def __init__(self):
        self.api_key = os.getenv('HUNTER_API_KEY', '')
        self.base_url = "https://api.hunter.io/v2"
        
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def domain_search(self, domain: str) -> Dict:
        """Find emails associated with a domain."""
        if not self.is_configured():
            return {}
        
        try:
            url = f"{self.base_url}/domain-search"
            params = {
                'domain': domain,
                'api_key': self.api_key,
                'type': 'personal',  # personal emails, not generic
                'limit': 10
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json().get('data', {})
            else:
                logging.debug(f"Hunter API error for {domain}: {response.status_code}")
                return {}
                
        except Exception as e:
            logging.debug(f"Hunter API error: {e}")
            return {}
    
    def email_finder(self, domain: str, first_name: str = None, last_name: str = None) -> Dict:
        """Find email for a specific person at a company."""
        if not self.is_configured():
            return {}
        
        try:
            url = f"{self.base_url}/email-finder"
            params = {
                'domain': domain,
                'api_key': self.api_key
            }
            
            if first_name:
                params['first_name'] = first_name
            if last_name:
                params['last_name'] = last_name
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json().get('data', {})
            return {}
            
        except Exception as e:
            logging.debug(f"Hunter email finder error: {e}")
            return {}
    
    def verify_email(self, email: str) -> Dict:
        """Verify if an email is valid using Hunter.io."""
        if not self.is_configured():
            return {'result': 'unknown', 'score': 0}
        
        try:
            url = f"{self.base_url}/email-verifier"
            params = {'email': email, 'api_key': self.api_key}
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json().get('data', {})
            return {'result': 'unknown', 'score': 0}
            
        except Exception as e:
            logging.debug(f"Hunter verify error: {e}")
            return {'result': 'unknown', 'score': 0}
    
    def generate_hr_emails(self, domain: str, patterns: List[str] = None) -> List[str]:
        """Generate potential HR email candidates for a domain using comprehensive patterns."""
        if not patterns:
            # Comprehensive email pattern templates based on best practices
            patterns = [
                # Standard HR emails
                'hr@{domain}',
                'careers@{domain}',
                'recruitment@{domain}',
                'jobs@{domain}',
                'hiring@{domain}',
                'talent@{domain}',
                'people@{domain}',
                
                # Regional variations (India-specific)
                'hr.india@{domain}',
                'careers.india@{domain}',
                'india.hr@{domain}',
                'india.careers@{domain}',
                'bangalore.hr@{domain}',
                'blr.careers@{domain}',
                
                # Department-specific
                'humanresources@{domain}',
                'talentacquisition@{domain}',
                'peopleoperations@{domain}',
                'recruiting@{domain}',
                'staffing@{domain}',
                
                # Common name patterns (placeholder for discovered names)
                # These would be dynamically generated based on discovered names
                'firstname.lastname@{domain}',
                'first.last@{domain}',
                'firstname@{domain}',
                'flastname@{domain}',  # first initial + last name
            ]
        
        emails = []
        for pattern in patterns:
            email = pattern.format(domain=domain)
            emails.append(email)
        
        return emails
    
    def generate_name_based_emails(self, domain: str, first_names: List[str], last_names: List[str]) -> List[str]:
        """Generate name-based email patterns from discovered HR names."""
        emails = []
        name_patterns = [
            '{first}.{last}@{domain}',
            '{first}{last}@{domain}',
            '{first}@{domain}',
            '{first_initial}{last}@{domain}',
            '{first}_{last}@{domain}',
            '{last}.{first}@{domain}',
        ]
        
        for first in first_names[:3]:  # Limit combinations
            for last in last_names[:3]:
                for pattern in name_patterns:
                    email = pattern.format(
                        first=first.lower(),
                        last=last.lower(),
                        first_initial=first[0].lower(),
                        domain=domain
                    )
                    emails.append(email)
        
        return list(set(emails))  # Remove duplicates


class EmailValidator:
    """Email validation using NeverBounce or ZeroBounce API."""
    
    def __init__(self):
        self.neverbounce_key = os.getenv('NEVERBOUNCE_API_KEY', '')
        self.zerobounce_key = os.getenv('ZEROBOUNCE_API_KEY', '')
        
    def is_configured(self) -> bool:
        return bool(self.neverbounce_key or self.zerobounce_key)
    
    def validate_neverbounce(self, email: str) -> Dict:
        """Validate email using NeverBounce API."""
        if not self.neverbounce_key:
            return {'result': 'unknown'}
        
        try:
            url = "https://api.neverbounce.com/v4/single/check"
            params = {
                'key': self.neverbounce_key,
                'email': email
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # NeverBounce results: valid, invalid, disposable, catchall, unknown
                return {
                    'result': data.get('result', 'unknown'),
                    'is_valid': data.get('result') == 'valid',
                    'flags': data.get('flags', [])
                }
            return {'result': 'unknown', 'is_valid': False}
            
        except Exception as e:
            logging.debug(f"NeverBounce error: {e}")
            return {'result': 'error', 'is_valid': False}
    
    def validate_zerobounce(self, email: str) -> Dict:
        """Validate email using ZeroBounce API."""
        if not self.zerobounce_key:
            return {'status': 'unknown'}
        
        try:
            url = "https://api.zerobounce.net/v2/validate"
            params = {
                'api_key': self.zerobounce_key,
                'email': email
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # ZeroBounce statuses: valid, invalid, catch-all, unknown, spamtrap, abuse, do_not_mail
                return {
                    'status': data.get('status', 'unknown'),
                    'is_valid': data.get('status') == 'valid',
                    'sub_status': data.get('sub_status', ''),
                    'domain_age_days': data.get('domain_age_days', 0),
                    'firstname': data.get('firstname', ''),
                    'lastname': data.get('lastname', ''),
                }
            return {'status': 'unknown', 'is_valid': False}
            
        except Exception as e:
            logging.debug(f"ZeroBounce error: {e}")
            return {'status': 'error', 'is_valid': False}
    
    def validate(self, email: str) -> Dict:
        """Validate email using available API (preference: NeverBounce > ZeroBounce)."""
        if self.neverbounce_key:
            return self.validate_neverbounce(email)
        elif self.zerobounce_key:
            return self.validate_zerobounce(email)
        else:
            # Fallback: basic syntax validation
            return self.basic_validate(email)
    
    def basic_validate(self, email: str) -> Dict:
        """Basic email validation without API."""
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        is_valid = bool(email_regex.match(email))
        
        # Skip known bad patterns
        bad_patterns = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon', 'postmaster']
        for pattern in bad_patterns:
            if pattern in email.lower():
                is_valid = False
                break
        
        return {
            'result': 'valid' if is_valid else 'invalid',
            'is_valid': is_valid,
            'method': 'basic_regex'
        }


class LeadScraper:
    """
    Main Lead Scraper - Orchestrates all API calls to find and validate HR leads.
    
    Flow:
    1. Search web using Google/Bing APIs for HR contacts
    2. Extract company domains from results
    3. Use Hunter.io to find email patterns
    4. Generate HR email candidates
    5. Validate emails using NeverBounce/ZeroBounce
    6. Save valid leads to leads.csv
    """
    
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    def __init__(self, exclude_it: bool = True):
        """Initialize the lead scraper.
        
        Args:
            exclude_it: If True, exclude IT companies (for design/non-IT roles)
        """
        self.google_api = GoogleSearchAPI()
        self.bing_api = BingSearchAPI()
        self.hunter_api = HunterIOAPI()
        self.email_validator = EmailValidator()
        self.industry_filter = IndustryFilter(exclude_it=exclude_it)
        
        # Session for web scraping fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Output paths
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.leads_path = os.path.join(self.data_dir, 'leads.csv')
        
        # Leads storage
        self.leads = []
        
        # Stats
        self.stats = {
            'domains_discovered': 0,
            'emails_found': 0,
            'emails_validated': 0,
            'emails_valid': 0,
            'it_companies_skipped': 0
        }
        
        logging.info("="*60)
        logging.info("🔍 LEAD SCRAPER - HR Lead Generation System")
        logging.info("="*60)
        logging.info(f"   Google API: {'✅ Configured' if self.google_api.is_configured() else '❌ Not configured'}")
        logging.info(f"   Bing API: {'✅ Configured' if self.bing_api.is_configured() else '❌ Not configured'}")
        logging.info(f"   Hunter.io: {'✅ Configured' if self.hunter_api.is_configured() else '❌ Not configured'}")
        logging.info(f"   Email Validator: {'✅ Configured' if self.email_validator.is_configured() else '⚠️ Basic validation only'}")
        logging.info(f"   Exclude IT Companies: {'✅ Yes' if exclude_it else '❌ No'}")
        logging.info("="*60)
    
    def extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if domain else None
        except:
            return None
    
    def extract_company_from_snippet(self, snippet: str, title: str) -> Optional[str]:
        """Extract company name from search result snippet or title."""
        import re
        
        text = f"{title} {snippet}".lower()
        
        # Common patterns to extract company names
        company_patterns = [
            r'at ([A-Z][a-zA-Z\s&]+?)(?:\s+is|\s+in|\s+-|\.|,)',
            r'([A-Z][a-zA-Z\s&]+?)(?:\s+is\s+hiring|\s+jobs|\s+careers)',
            r'join\s+([A-Z][a-zA-Z\s&]+?)(?:\s+as|\s+team|\.|,)',
            r'([A-Z][a-zA-Z\s&]+?)\s+(?:pvt\s+ltd|private\s+limited|ltd|inc|corp)',
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                company = match.group(1).strip().title()
                if len(company) > 2 and company not in ['Job', 'Jobs', 'Career', 'Careers', 'Apply', 'Hiring']:
                    return company
        
        return None
    
    def extract_company_from_snippet(self, snippet: str, title: str) -> Optional[str]:
        """Extract company name from search result snippet or title."""
        import re
        
        text = f"{title} {snippet}".lower()
        
        # Common patterns to extract company names
        company_patterns = [
            r'at ([A-Z][a-zA-Z\s&]+?)(?:\s+is|\s+in|\s+-|\.|,)',
            r'([A-Z][a-zA-Z\s&]+?)(?:\s+is\s+hiring|\s+jobs|\s+careers)',
            r'join\s+([A-Z][a-zA-Z\s&]+?)(?:\s+as|\s+team|\.|,)',
            r'([A-Z][a-zA-Z\s&]+?)\s+(?:pvt\s+ltd|private\s+limited|ltd|inc|corp)',
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                company = match.group(1).strip().title()
                if len(company) > 2 and company not in ['Job', 'Jobs', 'Career', 'Careers', 'Apply', 'Hiring']:
                    return company
        
        return None
    
    def extract_emails_from_text(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        emails = self.EMAIL_REGEX.findall(text)
        # Filter out image files and obvious non-emails
        valid_emails = []
        for email in emails:
            if not any(ext in email.lower() for ext in ['.png', '.jpg', '.gif', '.svg', '.css', '.js']):
                valid_emails.append(email.lower())
        return list(set(valid_emails))
    
    def scrape_page_for_emails(self, url: str) -> List[str]:
        """Scrape a webpage for email addresses."""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get all text
                page_text = soup.get_text()
                
                # Also check mailto links
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
                for link in mailto_links:
                    href = link.get('href', '')
                    email = href.replace('mailto:', '').split('?')[0]
                    if email:
                        page_text += f" {email}"
                
                return self.extract_emails_from_text(page_text)
        except Exception as e:
            logging.debug(f"Error scraping {url}: {e}")
        
        return []
    
    def search_leads_google(self, keywords: List[str], location: str = "Bangalore") -> List[Dict]:
        """Search for leads by first discovering companies with active job openings."""
        if not self.google_api.is_configured():
            logging.info("   ⚠️ Google API not configured, skipping...")
            return []
        
        logging.info("   🔍 Discovering companies with active job openings via Google...")
        leads = []
        discovered_companies = set()
        
        # Step 1: Discover companies that are actively hiring for these roles
        for keyword in keywords[:3]:  # Focus on top 3 keywords
            job_results = self.google_api.discover_hiring_companies(keyword, location)
            
            for result in job_results:
                url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                domain = self.extract_domain(url)
                
                # Extract company name from snippet/title
                company_name = self.extract_company_from_snippet(snippet, title)
                if not company_name and domain:
                    company_name = domain.replace('.com', '').replace('.in', '').title()
                
                if company_name:
                    discovered_companies.add(company_name)
                
                leads.append({
                    'source': 'google_job_discovery',
                    'keyword': keyword,
                    'company': company_name,
                    'domain': domain,
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        
        logging.info(f"   📊 Discovered {len(discovered_companies)} companies: {list(discovered_companies)[:10]}...")
        
        # Step 2: For each discovered company, search for HR contacts
        for company in list(discovered_companies)[:10]:  # Limit to top 10 companies
            # Search for HR profiles at this company
            hr_profiles = self.google_api.search_hr_profiles(company)
            for result in hr_profiles:
                leads.append({
                    'source': 'google_linkedin_hr',
                    'company': company,
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })
            
            # Search for company emails
            domain = None
            for lead in leads:
                if lead.get('company') == company and lead.get('domain'):
                    domain = lead.get('domain')
                    break
            
            if domain:
                email_results = self.google_api.search_company_emails_by_domain(domain)
                for result in email_results:
                    leads.append({
                        'source': 'google_company_emails',
                        'company': company,
                        'domain': domain,
                        'title': result.get('title', ''),
                        'url': result.get('link', ''),
                        'snippet': result.get('snippet', '')
                    })
            
            time.sleep(0.3)  # Rate limiting
        
        logging.info(f"   ✅ Found {len(leads)} leads from Google (companies + HR contacts)")
        return leads
    
    def search_leads_bing(self, keywords: List[str], location: str = "Bangalore") -> List[Dict]:
        """Search for leads by discovering companies with active openings via Bing."""
        if not self.bing_api.is_configured():
            logging.info("   ⚠️ Bing API not configured, skipping...")
            return []
        
        logging.info("   🔍 Discovering hiring companies via Bing Web Search...")
        leads = []
        discovered_companies = set()
        
        # Step 1: Discover companies with active job openings
        for keyword in keywords[:3]:
            job_results = self.bing_api.discover_hiring_companies_bing(keyword, location)
            
            for result in job_results:
                url = result.get('url', '')
                title = result.get('name', '')
                snippet = result.get('snippet', '')
                domain = self.extract_domain(url)
                
                # Extract company name
                company_name = self.extract_company_from_snippet(snippet, title)
                if not company_name and domain:
                    company_name = domain.replace('.com', '').replace('.in', '').title()
                
                if company_name:
                    discovered_companies.add(company_name)
                
                leads.append({
                    'source': 'bing_job_discovery',
                    'keyword': keyword,
                    'company': company_name,
                    'domain': domain,
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        
        logging.info(f"   📊 Discovered {len(discovered_companies)} companies via Bing")
        
        # Step 2: Search for HR contacts at discovered companies
        for company in list(discovered_companies)[:8]:  # Limit to 8 companies
            # Find domain for this company
            domain = None
            for lead in leads:
                if lead.get('company') == company and lead.get('domain'):
                    domain = lead.get('domain')
                    break
            
            if domain:
                # Search for HR emails by domain
                domain_results = self.bing_api.search_company_by_domain(domain)
                for result in domain_results:
                    leads.append({
                        'source': 'bing_hr_emails',
                        'company': company,
                        'domain': domain,
                        'title': result.get('name', ''),
                        'url': result.get('url', ''),
                        'snippet': result.get('snippet', '')
                    })
            
            time.sleep(0.3)
        
        logging.info(f"   ✅ Found {len(leads)} leads from Bing (companies + HR contacts)")
        return leads
    
    def enrich_with_hunter(self, domains: List[str]) -> Dict[str, List[Dict]]:
        """Use Hunter.io to find emails for domains."""
        if not self.hunter_api.is_configured():
            logging.info("   ⚠️ Hunter.io not configured, generating pattern-based emails...")
            return self._generate_pattern_emails(domains)
        
        logging.info(f"   🔍 Enriching {len(domains)} domains with Hunter.io...")
        
        domain_emails = {}
        
        for domain in domains[:20]:  # Limit API calls
            result = self.hunter_api.domain_search(domain)
            
            if result:
                emails = result.get('emails', [])
                pattern = result.get('pattern', '')
                
                domain_emails[domain] = {
                    'pattern': pattern,
                    'emails': [e.get('value') for e in emails if e.get('value')],
                    'organization': result.get('organization', ''),
                }
                
                self.stats['emails_found'] += len(emails)
            
            time.sleep(0.5)  # Rate limiting
        
        logging.info(f"   ✅ Found emails for {len(domain_emails)} domains")
        return domain_emails
    
    def _generate_pattern_emails(self, domains: List[str]) -> Dict[str, List[Dict]]:
        """Generate pattern-based HR emails when Hunter.io is not available."""
        domain_emails = {}
        
        for domain in domains:
            emails = self.hunter_api.generate_hr_emails(domain)
            domain_emails[domain] = {
                'pattern': 'generated',
                'emails': emails,
                'organization': ''
            }
            self.stats['emails_found'] += len(emails)
        
        return domain_emails
    
    def validate_emails(self, emails: List[str]) -> List[Dict]:
        """Validate a list of emails and return valid ones."""
        logging.info(f"   🔍 Validating {len(emails)} emails...")
        
        valid_leads = []
        
        for email in emails:
            self.stats['emails_validated'] += 1
            
            result = self.email_validator.validate(email)
            
            if result.get('is_valid', False) or result.get('result') == 'valid' or result.get('status') == 'valid':
                self.stats['emails_valid'] += 1
                valid_leads.append({
                    'email': email,
                    'validation_result': result
                })
            
            # Small delay for API rate limiting
            if self.email_validator.is_configured():
                time.sleep(0.3)
        
        logging.info(f"   ✅ {self.stats['emails_valid']} valid emails found")
        return valid_leads
    
    def scrape_leads(self, keywords: List[str] = None, location: str = "Bangalore", max_leads: int = 50) -> pd.DataFrame:
        """
        Main method to scrape leads.
        
        Args:
            keywords: Job keywords to search for (from JOB_KEYWORDS env var if not provided)
            location: Job location
            max_leads: Maximum number of leads to find
        
        Returns:
            DataFrame with validated leads
        """
        # Get keywords from environment if not provided (REQUIRED for targeted results)
        if not keywords:
            keywords_env = os.getenv('JOB_KEYWORDS', '')
            if keywords_env:
                keywords = [k.strip() for k in keywords_env.split(',')]
            else:
                # Generic fallback - workflow MUST provide JOB_KEYWORDS
                logging.warning("⚠️ JOB_KEYWORDS not set! Using generic search terms.")
                keywords = ['jobs', 'careers', 'hiring']
        
        logging.info(f"🎯 Scraping leads for: {', '.join(keywords[:5])}")
        logging.info(f"📍 Location: {location}")
        logging.info("")
        
        all_leads = []
        discovered_domains = set()
        discovered_emails = set()
        
        # Step 1: Search using available APIs
        logging.info("📡 STEP 1: Web Search for HR Contacts")
        logging.info("-" * 40)
        
        google_leads = self.search_leads_google(keywords, location)
        all_leads.extend(google_leads)
        
        bing_leads = self.search_leads_bing(keywords, location)
        all_leads.extend(bing_leads)
        
        # Step 2: Extract domains
        logging.info("")
        logging.info("🔗 STEP 2: Extract Company Domains")
        logging.info("-" * 40)
        
        for lead in all_leads:
            domain = lead.get('domain')
            if not domain and lead.get('url'):
                domain = self.extract_domain(lead['url'])
            
            if domain and domain not in discovered_domains:
                # Apply industry filter
                company_name = lead.get('title', domain)
                include, reason = self.industry_filter.should_include(company_name)
                
                if include:
                    discovered_domains.add(domain)
                    self.stats['domains_discovered'] += 1
                else:
                    self.stats['it_companies_skipped'] += 1
                    logging.debug(f"   ⏭️ Skipped {domain} ({reason})")
        
        logging.info(f"   ✅ Discovered {len(discovered_domains)} relevant domains")
        logging.info(f"   ⏭️ Skipped {self.stats['it_companies_skipped']} IT companies")
        
        # Step 3: Find emails using Hunter.io
        logging.info("")
        logging.info("📧 STEP 3: Find HR Emails (Hunter.io)")
        logging.info("-" * 40)
        
        domain_emails = self.enrich_with_hunter(list(discovered_domains)[:30])
        
        # Step 4: Also extract emails from snippets/pages
        logging.info("")
        logging.info("🔍 STEP 4: Extract Emails from Search Results")
        logging.info("-" * 40)
        
        for lead in all_leads:
            snippet = lead.get('snippet', '')
            emails = self.extract_emails_from_text(snippet)
            for email in emails:
                discovered_emails.add(email)
        
        # Add Hunter.io emails
        for domain, data in domain_emails.items():
            for email in data.get('emails', []):
                discovered_emails.add(email)
        
        logging.info(f"   ✅ Total unique emails found: {len(discovered_emails)}")
        
        # Step 5: Validate emails
        logging.info("")
        logging.info("✅ STEP 5: Validate Emails")
        logging.info("-" * 40)
        
        valid_leads = self.validate_emails(list(discovered_emails)[:max_leads])
        
        # Step 6: Prepare output
        logging.info("")
        logging.info("💾 STEP 6: Save Valid Leads")
        logging.info("-" * 40)
        
        leads_data = []
        for lead in valid_leads:
            email = lead['email']
            domain = email.split('@')[1] if '@' in email else ''
            
            leads_data.append({
                'company_name': domain_emails.get(domain, {}).get('organization', domain),
                'domain': domain,
                'email': email,
                'source': 'lead_scraper',
                'validation_status': lead.get('validation_result', {}).get('result', 'valid'),
                'discovered_at': datetime.now().isoformat()
            })
        
        # Create DataFrame
        df = pd.DataFrame(leads_data)
        
        # Save to CSV
        if not df.empty:
            if os.path.exists(self.leads_path):
                existing_df = pd.read_csv(self.leads_path)
                df = pd.concat([existing_df, df], ignore_index=True)
                df = df.drop_duplicates(subset=['email'], keep='last')
            
            df.to_csv(self.leads_path, index=False)
            logging.info(f"   ✅ Saved {len(leads_data)} leads to {self.leads_path}")
        
        # Print summary
        logging.info("")
        logging.info("="*60)
        logging.info("📊 LEAD SCRAPING SUMMARY")
        logging.info("="*60)
        logging.info(f"   Domains discovered: {self.stats['domains_discovered']}")
        logging.info(f"   IT companies skipped: {self.stats['it_companies_skipped']}")
        logging.info(f"   Emails found: {self.stats['emails_found']}")
        logging.info(f"   Emails validated: {self.stats['emails_validated']}")
        logging.info(f"   Valid emails: {self.stats['emails_valid']}")
        logging.info(f"   Leads saved: {len(leads_data)}")
        logging.info("="*60)
        
        return df


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lead Scraper - Find HR contacts for job applications')
    parser.add_argument('--keywords', '-k', type=str, help='Comma-separated job keywords')
    parser.add_argument('--location', '-l', type=str, default='Bangalore', help='Job location')
    parser.add_argument('--max-leads', '-m', type=int, default=50, help='Maximum leads to find')
    parser.add_argument('--include-it', action='store_true', help='Include IT companies')
    
    args = parser.parse_args()
    
    # Parse keywords
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',')]
    
    # Initialize scraper
    scraper = LeadScraper(exclude_it=not args.include_it)
    
    # Scrape leads
    df = scraper.scrape_leads(
        keywords=keywords,
        location=args.location,
        max_leads=args.max_leads
    )
    
    print(f"\n✅ Lead scraping complete! Found {len(df)} valid leads.")
    
    if not df.empty:
        print("\n📋 Sample leads:")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
