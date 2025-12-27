"""
Centralized Configuration for Portal Selectors and Settings
"""

import os

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESUMES_DIR = os.path.join(BASE_DIR, "resumes")
TAILORED_RESUMES_DIR = os.path.join(RESUMES_DIR, "tailored")
BASE_RESUME_PATH = os.path.join(RESUMES_DIR, "base_resume.pdf")
JOBS_CSV_PATH = os.path.join(DATA_DIR, "jobs_today.csv")
APPLIED_LOG_PATH = os.path.join(DATA_DIR, "applied_log.csv")
ERROR_LOG_PATH = os.path.join(DATA_DIR, "errors.log")

# --- User Application Details ---
# These will be used to auto-fill application forms
USER_DETAILS = {
    "full_name": os.getenv("APPLICANT_NAME", "Ajay Dhage"),
    "first_name": os.getenv("APPLICANT_FIRST_NAME", "Ajay"),
    "last_name": os.getenv("APPLICANT_LAST_NAME", "Dhage"),
    "email": os.getenv("APPLICANT_EMAIL", "ajay.dhage@example.com"),
    "phone": os.getenv("APPLICANT_PHONE", "+91 9876543210"),
    "location": os.getenv("APPLICANT_LOCATION", "Bangalore, Karnataka, India"),
    "city": os.getenv("APPLICANT_CITY", "Bangalore"),
    "country": os.getenv("APPLICANT_COUNTRY", "India"),
    "work_authorization": os.getenv("APPLICANT_WORK_AUTH", "Authorized to work in India"),
    "linkedin_url": os.getenv("APPLICANT_LINKEDIN", "https://www.linkedin.com/in/ajay-dhage"),
    "years_experience": os.getenv("APPLICANT_EXPERIENCE", "3"),
}


# --- Portal Configurations ---
# Storing selectors here makes them easier to update when websites change.
PORTAL_CONFIGS = {
    "linkedin": {
        "domain": "linkedin.com",
        "login_url": "https://www.linkedin.com/login",
        "user_data_dir": os.path.join(DATA_DIR, "playwright_user_data_linkedin"),
        "credentials": {
            "email_env": "LINKEDIN_EMAIL",
            "password_env": "LINKEDIN_PASSWORD",
        },
        "selectors": {
            "email_input": 'input[name="session_key"]',
            "password_input": 'input[name="session_password"]',
            "login_button": 'button[type="submit"]',
            "login_success_indicator": '#global-nav-search',
            "apply_button": 'button:has-text("Easy Apply"), button:has-text("Apply")',
            "upload_resume_input": 'input[type="file"]',
            "submit_application_button": 'button:has-text("Submit application")',
        }
    },
    "indeed": {
        "domain": "indeed.com",
        "login_url": "https://secure.indeed.com/account/login",
        "user_data_dir": os.path.join(DATA_DIR, "playwright_user_data_indeed"),
        "credentials": {
            "email_env": "INDEED_EMAIL",
            "password_env": "INDEED_PASSWORD",
        },
        "selectors": {
            "email_input": 'input[name="__email"]',
            "password_input": 'input[name="__password"]',
            "login_button": 'button[type="submit"]',
            "login_success_indicator": 'a[href*="profile"]',
            "apply_button_iframe": 'iframe[id^="vjs-container-iframe"]',
            "apply_button": 'button:has-text("Apply now"), button:has-text("Apply")',
            "upload_resume_input": 'input[type="file"]',
            "continue_button": 'button:has-text("Continue")',
        }
    },
    "naukri": {
        "domain": "naukri.com",
        "login_url": "https://www.naukri.com/nlogin/login",
        "user_data_dir": os.path.join(DATA_DIR, "playwright_user_data_naukri"),
        "credentials": {
            "email_env": "NAUKRI_EMAIL",
            "password_env": "NAUKRI_PASSWORD",
        },
        "selectors": {
            "email_input": 'input[placeholder="Enter your active Email ID / Username"]',
            "password_input": 'input[placeholder="Enter your password"]',
            "login_button": 'button[type="submit"]',
            "login_success_indicator": 'a[href*="mynaukri"]',
            "apply_button": 'button:has-text("Apply")',
            "application_sent_indicator": 'text="Your application has been sent"',
        }
    },
}

# --- Company Career Page Configurations ---
# Add companies you want to target with their career page URLs and selectors
COMPANY_CAREERS = {
    "google": {
        "name": "Google",
        "careers_url": "https://careers.google.com/jobs/results/",
        "search_params": {
            "q": "",  # Will be filled by keywords
            "location": "Remote",
        },
        "selectors": {
            "job_card": ".gc-card",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/results/']",
            "apply_button": "button:has-text('Apply')",
            "application_form": "form",
        }
    },
    "microsoft": {
        "name": "Microsoft",
        "careers_url": "https://careers.microsoft.com/professionals/us/en/search-results",
        "search_params": {
            "keywords": "",  # Will be filled by keywords
            "location": "Remote",
        },
        "selectors": {
            "job_card": "[data-ph-id*='ph-page-element-page']",
            "job_title": "h2",
            "job_link": "a[data-ph-id*='job-link']",
            "apply_button": "a:has-text('Apply now')",
        }
    },
    "amazon": {
        "name": "Amazon",
        "careers_url": "https://www.amazon.jobs/en/search",
        "search_params": {
            "base_query": "",  # Will be filled by keywords
            "loc_query": "Remote",
        },
        "selectors": {
            "job_card": ".job-tile",
            "job_title": ".job-title",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "#apply-button",
        }
    },
    "apple": {
        "name": "Apple",
        "careers_url": "https://jobs.apple.com/en-us/search",
        "search_params": {"team": ""},
        "selectors": {
            "job_card": ".table--advanced-search__item",
            "job_title": "a[id*='job-title']",
            "job_link": "a[id*='job-title']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "meta": {
        "name": "Meta",
        "careers_url": "https://www.metacareers.com/jobs/",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": "div[data-testid='job-card']",
            "job_title": "a",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "netflix": {
        "name": "Netflix",
        "careers_url": "https://jobs.netflix.com/search",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": ".search-results-item",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "tesla": {
        "name": "Tesla",
        "careers_url": "https://www.tesla.com/careers/search",
        "search_params": {"query": ""},
        "selectors": {
            "job_card": ".tds-site-search-item",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "nvidia": {
        "name": "NVIDIA",
        "careers_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": "li[data-automation-id='compositeContainer']",
            "job_title": "a[data-automation-id='jobTitle']",
            "job_link": "a[data-automation-id='jobTitle']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "adobe": {
        "name": "Adobe",
        "careers_url": "https://careers.adobe.com/us/en/search-results",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".information",
            "job_title": "h2",
            "job_link": "a[data-ph-id*='job-link']",
            "apply_button": "a:has-text('Apply now')",
        }
    },
    "salesforce": {
        "name": "Salesforce",
        "careers_url": "https://careers.salesforce.com/en/jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-result-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "oracle": {
        "name": "Oracle",
        "careers_url": "https://careers.oracle.com/jobs/",
        "search_params": {"keyword": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "ibm": {
        "name": "IBM",
        "careers_url": "https://www.ibm.com/careers/search",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "intel": {
        "name": "Intel",
        "careers_url": "https://jobs.intel.com/en/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "uber": {
        "name": "Uber",
        "careers_url": "https://www.uber.com/us/en/careers/list/",
        "search_params": {"query": ""},
        "selectors": {
            "job_card": "div[data-testid='job-card']",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "lyft": {
        "name": "Lyft",
        "careers_url": "https://www.lyft.com/careers/openings",
        "search_params": {"search": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "airbnb": {
        "name": "Airbnb",
        "careers_url": "https://careers.airbnb.com/positions/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".position-card",
            "job_title": "h3",
            "job_link": "a[href*='/positions/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "spotify": {
        "name": "Spotify",
        "careers_url": "https://jobs.lever.co/spotify",
        "search_params": {"query": ""},
        "selectors": {
            "job_card": ".posting",
            "job_title": "h5",
            "job_link": "a[href*='/spotify/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "shopify": {
        "name": "Shopify",
        "careers_url": "https://www.shopify.com/careers/search",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply now')",
        }
    },
    "stripe": {
        "name": "Stripe",
        "careers_url": "https://stripe.com/jobs/search",
        "search_params": {"query": ""},
        "selectors": {
            "job_card": ".JobsListItem",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/listing/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "zoom": {
        "name": "Zoom",
        "careers_url": "https://careers.zoom.us/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".opening",
            "job_title": "a",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "a:has-text('Apply for this job')",
        }
    },
    "atlassian": {
        "name": "Atlassian",
        "careers_url": "https://www.atlassian.com/company/careers/all-jobs",
        "search_params": {"search": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "paypal": {
        "name": "PayPal",
        "careers_url": "https://jobsearch.paypal-corp.com/en-US/search",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-result",
            "job_title": "h2",
            "job_link": "a[data-ph-id*='job-link']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "twitter": {
        "name": "Twitter (X)",
        "careers_url": "https://careers.twitter.com/en/roles.html",
        "search_params": {"search": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/roles/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "linkedin": {
        "name": "LinkedIn Corp",
        "careers_url": "https://careers.linkedin.com/search",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/jobs/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "cisco": {
        "name": "Cisco",
        "careers_url": "https://jobs.cisco.com/jobs/SearchJobs/",
        "search_params": {"21178=%5B169482%5D": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "a",
            "job_link": "a[href*='/ProjectDetail/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "walmart": {
        "name": "Walmart",
        "careers_url": "https://careers.walmart.com/results",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h2",
            "job_link": "a[href*='/us/jobs/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "target": {
        "name": "Target",
        "careers_url": "https://corporate.target.com/careers/job-search",
        "search_params": {"keyword": ""},
        "selectors": {
            "job_card": ".job-result",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "jpmorgan": {
        "name": "JPMorgan Chase",
        "careers_url": "https://careers.jpmorgan.com/us/en/search-results",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".information",
            "job_title": "h2",
            "job_link": "a[data-ph-id*='job-link']",
            "apply_button": "a:has-text('Apply now')",
        }
    },
    "goldmansachs": {
        "name": "Goldman Sachs",
        "careers_url": "https://www.goldmansachs.com/careers/find-a-career/search/",
        "search_params": {"searchQuery": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "morganstanley": {
        "name": "Morgan Stanley",
        "careers_url": "https://morganstanley.tal.net/vx/lang-en-GB/mobile-0/appcentre-1/brand-2/spa-1/candidate/jobboard/vacancy/1/adv/",
        "search_params": {"ftq": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/requisition/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "bankofamerica": {
        "name": "Bank of America",
        "careers_url": "https://careers.bankofamerica.com/en-us/job-search",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "citigroup": {
        "name": "Citigroup",
        "careers_url": "https://jobs.citi.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "wellsfargo": {
        "name": "Wells Fargo",
        "careers_url": "https://www.wellsfargojobs.com/en/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "capitalone": {
        "name": "Capital One",
        "careers_url": "https://www.capitalonecareers.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "deloitte": {
        "name": "Deloitte",
        "careers_url": "https://www2.deloitte.com/us/en/pages/careers/search-jobs.html",
        "search_params": {"keyword": ""},
        "selectors": {
            "job_card": ".job-result",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "pwc": {
        "name": "PwC",
        "careers_url": "https://www.pwc.com/us/en/careers/job-search.html",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "ey": {
        "name": "EY",
        "careers_url": "https://eygbl.referrals.selectminds.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "accenture": {
        "name": "Accenture",
        "careers_url": "https://www.accenture.com/us-en/careers/jobsearch",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "mckinsey": {
        "name": "McKinsey & Company",
        "careers_url": "https://www.mckinsey.com/careers/search-jobs",
        "search_params": {"query": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "bain": {
        "name": "Bain & Company",
        "careers_url": "https://www.bain.com/careers/find-a-role/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".role-card",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "bcg": {
        "name": "Boston Consulting Group",
        "careers_url": "https://careers.bcg.com/search",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "boeing": {
        "name": "Boeing",
        "careers_url": "https://jobs.boeing.com/search",
        "search_params": {"q": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "lockheedmartin": {
        "name": "Lockheed Martin",
        "careers_url": "https://www.lockheedmartinjobs.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "ge": {
        "name": "General Electric",
        "careers_url": "https://jobs.gecareers.com/global/en/search-results",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".information",
            "job_title": "h2",
            "job_link": "a[data-ph-id*='job-link']",
            "apply_button": "a:has-text('Apply now')",
        }
    },
    "ford": {
        "name": "Ford Motor Company",
        "careers_url": "https://corporate.ford.com/careers/job-search.html",
        "search_params": {"keyword": ""},
        "selectors": {
            "job_card": ".job-result",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "gm": {
        "name": "General Motors",
        "careers_url": "https://search-careers.gm.com/en/jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "dell": {
        "name": "Dell Technologies",
        "careers_url": "https://jobs.dell.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
    "hp": {
        "name": "HP Inc.",
        "careers_url": "https://jobs.hp.com/en-us/search/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply')",
        }
    },
    "vmware": {
        "name": "VMware",
        "careers_url": "https://careers.vmware.com/search-jobs",
        "search_params": {"k": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h2",
            "job_link": "a[href*='/job/']",
            "apply_button": "a:has-text('Apply Now')",
        }
    },
}

