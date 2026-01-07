"""
Centralized Configuration for Portal Selectors and Settings
"""

import os

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESUMES_DIR = os.path.join(BASE_DIR, "resumes")
TAILORED_RESUMES_DIR = os.path.join(RESUMES_DIR, "tailored")
# Resume filename from environment variable (set in workflow) - REQUIRED
RESUME_FILENAME = os.getenv("RESUME_FILENAME", "resume.pdf")
BASE_RESUME_PATH = os.path.join(RESUMES_DIR, RESUME_FILENAME)
JOBS_CSV_PATH = os.path.join(DATA_DIR, "jobs_today.csv")
APPLIED_LOG_PATH = os.path.join(DATA_DIR, "applied_log.csv")
ERROR_LOG_PATH = os.path.join(DATA_DIR, "errors.log")

# --- User Application Details ---
# ALL values should be set via environment variables in the workflow!
# These empty defaults ensure workflows must provide proper configuration.
USER_DETAILS = {
    "full_name": os.getenv("APPLICANT_NAME", ""),
    "first_name": os.getenv("APPLICANT_FIRST_NAME", ""),
    "last_name": os.getenv("APPLICANT_LAST_NAME", ""),
    "email": os.getenv("APPLICANT_EMAIL", os.getenv("SENDER_EMAIL", "")),
    "phone": os.getenv("APPLICANT_PHONE", ""),
    "location": os.getenv("APPLICANT_LOCATION", ""),
    "city": os.getenv("APPLICANT_CITY", ""),
    "country": os.getenv("APPLICANT_COUNTRY", ""),
    "work_authorization": os.getenv("APPLICANT_WORK_AUTH", ""),
    "linkedin_url": os.getenv("APPLICANT_LINKEDIN", ""),
    "years_experience": os.getenv("APPLICANT_EXPERIENCE", os.getenv("YEARS_EXPERIENCE", "")),
    # Portfolio & Project Links
    "github_url": os.getenv("APPLICANT_GITHUB", ""),
    "portfolio_url": os.getenv("APPLICANT_PORTFOLIO", ""),
    "kaggle_url": os.getenv("APPLICANT_KAGGLE", ""),
    # Key projects and skills - from workflow JOB_KEYWORDS or APPLICANT_SKILLS
    "key_projects": os.getenv("APPLICANT_PROJECTS", ""),
    "target_role": os.getenv("APPLICANT_TARGET_ROLE", os.getenv("JOB_KEYWORDS", "").split(",")[0].strip() if os.getenv("JOB_KEYWORDS", "") else ""),
    "key_skills": os.getenv("APPLICANT_SKILLS", os.getenv("JOB_KEYWORDS", "")),
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
            "email_input": 'input[name="session_key"], input#username',
            "password_input": 'input[name="session_password"], input#password',
            "login_button": 'button[type="submit"], button:has-text("Sign in")',
            # Multiple indicators for successful login
            "login_success_indicator": '#global-nav-search, .global-nav, .feed-identity-module, .search-global-typeahead, nav[aria-label*="Primary"]',
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
        # Alternative login URLs to try if main one is blocked
        "login_url_alternatives": [
            "https://www.naukri.com/nlogin/login",
            "https://login.naukri.com/",
            "https://www.naukri.com/registration/createAccount",
        ],
        "user_data_dir": os.path.join(DATA_DIR, "playwright_user_data_naukri"),
        "credentials": {
            "email_env": "NAUKRI_EMAIL",
            "password_env": "NAUKRI_PASSWORD",
        },
        "selectors": {
            # Multiple fallback selectors for email input
            "email_input": 'input[placeholder*="Email"], input[placeholder*="email"], input[type="text"][name*="email"], input#usernameField, input[placeholder*="Username"], input[name="usernameField"]',
            # Multiple fallback selectors for password input  
            "password_input": 'input[placeholder*="password"], input[placeholder*="Password"], input[type="password"], input#passwordField, input[name="passwordField"]',
            "login_button": 'button[type="submit"], button:has-text("Login"), button:has-text("Sign in"), div:has-text("Login"):not(:has(*))',
            # Multiple indicators for successful login
            "login_success_indicator": 'a[href*="mynaukri"], .nI-gNb-menuItems, img[class*="avatar"], .nI-gNb-drawer__toggle, div[class*="user-profile"]',
            "apply_button": 'button:has-text("Apply"), button:has-text("Apply on company site")',
            "application_sent_indicator": 'text="Your application has been sent", text="Applied successfully", text="Already applied"',
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
    # Indian IT Services & Consulting Giants
    "tcs": {
        "name": "Tata Consultancy Services",
        "careers_url": "https://www.tcs.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "infosys": {
        "name": "Infosys",
        "careers_url": "https://www.infosys.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".career-card",
            "job_title": "h3",
            "job_link": "a[href*='career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "wipro": {
        "name": "Wipro",
        "careers_url": "https://careers.wipro.com/careers-home/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "hcl": {
        "name": "HCL Technologies",
        "careers_url": "https://www.hcltech.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/careers/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "techm": {
        "name": "Tech Mahindra",
        "careers_url": "https://careers.techmahindra.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "ltimindtree": {
        "name": "LTIMindtree",
        "careers_url": "https://www.ltimindtree.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "mphasis": {
        "name": "Mphasis",
        "careers_url": "https://careers.mphasis.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "persistent": {
        "name": "Persistent Systems",
        "careers_url": "https://www.persistent.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".career-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "mindtree": {
        "name": "Mindtree",
        "careers_url": "https://www.mindtree.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cognizant": {
        "name": "Cognizant",
        "careers_url": "https://careers.cognizant.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    # Global Tech & Software Companies
    "sap": {
        "name": "SAP",
        "careers_url": "https://jobs.sap.com/search/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "servicenow": {
        "name": "ServiceNow",
        "careers_url": "https://careers.servicenow.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "workday": {
        "name": "Workday",
        "careers_url": "https://workday.wd5.myworkdayjobs.com/Workday",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "snowflake": {
        "name": "Snowflake",
        "careers_url": "https://careers.snowflake.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "databricks": {
        "name": "Databricks",
        "careers_url": "https://www.databricks.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "tableau": {
        "name": "Tableau",
        "careers_url": "https://www.salesforce.com/company/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "splunk": {
        "name": "Splunk",
        "careers_url": "https://www.splunk.com/en_us/careers.html",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "mongodb": {
        "name": "MongoDB",
        "careers_url": "https://www.mongodb.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "redis": {
        "name": "Redis",
        "careers_url": "https://redis.com/company/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "confluent": {
        "name": "Confluent",
        "careers_url": "https://www.confluent.io/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Cloud & Infrastructure
    "digitalocean": {
        "name": "DigitalOcean",
        "careers_url": "https://www.digitalocean.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cloudflare": {
        "name": "Cloudflare",
        "careers_url": "https://www.cloudflare.com/careers/jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "hashicorp": {
        "name": "HashiCorp",
        "careers_url": "https://www.hashicorp.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "veritas": {
        "name": "Veritas Technologies",
        "careers_url": "https://www.veritas.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "nutanix": {
        "name": "Nutanix",
        "careers_url": "https://www.nutanix.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # E-commerce & Marketplaces
    "flipkart": {
        "name": "Flipkart",
        "careers_url": "https://www.flipkartcareers.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-tile",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "snapdeal": {
        "name": "Snapdeal",
        "careers_url": "https://www.snapdeal.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "myntra": {
        "name": "Myntra",
        "careers_url": "https://www.myntra.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "meesho": {
        "name": "Meesho",
        "careers_url": "https://www.meesho.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "swiggy": {
        "name": "Swiggy",
        "careers_url": "https://careers.swiggy.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "zomato": {
        "name": "Zomato",
        "careers_url": "https://www.zomato.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "bigbasket": {
        "name": "BigBasket",
        "careers_url": "https://www.bigbasket.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "dunzo": {
        "name": "Dunzo",
        "careers_url": "https://www.dunzo.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Fintech & Payments
    "paytm": {
        "name": "Paytm",
        "careers_url": "https://careers.paytm.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "phonepe": {
        "name": "PhonePe",
        "careers_url": "https://www.phonepe.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "razorpay": {
        "name": "Razorpay",
        "careers_url": "https://razorpay.com/jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cred": {
        "name": "CRED",
        "careers_url": "https://careers.cred.club/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "mobikwik": {
        "name": "MobiKwik",
        "careers_url": "https://www.mobikwik.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "policybazaar": {
        "name": "PolicyBazaar",
        "careers_url": "https://www.policybazaar.com/about-us/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "zerodha": {
        "name": "Zerodha",
        "careers_url": "https://zerodha.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "upstox": {
        "name": "Upstox",
        "careers_url": "https://upstox.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # EdTech
    "byjus": {
        "name": "BYJU'S",
        "careers_url": "https://jobs.lever.co/byjus",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".posting",
            "job_title": "h5",
            "job_link": "a[href*='/byjus/']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "unacademy": {
        "name": "Unacademy",
        "careers_url": "https://unacademy.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "upgrad": {
        "name": "upGrad",
        "careers_url": "https://www.upgrad.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "vedantu": {
        "name": "Vedantu",
        "careers_url": "https://www.vedantu.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Travel & Hospitality Tech
    "oyo": {
        "name": "OYO",
        "careers_url": "https://www.oyorooms.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "makemytrip": {
        "name": "MakeMyTrip",
        "careers_url": "https://careers.makemytrip.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "goibibo": {
        "name": "Goibibo",
        "careers_url": "https://www.goibibo.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cleartrip": {
        "name": "Cleartrip",
        "careers_url": "https://www.cleartrip.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "ixigo": {
        "name": "ixigo",
        "careers_url": "https://www.ixigo.com/about/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Gaming & Entertainment
    "dream11": {
        "name": "Dream11",
        "careers_url": "https://www.dream11.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "mpl": {
        "name": "Mobile Premier League",
        "careers_url": "https://www.mpl.live/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "hike": {
        "name": "Hike",
        "careers_url": "https://hike.in/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Telecom
    "jio": {
        "name": "Reliance Jio",
        "careers_url": "https://careers.jio.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "airtel": {
        "name": "Bharti Airtel",
        "careers_url": "https://www.airtel.in/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "vodafone": {
        "name": "Vodafone Idea",
        "careers_url": "https://www.myvi.in/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Cybersecurity
    "paloalto": {
        "name": "Palo Alto Networks",
        "careers_url": "https://jobs.paloaltonetworks.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "fortinet": {
        "name": "Fortinet",
        "careers_url": "https://www.fortinet.com/corporate/about-us/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "crowdstrike": {
        "name": "CrowdStrike",
        "careers_url": "https://www.crowdstrike.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "zscaler": {
        "name": "Zscaler",
        "careers_url": "https://www.zscaler.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "okta": {
        "name": "Okta",
        "careers_url": "https://www.okta.com/company/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Semiconductor & Hardware
    "qualcomm": {
        "name": "Qualcomm",
        "careers_url": "https://www.qualcomm.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "amd": {
        "name": "AMD",
        "careers_url": "https://jobs.amd.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job/']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "broadcom": {
        "name": "Broadcom",
        "careers_url": "https://www.broadcom.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "micron": {
        "name": "Micron Technology",
        "careers_url": "https://jobs.micron.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "ti": {
        "name": "Texas Instruments",
        "careers_url": "https://careers.ti.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Networking
    "juniper": {
        "name": "Juniper Networks",
        "careers_url": "https://www.juniper.net/careers.html",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "arista": {
        "name": "Arista Networks",
        "careers_url": "https://www.arista.com/en/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "f5": {
        "name": "F5 Networks",
        "careers_url": "https://www.f5.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # SaaS & Business Software
    "freshworks": {
        "name": "Freshworks",
        "careers_url": "https://www.freshworks.com/company/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "zoho": {
        "name": "Zoho",
        "careers_url": "https://www.zoho.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "chargebee": {
        "name": "Chargebee",
        "careers_url": "https://www.chargebee.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "postman": {
        "name": "Postman",
        "careers_url": "https://www.postman.com/company/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "notion": {
        "name": "Notion",
        "careers_url": "https://www.notion.so/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "slack": {
        "name": "Slack",
        "careers_url": "https://slack.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "asana": {
        "name": "Asana",
        "careers_url": "https://asana.com/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "dropbox": {
        "name": "Dropbox",
        "careers_url": "https://www.dropbox.com/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "box": {
        "name": "Box",
        "careers_url": "https://www.box.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # AI & Machine Learning
    "openai": {
        "name": "OpenAI",
        "careers_url": "https://openai.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "anthropic": {
        "name": "Anthropic",
        "careers_url": "https://www.anthropic.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "huggingface": {
        "name": "Hugging Face",
        "careers_url": "https://huggingface.co/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "scale": {
        "name": "Scale AI",
        "careers_url": "https://scale.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cohere": {
        "name": "Cohere",
        "careers_url": "https://cohere.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Automotive Tech
    "waymo": {
        "name": "Waymo",
        "careers_url": "https://waymo.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "cruise": {
        "name": "Cruise",
        "careers_url": "https://getcruise.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "rivian": {
        "name": "Rivian",
        "careers_url": "https://careers.rivian.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "lucid": {
        "name": "Lucid Motors",
        "careers_url": "https://jobs.lucidmotors.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Logistics & Supply Chain Tech
    "delhivery": {
        "name": "Delhivery",
        "careers_url": "https://www.delhivery.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "xpressbees": {
        "name": "Xpressbees",
        "careers_url": "https://www.xpressbees.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "rivigo": {
        "name": "Rivigo",
        "careers_url": "https://rivigo.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Healthcare Tech
    "practo": {
        "name": "Practo",
        "careers_url": "https://www.practo.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "1mg": {
        "name": "1mg",
        "careers_url": "https://www.1mg.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "pharmeasy": {
        "name": "PharmEasy",
        "careers_url": "https://pharmeasy.in/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "netmeds": {
        "name": "Netmeds",
        "careers_url": "https://www.netmeds.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Real Estate Tech
    "housing": {
        "name": "Housing.com",
        "careers_url": "https://housing.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "99acres": {
        "name": "99acres",
        "careers_url": "https://www.99acres.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "magicbricks": {
        "name": "MagicBricks",
        "careers_url": "https://www.magicbricks.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Job Portals & HR Tech
    "naukri_corp": {
        "name": "Naukri (InfoEdge)",
        "careers_url": "https://careers.infoedge.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "indeed_corp": {
        "name": "Indeed (Company)",
        "careers_url": "https://www.indeed.jobs/career",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "glassdoor": {
        "name": "Glassdoor",
        "careers_url": "https://www.glassdoor.com/Jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "apna": {
        "name": "Apna",
        "careers_url": "https://apna.co/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "monster": {
        "name": "Monster",
        "careers_url": "https://www.monster.com/about/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    # Social Media & Communication
    "discord": {
        "name": "Discord",
        "careers_url": "https://discord.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "telegram": {
        "name": "Telegram",
        "careers_url": "https://telegram.org/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "reddit": {
        "name": "Reddit",
        "careers_url": "https://www.redditinc.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "pinterest": {
        "name": "Pinterest",
        "careers_url": "https://www.pinterestcareers.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "snapchat": {
        "name": "Snap Inc.",
        "careers_url": "https://careers.snap.com/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    # Additional Tech Companies
    "elastic": {
        "name": "Elastic",
        "careers_url": "https://www.elastic.co/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "twilio": {
        "name": "Twilio",
        "careers_url": "https://www.twilio.com/company/jobs",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "sendgrid": {
        "name": "SendGrid",
        "careers_url": "https://sendgrid.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "segment": {
        "name": "Segment",
        "careers_url": "https://segment.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "datadog": {
        "name": "Datadog",
        "careers_url": "https://www.datadoghq.com/careers/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "newrelic": {
        "name": "New Relic",
        "careers_url": "https://newrelic.com/about/culture",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "gitlab": {
        "name": "GitLab",
        "careers_url": "https://about.gitlab.com/jobs/",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-listing",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "github_corp": {
        "name": "GitHub (Company)",
        "careers_url": "https://github.com/about/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
    "bitbucket": {
        "name": "Bitbucket",
        "careers_url": "https://www.atlassian.com/company/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-item",
            "job_title": "h3",
            "job_link": "a[href*='/career']",
            "apply_button": "button:has-text('Apply Now')",
        }
    },
    "jenkins": {
        "name": "CloudBees (Jenkins)",
        "careers_url": "https://www.cloudbees.com/careers",
        "search_params": {"keywords": ""},
        "selectors": {
            "job_card": ".job-card",
            "job_title": "h3",
            "job_link": "a[href*='/job']",
            "apply_button": "button:has-text('Apply')",
        }
    },
}
