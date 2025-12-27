"""
Scrapes job listings from company career pages
"""
import logging
import os
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from utils.config import COMPANY_CAREERS

logger = logging.getLogger(__name__)


def scrape_company_jobs(keywords: list, companies: list = None, location: str = None) -> list:
    """
    Scrape jobs from company career pages
    
    Args:
        keywords: List of keywords to search for
        companies: List of company keys to scrape (e.g., ['google', 'microsoft'])
                  If None, scrapes all configured companies
        location: Job location (e.g., 'Bangalore', 'Remote', 'Hybrid')
    
    Returns:
        List of job dictionaries with keys: title, company, url, portal
    """
    jobs = []
    
    # Get location from environment variable if not provided
    if location is None:
        location = os.getenv("JOB_LOCATION", "Bangalore")
    
    # If no companies specified, use all configured companies
    if companies is None:
        companies = list(COMPANY_CAREERS.keys())
    
    # Filter to only valid companies
    companies = [c for c in companies if c in COMPANY_CAREERS]
    
    if not companies:
        logger.warning("No valid companies specified for scraping")
        return jobs
    
    logger.info(f"Scraping company career pages: {', '.join(companies)}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for company_key in companies:
            try:
                config = COMPANY_CAREERS[company_key]
                company_name = config["name"]
                
                logger.info(f"[{company_name}] Starting scrape for location: {location}")
                
                # Build search URL with keywords and location
                base_url = config["careers_url"]
                search_params = config.get("search_params", {}).copy()
                
                # Add keywords to search params
                keyword_str = " OR ".join(keywords[:5])  # Limit to top 5 keywords
                for key in search_params:
                    if "keyword" in key.lower() or "query" in key.lower() or key == "q":
                        search_params[key] = keyword_str
                        break
                
                # Add location to search params
                location_map = {
                    "Bangalore": "Bangalore",
                    "Remote": "Remote",
                    "Hybrid": "Remote",  # Most companies tag hybrid as remote
                    "Any": ""
                }
                mapped_location = location_map.get(location, location)
                
                # Add location to search params if not "Any"
                if mapped_location:
                    for key in search_params:
                        if "location" in key.lower() or "loc" in key.lower():
                            search_params[key] = mapped_location
                            break
                    else:
                        # If no location field found, add it
                        search_params["location"] = mapped_location
                
                # Build full URL
                if search_params:
                    search_url = f"{base_url}?{urlencode(search_params)}"
                else:
                    search_url = base_url
                
                logger.info(f"[{company_name}] Navigating to {search_url}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)  # Wait for dynamic content
                
                # Get page content
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract job cards using configured selectors
                selectors = config["selectors"]
                job_card_selector = selectors.get("job_card")
                
                if not job_card_selector:
                    logger.warning(f"[{company_name}] No job card selector configured")
                    continue
                
                # Find job cards using CSS selector
                job_cards = soup.select(job_card_selector)
                logger.info(f"[{company_name}] Found {len(job_cards)} job cards")
                
                for card in job_cards[:10]:  # Limit to first 10 jobs per company
                    try:
                        # Extract title
                        title_element = card.select_one(selectors.get("job_title", "h2, h3"))
                        title = title_element.text.strip() if title_element else "Unknown Title"
                        
                        # Extract link
                        link_element = card.select_one(selectors.get("job_link", "a"))
                        if not link_element:
                            continue
                        
                        job_url = link_element.get('href', '')
                        
                        # Make URL absolute if it's relative
                        if job_url.startswith('/'):
                            from urllib.parse import urlparse
                            parsed_base = urlparse(base_url)
                            job_url = f"{parsed_base.scheme}://{parsed_base.netloc}{job_url}"
                        
                        if not job_url or job_url == '#':
                            continue
                        
                        jobs.append({
                            "title": title,
                            "company": company_name,
                            "url": job_url,
                            "portal": f"company_{company_key}"
                        })
                        
                        logger.info(f"[{company_name}] ✓ {title}")
                        
                    except Exception as e:
                        logger.error(f"[{company_name}] Error parsing job card: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"[{company_name}] Error scraping career page: {e}")
                continue
        
        browser.close()
    
    logger.info(f"Total company jobs scraped: {len(jobs)}")
    return jobs
