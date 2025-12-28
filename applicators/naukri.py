import logging
import time
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from .base import BaseApplicator
import scripts.tracker as tracker

class NaukriApplicator(BaseApplicator):
    """Applicator for Naukri jobs."""

    def __init__(self):
        super().__init__("naukri")

    def apply_to_job(self, page: Page, job: dict):
        """Applies to a single Naukri job."""
        try:
            job_url = job.get('url', job.get('link', ''))
            if not job_url:
                logging.error(f"No URL found for job: {job.get('title', 'Unknown')}")
                return
            
            logging.info(f"Applying to: {job['title']} at {job['company']}")
            page.goto(job_url, timeout=60000)
            time.sleep(4)

            apply_button = page.locator(self.config["selectors"]["apply_button"]).first
            if not apply_button.is_visible():
                logging.warning(f"No 'Apply' button found for {job['title']}. Skipping.")
                return

            apply_button.click()
            time.sleep(5)

            # Naukri can sometimes auto-submit if the profile is complete.
            if page.locator(self.config["selectors"]["application_sent_indicator"]).is_visible():
                logging.info("Application submitted successfully on Naukri (auto-submit).")
                tracker.track_application(job['title'], job['company'], job_url)
            else:
                # If not auto-submitted, it may require more steps.
                logging.info(f"Application for {job['title']} may require manual steps.")
                # For now, we track it as "attempted".
                tracker.track_application(job['title'], job['company'], job_url)

        except PlaywrightTimeoutError:
            logging.error(f"Timeout while applying for {job['title']}.")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {job['title']}: {e}")
            page.screenshot(path=os.path.join("data", f"error_naukri_{job['title']}.png"))
