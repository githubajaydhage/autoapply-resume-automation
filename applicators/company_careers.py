"""
Company Career Pages Applicator - Generic handler for company career websites
"""
import logging
from playwright.sync_api import Page, TimeoutError
from .base import BaseApplicator
from utils.config import COMPANY_CAREERS

logger = logging.getLogger(__name__)


class CompanyCareersApplicator(BaseApplicator):
    """Handles job applications on company career pages"""
    
    def __init__(self, page: Page, company_key: str):
        """
        Initialize the company careers applicator
        
        Args:
            page: Playwright page object
            company_key: Key from COMPANY_CAREERS config (e.g., 'google', 'microsoft')
        """
        self.company_key = company_key
        self.company_config = COMPANY_CAREERS.get(company_key)
        
        if not self.company_config:
            raise ValueError(f"Company '{company_key}' not found in COMPANY_CAREERS config")
        
        # Company career pages typically don't require login
        # Set dummy portal_key to avoid base class errors
        super().__init__(page, portal_key=None)
        self.company_name = self.company_config["name"]
        
    def login(self) -> bool:
        """
        Company career pages typically don't require login.
        Override to skip authentication.
        """
        logger.info(f"[{self.company_name}] No login required for company career pages")
        return True
    
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
                    'button[type="submit"]'
                ]
                
                for submit_selector in submit_selectors:
                    if self.page.locator(submit_selector).count():
                        logger.info(f"[{self.company_name}] Submitting application")
                        self.page.locator(submit_selector).first.click()
                        self.page.wait_for_timeout(3000)
                        
                        # Check for success indicators
                        success_indicators = [
                            'text="Application submitted"',
                            'text="Thank you"',
                            'text="Success"',
                            'text="Your application has been received"'
                        ]
                        
                        for indicator in success_indicators:
                            if self.page.locator(indicator).count():
                                logger.info(f"[{self.company_name}] ✓ Application submitted successfully")
                                return True
                        
                        # If no explicit success, assume it worked
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
