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
    # Add Glassdoor and ZipRecruiter configs here if needed
}
