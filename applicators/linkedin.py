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

    def apply_to_job(self, page: Page, job: dict):
        """Applies to a single LinkedIn job."""
        try:
            logging.info(f"Applying to: {job['title']} at {job['company']}")
            page.goto(job['link'], timeout=60000)
            time.sleep(3)

            apply_button = page.locator(self.config["selectors"]["apply_button"]).first
            if not apply_button.is_visible():
                logging.warning(f"No 'Easy Apply' button found for {job['title']}. Skipping.")
                return

            apply_button.click()
            
            page.wait_for_selector('div[role="dialog"]', timeout=15000)
            
            resume_path = self._get_tailored_resume_path(job)
            if os.path.exists(resume_path):
                upload_input = page.locator(self.config["selectors"]["upload_resume_input"])
                if upload_input.is_visible(timeout=5000):
                    upload_input.set_input_files(resume_path)
                    logging.info("Uploaded tailored resume.")
            
            # This is a simplification. Real-world scenarios require navigating
            # multiple steps in the modal.
            submit_button = page.locator(self.config["selectors"]["submit_application_button"]).first
            if submit_button.is_visible():
                # submit_button.click() # Use with caution
                logging.info("Simulating final submission click (currently commented out).")
                tracker.track_application(job['title'], job['company'], job['link'])
            else:
                logging.warning("Could not find the final submit button.")

        except PlaywrightTimeoutError:
            logging.error(f"Timeout while applying for {job['title']}.")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {job['title']}: {e}")
            page.screenshot(path=os.path.join("data", f"error_linkedin_{job['title']}.png"))
