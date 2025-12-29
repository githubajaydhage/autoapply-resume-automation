"""
Curated HR Email Database - Pre-verified HR contact emails for major companies
These are publicly available HR/recruitment emails from company websites and job postings
"""

import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


# CURATED HR/RECRUITMENT EMAILS - Publicly available from company career pages
# These are general recruitment inboxes, not personal emails

CURATED_HR_EMAILS = [
    # Major Indian IT Companies (VERIFIED - removed bounced emails)
    # Removed: careers@infosys.com, askhr@infosys.com, careers@tcs.com, resume@tcs.com (bounced)
    # Removed: recruitment@wipro.com (bounced), careers@mindtree.com (bounced)
    # Removed: careers@ltimindtree.com (bounced), careers.india@capgemini.com (bounced)
    # Removed: india.recruiting@accenture.com (bounced), careers@in.ey.com (bounced)
    # Removed: careers@kpmg.com (bounced), in_careers@pwc.com (bounced)
    
    {"company": "Wipro", "email": "careers@wipro.com", "type": "general"},
    {"company": "Wipro", "email": "helpdesk.recruitment@wipro.com", "type": "hr"},  # Verified working
    {"company": "HCL Technologies", "email": "careers@hcl.com", "type": "general"},
    {"company": "Tech Mahindra", "email": "careers@techmahindra.com", "type": "general"},
    {"company": "Mphasis", "email": "careers@mphasis.com", "type": "general"},
    {"company": "Mphasis", "email": "accomodationrequest@mphasis.com", "type": "general"},  # Verified working
    {"company": "Cognizant", "email": "careers@cognizant.com", "type": "general"},
    {"company": "Deloitte", "email": "indiatalent@deloitte.com", "type": "general"},
    
    # Startups & Product Companies (India) - VERIFIED WORKING
    {"company": "Razorpay", "email": "careers@razorpay.com", "type": "general"},
    {"company": "Razorpay", "email": "career@razorpay.com", "type": "general"},  # Verified working
    {"company": "Zerodha", "email": "careers@zerodha.com", "type": "general"},
    {"company": "PhonePe", "email": "careers@phonepe.com", "type": "general"},  # Verified working
    {"company": "Swiggy", "email": "careers@swiggy.in", "type": "general"},  # Verified working
    {"company": "Zomato", "email": "careers@zomato.com", "type": "general"},  # Verified working
    # Removed: careers@cred.club (mailbox doesn't exist)
    {"company": "Meesho", "email": "careers@meesho.com", "type": "general"},  # Verified working
    {"company": "Groww", "email": "careers@groww.in", "type": "general"},  # Verified working
    {"company": "Freshworks", "email": "careers@freshworks.com", "type": "general"},  # Verified working
    # Removed: careers@zohocorp.com (doesn't exist)
    {"company": "Zoho", "email": "jobs@zohocorp.com", "type": "general"},  # Verified working
    # Removed: careers@flipkart.com (doesn't exist)
    # Removed: careers@olacabs.com (bounced)
    # Removed: careers@paytm.com (bounced)
    # Removed: careers@dream11.com (doesn't exist)
    # Removed: careers@byjus.com (doesn't exist)
    {"company": "Unacademy", "email": "careers@unacademy.com", "type": "general"},  # Verified working
    # Removed: careers@upgrad.com (doesn't exist)
    {"company": "Dunzo", "email": "careers@dunzo.in", "type": "general"},  # Verified working
    {"company": "Urban Company", "email": "careers@urbancompany.com", "type": "general"},  # Verified working
    {"company": "PolicyBazaar", "email": "careers@policybazaar.com", "type": "general"},  # Verified working
    {"company": "Nykaa", "email": "careers@nykaa.com", "type": "general"},  # Verified working
    # Removed: careers@lenskart.com (bounced)
    # Removed: careers@bigbasket.com (bounced)
    {"company": "Delhivery", "email": "careers@delhivery.com", "type": "general"},
    # Removed: careers@sharechat.co (bounced)
    # Removed: careers@atherenergy.com (bounced)
    {"company": "Rapido", "email": "careers@rapido.bike", "type": "general"},
    
    # Global Tech Giants (Most don't accept direct emails)
    # Removed: jobs@google.com, careers@microsoft.com (rejected), jobs@apple.com, etc.
    {"company": "IBM", "email": "recrops@ca.ibm.com", "type": "general"},  # Verified working
    
    # Banks & Finance (India) - Keep cautiously
    {"company": "HDFC Bank", "email": "hrcare@hdfcbank.com", "type": "hr"},
    {"company": "ICICI Bank", "email": "careers@icicibank.com", "type": "general"},
    {"company": "Kotak Mahindra", "email": "careers@kotak.com", "type": "general"},
    {"company": "Axis Bank", "email": "careers@axisbank.com", "type": "general"},
    {"company": "Yes Bank", "email": "careers@yesbank.in", "type": "general"},
    {"company": "Bajaj Finance", "email": "careers@bajajfinserv.in", "type": "general"},
    
    # Consulting & Analytics (Verified)
    {"company": "Mu Sigma", "email": "careers@mu-sigma.com", "type": "general"},
    {"company": "Fractal Analytics", "email": "careers@fractal.ai", "type": "general"},
    {"company": "Tiger Analytics", "email": "careers@tigeranalytics.com", "type": "general"},
    {"company": "LatentView", "email": "careers@latentview.com", "type": "general"},
    
    # E-commerce & Retail
    {"company": "Myntra", "email": "careers@myntra.com", "type": "general"},
    {"company": "FirstCry", "email": "careers@firstcry.com", "type": "general"},
    
    # Additional verified emails from previous runs
    {"company": "BharatPe", "email": "careers@bharatpe.com", "type": "general"},
    {"company": "Birlasoft", "email": "careers@birlasoft.com", "type": "general"},
    {"company": "BlackBuck", "email": "careers@blackbuck.com", "type": "general"},
    {"company": "BrowserStack", "email": "careers@browserstack.com", "type": "general"},
    {"company": "Cars24", "email": "careers@cars24.com", "type": "general"},
    {"company": "Chargebee", "email": "careers@chargebee.com", "type": "general"},
    {"company": "ClearTax", "email": "careers@cleartax.in", "type": "general"},
    {"company": "Cleartrip", "email": "careers@cleartrip.com", "type": "general"},
    {"company": "Coforge", "email": "careers@coforge.com", "type": "general"},
    {"company": "Cyient", "email": "careers@cyient.com", "type": "general"},
    {"company": "Darwinbox", "email": "careers@darwinbox.com", "type": "general"},
    {"company": "Druva", "email": "careers@druva.com", "type": "general"},
    {"company": "Freecharge", "email": "careers@freecharge.in", "type": "general"},
    {"company": "Games24x7", "email": "careers@games24x7.com", "type": "general"},
    {"company": "Genpact", "email": "careers@genpact.com", "type": "general"},
    {"company": "Goibibo", "email": "careers@goibibo.com", "type": "general"},
    {"company": "Happiest Minds", "email": "careers@happiestminds.com", "type": "general"},
    {"company": "HashedIn", "email": "careers@hashedin.com", "type": "general"},
    {"company": "HealthKart", "email": "careers@healthkart.com", "type": "general"},
    {"company": "Hexaware", "email": "careers@hexaware.com", "type": "general"},
    {"company": "Housing.com", "email": "careers@housing.com", "type": "general"},
    {"company": "Icertis", "email": "careers@icertis.com", "type": "general"},
    {"company": "Ixigo", "email": "careers@ixigo.com", "type": "general"},
    {"company": "LatentView Analytics", "email": "careers@latentview.com", "type": "general"},
    {"company": "LeadSquared", "email": "careers@leadsquared.com", "type": "general"},
    {"company": "MPL", "email": "careers@mpl.live", "type": "general"},
    {"company": "MagicBricks", "email": "careers@magicbricks.com", "type": "general"},
    {"company": "MobiKwik", "email": "careers@mobikwik.com", "type": "general"},
    {"company": "Netmeds", "email": "careers@netmeds.com", "type": "general"},
    {"company": "NoBroker", "email": "careers@nobroker.com", "type": "general"},
    {"company": "PayU", "email": "careers@payu.in", "type": "general"},
    {"company": "PharmEasy", "email": "careers@pharmeasy.in", "type": "general"},
    {"company": "Physics Wallah", "email": "careers@physicswallah.com", "type": "general"},
    {"company": "Porter", "email": "careers@porter.in", "type": "general"},
    {"company": "Postman", "email": "careers@postman.com", "type": "general"},
    {"company": "Practo", "email": "careers@practo.com", "type": "general"},
    {"company": "Purplle", "email": "careers@purplle.com", "type": "general"},
    {"company": "Rivigo", "email": "careers@rivigo.com", "type": "general"},
    {"company": "Slice", "email": "careers@sliceit.com", "type": "general"},
    {"company": "Sonata Software", "email": "careers@sonata-software.com", "type": "general"},
    {"company": "Spinny", "email": "careers@spinny.com", "type": "general"},
    {"company": "Tata 1mg", "email": "careers@1mg.com", "type": "general"},
    {"company": "Testbook", "email": "careers@testbook.com", "type": "general"},
    {"company": "ThoughtSpot", "email": "careers@thoughtspot.com", "type": "general"},
    {"company": "Tredence", "email": "careers@tredence.com", "type": "general"},
    {"company": "Vedantu", "email": "careers@vedantu.com", "type": "general"},
    {"company": "Whatfix", "email": "careers@whatfix.com", "type": "general"},
    {"company": "Zensar", "email": "careers@zensar.com", "type": "general"},
]


class CuratedHRDatabase:
    """Provides curated, pre-verified HR contact emails."""
    
    # Industry keywords mapping
    INDUSTRY_KEYWORDS = {
        'interior_design': ['interior', 'design', 'architect', 'autocad', 'revit', 'sketchup',
                           'estimation', 'quantity surveyor', 'billing', 'drafting', 'civil',
                           'construction', '3ds max', 'furniture', 'decor'],
        'it_tech': ['software', 'developer', 'devops', 'cloud', 'data', 'python', 'java',
                   'engineer', 'backend', 'frontend', 'fullstack', 'sre', 'kubernetes', 'aws'],
        'finance': ['finance', 'banking', 'analyst', 'accounting', 'audit'],
    }
    
    # Companies by industry
    INTERIOR_DESIGN_COMPANIES = [
        'livspace', 'homelane', 'designcafe', 'bonito', 'urbanclap', 'decorpot',
        'infini home', 'interior company', 'arrivae', 'godrej interio', 'asian paints',
        'sleek', 'wooden street', 'urban ladder', 'pepperfry', 'nilkamal', 'hafele',
        'hettich', 'prestige', 'sobha', 'brigade', 'puravankara', 'godrej properties',
        'dlf', 'l&t realty', 'mahindra lifespace', 'lodha', 'oberoi realty', 'shapoorji',
        'embassy', 'bengaluru development', 'total environment', 'mantri', 'salarpuria',
        'century real estate', 'sumadhura', 'vaishnavi', 'shriram properties', 'birla estates',
        'tata housing', 'rohan builders', 'nahar', 'hm constructions', 'hiranandani',
        'kalpataru', 'l&t construction', 'simplex', 'nagarjuna construction', 'ultratech',
        'acc cement', 'ambuja cement', 'dalmia cement', 'jk cement', 'saint-gobain',
        'nippon paint', 'kansai nerolac', 'berger paints', 'indigo paints'
    ]
    
    def __init__(self):
        self.emails = CURATED_HR_EMAILS
        self.job_keywords = os.environ.get('JOB_KEYWORDS', '').lower()
        
    def _detect_industry(self) -> str:
        """Detect which industry the user is targeting based on JOB_KEYWORDS."""
        if not self.job_keywords:
            return 'all'
        
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            if any(kw in self.job_keywords for kw in keywords):
                return industry
        return 'all'
    
    def _is_interior_design_company(self, company_name: str) -> bool:
        """Check if company is in interior design/construction industry."""
        company_lower = company_name.lower()
        return any(ic in company_lower for ic in self.INTERIOR_DESIGN_COMPANIES)
        
    def get_all_emails(self) -> pd.DataFrame:
        """Get all curated HR emails as DataFrame, prioritized by industry."""
        df = pd.DataFrame(self.emails)
        df['source'] = 'curated_database'
        df['scraped_at'] = datetime.now().isoformat()
        
        # Detect industry and prioritize
        industry = self._detect_industry()
        logging.info(f"🎯 Detected industry from JOB_KEYWORDS: {industry}")
        
        if industry == 'interior_design':
            # Add priority column - interior design companies first
            df['is_priority'] = df['company'].apply(self._is_interior_design_company)
            df = df.sort_values('is_priority', ascending=False).reset_index(drop=True)
            priority_count = df['is_priority'].sum()
            logging.info(f"📊 Prioritized {priority_count} interior design companies to the top")
            df = df.drop(columns=['is_priority'])
        
        return df
    
    def get_emails_for_company(self, company_name: str) -> list:
        """Get HR emails for a specific company."""
        company_lower = company_name.lower()
        matching = [
            e for e in self.emails 
            if company_lower in e['company'].lower()
        ]
        return matching
    
    def get_emails_by_type(self, email_type: str = "general") -> list:
        """Get emails by type (general, hr, recruitment)."""
        return [e for e in self.emails if e['type'] == email_type]
    
    def save_to_csv(self, filepath: str = None):
        """Save curated emails to CSV."""
        if not filepath:
            filepath = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'curated_hr_emails.csv'
            )
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = self.get_all_emails()
        df.to_csv(filepath, index=False)
        logging.info(f"💾 Saved {len(df)} curated HR emails to {filepath}")
        return df


def main():
    """Load and save curated HR email database."""
    logging.info("="*60)
    logging.info("📧 CURATED HR EMAIL DATABASE")
    logging.info("="*60)
    
    db = CuratedHRDatabase()
    df = db.save_to_csv()
    
    # Also save to all_hr_emails.csv for compatibility
    all_hr_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv'
    )
    
    # Load existing if any
    if os.path.exists(all_hr_path):
        existing = pd.read_csv(all_hr_path)
        if existing.empty:
            combined = df
        else:
            combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['email'], keep='first')
    else:
        combined = df
    
    combined.to_csv(all_hr_path, index=False)
    
    logging.info(f"✅ Total HR emails available: {len(combined)}")
    logging.info("="*60)
    
    # Print summary by company type
    logging.info("\n📊 EMAIL SUMMARY:")
    logging.info(f"   Total emails: {len(df)}")
    logging.info(f"   Unique companies: {df['company'].nunique()}")
    
    return df


if __name__ == "__main__":
    main()
