from abc import ABC, abstractmethod
import logging
import os
import time
import random
import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.browser_manager import BrowserManager
from utils.config import PORTAL_CONFIGS
import scripts.tracker as tracker

class BaseApplicator(ABC):
    """Abstract base class for all job portal applicators."""

    def __init__(self, portal_name):
        self.portal_name = portal_name
        self.config = PORTAL_CONFIGS[portal_name]
        self.browser_manager = BrowserManager(
            user_data_dir=self.config["user_data_dir"],
            headless=True # Always headless in production
        )

    def run(self, jobs):
        """The main execution method for an applicator."""
        logging.info(f"--- Starting {self.portal_name.capitalize()} Application Process ---")
        
        with self.browser_manager as page:
            if not self.login(page):
                logging.error(f"Login failed for {self.portal_name}. Aborting.")
                return

            for job in jobs:
                self.apply_to_job(page, job)
                sleep_time = random.uniform(10, 25)
                logging.info(f"Waiting for {sleep_time:.2f} seconds before the next application.")
                time.sleep(sleep_time)

        logging.info(f"--- {self.portal_name.capitalize()} Application Process Finished ---")

    def login(self, page: Page) -> bool:
        """Handles the login process for the portal."""
        logging.info(f"Attempting to log in to {self.portal_name}...")
        
        email = os.getenv(self.config["credentials"]["email_env"])
        password = os.getenv(self.config["credentials"]["password_env"])

        if not email or not password:
            logging.error(f"Credentials for {self.portal_name} not found in environment variables.")
            return False

        try:
            page.goto(self.config["login_url"], timeout=60000)
            
            page.fill(self.config["selectors"]["email_input"], email)
            time.sleep(random.uniform(1, 2))
            page.fill(self.config["selectors"]["password_input"], password)
            time.sleep(random.uniform(1, 2))
            page.click(self.config["selectors"]["login_button"])

            page.wait_for_selector(self.config["selectors"]["login_success_indicator"], timeout=60000)
            logging.info(f"Login to {self.portal_name} successful.")
            return True
        except PlaywrightTimeoutError:
            logging.error(f"Login to {self.portal_name} failed or took too long.")
            page.screenshot(path=os.path.join("data", f"login_failure_{self.portal_name}.png"))
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during login for {self.portal_name}: {e}")
            return False

    @abstractmethod
    def apply_to_job(self, page: Page, job: dict):
        """Abstract method to apply to a single job."""
        pass

    def _get_tailored_resume_path(self, job: dict) -> str:
        """Constructs the path for the tailored resume."""
        from utils.config import TAILORED_RESUMES_DIR
        safe_title = re.sub(r'[\\/*?:"<>|]', "", job["title"])
        safe_company = re.sub(r'[\\/*?:"<>|]', "", job["company"])
        return os.path.join(TAILORED_RESUMES_DIR, f"{safe_company}_{safe_title}.pdf")
