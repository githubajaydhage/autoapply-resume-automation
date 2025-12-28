from playwright.sync_api import sync_playwright, Page, BrowserContext
import logging
import time
import random

class BrowserManager:
    """A class to manage the Playwright browser instance with anti-detection measures."""

    def __init__(self, user_data_dir, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.user_data_dir = user_data_dir
        self.headless = headless

    def start(self):
        """Starts the browser with stealth settings to avoid detection."""
        logging.info("Starting browser...")
        self.playwright = sync_playwright().start()
        
        # Anti-detection browser arguments
        browser_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
        ]
        
        # Realistic viewport and user agent
        self.context = self.playwright.chromium.launch_persistent_context(
            self.user_data_dir,
            headless=self.headless,
            slow_mo=random.randint(500, 1500),  # Randomize slowdown
            args=browser_args,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 12.9716, "longitude": 77.5946},  # Bangalore
            permissions=["geolocation"],
        )
        
        self.page = self.context.new_page()
        
        # Additional anti-detection: override webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = { runtime: {} };
        """)
        
        logging.info("Browser started successfully with anti-detection measures.")
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
