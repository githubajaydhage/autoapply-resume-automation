import logging
import time
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .base import BaseApplicator
import scripts.tracker as tracker

class IndeedApplicator(BaseApplicator):
    """Applicator for Indeed jobs."""

    def __init__(self):
        super().__init__("indeed")

    def apply_to_job(self, page: Page, job: dict):
        """Applies to a single Indeed job."""
        try:
            logging.info(f"Applying to: {job['title']} at {job['company']}")
            page.goto(job['link'], timeout=60000)
            time.sleep(3)

            iframe_selector = self.config["selectors"]["apply_button_iframe"]
            try:
                page.wait_for_selector(iframe_selector, timeout=10000)
                frame = page.frame_locator(iframe_selector)
                apply_button = frame.locator(self.config["selectors"]["apply_button"]).first
            except PlaywrightTimeoutError:
                frame = page
                apply_button = frame.locator(self.config["selectors"]["apply_button"]).first

            if not apply_button.is_visible():
                logging.warning(f"No 'Apply' button found for {job['title']}. Skipping.")
                return

            apply_button.click()
            time.sleep(5)

            resume_path = self._get_tailored_resume_path(job)
            if os.path.exists(resume_path):
                upload_input = page.locator(self.config["selectors"]["upload_resume_input"])
                if upload_input.is_visible(timeout=5000):
                    upload_input.set_input_files(resume_path)
                    logging.info("Uploaded tailored resume.")

            # Indeed's flow is complex; this is a simplified attempt to navigate it.
            continue_button = page.locator(self.config["selectors"]["continue_button"]).first
            if continue_button.is_visible():
                # continue_button.click() # Use with caution
                logging.info("Simulating 'Continue' click (commented out).")

            logging.info(f"Application for {job['title']} requires manual review to complete.")
            # In a real-world scenario, you'd need more logic here to handle questions.
            # For now, we track it as "attempted".
            tracker.track_application(job['title'], job['company'], job['link'])

        except PlaywrightTimeoutError:
            logging.error(f"Timeout while applying for {job['title']}.")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {job['title']}: {e}")
            page.screenshot(path=os.path.join("data", f"error_indeed_{job['title']}.png"))
