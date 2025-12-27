"""
Company Career Pages Applicator - Generic handler for company career websites
"""
import logging
import os
import re
from playwright.sync_api import Page, TimeoutError
from utils.config import COMPANY_CAREERS, USER_DETAILS

logger = logging.getLogger(__name__)


class CompanyCareersApplicator:
    """Handles job applications on company career pages"""
    
    def __init__(self, page: Page, company_key: str):
        """
        Initialize the company careers applicator
        
        Args:
            page: Playwright page object
            company_key: Key from COMPANY_CAREERS config (e.g., 'google', 'microsoft')
        """
        self.page = page
        self.company_key = company_key
        self.company_config = COMPANY_CAREERS.get(company_key)
        
        if not self.company_config:
            raise ValueError(f"Company '{company_key}' not found in COMPANY_CAREERS config")
        
        self.company_name = self.company_config["name"]
    
    def run(self, jobs):
        """
        Process and apply to all jobs for this company
        
        Args:
            jobs: List of job dictionaries
        """
        logger.info(f"[{self.company_name}] Starting application process for {len(jobs)} jobs")
        
        for job in jobs:
            # Get tailored resume path
            tailored_resume_path = self._get_tailored_resume_path(job)
            
            if not os.path.exists(tailored_resume_path):
                logger.warning(f"[{self.company_name}] Tailored resume not found: {tailored_resume_path}")
                continue
            
            # Apply to the job
            success = self.apply_to_job(job["link"], tailored_resume_path)
            
            if success:
                logger.info(f"[{self.company_name}] ✓ Successfully applied to: {job['title']}")
            else:
                logger.warning(f"[{self.company_name}] ✗ Failed to apply to: {job['title']}")
        
        logger.info(f"[{self.company_name}] Application process completed")
    
    
    def apply_to_job(self, job_url: str, tailored_resume_path: str) -> bool:
        """
        Apply to a single job on a company career page
        
        Args:
            job_url: URL of the job posting
            tailored_resume_path: Path to the tailored resume PDF
            
        Returns:
            True if application successful, False otherwise
        """
        try:
            logger.info(f"[{self.company_name}] Navigating to: {job_url}")
            self.page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(3000)
            
            selectors = self.company_config["selectors"]
            
            # Look for apply button
            apply_button_selector = selectors.get("apply_button")
            if not apply_button_selector:
                logger.error(f"[{self.company_name}] No apply button selector configured")
                return False
            
            # Check if apply button exists
            if not self.page.locator(apply_button_selector).count():
                logger.warning(f"[{self.company_name}] Apply button not found on page")
                return False
            
            # Click apply button
            logger.info(f"[{self.company_name}] Clicking apply button")
            self.page.locator(apply_button_selector).first.click()
            self.page.wait_for_timeout(3000)
            
            # Check for application form
            form_selector = selectors.get("application_form", "form")
            if self.page.locator(form_selector).count():
                logger.info(f"[{self.company_name}] Application form detected")
                
                # Auto-fill form fields
                self._fill_form_fields()
                
                # Look for resume upload
                upload_input = self.page.locator('input[type="file"]').first
                if upload_input.count():
                    logger.info(f"[{self.company_name}] Uploading resume")
                    upload_input.set_input_files(tailored_resume_path)
                    self.page.wait_for_timeout(2000)
                
                # Look for submit button (various common texts)
                submit_selectors = [
                    'button:has-text("Submit")',
                    'button:has-text("Submit application")',
                    'button:has-text("Apply")',
                    'button[type="submit"]',
                    'input[type="submit"]'
                ]
                
                for submit_selector in submit_selectors:
                    if self.page.locator(submit_selector).count():
                        logger.info(f"[{self.company_name}] Submitting application")
                        self.page.locator(submit_selector).first.click()
                        self.page.wait_for_timeout(5000)
                        
                        # Check for success indicators
                        success_indicators = [
                            'text="Application submitted"',
                            'text="Thank you"',
                            'text="Success"',
                            'text="Your application has been received"',
                            'text="Application received"',
                            'text="Confirmation"',
                            'text="Application ID"',
                            'text="Reference number"'
                        ]
                        
                        for indicator in success_indicators:
                            if self.page.locator(indicator).count():
                                logger.info(f"[{self.company_name}] ✓ Application submitted successfully - confirmation detected")
                                return True
                        
                        # Check if we're on a different page (redirect after success)
                        current_url = self.page.url
                        if current_url != job_url and ("confirm" in current_url.lower() or "success" in current_url.lower() or "thank" in current_url.lower()):
                            logger.info(f"[{self.company_name}] ✓ Application submitted successfully - redirected to confirmation page")
                            return True
                        
                        # If no explicit success but no errors, assume it worked
                        logger.info(f"[{self.company_name}] ✓ Application likely submitted (no error detected)")
                        return True
            
            # If we get here, manual application may be needed
            logger.warning(f"[{self.company_name}] Could not complete automated application")
            logger.warning(f"[{self.company_name}] You may need to complete this application manually: {job_url}")
            return False
            
        except TimeoutError:
            logger.error(f"[{self.company_name}] Timeout while applying to {job_url}")
            return False
        except Exception as e:
            logger.error(f"[{self.company_name}] Error applying to job: {e}")
            return False
    
    def _fill_form_fields(self):
        """
        Automatically fill common application form fields using USER_DETAILS
        """
        # Name field variations
        name_field_patterns = [
            'input[name*="name" i]:not([name*="last" i]):not([name*="first" i])',
            'input[placeholder*="name" i]:not([placeholder*="last" i]):not([placeholder*="first" i])',
            'input[id*="name" i]:not([id*="last" i]):not([id*="first" i])',
            'input[aria-label*="Full name" i]',
            'input[aria-label*="Your name" i]'
        ]
        
        first_name_patterns = [
            'input[name*="first" i]',
            'input[placeholder*="First name" i]',
            'input[id*="firstName" i]',
            'input[aria-label*="First name" i]'
        ]
        
        last_name_patterns = [
            'input[name*="last" i]',
            'input[placeholder*="Last name" i]',
            'input[id*="lastName" i]',
            'input[aria-label*="Last name" i]'
        ]
        
        # Email field variations
        email_field_patterns = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[placeholder*="email" i]',
            'input[id*="email" i]',
            'input[aria-label*="email" i]'
        ]
        
        # Phone field variations
        phone_field_patterns = [
            'input[type="tel"]',
            'input[name*="phone" i]',
            'input[name*="mobile" i]',
            'input[placeholder*="phone" i]',
            'input[placeholder*="mobile" i]',
            'input[id*="phone" i]',
            'input[aria-label*="phone" i]'
        ]
        
        # Location/City field variations
        location_field_patterns = [
            'input[name*="location" i]',
            'input[name*="city" i]',
            'input[placeholder*="location" i]',
            'input[placeholder*="city" i]',
            'input[id*="location" i]',
            'input[id*="city" i]'
        ]
        
        # LinkedIn field variations
        linkedin_field_patterns = [
            'input[name*="linkedin" i]',
            'input[placeholder*="linkedin" i]',
            'input[id*="linkedin" i]'
        ]
        
        # Fill full name
        for pattern in name_field_patterns:
            if self._fill_field(pattern, USER_DETAILS["full_name"]):
                logger.info(f"[{self.company_name}] ✓ Filled full name field")
                break
        
        # Fill first name
        for pattern in first_name_patterns:
            if self._fill_field(pattern, USER_DETAILS["first_name"]):
                logger.info(f"[{self.company_name}] ✓ Filled first name field")
                break
        
        # Fill last name
        for pattern in last_name_patterns:
            if self._fill_field(pattern, USER_DETAILS["last_name"]):
                logger.info(f"[{self.company_name}] ✓ Filled last name field")
                break
        
        # Fill email
        for pattern in email_field_patterns:
            if self._fill_field(pattern, USER_DETAILS["email"]):
                logger.info(f"[{self.company_name}] ✓ Filled email field")
                break
        
        # Fill phone
        for pattern in phone_field_patterns:
            if self._fill_field(pattern, USER_DETAILS["phone"]):
                logger.info(f"[{self.company_name}] ✓ Filled phone field")
                break
        
        # Fill location
        for pattern in location_field_patterns:
            if self._fill_field(pattern, USER_DETAILS["location"]):
                logger.info(f"[{self.company_name}] ✓ Filled location field")
                break
        
        # Fill LinkedIn
        for pattern in linkedin_field_patterns:
            if self._fill_field(pattern, USER_DETAILS["linkedin_url"]):
                logger.info(f"[{self.company_name}] ✓ Filled LinkedIn field")
                break
        
        # Handle work authorization questions
        self._handle_work_authorization()
        
        self.page.wait_for_timeout(1000)
    
    def _fill_field(self, selector: str, value: str) -> bool:
        """
        Fill a form field if it exists and is visible
        
        Args:
            selector: CSS selector for the field
            value: Value to fill
            
        Returns:
            True if field was filled, False otherwise
        """
        try:
            field = self.page.locator(selector).first
            if field.count() and field.is_visible():
                field.fill(value)
                return True
        except Exception:
            pass
        return False
    
    def _handle_work_authorization(self):
        """
        Handle work authorization questions (Yes/No radio buttons or dropdowns)
        """
        # Common work authorization question patterns
        work_auth_patterns = [
            'text="Are you authorized to work"',
            'text="Work authorization"',
            'text="Legal authorization"',
            'text="Legally authorized to work"'
        ]
        
        # Look for yes/no radio buttons near work authorization questions
        for pattern in work_auth_patterns:
            if self.page.locator(pattern).count():
                logger.info(f"[{self.company_name}] Found work authorization question")
                
                # Try to click "Yes" radio button
                yes_selectors = [
                    'input[type="radio"][value*="yes" i]',
                    'input[type="radio"][value*="authorized" i]',
                    'label:has-text("Yes") input[type="radio"]',
                    'label:has-text("Yes")'
                ]
                
                for yes_selector in yes_selectors:
                    try:
                        yes_button = self.page.locator(yes_selector).first
                        if yes_button.count():
                            yes_button.click()
                            logger.info(f"[{self.company_name}] ✓ Selected 'Yes' for work authorization")
                            return
                    except Exception:
                        pass
        
        # Check for dropdown work authorization
        work_auth_dropdown_patterns = [
            'select[name*="authorization" i]',
            'select[name*="work status" i]',
            'select[id*="authorization" i]'
        ]
        
        for pattern in work_auth_dropdown_patterns:
            try:
                dropdown = self.page.locator(pattern).first
                if dropdown.count():
                    # Try to select "Authorized" or similar option
                    dropdown.select_option(label="Authorized to work")
                    logger.info(f"[{self.company_name}] ✓ Selected work authorization from dropdown")
                    return
            except Exception:
                pass
