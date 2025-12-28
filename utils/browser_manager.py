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
        
        # Comprehensive anti-detection script
        self.page.add_init_script("""
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ];
                }
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'en-IN']
            });
            
            // Add chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Hide automation indicators
            delete navigator.__proto__.webdriver;
            
            // Override User-Agent Client Hints
            if (navigator.userAgentData) {
                Object.defineProperty(navigator, 'userAgentData', {
                    get: () => ({
                        brands: [
                            { brand: 'Not_A Brand', version: '8' },
                            { brand: 'Chromium', version: '120' },
                            { brand: 'Google Chrome', version: '120' }
                        ],
                        mobile: false,
                        platform: 'Windows'
                    })
                });
            }
            
            // Override connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });
            
            // Canvas fingerprint randomization
            const getImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function() {
                const imageData = getImageData.apply(this, arguments);
                for (let i = 0; i < imageData.data.length; i += 100) {
                    imageData.data[i] = imageData.data[i] ^ (Math.random() * 2 | 0);
                }
                return imageData;
            };
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
