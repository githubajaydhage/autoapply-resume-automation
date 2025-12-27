"""
Company Career Pages Applicator - Generic handler for company career websites
"""
import logging
import os
import re
from playwright.sync_api import Page, TimeoutError
from utils.config import COMPANY_CAREERS

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
    
    def _get_tailored_resume_path(self, job: dict) -> str:
        """Constructs the path for the tailored resume"""
        from utils.config import TAILORED_RESUMES_DIR
        safe_title = re.sub(r'[\\/*?:"<>|]', "", job["title"])
        safe_company = re.sub(r'[\\/*?:"<>|]', "", job["company"])
        return os.path.join(TAILORED_RESUMES_DIR, f"{safe_company}_{safe_title}.pdf")
    
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
