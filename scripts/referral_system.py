"""
Referral Request System - Auto-Research & Auto-Send
Automatically finds employees at target companies and sends referral requests.
Features:
1. Auto-research employees using LinkedIn/Google
2. Auto-generate email addresses using company patterns
3. Auto-send direct referral requests
4. Track sent referrals and avoid duplicates
"""

import os
import re
import time
import random
import logging
import smtplib
import ssl
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from string import Template
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import quote_plus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ReferralRequestSystem:
    """Generate and send referral request emails."""
    
    # Common company email patterns
    EMAIL_PATTERNS = {
        'google': '{first}.{last}@google.com',
        'microsoft': '{first}.{last}@microsoft.com',
        'amazon': '{first}{last}@amazon.com',
        'meta': '{first}.{last}@fb.com',
        'apple': '{first}_{last}@apple.com',
        'netflix': '{first}.{last}@netflix.com',
        'salesforce': '{first}.{last}@salesforce.com',
        'adobe': '{first}{last}@adobe.com',
        'linkedin': '{first}{last}@linkedin.com',
        'uber': '{first}.{last}@uber.com',
        'twitter': '{first}{last}@twitter.com',
        'stripe': '{first}@stripe.com',
        'airbnb': '{first}.{last}@airbnb.com',
        'spotify': '{first}.{last}@spotify.com',
        'nvidia': '{first}{last}@nvidia.com',
        'intel': '{first}.{last}@intel.com',
        'ibm': '{first}.{last}@ibm.com',
        'oracle': '{first}.{last}@oracle.com',
        'cisco': '{first}{last}@cisco.com',
        'vmware': '{first}.{last}@vmware.com',
        # Indian companies
        'infosys': '{first}.{last}@infosys.com',
        'tcs': '{first}.{last}@tcs.com',
        'wipro': '{first}.{last}@wipro.com',
        'hcl': '{first}.{last}@hcl.com',
        'techm': '{first}.{last}@techmahindra.com',
        'flipkart': '{first}.{last}@flipkart.com',
        'paytm': '{first}.{last}@paytm.com',
        'zomato': '{first}.{last}@zomato.com',
        'swiggy': '{first}@swiggy.in',
        'razorpay': '{first}.{last}@razorpay.com',
        'zerodha': '{first}@zerodha.com',
        'phonepe': '{first}.{last}@phonepe.com',
        'cred': '{first}@cred.club',
        'myntra': '{first}.{last}@myntra.com',
        'ola': '{first}.{last}@olacabs.com',
        'byju': '{first}.{last}@byjus.com',
        'freshworks': '{first}.{last}@freshworks.com',
        'zoho': '{first}@zohocorp.com',
        'accenture': '{first}.{last}@accenture.com',
        'cognizant': '{first}.{last}@cognizant.com',
        'capgemini': '{first}.{last}@capgemini.com',
        'deloitte': '{first}.{last}@deloitte.com',
        'pwc': '{first}.{last}@pwc.com',
        'kpmg': '{first}.{last}@kpmg.com',
        'ey': '{first}.{last}@ey.com',
        'default': '{first}.{last}@{company}.com'
    }
    
    # Common Indian first names for auto-research (for finding employees)
    COMMON_NAMES = {
        'male': ['Rahul', 'Amit', 'Raj', 'Arun', 'Vijay', 'Sanjay', 'Deepak', 'Pradeep', 
                 'Ravi', 'Suresh', 'Mahesh', 'Rajesh', 'Prakash', 'Kiran', 'Anand',
                 'Ajay', 'Vikram', 'Nitin', 'Ashok', 'Manoj', 'Sachin', 'Rohan'],
        'female': ['Priya', 'Neha', 'Pooja', 'Anjali', 'Shruti', 'Divya', 'Kavita', 
                   'Sunita', 'Rekha', 'Meena', 'Anita', 'Swati', 'Nisha', 'Ritu',
                   'Sneha', 'Deepa', 'Shweta', 'Pallavi', 'Archana', 'Rashmi']
    }
    
    # Common last names
    COMMON_LASTNAMES = ['Sharma', 'Gupta', 'Singh', 'Kumar', 'Verma', 'Jain', 'Patel', 
                        'Agarwal', 'Reddy', 'Rao', 'Nair', 'Menon', 'Iyer', 'Pillai',
                        'Desai', 'Shah', 'Mehta', 'Kapoor', 'Malhotra', 'Chopra',
                        'Bansal', 'Goel', 'Mishra', 'Pandey', 'Tiwari', 'Saxena']
    
    # Referral request templates
    TEMPLATES = {
        'connection': """Hi ${employee_name},

I hope this message finds you well! I came across your profile while researching ${company} and noticed your impressive work as a ${employee_role}.

I'm ${my_name}, a ${my_role} with ${my_experience} of experience. I recently applied for the ${job_title} position at ${company} and was wondering if you might be open to a brief chat about your experience there.

I'm particularly interested in:
• The team culture and work environment
• Growth opportunities for someone in this role
• Any advice for standing out as a candidate

I completely understand if you're busy, but even a 15-minute call would be incredibly helpful. I'm also happy to share my resume if you'd be willing to refer me for the position.

Thank you for considering this, and I look forward to connecting!

Best regards,
${my_name}
${my_phone}
${my_linkedin}""",

        'direct_referral': """Hi ${employee_name},

I hope you're doing well! I'm reaching out because I'm very interested in the ${job_title} position at ${company}.

My name is ${my_name}, and I'm a ${my_role} with ${my_experience} of experience in ${my_skills}. I believe my background would be a great fit for this role.

I noticed you work at ${company} and wanted to ask if you might be willing to refer me for this position. I know referral bonuses are often offered, so this could potentially be a win-win!

Here's a quick summary of why I'd be a strong candidate:
${qualifications}

I've attached my resume for your reference. If you're open to it, I'd be happy to schedule a quick call to discuss my qualifications.

Thank you for your time and consideration. Even if you're unable to help, I appreciate you reading this.

Best regards,
${my_name}
${my_phone}
${my_linkedin}""",

        'alumni': """Hi ${employee_name},

I hope this message finds you well! I'm reaching out as a fellow ${alumni_connection}.

I'm ${my_name}, and I'm currently exploring opportunities in ${my_field}. I noticed you've built an impressive career at ${company}, and I'd love to learn from your experience.

I recently came across the ${job_title} position and I believe it would be a great fit for my background. I have ${my_experience} of experience in ${my_skills}.

Would you be open to a brief chat? I'd really appreciate any insights you could share about the company culture, interview process, or the team.

If you're comfortable, I would also be grateful if you could consider referring me for the position.

Thank you for your time!

Best,
${my_name}
${my_phone}
${my_linkedin}""",

        'short': """Hi ${employee_name},

I'm ${my_name}, applying for the ${job_title} role at ${company}. 

Quick ask: Would you consider referring me? I have ${my_experience} in ${my_skills} and I'm confident I'd be a great fit.

Happy to share my resume or chat briefly if helpful.

Thanks!
${my_name}
${my_phone}""",

        'auto_referral': """Hi,

I'm ${my_name}, a ${my_role} with ${my_experience} experience in ${my_skills}.

I'm interested in the ${job_title} position at ${company} and would really appreciate a referral. Referral bonuses are usually offered - so it's a win-win!

My qualifications:
${qualifications}

Please let me know if you'd be willing to refer me. Happy to share my resume.

Thanks!
${my_name}
📞 ${my_phone}
🔗 ${my_linkedin}"""
    }
    
    def __init__(self):
        """Initialize the referral request system."""
        self.my_name = os.getenv('APPLICANT_NAME', 'Your Name')
        self.my_email = os.getenv('SENDER_EMAIL', '')
        self.my_phone = os.getenv('APPLICANT_PHONE', '')
        self.my_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        # Use APPLICANT_TARGET_ROLE or first keyword from JOB_KEYWORDS
        job_keywords = os.getenv('JOB_KEYWORDS', '')
        default_role = job_keywords.split(',')[0].strip().title() if job_keywords else 'Professional'
        self.my_role = os.getenv('APPLICANT_TARGET_ROLE', default_role)
        self.my_experience = os.getenv('APPLICANT_EXPERIENCE', os.getenv('YEARS_EXPERIENCE', '3+')) + ' years'
        self.my_skills = os.getenv('APPLICANT_SKILLS', os.getenv('JOB_KEYWORDS', 'professional skills'))
        
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Resume path for attachment
        self.resume_path = os.getenv('RESUME_PATH', 'resumes/resume.pdf')
        
        # Output directory
        self.output_dir = 'data'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Log file
        self.log_file = os.path.join(self.output_dir, 'referral_requests_log.csv')
        
        logging.info(f"🤝 Referral Request System initialized for {self.my_name}")
        
        # HTTP session for web requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Track sent referrals to avoid duplicates
        self.sent_referrals = self._load_sent_referrals()
    
    def _load_sent_referrals(self) -> set:
        """Load list of already sent referral emails."""
        if os.path.exists(self.log_file):
            try:
                df = pd.read_csv(self.log_file)
                if 'recipient_email' in df.columns:
                    return set(df['recipient_email'].str.lower().dropna().tolist())
            except Exception:
                pass
        return set()
    
    def auto_discover_employees(self, company: str, job_title: str, max_contacts: int = 3) -> List[Dict]:
        """
        Auto-discover potential employees at a company using multiple methods.
        Returns list of potential contacts with guessed emails.
        """
        employees = []
        company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
        
        logging.info(f"🔍 Auto-discovering employees at {company}...")
        
        # Method 0: Check growing employees database first (from advanced discovery)
        employees.extend(self._get_discovered_employees(company))
        
        # Method 1: Check curated employee database
        if len(employees) < max_contacts:
            employees.extend(self._get_curated_employees(company, job_title))
        
        # Method 2: Search LinkedIn via DuckDuckGo (more bot-friendly than Google)
        if len(employees) < max_contacts:
            employees.extend(self._search_duckduckgo(company, job_title))
        
        # Method 3: Generate targeted contacts for well-known companies
        if len(employees) < max_contacts:
            employees.extend(self._generate_targeted_contacts(company, job_title, max_contacts - len(employees)))
        
        # Remove duplicates and limit
        seen_emails = set()
        unique_employees = []
        for emp in employees:
            email = emp.get('email', '').lower()
            if email and email not in seen_emails and email not in self.sent_referrals:
                seen_emails.add(email)
                unique_employees.append(emp)
                if len(unique_employees) >= max_contacts:
                    break
        
        logging.info(f"✅ Found {len(unique_employees)} potential contacts at {company}")
        return unique_employees
    
    def _get_discovered_employees(self, company: str) -> List[Dict]:
        """Get employees from growing discovered database."""
        employees = []
        discovered_path = os.path.join(self.output_dir, 'discovered_employees.csv')
        
        if os.path.exists(discovered_path):
            try:
                df = pd.read_csv(discovered_path)
                company_lower = company.lower()
                
                # Find matches
                matches = df[df['company'].str.lower().str.contains(company_lower, na=False)]
                
                for _, row in matches.head(3).iterrows():
                    if row.get('email') or row.get('linkedin_url'):
                        employees.append({
                            'name': row.get('name', 'Employee'),
                            'role': row.get('role', 'Employee'),
                            'company': company,
                            'email': row.get('email', ''),
                            'linkedin_url': row.get('linkedin_url', ''),
                            'source': 'discovered_database'
                        })
                
                if employees:
                    logging.info(f"   📈 Found {len(employees)} from discovered database")
                    
            except Exception as e:
                logging.debug(f"Error loading discovered employees: {e}")
        
        return employees
    
    def _search_linkedin_profiles(self, company: str, job_title: str) -> List[Dict]:
        """Search for LinkedIn profiles of employees at the company."""
        employees = []
        
        try:
            # Google search for LinkedIn profiles
            search_query = f'site:linkedin.com/in "{company}" "{job_title}" OR "Software Engineer" OR "Data Analyst"'
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&num=10"
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract names from LinkedIn profile snippets
                for result in soup.find_all(['h3', 'div'], class_=re.compile(r'tF2Cxc|g')):
                    text = result.get_text()
                    
                    # Try to extract name pattern: "Name - Title - Company"
                    name_match = re.search(r'^([A-Z][a-z]+ [A-Z][a-z]+)', text)
                    if name_match:
                        full_name = name_match.group(1)
                        names = full_name.split()
                        if len(names) >= 2:
                            first_name, last_name = names[0], names[-1]
                            emails = self.guess_email(first_name, last_name, company)
                            
                            if emails:
                                employees.append({
                                    'name': full_name,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'role': 'Employee',
                                    'company': company,
                                    'email': emails[0],  # Use best guess
                                    'all_emails': emails,
                                    'source': 'linkedin_search'
                                })
                            
                            if len(employees) >= 3:
                                break
                                
        except Exception as e:
            logging.debug(f"LinkedIn search error: {e}")
        
        return employees
    
    # Curated employee database for major companies (publicly available from LinkedIn, company websites)
    CURATED_EMPLOYEES = {
        # Interior Design & Architecture Companies (for Yogeshwari)
        'livspace': [
            {'name': 'Anuj Srivastava', 'role': 'CEO', 'email': 'anuj@livspace.com'},
            {'name': 'Ramakant Sharma', 'role': 'Co-founder', 'email': 'ramakant@livspace.com'},
            {'name': 'Talent Team', 'role': 'HR', 'email': 'careers@livspace.com'},
        ],
        'homelane': [
            {'name': 'Srikanth Iyer', 'role': 'Co-founder', 'email': 'srikanth@homelane.com'},
            {'name': 'Tanuj Choudhry', 'role': 'Co-founder', 'email': 'tanuj@homelane.com'},
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@homelane.com'},
        ],
        'designcafe': [
            {'name': 'Gita Ramanan', 'role': 'Co-founder', 'email': 'gita@designcafe.com'},
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@designcafe.com'},
        ],
        'bonito': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@bonito.in'},
            {'name': 'HR Team', 'role': 'General', 'email': 'hr@bonito.in'},
        ],
        'decorpot': [
            {'name': 'Vivek Bingumalla', 'role': 'Founder', 'email': 'vivek@decorpot.com'},
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@decorpot.com'},
        ],
        'godrej interio': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@godrejinterio.com'},
        ],
        'asian paints': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@asianpaints.com'},
        ],
        'prestige': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@prestigeconstructions.com'},
        ],
        'sobha': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@sobha.com'},
        ],
        'brigade': [
            {'name': 'HR Team', 'role': 'Recruitment', 'email': 'careers@brigadegroup.com'},
        ],
        # Major Tech Companies
        'google': [
            {'name': 'Google Referrals', 'role': 'Recruitment', 'email': 'referrals@google.com'},
        ],
        'microsoft': [
            {'name': 'Microsoft Careers', 'role': 'Recruitment', 'email': 'askhr@microsoft.com'},
        ],
        'amazon': [
            {'name': 'Amazon Recruiting', 'role': 'Recruitment', 'email': 'referrals@amazon.com'},
        ],
        'flipkart': [
            {'name': 'Flipkart Talent', 'role': 'Recruitment', 'email': 'talent@flipkart.com'},
        ],
        'swiggy': [
            {'name': 'Swiggy HR', 'role': 'Recruitment', 'email': 'careers@swiggy.in'},
        ],
        'zomato': [
            {'name': 'Zomato People', 'role': 'Recruitment', 'email': 'careers@zomato.com'},
        ],
        'phonepe': [
            {'name': 'PhonePe Talent', 'role': 'Recruitment', 'email': 'careers@phonepe.com'},
        ],
        'razorpay': [
            {'name': 'Razorpay HR', 'role': 'Recruitment', 'email': 'careers@razorpay.com'},
        ],
        'meesho': [
            {'name': 'Meesho Talent', 'role': 'Recruitment', 'email': 'careers@meesho.com'},
        ],
        'cred': [
            {'name': 'CRED People', 'role': 'Recruitment', 'email': 'people@cred.club'},
        ],
        'infosys': [
            {'name': 'Infosys HR', 'role': 'Recruitment', 'email': 'careers@infosys.com'},
        ],
        'tcs': [
            {'name': 'TCS Careers', 'role': 'Recruitment', 'email': 'careers@tcs.com'},
        ],
        'wipro': [
            {'name': 'Wipro Recruitment', 'role': 'Recruitment', 'email': 'helpdesk.recruitment@wipro.com'},
        ],
    }
    
    def _get_curated_employees(self, company: str, job_title: str) -> List[Dict]:
        """Get employees from curated database."""
        employees = []
        company_lower = company.lower()
        
        # Check for exact or partial match
        for curated_company, contacts in self.CURATED_EMPLOYEES.items():
            if curated_company in company_lower or company_lower in curated_company:
                for contact in contacts:
                    if contact['email'].lower() not in self.sent_referrals:
                        employees.append({
                            'name': contact['name'],
                            'first_name': contact['name'].split()[0] if ' ' in contact['name'] else contact['name'],
                            'last_name': contact['name'].split()[-1] if ' ' in contact['name'] else '',
                            'role': contact['role'],
                            'company': company,
                            'email': contact['email'],
                            'source': 'curated_database'
                        })
                break
        
        return employees
    
    def _search_duckduckgo(self, company: str, job_title: str) -> List[Dict]:
        """Search for employees using DuckDuckGo (more bot-friendly)."""
        employees = []
        
        try:
            # DuckDuckGo HTML search (no API key needed)
            search_query = f'{company} employees linkedin'
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract results from DuckDuckGo
                for result in soup.find_all('a', class_='result__a'):
                    text = result.get_text()
                    href = result.get('href', '')
                    
                    # Look for LinkedIn profiles
                    if 'linkedin.com/in/' in href:
                        # Try to extract name from title
                        name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
                        if name_match:
                            full_name = name_match.group(1)
                            names = full_name.split()
                            if len(names) >= 2:
                                first_name, last_name = names[0], names[-1]
                                emails = self.guess_email(first_name, last_name, company)
                                
                                if emails:
                                    employees.append({
                                        'name': full_name,
                                        'first_name': first_name,
                                        'last_name': last_name,
                                        'role': 'Employee',
                                        'company': company,
                                        'email': emails[0],
                                        'all_emails': emails,
                                        'source': 'duckduckgo_search'
                                    })
                                
                                if len(employees) >= 3:
                                    break
                                    
        except Exception as e:
            logging.debug(f"DuckDuckGo search error: {e}")
        
        return employees
    
    def _generate_targeted_contacts(self, company: str, job_title: str, count: int = 2) -> List[Dict]:
        """
        Generate targeted contacts for companies with known email patterns.
        Only generates contacts for companies where we know the email format.
        """
        employees = []
        company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
        
        # Check if company has a known email pattern
        if company_clean not in self.EMAIL_PATTERNS and not self._has_common_email_pattern(company):
            return employees
        
        # HR/Recruitment titles that are commonly reachable
        hr_roles = ['HR Manager', 'Talent Acquisition', 'Recruiter', 'People Operations']
        hr_names = [
            ('Priya', 'Sharma'), ('Rahul', 'Gupta'), ('Neha', 'Singh'), 
            ('Amit', 'Kumar'), ('Pooja', 'Verma'), ('Ravi', 'Patel')
        ]
        
        random.shuffle(hr_names)
        
        for (first_name, last_name) in hr_names[:count]:
            emails = self.guess_email(first_name, last_name, company)
            if emails:
                email = emails[0]
                if email.lower() not in self.sent_referrals:
                    employees.append({
                        'name': f"{first_name} {last_name}",
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': random.choice(hr_roles),
                        'company': company,
                        'email': email,
                        'all_emails': emails,
                        'source': 'targeted_generation'
                    })
        
        return employees
    
    def _has_common_email_pattern(self, company: str) -> bool:
        """Check if company likely has a standard corporate email pattern."""
        # Companies with .com domains usually have standard patterns
        company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
        
        # Known companies with reliable email patterns
        known_patterns = [
            'accenture', 'cognizant', 'infosys', 'tcs', 'wipro', 'hcl',
            'deloitte', 'pwc', 'kpmg', 'ey', 'capgemini', 'ibm',
            'google', 'microsoft', 'amazon', 'meta', 'apple', 'netflix',
            'flipkart', 'swiggy', 'zomato', 'phonepe', 'razorpay', 'paytm',
            'livspace', 'homelane', 'designcafe', 'bonito', 'decorpot',
            'prestige', 'sobha', 'brigade', 'puravankara', 'godrej',
        ]
        
        return any(pattern in company_clean for pattern in known_patterns)

    def _generate_synthetic_contacts(self, company: str, job_title: str, count: int = 3) -> List[Dict]:
        """
        Generate synthetic employee contacts based on common name patterns.
        These are best-guess emails that may or may not be valid.
        """
        employees = []
        
        # Combine male and female names
        all_first_names = self.COMMON_NAMES['male'] + self.COMMON_NAMES['female']
        random.shuffle(all_first_names)
        
        used_names = set()
        
        for first_name in all_first_names:
            if len(employees) >= count:
                break
            
            # Pick a random last name
            last_name = random.choice(self.COMMON_LASTNAMES)
            full_name = f"{first_name} {last_name}"
            
            if full_name in used_names:
                continue
            used_names.add(full_name)
            
            emails = self.guess_email(first_name, last_name, company)
            
            if emails:
                email = emails[0]
                # Skip if already sent
                if email.lower() in self.sent_referrals:
                    continue
                    
                employees.append({
                    'name': full_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'Employee',
                    'company': company,
                    'email': email,
                    'all_emails': emails,
                    'source': 'synthetic'
                })
        
        return employees
    
    def auto_send_referrals_for_jobs(self, jobs_df: pd.DataFrame, 
                                      max_per_company: int = 2,
                                      max_total: int = 10,
                                      delay_range: Tuple[int, int] = (60, 120)) -> Dict:
        """
        Automatically research and send referral requests for jobs in the DataFrame.
        
        Args:
            jobs_df: DataFrame with 'company' and 'title' columns
            max_per_company: Max referral requests per company
            max_total: Max total referral requests to send
            delay_range: Delay range in seconds between emails
            
        Returns:
            Stats dict with sent/failed counts
        """
        stats = {'sent': 0, 'failed': 0, 'skipped': 0, 'companies': []}
        
        if jobs_df.empty:
            logging.warning("No jobs to process!")
            return stats
        
        # Get unique companies
        if 'company' not in jobs_df.columns:
            logging.error("❌ jobs_df must have 'company' column")
            return stats
        
        companies = jobs_df['company'].dropna().unique().tolist()
        logging.info(f"🏢 Processing {len(companies)} companies for referral requests...")
        
        total_sent = 0
        
        for company in companies:
            if total_sent >= max_total:
                logging.info(f"📊 Reached max limit of {max_total} referrals")
                break
            
            # Get job title for this company
            company_jobs = jobs_df[jobs_df['company'] == company]
            job_title = company_jobs.iloc[0].get('title', 'Software Position')
            if pd.isna(job_title):
                job_title = 'Software Position'
            
            logging.info(f"\n🏢 Processing {company} - {job_title}")
            
            # Auto-discover employees
            employees = self.auto_discover_employees(company, job_title, max_contacts=max_per_company)
            
            if not employees:
                logging.info(f"   ⏭️ No contacts found for {company}")
                stats['skipped'] += 1
                continue
            
            stats['companies'].append(company)
            
            for emp in employees:
                if total_sent >= max_total:
                    break
                
                email = emp.get('email')
                if not email or email.lower() in self.sent_referrals:
                    continue
                
                # Send referral request
                success = self.send_referral_request(
                    recipient_email=email,
                    employee_name=emp.get('name', 'Hi there'),
                    employee_role=emp.get('role', 'Employee'),
                    company=company,
                    job_title=job_title,
                    template_type='auto_referral'
                )
                
                if success:
                    stats['sent'] += 1
                    total_sent += 1
                    self.sent_referrals.add(email.lower())
                else:
                    stats['failed'] += 1
                
                # Delay between emails
                if total_sent < max_total:
                    delay = random.randint(delay_range[0], delay_range[1])
                    logging.info(f"   ⏳ Waiting {delay}s before next...")
                    time.sleep(delay)
        
        logging.info(f"\n📊 Auto-Referral Summary:")
        logging.info(f"   ✅ Sent: {stats['sent']}")
        logging.info(f"   ❌ Failed: {stats['failed']}")
        logging.info(f"   ⏭️ Skipped: {stats['skipped']}")
        logging.info(f"   🏢 Companies: {len(stats['companies'])}")
        
        return stats

    def guess_email(self, first_name: str, last_name: str, company: str) -> List[str]:
        """Generate possible email addresses for an employee."""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
        
        # Get company-specific pattern
        pattern = self.EMAIL_PATTERNS.get(company_clean)
        
        emails = []
        
        if pattern:
            email = pattern.format(first=first, last=last, company=company_clean)
            emails.append(email)
        
        # Generate common variations
        variations = [
            f"{first}.{last}@{company_clean}.com",
            f"{first}{last}@{company_clean}.com",
            f"{first}_{last}@{company_clean}.com",
            f"{first[0]}{last}@{company_clean}.com",
            f"{first}@{company_clean}.com",
            f"{first}.{last[0]}@{company_clean}.com",
        ]
        
        for v in variations:
            if v not in emails:
                emails.append(v)
        
        return emails[:3]  # Return top 3 guesses
    
    def generate_qualifications_list(self) -> str:
        """Generate qualifications bullet list."""
        qualifications = [
            f"• {self.my_experience} of hands-on experience",
            f"• Strong skills in {self.my_skills}",
            "• Track record of delivering quality work on time",
            "• Excellent communication and teamwork abilities"
        ]
        return '\n'.join(qualifications)
    
    def generate_referral_request(self,
                                   employee_name: str,
                                   employee_role: str,
                                   company: str,
                                   job_title: str,
                                   template_type: str = 'connection',
                                   alumni_connection: str = None) -> str:
        """Generate a personalized referral request email."""
        
        template = Template(self.TEMPLATES.get(template_type, self.TEMPLATES['connection']))
        
        return template.substitute(
            employee_name=employee_name.split()[0],  # First name only
            employee_role=employee_role,
            company=company,
            job_title=job_title,
            my_name=self.my_name,
            my_role=self.my_role,
            my_experience=self.my_experience,
            my_skills=self.my_skills,
            my_phone=self.my_phone,
            my_linkedin=f"LinkedIn: {self.my_linkedin}" if self.my_linkedin else "",
            qualifications=self.generate_qualifications_list(),
            alumni_connection=alumni_connection or "our network",
            my_field=self.my_skills
        )
    
    def generate_subject(self, job_title: str, company: str, template_type: str) -> str:
        """Generate email subject line."""
        subjects = {
            'connection': [
                f"Quick question about {company}",
                f"Coffee chat request - {company}",
                f"Seeking advice about {job_title} at {company}",
            ],
            'direct_referral': [
                f"Referral request for {job_title} position",
                f"Would you consider referring me? - {job_title}",
                f"Seeking referral: {job_title} at {company}",
            ],
            'alumni': [
                f"Fellow alumni reaching out - {company}",
                f"Connection request from a fellow graduate",
                f"Alumni networking - {job_title} opportunity",
            ],
            'short': [
                f"Quick referral request - {job_title}",
                f"Referral for {job_title}?",
            ]
        }
        
        options = subjects.get(template_type, subjects['connection'])
        return random.choice(options)
    
    def send_referral_request(self,
                               recipient_email: str,
                               employee_name: str,
                               employee_role: str,
                               company: str,
                               job_title: str,
                               template_type: str = 'connection') -> bool:
        """Send a referral request email."""
        
        if not self.sender_password:
            logging.error("❌ SENDER_PASSWORD not set")
            return False
        
        try:
            subject = self.generate_subject(job_title, company, template_type)
            body = self.generate_referral_request(
                employee_name=employee_name,
                employee_role=employee_role,
                company=company,
                job_title=job_title,
                template_type=template_type
            )
            
            message = MIMEMultipart()
            message['From'] = f"{self.my_name} <{self.my_email}>"
            message['To'] = recipient_email
            message['Subject'] = subject
            # Use UTF-8 encoding to handle emojis and special characters
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Attach resume if available
            if os.path.exists(self.resume_path):
                try:
                    with open(self.resume_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    
                    filename = os.path.basename(self.resume_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    message.attach(part)
                    logging.info(f"📎 Attached resume: {filename}")
                except Exception as e:
                    logging.warning(f"Could not attach resume: {e}")
            else:
                logging.warning(f"⚠️ Resume not found at {self.resume_path}")
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.my_email, self.sender_password)
                server.sendmail(self.my_email, recipient_email, message.as_string())
            
            logging.info(f"✅ Referral request sent to {employee_name} at {company}")
            self._log_request(recipient_email, employee_name, company, job_title, 'sent')
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send to {recipient_email}: {e}")
            self._log_request(recipient_email, employee_name, company, job_title, f'failed: {e}')
            return False
    
    def _log_request(self, email: str, name: str, company: str, job_title: str, status: str):
        """Log referral request to CSV."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'recipient_email': email,
            'employee_name': name,
            'company': company,
            'job_title': job_title,
            'status': status
        }
        
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.log_file, index=False)
    
    def find_employees_to_contact(self, company: str, job_title: str = None) -> List[Dict]:
        """
        Find potential employees to contact at a company.
        In a real implementation, this would use LinkedIn API or web scraping.
        For now, returns placeholder data that user should fill in.
        """
        logging.info(f"🔍 Finding employees at {company}...")
        
        # Placeholder - in production, use LinkedIn Sales Navigator or similar
        # Return format for manual entry
        template = {
            'company': company,
            'job_title': job_title,
            'employees': [
                {
                    'name': 'Employee Name',
                    'role': 'Software Engineer / HR',
                    'email': 'to be determined',
                    'linkedin': 'linkedin.com/in/profile'
                }
            ],
            'email_pattern': self.EMAIL_PATTERNS.get(
                re.sub(r'[^a-z0-9]', '', company.lower()),
                self.EMAIL_PATTERNS['default']
            )
        }
        
        return template
    
    def process_employee_list(self, employee_file: str) -> Dict:
        """Process a CSV file with employee contacts and send referral requests."""
        
        if not os.path.exists(employee_file):
            logging.error(f"❌ File not found: {employee_file}")
            return {'sent': 0, 'failed': 0}
        
        df = pd.read_csv(employee_file)
        required_cols = ['name', 'email', 'company', 'job_title']
        
        if not all(col in df.columns for col in required_cols):
            logging.error(f"❌ Missing columns. Required: {required_cols}")
            return {'sent': 0, 'failed': 0}
        
        stats = {'sent': 0, 'failed': 0}
        
        for idx, row in df.iterrows():
            success = self.send_referral_request(
                recipient_email=row['email'],
                employee_name=row['name'],
                employee_role=row.get('role', 'Employee'),
                company=row['company'],
                job_title=row['job_title'],
                template_type=row.get('template', 'connection')
            )
            
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            
            # Delay between emails
            if idx < len(df) - 1:
                delay = random.uniform(120, 180)  # 2-3 minutes
                logging.info(f"⏳ Waiting {delay:.0f}s...")
                time.sleep(delay)
        
        return stats


def create_employee_template(output_file: str = 'data/referral_contacts.csv'):
    """Create a template CSV for entering employee contacts."""
    template_data = [
        {
            'name': 'John Smith',
            'email': 'john.smith@company.com',
            'role': 'Senior Software Engineer',
            'company': 'TechCorp',
            'job_title': 'Python Developer',
            'template': 'connection',
            'notes': 'Found on LinkedIn - same college'
        }
    ]
    
    df = pd.DataFrame(template_data)
    df.to_csv(output_file, index=False)
    
    logging.info(f"📝 Template created: {output_file}")
    logging.info("Fill in employee details and run the system to send referral requests.")
    
    return output_file


def main():
    """Main function for referral request system - AUTO MODE."""
    logging.info("="*60)
    logging.info("🤝 AUTO REFERRAL REQUEST SYSTEM")
    logging.info("   Referrals have 10x higher response rate than cold emails!")
    logging.info("="*60)
    
    system = ReferralRequestSystem()
    
    # Get max referrals from env or default to 10 (reduced from unlimited)
    max_referrals = int(os.getenv('MAX_REFERRAL_REQUESTS', '10'))
    max_per_company = int(os.getenv('MAX_REFERRALS_PER_COMPANY', '1'))  # Only 1 contact per company
    
    # Priority 1: Check for jobs_today.csv to auto-send referrals
    jobs_file = 'data/jobs_today.csv'
    
    if os.path.exists(jobs_file):
        logging.info(f"💼 Loading jobs from {jobs_file}...")
        jobs_df = pd.read_csv(jobs_file)
        
        if not jobs_df.empty:
            logging.info(f"🏢 Found {len(jobs_df)} jobs from {jobs_df['company'].nunique()} companies")
            logging.info(f"🚀 Auto-sending referral requests (max {max_referrals})...\n")
            
            # Auto-research and send referrals
            stats = system.auto_send_referrals_for_jobs(
                jobs_df=jobs_df,
                max_per_company=max_per_company,
                max_total=max_referrals,
                delay_range=(5, 15)  # 5-15 seconds delay for fast execution
            )
            
            logging.info("\n" + "="*60)
            logging.info("📊 REFERRAL REQUEST SUMMARY")
            logging.info("="*60)
            logging.info(f"   ✅ Referrals Sent: {stats['sent']}")
            logging.info(f"   ❌ Failed: {stats['failed']}")
            logging.info(f"   ⏭️ Companies Skipped: {stats['skipped']}")
            logging.info(f"   🏢 Companies Processed: {len(stats['companies'])}")
            
            if stats['companies']:
                logging.info(f"\n   Companies contacted:")
                for company in stats['companies'][:10]:
                    logging.info(f"      • {company}")
        else:
            logging.warning("⚠️ jobs_today.csv is empty!")
    else:
        logging.info(f"⚠️ No {jobs_file} found. Running in manual mode...")
        
        # Fallback: Check for manual contacts file
        contacts_file = 'data/referral_contacts.csv'
        
        if os.path.exists(contacts_file):
            logging.info(f"📂 Found contacts file: {contacts_file}")
            stats = system.process_employee_list(contacts_file)
            
            logging.info(f"\n📊 Summary:")
            logging.info(f"   ✅ Sent: {stats['sent']}")
            logging.info(f"   ❌ Failed: {stats['failed']}")
        else:
            # Create template for manual use
            logging.info("📝 Creating template for manual contacts...")
            create_employee_template(contacts_file)
            
            # Demo auto-referral template
            logging.info("\n📧 Sample Auto-Referral Email:")
            logging.info("="*40)
            
            sample = system.generate_referral_request(
                employee_name="Team",
                employee_role="Employee",
                company="Google",
                job_title="Python Developer",
                template_type="auto_referral"
            )
            print(sample)
            
            logging.info("\n💡 To enable auto-referrals:")
            logging.info("1. Run job scraper first to create jobs_today.csv")
            logging.info("2. System will auto-research employees at each company")
            logging.info("3. Referral requests will be sent automatically")
    
    logging.info("\n" + "="*60)
    logging.info("✅ Referral system complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
