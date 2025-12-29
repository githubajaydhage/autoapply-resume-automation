"""
Smart Job Matcher - Matches scraped jobs to HR emails and filters by resume match score
Only sends applications when there's a real job match!
"""

import pandas as pd
import os
import re
import logging
from datetime import datetime
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class SmartJobMatcher:
    """Matches jobs to HR emails and filters based on resume compatibility."""
    
    # Company name variations/aliases
    COMPANY_ALIASES = {
        # Indian IT Giants
        'tcs': ['tata consultancy', 'tata consultancy services'],
        'wipro': ['wipro limited', 'wipro technologies'],
        'infosys': ['infosys limited', 'infosys technologies'],
        'hcl': ['hcl technologies', 'hcl tech', 'hindustan computers'],
        'tech mahindra': ['techmahindra', 'mahindra tech'],
        'mindtree': ['ltimindtree', 'lti mindtree', 'l&t mindtree'],
        'cognizant': ['cognizant technology', 'cts'],
        'mphasis': ['mphasis limited'],
        
        # Startups
        'razorpay': [],
        'phonepe': ['phone pe'],
        'swiggy': [],
        'zomato': [],
        'cred': [],
        'meesho': [],
        'groww': [],
        'freshworks': ['freshdesk'],
        'zoho': ['zoho corp', 'zohocorp'],
        'flipkart': ['flipkart internet'],
        'ola': ['olacabs', 'ola cabs', 'ani technologies'],
        'paytm': ['one97', 'paytm payments'],
        'byjus': ["byju's", 'think & learn'],
        'unacademy': [],
        'dunzo': [],
        'urban company': ['urbancompany', 'urbanclap'],
        'policybazaar': ['policy bazaar', 'pb fintech'],
        'nykaa': ['fsn e-commerce'],
        
        # Global Giants
        'google': ['alphabet'],
        'microsoft': ['msft'],
        'amazon': ['aws', 'amazon web services'],
        'meta': ['facebook', 'fb'],
        'apple': [],
        'netflix': [],
        'uber': [],
        'salesforce': [],
        'adobe': [],
        'oracle': [],
        'ibm': ['international business machines'],
        'sap': [],
    }
    
    def __init__(self, min_match_score: int = 50):
        """
        Initialize the matcher.
        
        Args:
            min_match_score: Minimum resume match score (0-100) to consider a job
        """
        self.min_match_score = min_match_score
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Build reverse alias lookup
        self.company_lookup = {}
        for canonical, aliases in self.COMPANY_ALIASES.items():
            self.company_lookup[canonical.lower()] = canonical
            for alias in aliases:
                self.company_lookup[alias.lower()] = canonical
    
    def normalize_company_name(self, company: str) -> str:
        """Normalize company name for matching."""
        if not company or pd.isna(company):
            return ""
        
        company = str(company).lower().strip()
        
        # Remove common suffixes
        for suffix in [' inc', ' inc.', ' ltd', ' ltd.', ' limited', ' pvt', ' private', 
                       ' llc', ' corp', ' corporation', ' technologies', ' tech', ' solutions']:
            company = company.replace(suffix, '')
        
        company = company.strip()
        
        # Check alias lookup
        if company in self.company_lookup:
            return self.company_lookup[company]
        
        return company
    
    def calculate_company_similarity(self, company1: str, company2: str) -> float:
        """Calculate similarity between two company names."""
        norm1 = self.normalize_company_name(company1)
        norm2 = self.normalize_company_name(company2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Partial match (one contains the other)
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Sequence matcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def extract_domain_from_email(self, email: str) -> str:
        """Extract company name from email domain."""
        if not email or '@' not in email:
            return ""
        
        domain = email.split('@')[1].lower()
        
        # Remove common TLDs
        for tld in ['.com', '.in', '.co.in', '.org', '.net', '.io', '.ai', '.club', '.co']:
            domain = domain.replace(tld, '')
        
        return domain
    
    def load_jobs(self) -> pd.DataFrame:
        """Load scraped jobs with match scores."""
        jobs_path = os.path.join(self.data_path, 'jobs_today.csv')
        match_path = os.path.join(self.data_path, 'job_match_scores.csv')
        
        if not os.path.exists(jobs_path):
            logging.warning("No jobs file found!")
            return pd.DataFrame()
        
        jobs_df = pd.read_csv(jobs_path)
        logging.info(f"📋 Loaded {len(jobs_df)} jobs")
        
        # Try to load match scores
        if os.path.exists(match_path):
            try:
                match_df = pd.read_csv(match_path)
                # Merge match scores with jobs - check if required columns exist
                if 'match_score' in match_df.columns:
                    # Determine merge columns based on what's available
                    merge_cols = []
                    for col in ['title', 'company']:
                        if col in match_df.columns and col in jobs_df.columns:
                            merge_cols.append(col)
                    
                    if merge_cols:
                        select_cols = merge_cols + ['match_score']
                        jobs_df = jobs_df.merge(
                            match_df[select_cols], 
                            on=merge_cols, 
                            how='left'
                        )
                        logging.info(f"📊 Loaded match scores for jobs (merged on: {merge_cols})")
                    else:
                        logging.warning("Match scores file missing required columns for merge")
            except Exception as e:
                logging.warning(f"Could not load match scores: {e}")
        
        # Fill missing match scores with 50 (neutral)
        if 'match_score' not in jobs_df.columns:
            jobs_df['match_score'] = 50
        jobs_df['match_score'] = jobs_df['match_score'].fillna(50)
        
        return jobs_df
    
    def load_hr_emails(self) -> pd.DataFrame:
        """Load all HR emails from various sources."""
        hr_emails = []
        
        # Source 1: Curated HR database
        curated_path = os.path.join(self.data_path, 'curated_hr_emails.csv')
        if os.path.exists(curated_path):
            curated_df = pd.read_csv(curated_path)
            if 'email' in curated_df.columns:
                curated_df = curated_df.rename(columns={'email': 'hr_email'})
            hr_emails.append(curated_df)
            logging.info(f"📋 Loaded {len(curated_df)} curated HR emails")
        
        # Source 2: Verified HR emails (highest quality)
        verified_path = os.path.join(self.data_path, 'verified_hr_emails.csv')
        if os.path.exists(verified_path):
            verified_df = pd.read_csv(verified_path)
            if 'email' in verified_df.columns:
                verified_df = verified_df.rename(columns={'email': 'hr_email'})
            hr_emails.append(verified_df)
            logging.info(f"✅ Loaded {len(verified_df)} verified HR emails")
        
        # Source 3: Scraped HR emails
        scraped_path = os.path.join(self.data_path, 'all_hr_emails.csv')
        if os.path.exists(scraped_path):
            scraped_df = pd.read_csv(scraped_path)
            hr_emails.append(scraped_df)
            logging.info(f"🔍 Loaded scraped HR emails")
        
        if not hr_emails:
            logging.warning("No HR emails found!")
            return pd.DataFrame()
        
        # Combine and dedupe
        emails_df = pd.concat(hr_emails, ignore_index=True)
        emails_df = emails_df.drop_duplicates(subset=['hr_email'], keep='first')
        
        return emails_df
    
    def load_known_bad_emails(self) -> set:
        """Load emails known to bounce/fail."""
        bad_emails = set()
        
        # Bounced emails
        bounced_path = os.path.join(self.data_path, 'bounced_emails.csv')
        if os.path.exists(bounced_path):
            try:
                df = pd.read_csv(bounced_path)
                if 'email' in df.columns:
                    bad_emails.update(df['email'].str.lower().dropna())
                elif 'bounced_email' in df.columns:
                    bad_emails.update(df['bounced_email'].str.lower().dropna())
            except:
                pass
        
        # Known bad emails
        known_bad_path = os.path.join(self.data_path, 'known_bad_emails.csv')
        if os.path.exists(known_bad_path):
            try:
                df = pd.read_csv(known_bad_path)
                if 'email' in df.columns:
                    bad_emails.update(df['email'].str.lower().dropna())
            except:
                pass
        
        # Problematic emails
        prob_path = os.path.join(self.data_path, 'problematic_emails.csv')
        if os.path.exists(prob_path):
            try:
                df = pd.read_csv(prob_path)
                if 'email' in df.columns:
                    bad_emails.update(df['email'].str.lower().dropna())
            except:
                pass
        
        logging.info(f"🚫 Loaded {len(bad_emails)} known bad emails to exclude")
        return bad_emails
    
    def match_jobs_to_hr(self, jobs_df: pd.DataFrame, hr_df: pd.DataFrame) -> pd.DataFrame:
        """
        Match jobs to HR emails based on company name matching.
        
        Returns DataFrame with matched jobs and their corresponding HR emails.
        """
        if jobs_df.empty or hr_df.empty:
            return pd.DataFrame()
        
        matches = []
        
        for _, job in jobs_df.iterrows():
            job_company = str(job.get('company', '')).lower().strip()
            job_title = job.get('title', 'Open Position')
            job_url = job.get('url', job.get('link', ''))
            match_score = job.get('match_score', 50)
            
            if not job_company:
                continue
            
            # Filter by minimum match score
            if match_score < self.min_match_score:
                continue
            
            # Find matching HR emails
            for _, hr in hr_df.iterrows():
                hr_email = hr.get('hr_email', '')
                hr_company = str(hr.get('company', '')).lower().strip()
                
                if not hr_email:
                    continue
                
                # Try multiple matching strategies
                similarity = 0.0
                
                # Strategy 1: Direct company name match
                if hr_company:
                    similarity = max(similarity, self.calculate_company_similarity(job_company, hr_company))
                
                # Strategy 2: Extract company from email domain
                email_domain_company = self.extract_domain_from_email(hr_email)
                if email_domain_company:
                    similarity = max(similarity, self.calculate_company_similarity(job_company, email_domain_company))
                
                # If good match found
                if similarity >= 0.7:
                    matches.append({
                        'job_title': job_title,
                        'job_company': job.get('company', ''),
                        'job_url': job_url,
                        'job_match_score': match_score,
                        'hr_email': hr_email,
                        'hr_company': hr.get('company', ''),
                        'company_similarity': similarity,
                        'source': hr.get('source', 'curated')
                    })
        
        result_df = pd.DataFrame(matches)
        
        if not result_df.empty:
            # Remove duplicates (same email + same job)
            result_df = result_df.drop_duplicates(subset=['hr_email', 'job_title'], keep='first')
            # Sort by match score descending
            result_df = result_df.sort_values('job_match_score', ascending=False)
        
        logging.info(f"🎯 Found {len(result_df)} job-to-HR matches")
        return result_df
    
    def get_unmatched_hr_for_general_outreach(self, hr_df: pd.DataFrame, matched_emails: set) -> pd.DataFrame:
        """
        Get HR emails that didn't match any specific job, for general outreach.
        These will be sent generic "Data Analyst" applications.
        """
        unmatched = hr_df[~hr_df['hr_email'].isin(matched_emails)].copy()
        unmatched['job_title'] = 'Data Analyst / Software Engineer'
        unmatched['job_company'] = unmatched.get('company', 'Your Company')
        unmatched['job_url'] = ''
        unmatched['job_match_score'] = 50  # Neutral score
        
        return unmatched
    
    def create_prioritized_application_list(self, max_applications: int = 50) -> pd.DataFrame:
        """
        Create a prioritized list of applications to send.
        
        Priority order:
        1. High match score jobs (70%+) with matched HR emails
        2. Medium match score jobs (50-70%) with matched HR emails
        3. General outreach to unmatched HR emails
        """
        logging.info("="*60)
        logging.info("🎯 SMART JOB MATCHER")
        logging.info("="*60)
        
        # Load data
        jobs_df = self.load_jobs()
        hr_df = self.load_hr_emails()
        bad_emails = self.load_known_bad_emails()
        
        if jobs_df.empty or hr_df.empty:
            logging.error("Missing jobs or HR emails data!")
            return pd.DataFrame()
        
        # Filter out bad emails
        hr_df = hr_df[~hr_df['hr_email'].str.lower().isin(bad_emails)]
        logging.info(f"📊 {len(hr_df)} valid HR emails after filtering")
        
        # Match jobs to HR emails
        matched_df = self.match_jobs_to_hr(jobs_df, hr_df)
        
        # Categorize matches
        high_priority = matched_df[matched_df['job_match_score'] >= 70].copy()
        high_priority['priority'] = 1
        
        medium_priority = matched_df[(matched_df['job_match_score'] >= 50) & 
                                     (matched_df['job_match_score'] < 70)].copy()
        medium_priority['priority'] = 2
        
        # Get unmatched HR for general outreach
        matched_emails = set(matched_df['hr_email'].unique()) if not matched_df.empty else set()
        unmatched_hr = self.get_unmatched_hr_for_general_outreach(hr_df, matched_emails)
        unmatched_hr['priority'] = 3
        
        # Combine all
        all_applications = pd.concat([
            high_priority,
            medium_priority,
            unmatched_hr
        ], ignore_index=True)
        
        # Sort by priority, then by match score
        all_applications = all_applications.sort_values(['priority', 'job_match_score'], 
                                                        ascending=[True, False])
        
        # Limit to max applications
        result = all_applications.head(max_applications)
        
        # Log summary
        logging.info(f"\n📊 APPLICATION PRIORITY BREAKDOWN:")
        logging.info(f"   🟢 High Priority (70%+ match): {len(high_priority)}")
        logging.info(f"   🟡 Medium Priority (50-70%): {len(medium_priority)}")
        logging.info(f"   🔵 General Outreach: {len(unmatched_hr)}")
        logging.info(f"   📨 Total to send: {len(result)}")
        
        # Save the prioritized list
        output_path = os.path.join(self.data_path, 'prioritized_applications.csv')
        result.to_csv(output_path, index=False)
        logging.info(f"💾 Saved prioritized applications to {output_path}")
        
        return result


def main():
    """Test the smart job matcher."""
    matcher = SmartJobMatcher(min_match_score=50)
    applications = matcher.create_prioritized_application_list(max_applications=50)
    
    if not applications.empty:
        print("\n📋 TOP 10 PRIORITIZED APPLICATIONS:")
        for idx, row in applications.head(10).iterrows():
            print(f"   {row.get('job_title', 'N/A')} at {row.get('job_company', 'N/A')}")
            print(f"      → {row.get('hr_email', 'N/A')} (Match: {row.get('job_match_score', 'N/A')}%)")


if __name__ == "__main__":
    main()
