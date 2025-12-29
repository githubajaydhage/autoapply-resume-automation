"""
Recruiting Agencies Database & Finder
Sends resumes to staffing agencies that specialize in various industries.
"""

import os
import logging
import requests
import re
import random
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)


class RecruitingAgencyFinder:
    """Find and manage recruiting agencies for job applications."""
    
    # Curated database of recruiting agencies in India
    # Organized by specialization
    AGENCIES_DATABASE = {
        # General Staffing Agencies (Bangalore/India)
        'general': [
            {'name': 'TeamLease', 'email': 'careers@teamlease.com', 'specialization': 'General Staffing'},
            {'name': 'Quess Corp', 'email': 'recruitment@quesscorp.com', 'specialization': 'General Staffing'},
            {'name': 'Randstad India', 'email': 'info.india@randstad.in', 'specialization': 'General Staffing'},
            {'name': 'Adecco India', 'email': 'india.careers@adecco.com', 'specialization': 'General Staffing'},
            {'name': 'ManpowerGroup India', 'email': 'india@manpowergroup.com', 'specialization': 'General Staffing'},
            {'name': 'Kelly Services India', 'email': 'india@kellyservices.com', 'specialization': 'General Staffing'},
            {'name': 'ABC Consultants', 'email': 'resume@abcconsultants.in', 'specialization': 'Executive Search'},
            {'name': 'Naukri Hiring', 'email': 'hiring@naukri.com', 'specialization': 'Job Portal'},
            {'name': 'Indeed Hiring', 'email': 'employers@indeed.com', 'specialization': 'Job Portal'},
            {'name': 'Monster India', 'email': 'employers@monsterindia.com', 'specialization': 'Job Portal'},
        ],
        
        # Interior Design / Architecture Specialists
        'interior_design': [
            {'name': 'Designerrs Academy Placements', 'email': 'placements@designerrs.com', 'specialization': 'Design'},
            {'name': 'ISDI Placements', 'email': 'placements@isdi.in', 'specialization': 'Design'},
            {'name': 'Creative Heads', 'email': 'info@creativeheads.in', 'specialization': 'Creative/Design'},
            {'name': 'Design Avenue Recruitment', 'email': 'hr@designavenue.in', 'specialization': 'Interior Design'},
            {'name': 'Arch Staffing', 'email': 'resume@archstaffing.in', 'specialization': 'Architecture'},
            {'name': 'Build Talent', 'email': 'careers@buildtalent.in', 'specialization': 'Construction/Interior'},
            {'name': 'Space Matrix Recruitment', 'email': 'hr@spacematrix.com', 'specialization': 'Interior Design'},
            {'name': 'JLL India Recruitment', 'email': 'careers.india@jll.com', 'specialization': 'Real Estate/Design'},
            {'name': 'Colliers India', 'email': 'careers.india@colliers.com', 'specialization': 'Real Estate/Design'},
            {'name': 'Cushman Wakefield India', 'email': 'careers.india@cushwake.com', 'specialization': 'Real Estate/Design'},
        ],
        
        # IT / DevOps / Cloud Specialists
        'it_devops': [
            {'name': 'Experis IT', 'email': 'experis.india@experis.com', 'specialization': 'IT Staffing'},
            {'name': 'Tekwissen', 'email': 'resumes@tekwissen.com', 'specialization': 'IT Staffing'},
            {'name': 'Cyient Talent', 'email': 'careers@cyient.com', 'specialization': 'Engineering/IT'},
            {'name': 'Mastech Digital', 'email': 'careers@mastechdigital.com', 'specialization': 'IT/Cloud'},
            {'name': 'NLB Services', 'email': 'careers@nlbservices.com', 'specialization': 'IT Staffing'},
            {'name': 'Nous Infosystems', 'email': 'careers@nousinfo.com', 'specialization': 'IT/Cloud'},
            {'name': 'Xoriant Staffing', 'email': 'careers@xoriant.com', 'specialization': 'IT/DevOps'},
            {'name': 'Mindtree Consulting', 'email': 'careers@mindtree.com', 'specialization': 'IT/Cloud'},
            {'name': 'Persistent Systems', 'email': 'careers@persistent.com', 'specialization': 'IT/DevOps'},
            {'name': 'Mphasis Recruitment', 'email': 'careers@mphasis.com', 'specialization': 'IT Staffing'},
            {'name': 'Coforge Careers', 'email': 'careers@coforge.com', 'specialization': 'IT/Cloud'},
            {'name': 'LTIMindtree', 'email': 'careers@ltimindtree.com', 'specialization': 'IT/DevOps'},
            {'name': 'Sonata Software', 'email': 'careers@sonata-software.com', 'specialization': 'IT Staffing'},
            {'name': 'Zensar Technologies', 'email': 'careers@zensar.com', 'specialization': 'IT/Cloud'},
        ],
        
        # Bangalore-specific agencies
        'bangalore': [
            {'name': 'Careernet', 'email': 'resume@careernet.in', 'specialization': 'General - Bangalore'},
            {'name': 'SkillVentory', 'email': 'resume@skillventory.com', 'specialization': 'General - Bangalore'},
            {'name': 'Wenger Watson', 'email': 'resume@wengerwatson.com', 'specialization': 'Executive Search'},
            {'name': 'Gi Group India', 'email': 'bangalore@gigroup.com', 'specialization': 'General - Bangalore'},
            {'name': 'CIEL HR', 'email': 'bangalore@cielhr.com', 'specialization': 'General - Bangalore'},
            {'name': 'Hire Right', 'email': 'resume@hireright.in', 'specialization': 'Background/Staffing'},
            {'name': 'Antal International', 'email': 'india@antal.com', 'specialization': 'Executive Search'},
            {'name': 'Michael Page India', 'email': 'bangalore@michaelpage.com', 'specialization': 'Executive Search'},
            {'name': 'Robert Walters India', 'email': 'bangalore@robertwalters.com', 'specialization': 'Executive Search'},
            {'name': 'Hays India', 'email': 'bangalore@hays.com', 'specialization': 'Executive Search'},
        ],
        
        # Freelance / Gig Economy Platforms
        'freelance': [
            {'name': 'Upwork', 'email': 'support@upwork.com', 'specialization': 'Freelance'},
            {'name': 'Fiverr Business', 'email': 'business@fiverr.com', 'specialization': 'Freelance'},
            {'name': 'Toptal', 'email': 'apply@toptal.com', 'specialization': 'Freelance'},
            {'name': 'Flexiple', 'email': 'careers@flexiple.com', 'specialization': 'Freelance'},
            {'name': 'Turing', 'email': 'apply@turing.com', 'specialization': 'Remote Jobs'},
            {'name': 'Arc.dev', 'email': 'developers@arc.dev', 'specialization': 'Remote Jobs'},
        ],
    }
    
    def __init__(self, job_keywords: List[str] = None):
        """Initialize with job keywords to determine relevant agencies."""
        self.job_keywords = job_keywords or []
        self.job_keywords_lower = [kw.lower() for kw in self.job_keywords]
        
    def _determine_category(self) -> List[str]:
        """Determine which agency categories to use based on job keywords."""
        categories = ['general', 'bangalore']  # Always include these
        
        keywords_str = ' '.join(self.job_keywords_lower)
        
        # Interior design keywords
        interior_keywords = ['interior', 'design', 'architect', 'autocad', '3ds max', 
                            'sketchup', 'revit', 'furniture', 'decor', 'space',
                            'estimation', 'quantity surveyor', 'billing engineer',
                            'drafting', 'civil', 'construction']
        is_interior = any(kw in keywords_str for kw in interior_keywords)
        if is_interior:
            categories.append('interior_design')
            
        # IT/DevOps keywords - only if NOT interior design
        # The keyword 'engineer' alone should NOT trigger IT for estimation/billing engineers
        it_keywords = ['devops', 'cloud', 'aws', 'azure', 'kubernetes', 'docker',
                      'python', 'java', 'developer', 'sre', 'platform', 'software',
                      'backend', 'frontend', 'fullstack', 'data engineer', 'ml engineer']
        is_it = any(kw in keywords_str for kw in it_keywords)
        if is_it and not is_interior:
            categories.append('it_devops')
            
        return list(set(categories))
    
    def get_relevant_agencies(self, max_agencies: int = 30) -> List[Dict]:
        """Get agencies relevant to the job keywords."""
        categories = self._determine_category()
        logging.info(f"📋 Selected agency categories: {categories}")
        
        all_agencies = []
        for category in categories:
            agencies = self.AGENCIES_DATABASE.get(category, [])
            all_agencies.extend(agencies)
        
        # Remove duplicates by email
        seen_emails = set()
        unique_agencies = []
        for agency in all_agencies:
            if agency['email'].lower() not in seen_emails:
                seen_emails.add(agency['email'].lower())
                unique_agencies.append(agency)
        
        # Shuffle and limit
        random.shuffle(unique_agencies)
        result = unique_agencies[:max_agencies]
        
        logging.info(f"🏢 Found {len(result)} recruiting agencies for your profile")
        return result
    
    def search_agencies_online(self, location: str = "Bangalore") -> List[Dict]:
        """Search for recruiting agencies online using DuckDuckGo."""
        agencies = []
        
        # Build search queries based on job keywords
        keyword_str = ' '.join(self.job_keywords[:3]) if self.job_keywords else 'jobs'
        queries = [
            f"{keyword_str} recruitment agency {location} email",
            f"{keyword_str} staffing company {location} careers",
            f"placement consultancy {keyword_str} {location}",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for query in queries[:2]:  # Limit to 2 queries
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Extract emails from response
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails = re.findall(email_pattern, response.text)
                    
                    for email in emails[:5]:
                        if self._is_valid_agency_email(email):
                            agencies.append({
                                'name': email.split('@')[1].split('.')[0].title() + ' Recruitment',
                                'email': email,
                                'specialization': 'Staffing Agency',
                                'source': 'online_search'
                            })
                
                time.sleep(1)  # Polite delay
                
            except Exception as e:
                logging.debug(f"Search failed for {query}: {e}")
                continue
        
        logging.info(f"🔍 Found {len(agencies)} agencies from online search")
        return agencies
    
    def _is_valid_agency_email(self, email: str) -> bool:
        """Check if email looks like a valid agency/HR email."""
        email_lower = email.lower()
        
        # Skip invalid patterns
        invalid_patterns = [
            'example.com', 'test.com', 'gmail.com', 'yahoo.com', 'hotmail.com',
            'outlook.com', 'noreply', 'no-reply', 'donotreply', 'unsubscribe',
            'bounce', 'mailer-daemon', 'postmaster'
        ]
        
        if any(pattern in email_lower for pattern in invalid_patterns):
            return False
        
        # Prefer HR-related emails
        hr_patterns = ['hr', 'career', 'recruit', 'talent', 'resume', 'job', 
                      'hiring', 'placement', 'apply', 'staffing']
        
        return any(pattern in email_lower for pattern in hr_patterns)
    
    def get_all_agencies(self, include_online_search: bool = True, max_total: int = 50) -> List[Dict]:
        """Get all agencies from database and optionally online search."""
        all_agencies = self.get_relevant_agencies(max_agencies=40)
        
        if include_online_search:
            online_agencies = self.search_agencies_online()
            
            # Add online agencies if not already in list
            existing_emails = {a['email'].lower() for a in all_agencies}
            for agency in online_agencies:
                if agency['email'].lower() not in existing_emails:
                    all_agencies.append(agency)
                    existing_emails.add(agency['email'].lower())
        
        return all_agencies[:max_total]


def get_agency_emails_for_profile(job_keywords: List[str] = None, max_agencies: int = 30) -> List[Dict]:
    """
    Main function to get recruiting agency emails for a profile.
    
    Args:
        job_keywords: List of job-related keywords
        max_agencies: Maximum number of agencies to return
        
    Returns:
        List of agency dictionaries with name, email, specialization
    """
    if job_keywords is None:
        # Get from environment
        keywords_str = os.environ.get('JOB_KEYWORDS', '')
        job_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
    
    finder = RecruitingAgencyFinder(job_keywords)
    agencies = finder.get_all_agencies(include_online_search=True, max_total=max_agencies)
    
    logging.info(f"✅ Total recruiting agencies found: {len(agencies)}")
    return agencies


if __name__ == "__main__":
    # Test with interior design keywords
    keywords = ["interior designer", "autocad", "3ds max", "sketchup"]
    agencies = get_agency_emails_for_profile(keywords, max_agencies=20)
    
    print("\n📋 Recruiting Agencies for Interior Design Profile:")
    print("-" * 60)
    for agency in agencies:
        print(f"  • {agency['name']}: {agency['email']} ({agency['specialization']})")
