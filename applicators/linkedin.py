import logging
import time
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .base import BaseApplicator
import scripts.tracker as tracker

class LinkedInApplicator(BaseApplicator):
    """Applicator for LinkedIn jobs."""

    def __init__(self):
        super().__init__("linkedin")

    def apply_to_job(self, page: Page, job: dict) -> bool:
        """Applies to a single LinkedIn job. Returns True if successful."""
        try:
            job_url = job.get('url', job.get('link', ''))
            if not job_url:
                logging.error(f"No URL found for job: {job.get('title', 'Unknown')}")
                return False
            
            logging.info(f"Applying to: {job['title']} at {job['company']}")
            page.goto(job_url, timeout=60000)
            time.sleep(3)

            apply_button = page.locator(self.config["selectors"]["apply_button"]).first
            if not apply_button.is_visible():
                logging.warning(f"No 'Easy Apply' button found for {job['title']}. Skipping.")
                return False

            apply_button.click()
            
            page.wait_for_selector('div[role="dialog"]', timeout=15000)
            
            resume_path = self._get_tailored_resume_path(job)
            if os.path.exists(resume_path):
                upload_input = page.locator(self.config["selectors"]["upload_resume_input"])
                if upload_input.is_visible(timeout=5000):
                    upload_input.set_input_files(resume_path)
                    logging.info("Uploaded tailored resume.")
            
            # Handle multi-step Easy Apply modal
            max_steps = 10
            for step in range(max_steps):
                # Check for review/submit button
                submit_button = page.locator(self.config["selectors"]["submit_application_button"]).first
                if submit_button.is_visible():
                    submit_button.click()
                    time.sleep(2)
                    # Check if application was submitted
                    if page.locator("text=Application sent").is_visible(timeout=5000):
                        logging.info(f"✅ Successfully applied to {job['title']} at {job['company']}")
                        tracker.track_application(job['title'], job['company'], job.get('url', job.get('link', '')))
                        return True
                    break
                
                # Check for Next button to proceed through steps
                next_button = page.locator('button[aria-label="Continue to next step"]').first
                if next_button.is_visible():
                    next_button.click()
                    time.sleep(1)
                    continue
                    
                # Try alternative next button
                next_alt = page.locator('button:has-text("Next")').first
                if next_alt.is_visible():
                    next_alt.click()
                    time.sleep(1)
                    continue
                    
                break
            
            logging.warning(f"Could not complete application for {job['title']}")
            return False

        except PlaywrightTimeoutError:
            logging.error(f"Timeout while applying for {job['title']}.")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred for {job['title']}: {e}")
            page.screenshot(path=os.path.join("data", f"error_linkedin_{job['title']}.png"))
            return False
