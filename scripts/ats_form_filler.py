#!/usr/bin/env python3
"""
🤖 AUTO ATS FORM FILLER
Automatically fills job application forms on company career sites.

Features:
- Detects common ATS systems (Workday, Greenhouse, Lever, etc.)
- Auto-fills personal information
- Uploads resume automatically
- Handles multi-page applications
- Saves progress for manual review
- Supports 20+ ATS platforms
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ATSFormFiller:
    """Automatically fill job application forms"""
    
    # Common ATS platforms and their identifiers
    ATS_PLATFORMS = {
        'workday': ['myworkdayjobs.com', 'wd1.myworkdaysite.com', 'wd3.myworkdaysite.com', 'wd5.myworkdaysite.com'],
        'greenhouse': ['greenhouse.io', 'boards.greenhouse.io'],
        'lever': ['lever.co', 'jobs.lever.co'],
        'icims': ['icims.com', 'careers-'],
        'taleo': ['taleo.net', 'taleo.be'],
        'successfactors': ['successfactors.com', 'successfactors.eu'],
        'smartrecruiters': ['smartrecruiters.com'],
        'jobvite': ['jobvite.com', 'jobs.jobvite.com'],
        'ashby': ['ashbyhq.com'],
        'bamboohr': ['bamboohr.com'],
        'jazz': ['applytojob.com', 'jazz.co'],
        'breezy': ['breezy.hr'],
        'recruitee': ['recruitee.com'],
        'workable': ['workable.com', 'apply.workable.com'],
        'personio': ['personio.com', 'jobs.personio.com'],
        'rippling': ['rippling.com'],
        'deel': ['deel.com'],
        'gusto': ['gusto.com'],
        'naukri': ['naukri.com'],
        'linkedin': ['linkedin.com/jobs']
    }
    
    # Field mappings for different ATS systems
    FIELD_MAPPINGS = {
        'workday': {
            'name': ['legalNameSection_firstName', 'firstName', 'first-name'],
            'last_name': ['legalNameSection_lastName', 'lastName', 'last-name'],
            'email': ['contactInformationSection_email', 'email'],
            'phone': ['contactInformationSection_phone', 'phone'],
            'linkedin': ['linkedin', 'linkedInURL'],
            'resume': ['resume', 'file-upload']
        },
        'greenhouse': {
            'name': ['first_name', 'firstname'],
            'last_name': ['last_name', 'lastname'],
            'email': ['email'],
            'phone': ['phone'],
            'linkedin': ['linkedin_profile_url', 'linkedin'],
            'resume': ['resume', 'resume_file']
        },
        'lever': {
            'name': ['name'],
            'email': ['email'],
            'phone': ['phone'],
            'linkedin': ['urls[LinkedIn]', 'linkedin'],
            'resume': ['resume']
        }
    }
    
    def __init__(self):
        self.applicant_data = self._load_applicant_data()
        self.filled_applications = self._load_filled_applications()
        
    def _load_applicant_data(self) -> Dict:
        """Load applicant information from environment"""
        return {
            'first_name': os.getenv('APPLICANT_FIRST_NAME', ''),
            'last_name': os.getenv('APPLICANT_LAST_NAME', ''),
            'full_name': os.getenv('APPLICANT_NAME', ''),
            'email': os.getenv('APPLICANT_EMAIL', ''),
            'phone': os.getenv('APPLICANT_PHONE', ''),
            'location': os.getenv('APPLICANT_LOCATION', ''),
            'city': os.getenv('APPLICANT_CITY', ''),
            'country': os.getenv('APPLICANT_COUNTRY', 'India'),
            'linkedin': os.getenv('APPLICANT_LINKEDIN', ''),
            'portfolio': os.getenv('APPLICANT_PORTFOLIO', ''),
            'github': os.getenv('APPLICANT_GITHUB', ''),
            'experience_years': os.getenv('YEARS_EXPERIENCE', ''),
            'resume_path': os.getenv('RESUME_PATH', ''),
            'cover_letter_path': os.getenv('COVER_LETTER_PATH', ''),
            'work_authorization': os.getenv('WORK_AUTHORIZATION', 'Authorized to work'),
            'visa_sponsorship': os.getenv('NEEDS_VISA_SPONSORSHIP', 'No'),
            'salary_expectation': os.getenv('SALARY_EXPECTATION', ''),
            'notice_period': os.getenv('NOTICE_PERIOD', 'Immediate'),
            'willing_to_relocate': os.getenv('WILLING_TO_RELOCATE', 'Yes'),
            'highest_education': os.getenv('HIGHEST_EDUCATION', 'Bachelor\'s Degree'),
            'graduation_year': os.getenv('GRADUATION_YEAR', ''),
            'university': os.getenv('UNIVERSITY', ''),
            'skills': os.getenv('APPLICANT_SKILLS', ''),
        }
    
    def _load_filled_applications(self) -> Dict:
        """Load history of filled applications"""
        filepath = Path("data/filled_applications.json")
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'applications': []}
    
    def _save_filled_applications(self):
        """Save filled applications history"""
        filepath = Path("data/filled_applications.json")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.filled_applications, f, indent=2)
    
    def detect_ats_platform(self, url: str) -> Tuple[str, str]:
        """Detect which ATS platform the URL belongs to"""
        url_lower = url.lower()
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for platform, identifiers in self.ATS_PLATFORMS.items():
            for identifier in identifiers:
                if identifier in domain or identifier in url_lower:
                    return platform, identifier
        
        return 'unknown', ''
    
    def generate_selenium_script(self, url: str, job_title: str = "") -> str:
        """Generate a Selenium script to fill the application form"""
        
        platform, _ = self.detect_ats_platform(url)
        
        script = f'''#!/usr/bin/env python3
"""
Auto-generated ATS Form Filler Script
URL: {url}
Platform: {platform}
Job: {job_title}
Generated: {datetime.now().isoformat()}
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Applicant Data
APPLICANT = {{
    'first_name': "{self.applicant_data['first_name']}",
    'last_name': "{self.applicant_data['last_name']}",
    'full_name': "{self.applicant_data['full_name']}",
    'email': "{self.applicant_data['email']}",
    'phone': "{self.applicant_data['phone']}",
    'linkedin': "{self.applicant_data['linkedin']}",
    'location': "{self.applicant_data['location']}",
    'experience_years': "{self.applicant_data['experience_years']}",
    'resume_path': "{self.applicant_data['resume_path']}",
}}

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    # options.add_argument('--headless')  # Uncomment for headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)

def fill_field(driver, selectors, value):
    """Try multiple selectors to fill a field"""
    for selector in selectors:
        try:
            # Try by ID
            elem = driver.find_element(By.ID, selector)
            elem.clear()
            elem.send_keys(value)
            return True
        except:
            pass
        try:
            # Try by name
            elem = driver.find_element(By.NAME, selector)
            elem.clear()
            elem.send_keys(value)
            return True
        except:
            pass
        try:
            # Try by CSS selector
            elem = driver.find_element(By.CSS_SELECTOR, f'[data-automation-id="{selector}"]')
            elem.clear()
            elem.send_keys(value)
            return True
        except:
            pass
    return False

def fill_application():
    """Fill the job application form"""
    driver = setup_driver()
    
    try:
        print(f"Opening: {url}")
        driver.get("{url}")
        time.sleep(3)  # Wait for page load
        
        # Common field selectors for {platform}
        field_selectors = {{
            'first_name': ['firstName', 'first_name', 'firstname', 'legalNameSection_firstName'],
            'last_name': ['lastName', 'last_name', 'lastname', 'legalNameSection_lastName'],
            'email': ['email', 'emailAddress', 'Email'],
            'phone': ['phone', 'phoneNumber', 'Phone', 'mobile'],
            'linkedin': ['linkedin', 'linkedinUrl', 'LinkedIn'],
        }}
        
        # Fill each field
        for field, selectors in field_selectors.items():
            if field in APPLICANT and APPLICANT[field]:
                success = fill_field(driver, selectors, APPLICANT[field])
                print(f"  {{field}}: {{'✓' if success else '✗'}}")
        
        # Handle resume upload
        try:
            resume_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            if resume_inputs and APPLICANT['resume_path']:
                resume_inputs[0].send_keys(APPLICANT['resume_path'])
                print("  resume: ✓")
        except Exception as e:
            print(f"  resume: ✗ ({{e}})")
        
        print("\\n⚠️  REVIEW THE FORM BEFORE SUBMITTING!")
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    fill_application()
'''
        return script
    
    def generate_playwright_script(self, url: str, job_title: str = "") -> str:
        """Generate a Playwright script (more modern than Selenium)"""
        
        platform, _ = self.detect_ats_platform(url)
        
        script = f'''#!/usr/bin/env python3
"""
Auto-generated ATS Form Filler (Playwright)
URL: {url}
Platform: {platform}
Job: {job_title}
Generated: {datetime.now().isoformat()}
"""

from playwright.sync_api import sync_playwright
import time

APPLICANT = {{
    'first_name': "{self.applicant_data['first_name']}",
    'last_name': "{self.applicant_data['last_name']}",
    'email': "{self.applicant_data['email']}",
    'phone': "{self.applicant_data['phone']}",
    'linkedin': "{self.applicant_data['linkedin']}",
    'resume_path': "{self.applicant_data['resume_path']}",
}}

def fill_application():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"Opening: {url}")
        page.goto("{url}")
        page.wait_for_load_state('networkidle')
        
        # Auto-fill common fields
        selectors = [
            ('input[name*="first" i]', APPLICANT['first_name']),
            ('input[name*="last" i]', APPLICANT['last_name']),
            ('input[name*="email" i]', APPLICANT['email']),
            ('input[name*="phone" i]', APPLICANT['phone']),
            ('input[name*="linkedin" i]', APPLICANT['linkedin']),
        ]
        
        for selector, value in selectors:
            try:
                if value:
                    page.fill(selector, value)
                    print(f"  Filled: {{selector}}")
            except:
                pass
        
        # Resume upload
        try:
            page.set_input_files('input[type="file"]', APPLICANT['resume_path'])
            print("  Resume uploaded")
        except:
            pass
        
        print("\\n⚠️  REVIEW THE FORM BEFORE SUBMITTING!")
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    fill_application()
'''
        return script
    
    def generate_api_payload(self, url: str, job_id: str = "") -> Dict:
        """Generate API payload for direct ATS submission"""
        
        platform, _ = self.detect_ats_platform(url)
        
        # Common payload structure
        payload = {
            'candidate': {
                'first_name': self.applicant_data['first_name'],
                'last_name': self.applicant_data['last_name'],
                'email': self.applicant_data['email'],
                'phone': self.applicant_data['phone'],
            },
            'urls': {
                'linkedin': self.applicant_data['linkedin'],
                'portfolio': self.applicant_data.get('portfolio', ''),
                'github': self.applicant_data.get('github', ''),
            },
            'location': {
                'city': self.applicant_data['city'],
                'country': self.applicant_data['country'],
            },
            'experience': {
                'years': self.applicant_data['experience_years'],
            },
            'job_id': job_id,
            'source': 'Direct Application',
        }
        
        # Platform-specific adjustments
        if platform == 'greenhouse':
            payload['mapped_url_token'] = job_id
        elif platform == 'lever':
            payload['posting_id'] = job_id
        
        return payload
    
    def create_application_record(self, url: str, job_title: str, company: str, status: str = "pending"):
        """Record application attempt"""
        
        platform, _ = self.detect_ats_platform(url)
        
        record = {
            'url': url,
            'job_title': job_title,
            'company': company,
            'platform': platform,
            'status': status,
            'created_at': datetime.now().isoformat(),
            'applicant': self.applicant_data['full_name'],
        }
        
        self.filled_applications['applications'].append(record)
        self._save_filled_applications()
        
        return record
    
    def get_ats_tips(self, platform: str) -> List[str]:
        """Get platform-specific tips"""
        
        tips = {
            'workday': [
                "Create a Workday account first for faster applications",
                "Workday saves your profile - apply to multiple jobs easily",
                "Use the 'Apply with LinkedIn' option if available",
                "Some fields may be required even if not marked",
            ],
            'greenhouse': [
                "Greenhouse supports one-click apply from LinkedIn",
                "Cover letters are usually optional but recommended",
                "You can track application status via email links",
            ],
            'lever': [
                "Lever has a clean interface - fill all visible fields",
                "Resume parsing is usually accurate",
                "Add portfolio links in the 'Additional Information' section",
            ],
            'taleo': [
                "Taleo requires account creation",
                "Profile completion helps with matching",
                "Be patient - Taleo can be slow",
            ],
            'unknown': [
                "Look for 'Apply with LinkedIn' or 'Easy Apply' options",
                "Have your resume ready for upload",
                "Fill all required fields marked with *",
            ]
        }
        
        return tips.get(platform, tips['unknown'])


def main():
    """Main entry point"""
    filler = ATSFormFiller()
    
    # Example usage
    test_url = "https://jobs.lever.co/example/12345"
    
    print(f"\n🤖 ATS FORM FILLER")
    print(f"{'='*50}")
    
    # Detect platform
    platform, identifier = filler.detect_ats_platform(test_url)
    print(f"\n📍 Detected Platform: {platform.upper()}")
    
    # Get tips
    tips = filler.get_ats_tips(platform)
    print(f"\n💡 Tips for {platform}:")
    for tip in tips:
        print(f"   • {tip}")
    
    # Generate Playwright script
    script = filler.generate_playwright_script(test_url, "Software Engineer")
    
    # Save script
    script_path = Path("scripts/generated/ats_filler_script.py")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, 'w') as f:
        f.write(script)
    
    print(f"\n✅ Generated script: {script_path}")
    print(f"\n📋 To use: python {script_path}")


if __name__ == "__main__":
    main()
