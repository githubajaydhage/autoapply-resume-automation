from abc import ABC, abstractmethod
import logging
import os
import time
import random
import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.browser_manager import BrowserManager
from utils.config import PORTAL_CONFIGS
from utils.resume_naming import get_resume_naming_manager
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
        # Initialize resume naming manager
        from utils.config import TAILORED_RESUMES_DIR
        self.resume_naming_manager = get_resume_naming_manager(TAILORED_RESUMES_DIR)
        # Track actual successful applications
        self.applied_count = 0
        self.login_successful = False

    def run(self, jobs):
        """The main execution method for an applicator."""
        logging.info(f"--- Starting {self.portal_name.capitalize()} Application Process ---")
        self.applied_count = 0  # Reset counter
        
        with self.browser_manager as page:
            if not self.login(page):
                logging.error(f"Login failed for {self.portal_name}. Aborting.")
                self.login_successful = False
                return
            
            self.login_successful = True

            for job in jobs:
                try:
                    success = self.apply_to_job(page, job)
                    if success:
                        self.applied_count += 1
                        logging.info(f"✅ Successfully applied to {job.get('title', 'Unknown')} ({self.applied_count} total)")
                except Exception as e:
                    logging.error(f"Error applying to job: {e}")
                
                sleep_time = random.uniform(10, 25)
                logging.info(f"Waiting for {sleep_time:.2f} seconds before the next application.")
                time.sleep(sleep_time)

        logging.info(f"--- {self.portal_name.capitalize()} Application Process Finished ---")
        logging.info(f"📊 Applied to {self.applied_count} out of {len(jobs)} jobs")

    def login(self, page: Page) -> bool:
        """Handles the login process for the portal with retry logic."""
        logging.info(f"Attempting to log in to {self.portal_name}...")
        
        email = os.getenv(self.config["credentials"]["email_env"])
        password = os.getenv(self.config["credentials"]["password_env"])

        if not email or not password:
            logging.error(f"Credentials for {self.portal_name} not found in environment variables.")
            logging.error(f"Email env var: {self.config['credentials']['email_env']} = {'SET' if email else 'NOT SET'}")
            logging.error(f"Password env var: {self.config['credentials']['password_env']} = {'SET' if password else 'NOT SET'}")
            return False

        # Get list of login URLs to try (main + alternatives)
        login_urls = [self.config["login_url"]]
        if "login_url_alternatives" in self.config:
            login_urls = self.config["login_url_alternatives"]

        max_retries = 2
        for attempt in range(max_retries):
            # Try each login URL
            login_url = login_urls[attempt % len(login_urls)]
            
            try:
                logging.info(f"Login attempt {attempt + 1}/{max_retries} for {self.portal_name}")
                
                # Navigate with extended timeout
                logging.info(f"Navigating to: {login_url}")
                page.goto(login_url, timeout=90000, wait_until="domcontentloaded")
                time.sleep(random.uniform(2, 4))  # Human-like delay
                
                # Check immediately for Access Denied
                page_title = page.title().lower()
                page_content = page.content().lower()[:1000]
                
                if 'access denied' in page_title or 'access denied' in page_content or 'blocked' in page_title:
                    logging.error(f"❌ ACCESS DENIED by {self.portal_name.upper()} on URL: {login_url}")
                    logging.error("The site is blocking automated access from this IP/browser.")
                    page.screenshot(path=os.path.join("data", f"access_denied_{self.portal_name}_{attempt}.png"))
                    logging.info(f"📸 Screenshot saved: access_denied_{self.portal_name}_{attempt}.png")
                    continue  # Try next URL/attempt
                
                # Screenshot: Login page loaded
                page.screenshot(path=os.path.join("data", f"1_login_page_{self.portal_name}.png"))
                logging.info(f"📸 Screenshot saved: 1_login_page_{self.portal_name}.png")
                logging.info(f"Current URL: {page.url}")
                
                # Check if already logged in (persistent context may have session)
                try:
                    page.wait_for_selector(self.config["selectors"]["login_success_indicator"], timeout=5000)
                    logging.info(f"Already logged in to {self.portal_name} (session restored).")
                    page.screenshot(path=os.path.join("data", f"already_logged_in_{self.portal_name}.png"))
                    return True
                except PlaywrightTimeoutError:
                    logging.info("Not logged in yet, proceeding with login...")
                
                # Find and fill email
                logging.info(f"Looking for email input: {self.config['selectors']['email_input']}")
                email_input = page.locator(self.config["selectors"]["email_input"]).first
                if email_input.count() > 0:
                    logging.info("✅ Email input found")
                    email_input.click()
                    time.sleep(random.uniform(0.5, 1))
                    email_input.fill("")  # Clear first
                    for char in email:
                        email_input.type(char, delay=random.randint(50, 150))
                    time.sleep(random.uniform(1, 2))
                    logging.info("✅ Email entered")
                else:
                    logging.error("❌ Email input NOT found!")
                    page.screenshot(path=os.path.join("data", f"email_not_found_{self.portal_name}.png"))
                
                # Find and fill password
                logging.info(f"Looking for password input: {self.config['selectors']['password_input']}")
                password_input = page.locator(self.config["selectors"]["password_input"]).first
                if password_input.count() > 0:
                    logging.info("✅ Password input found")
                    password_input.click()
                    time.sleep(random.uniform(0.5, 1))
                    password_input.fill("")  # Clear first
                    for char in password:
                        password_input.type(char, delay=random.randint(50, 150))
                    time.sleep(random.uniform(1, 2))
                    logging.info("✅ Password entered")
                else:
                    logging.error("❌ Password input NOT found!")
                    page.screenshot(path=os.path.join("data", f"password_not_found_{self.portal_name}.png"))
                
                # Screenshot before clicking login
                page.screenshot(path=os.path.join("data", f"2_before_login_click_{self.portal_name}.png"))
                logging.info(f"📸 Screenshot saved: 2_before_login_click_{self.portal_name}.png")
                
                # Click login button
                logging.info(f"Looking for login button: {self.config['selectors']['login_button']}")
                login_btn = page.locator(self.config["selectors"]["login_button"]).first
                if login_btn.count() > 0:
                    logging.info("✅ Login button found, clicking...")
                    login_btn.click()
                else:
                    logging.error("❌ Login button NOT found!")
                    page.screenshot(path=os.path.join("data", f"login_btn_not_found_{self.portal_name}.png"))
                
                time.sleep(random.uniform(3, 5))
                
                # Take screenshot after clicking login
                page.screenshot(path=os.path.join("data", f"3_after_login_click_{self.portal_name}.png"))
                logging.info(f"📸 Screenshot saved: 3_after_login_click_{self.portal_name}.png")
                
                # Log current URL for debugging
                current_url = page.url
                logging.info(f"Current URL after login click: {current_url}")
                
                # Log page title for debugging
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                page_title = page.title()
                logging.info(f"Page title: {page_title}")
                
                # Check for Access Denied (Naukri blocks headless browsers)
                if 'access denied' in page_title.lower() or 'access denied' in page.content().lower():
                    logging.error(f"❌ ACCESS DENIED by {self.portal_name.upper()}! Site is blocking automated access.")
                    logging.error("This usually means the site detected the headless browser.")
                    page.screenshot(path=os.path.join("data", f"access_denied_{self.portal_name}.png"))
                    continue  # Try next attempt
                
                # Check for common error messages - more comprehensive
                error_selectors = [
                    # LinkedIn specific errors
                    '#error-for-password',  # LinkedIn password error
                    '#error-for-username',  # LinkedIn username error
                    '.form__label--error',  # LinkedIn form error
                    '[data-error]',  # Generic data error
                    'span:has-text("wrong password")',
                    'span:has-text("incorrect")',
                    'p:has-text("password")',  # Error paragraph
                    # Generic
                    'text=wrong password',
                    'text=incorrect password', 
                    'text=invalid credentials',
                    'text=account locked',
                    'text=too many attempts',
                    'text=please try again',
                    'text=doesn\'t match',
                    '.error-message',
                    '.alert-error',
                    '.error',
                    '[role="alert"]',
                ]
                
                error_found = False
                for err_sel in error_selectors:
                    try:
                        err_elem = page.locator(err_sel).first
                        if err_elem.is_visible(timeout=1000):
                            error_text = err_elem.text_content()
                            logging.error(f"❌ Login error detected: {err_sel}")
                            logging.error(f"❌ Error text: {error_text}")
                            page.screenshot(path=os.path.join("data", f"login_error_{self.portal_name}.png"))
                            error_found = True
                            break
                    except:
                        continue
                
                # If still on login page after clicking login, something went wrong
                if not error_found and 'login' in current_url.lower():
                    logging.warning("⚠️ Still on login page after clicking login - checking page content")
                    # Get any visible text that might indicate an error
                    try:
                        body_text = page.locator('body').text_content()[:500]
                        if any(x in body_text.lower() for x in ['error', 'incorrect', 'invalid', 'wrong', 'failed']):
                            logging.error(f"❌ Page contains error text: {body_text[:200]}")
                    except:
                        pass
                
                # Check for verification/checkpoint page (both LinkedIn and Naukri)
                checkpoint_selectors = [
                    'input[name="pin"]',  # PIN verification
                    'text=verify',  # Various verification messages
                    'text=security check',
                    'text=confirm your identity',
                    'text=we need to verify',
                    'text=OTP',  # Naukri OTP
                    'text=one time password',
                    '#captcha',
                    '.challenge',
                    'input[placeholder*="OTP"]',  # Naukri OTP input
                    'input[placeholder*="code"]',
                    'text=suspicious',
                    'text=unusual activity',
                ]
                
                # Check if we're on a verification page
                is_checkpoint = False
                for selector in checkpoint_selectors:
                    try:
                        if page.locator(selector).first.is_visible(timeout=2000):
                            is_checkpoint = True
                            logging.warning(f"⚠️ {self.portal_name.upper()} verification/checkpoint detected!")
                            logging.warning(f"Matched selector: {selector}")
                            logging.info("Waiting up to 5 minutes for manual verification...")
                            page.screenshot(path=os.path.join("data", f"checkpoint_detected_{self.portal_name}.png"))
                            break
                    except:
                        continue
                
                if is_checkpoint:
                    # Wait longer for manual verification (5 minutes)
                    try:
                        page.wait_for_selector(self.config["selectors"]["login_success_indicator"], timeout=300000)
                        logging.info(f"✅ Verification completed! Login to {self.portal_name} successful.")
                        page.screenshot(path=os.path.join("data", f"login_success_{self.portal_name}.png"))
                        return True
                    except PlaywrightTimeoutError:
                        logging.error("Verification timed out after 5 minutes.")
                        page.screenshot(path=os.path.join("data", f"verification_timeout_{self.portal_name}.png"))
                        raise
                
                # Check if already on home page / logged in
                # Sometimes login redirects directly without showing the indicator
                if self.portal_name == "linkedin" and "/feed" in page.url:
                    logging.info(f"✅ Login to {self.portal_name} successful (redirected to feed).")
                    return True
                
                if self.portal_name == "naukri" and "naukri.com" in page.url and "/nlogin" not in page.url:
                    # Check for common logged-in indicators on Naukri
                    try:
                        # Multiple possible indicators for Naukri logged-in state
                        naukri_logged_in = page.locator('a[href*="mynaukri"], .nI-gNb-menuItems, .nI-gNb-drawer, img[class*="avatar"], img[alt="user"]').first
                        if naukri_logged_in.is_visible(timeout=5000):
                            logging.info(f"✅ Login to {self.portal_name} successful (found nav element).")
                            page.screenshot(path=os.path.join("data", f"login_success_{self.portal_name}.png"))
                            return True
                    except:
                        pass
                
                # Wait for login success with extended timeout
                page.wait_for_selector(self.config["selectors"]["login_success_indicator"], timeout=120000)
                logging.info(f"Login to {self.portal_name} successful.")
                page.screenshot(path=os.path.join("data", f"login_success_{self.portal_name}.png"))
                return True
                
            except PlaywrightTimeoutError:
                logging.warning(f"Login attempt {attempt + 1} timed out for {self.portal_name}.")
                page.screenshot(path=os.path.join("data", f"login_failure_{self.portal_name}_attempt{attempt+1}.png"))
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
            except Exception as e:
                logging.error(f"Error during login attempt {attempt + 1} for {self.portal_name}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
        
        logging.error(f"All login attempts failed for {self.portal_name}.")
        return False

    @abstractmethod
    def apply_to_job(self, page: Page, job: dict):
        """Abstract method to apply to a single job."""
        pass

    def _get_tailored_resume_path(self, job: dict) -> str:
        """Constructs the path for the tailored resume with fallback logic."""
        # Try to find existing resume with multiple naming patterns
        resume_path = self.resume_naming_manager.find_matching_resume(job)
        
        if resume_path and os.path.exists(resume_path):
            logging.info(f"Found existing tailored resume: {resume_path}")
            return resume_path
        
        # If not found, use standardized naming (this is what should be created)
        expected_path = self.resume_naming_manager.get_tailored_resume_path(job, use_standardized_title=True)
        
        if not os.path.exists(expected_path):
            # Log detailed information for debugging
            original_title = job.get("title", "Unknown")
            standardized_title = self.resume_naming_manager.title_standardizer.standardize_title(original_title)
            company = job.get("company", "Unknown")
            
            logging.warning(f"Tailored resume not found for {company} - {original_title}")
            logging.warning(f"Expected standardized title: {standardized_title}")
            logging.warning(f"Expected path: {expected_path}")
            
            # List available resumes for debugging
            from utils.config import TAILORED_RESUMES_DIR
            if os.path.exists(TAILORED_RESUMES_DIR):
                available_resumes = [f for f in os.listdir(TAILORED_RESUMES_DIR) if f.endswith('.pdf')]
                logging.info(f"Available tailored resumes: {available_resumes}")
        
        return expected_path
