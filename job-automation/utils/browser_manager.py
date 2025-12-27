from playwright.sync_api import sync_playwright, Page, BrowserContext
import logging
import time

class BrowserManager:
    """A class to manage the Playwright browser instance, context, and page."""

    def __init__(self, user_data_dir, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.user_data_dir = user_data_dir
        self.headless = headless

    def start(self):
        """Starts the browser and creates a new page."""
        logging.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            self.user_data_dir,
            headless=self.headless,
            slow_mo=1000,
            args=["--start-maximized"]
        )
        self.page = self.context.new_page()
        logging.info("Browser started successfully.")
        return self.page

    def stop(self):
        """Stops the browser and cleans up."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        logging.info("Browser stopped.")

    def __enter__(self):
        """Context manager entry point."""
        self.start()
        return self.page

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.stop()
