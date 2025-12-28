import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from pathlib import Path
import fitz # PyMuPDF
import re
import os
from urllib.parse import quote_plus
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

# --- Configuration ---
# Job roles to search for
JOB_ROLES = [
    "Data Analyst",
    "Business Intelligence Analyst",
    "BI Developer",
    "Business Analyst",
    "Data Engineer",
    "Analytics Engineer",
    "Technical Support Engineer",
    "Technical Analyst",
    "Systems Analyst",
    "IT Analyst",
    "Support Engineer",
    "Technical Support",
    "Application Support",
    "Data Operations Analyst"
]

# Base search URL for Indeed
INDEED_BASE_URL = "https://www.indeed.com/rss"

# --- Path Configuration ---
from utils.config import DATA_DIR, JOBS_CSV_PATH, ERROR_LOG_PATH, BASE_RESUME_PATH

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ERROR_LOG_PATH),
        logging.StreamHandler()
    ]
)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logging.error(f"Could not read PDF {pdf_path}: {e}")
        return ""

def extract_skills_from_resume(resume_text):
    """Extracts relevant data/analytics skills from resume text."""
    skills = []
    
    # Prioritized data/analytics skills to search for
    relevant_skills = [
        # BI Tools
        "Power BI", "Tableau", "Looker", "QlikView", "SSRS",
        # Databases & Query Languages
        "SQL", "MySQL", "PostgreSQL", "Oracle", "T-SQL", "SSMS",
        # Programming
        "Python", "R", "DAX", "M Query", "Power Query",
        # Data Processing
        "ETL", "Data Warehouse", "Data Pipeline", "Data Modeling",
        # Excel & Office
        "Excel", "Advanced Excel", "VBA", "Pivot Tables",
        # Cloud Platforms
        "Azure", "AWS", "GCP", "Snowflake", "BigQuery",
        # Visualization
        "Data Visualization", "Dashboard", "KPI", "Reporting"
    ]
    
    # Extract skills present in resume
    for skill in relevant_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            skills.append(skill)
    
    # Add core competencies if skills list is short
    if len(skills) < 3:
        skills.extend(["SQL", "Power BI", "Excel"])
    
    return list(set(skills))[:8]  # Return unique skills, limit to top 8

def construct_search_queries(skills):
    """Constructs search queries from roles and skills."""
    queries = []
    for role in JOB_ROLES:
        # Main role query only - don't add skill variations to avoid rate limiting
        queries.append(role)
    
    # Add a few skill-based queries for top skills
    queries.extend(skills[:3])
    
    return queries

def get_rss_feeds(queries):
    """Generates Indeed RSS feed URLs from search queries."""
    feeds = {}
    
    # Get location and freshness from environment variables set by the workflow
    location = os.getenv("JOB_LOCATION", "Bangalore")
    freshness_days = os.getenv("JOB_FRESHNESS", "1") # Default to last 24 hours

    # Map freshness input to Indeed's 'fromage' parameter
    freshness_map = {
        "Last 24 hours": "1",
        "Last 3 days": "3",
        "Last 7 days": "7",
        "Any": ""
    }
    fromage = freshness_map.get(freshness_days, "")

    # Map location to Indeed's location format
    location_map = {
        "Bangalore": "Bangalore, Karnataka",
        "Remote": "Remote",
        "Hybrid": "Hybrid Remote",
        "Any": ""
    }
    mapped_location = location_map.get(location, location)

    for query in queries:
        location_param = ""
        if mapped_location:
            location_param = f"&l={quote_plus(mapped_location)}"
        
        fromage_param = ""
        if fromage:
            fromage_param = f"&fromage={fromage}"

        feed_name = f"Indeed - {query} ({location})"
        feed_url = f"{INDEED_BASE_URL}?q={quote_plus(query)}{location_param}{fromage_param}"
        feeds[feed_name] = feed_url
        
    return feeds

def clean_summary(summary_html):
    """Cleans HTML tags from the job summary."""
    soup = BeautifulSoup(summary_html, "lxml")
    return soup.get_text().strip()

def create_session_with_retries():
    """Creates a requests session with advanced anti-detection measures."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=2,  # Reduced retries for speed
        backoff_factor=0.5,  # Faster backoff
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Advanced anti-detection headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Connection': 'keep-alive',
    })
    
    return session

def fetch_jobs(rss_feeds):
    """Fetches jobs from RSS feeds with advanced anti-detection."""
    jobs_list = []
    session = create_session_with_retries()
    
    # Try different Indeed domains and approaches
    indeed_alternatives = [
        "https://rss.indeed.com/rss",  # Alternative RSS endpoint
        "https://www.indeed.co.in/rss",  # India domain  
        "https://indeed.com/rss",  # No www
    ]
    
    for feed_name, feed_url in rss_feeds.items():
        if "indeed.com" in feed_url.lower():
            # Special handling for Indeed with multiple fallbacks
            success = False
            for alt_base in indeed_alternatives:
                try:
                    # Reconstruct URL with alternative base
                    url_parts = feed_url.split('?', 1)
                    if len(url_parts) > 1:
                        alt_url = f"{alt_base}?{url_parts[1]}"
                    else:
                        alt_url = alt_base
                    
                    logging.info(f"Trying Indeed alternative: {alt_base}")
                    
                    # Random delay to avoid detection
                    time.sleep(random.uniform(1, 3))
                    
                    # Fetch with session
                    response = session.get(alt_url, timeout=15)
                    
                    if response.status_code == 403:
                        logging.warning(f"403 Forbidden from {alt_base}, trying next...")
                        continue
                        
                    response.raise_for_status()
                    
                    # Parse feed from response content
                    feed = feedparser.parse(response.content)
                    
                    if hasattr(feed, 'entries') and len(feed.entries) > 0:
                        logging.info(f"✅ SUCCESS: Found {len(feed.entries)} jobs from Indeed")
                        
                        for entry in feed.entries:
                            job = {
                                "title": entry.title,
                                "company": entry.get("author", "N/A"),
                                "link": entry.link,
                                "published": entry.get("published", "N/A"),
                                "summary": clean_summary(entry.get("summary", "")),
                                "location": "Bangalore",
                                "portal": "Indeed"
                            }
                            jobs_list.append(job)
                        
                        success = True
                        break  # Exit alternative loop on success
                        
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Network error with {alt_base}: {e}")
                    continue
                except Exception as e:
                    logging.warning(f"Parse error with {alt_base}: {e}")
                    continue
            
            if not success:
                logging.error(f"❌ All Indeed alternatives failed for {feed_name}")
        else:
            # Handle non-Indeed feeds normally  
            try:
                logging.info(f"Fetching jobs from: {feed_name}")
                
                # Fetch with proper headers using requests
                response = session.get(feed_url, timeout=30)
                response.raise_for_status()
                
                # Parse the RSS feed from the response content
                feed = feedparser.parse(response.content)
                
                if feed.bozo:
                    logging.warning(f"Could not parse feed {feed_name}: {feed.bozo_exception}")
                    continue

                if not feed.entries:
                    logging.info(f"No jobs found in feed: {feed_name}")
                    continue
                    
                logging.info(f"Found {len(feed.entries)} jobs in {feed_name}")

                for entry in feed.entries:
                    job = {
                        "title": entry.title,
                        "company": entry.get("author", "N/A"),
                        "link": entry.link,
                        "published": entry.get("published", "N/A"),
                        "summary": clean_summary(entry.get("summary", "")),
                        "location": "Bangalore",
                        "portal": "RSS"
                    }
                    jobs_list.append(job)
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Network error fetching from {feed_name}: {e}")
            except Exception as e:
                logging.error(f"Could not parse feed {feed_name}: {e}")

        # Rate limiting between feeds
        time.sleep(random.uniform(2, 4))
    
    logging.info(f"📊 Total jobs fetched from RSS feeds: {len(jobs_list)}")
    return jobs_list

def save_jobs_to_csv(jobs_list):
    """Saves a list of jobs to a CSV file, avoiding duplicates."""
    if not jobs_list:
        logging.info("No new jobs found to save.")
        return

    new_jobs_df = pd.DataFrame(jobs_list)
    
    # Normalize column names: handle both 'link' and 'url' as the same field
    if 'link' in new_jobs_df.columns and 'url' not in new_jobs_df.columns:
        new_jobs_df = new_jobs_df.rename(columns={'link': 'url'})

    if os.path.exists(JOBS_CSV_PATH):
        try:
            existing_jobs_df = pd.read_csv(JOBS_CSV_PATH)
            # Normalize existing CSV column names too
            if 'link' in existing_jobs_df.columns and 'url' not in existing_jobs_df.columns:
                existing_jobs_df = existing_jobs_df.rename(columns={'link': 'url'})
            
            # Filter duplicates using 'url' column if it exists
            if 'url' in new_jobs_df.columns and 'url' in existing_jobs_df.columns:
                new_jobs_df = new_jobs_df[~new_jobs_df['url'].isin(existing_jobs_df['url'])]
            elif 'url' in new_jobs_df.columns:
                # No url column in existing, all new jobs are unique
                pass
        except pd.errors.EmptyDataError:
            existing_jobs_df = pd.DataFrame()
    else:
        existing_jobs_df = pd.DataFrame()

    if not new_jobs_df.empty:
        combined_df = pd.concat([existing_jobs_df, new_jobs_df], ignore_index=True)
        combined_df.to_csv(JOBS_CSV_PATH, index=False)
        logging.info(f"Saved {len(new_jobs_df)} new jobs to {JOBS_CSV_PATH}")
    else:
        logging.info("No new unique jobs to add to the CSV.")


if __name__ == "__main__":
    logging.info("--- Starting Dynamic Job Scraping ---")
    
    Path(DATA_DIR).mkdir(exist_ok=True)
    
    logging.info("🚀 Starting OPTIMIZED Job Scraping System")
    
    resume_text = extract_text_from_pdf(BASE_RESUME_PATH)
    if not resume_text:
        logging.error("Could not read resume. Aborting job scrape.")
        exit(1)
    
    skills = extract_skills_from_resume(resume_text)
    logging.info(f"Extracted skills from resume: {skills}")
    
    # Step 1: RSS feeds with Indeed anti-detection (optimized)
    logging.info("📡 Fetching RSS feeds with anti-detection...")
    start_rss = time.time()
    search_queries = construct_search_queries(skills[:8])  # Limit to top 8 skills for speed
    rss_feeds = get_rss_feeds(search_queries)
    rss_jobs = fetch_jobs(rss_feeds)
    rss_time = time.time() - start_rss
    logging.info(f"✅ RSS complete: {len(rss_jobs)} jobs in {rss_time:.1f}s")
    
    # Step 2: Company scraping is disabled (module was removed)
    # Jobs will come from existing data or manual sources
    logging.info("🏢 Company scraping: Using existing job data")
    company_jobs = []
    
    # Step 3: Combine and format results
    all_jobs = []
    
    # Add RSS jobs
    for job in rss_jobs:
        all_jobs.append({
            "title": job["title"],
            "company": job["company"],
    # Step 4: If no jobs from RSS (all blocked), try public scraper
    if not rss_jobs:
        logging.info("📡 RSS feeds blocked, trying public page scraping...")
        try:
            from scripts.linkedin_public_scraper import scrape_jobs_public
            public_jobs_df = scrape_jobs_public(location=location)
            if not public_jobs_df.empty:
                for _, job in public_jobs_df.iterrows():
                    all_jobs.append({
                        "title": job.get("title", "Unknown"),
                        "company": job.get("company", "Unknown"),
                        "link": job.get("url", ""),
                        "summary": job.get("description", ""),
                        "portal": job.get("source", "public"),
                        "location": job.get("location", location),
                        "posted_date": job.get("scraped_at", "Recent")
                    })
                logging.info(f"✅ Found {len(public_jobs_df)} jobs via public scraping")
        except Exception as e:
            logging.warning(f"Public scraper error: {e}")
    else:
        # Add RSS jobs
        for job in rss_jobs:
            all_jobs.append({
                "title": job["title"],
                "company": job["company"],
                "link": job["link"],
                "summary": job.get("summary", ""),
                "portal": job.get("portal", "RSS"),
                "location": job.get("location", "Bangalore"),
                "posted_date": job.get("published", "Recent")
            })
    
    # Add company jobs  
    for job in company_jobs:
        all_jobs.append({
            "title": job["title"],
            "company": job["company"],
            "link": job["link"],
            "summary": job.get("summary", f"Job from {job['company']} career page"),
            "portal": job.get("portal", "company"),
            "location": job.get("location", "Bangalore"),
            "posted_date": job.get("posted_date", "Recent")
        })
    
    # Step 5: Save results
    if all_jobs:
        save_jobs_to_csv(all_jobs)
        total_time = time.time() - start_rss
        logging.info(f"🎯 OPTIMIZED SCRAPING COMPLETE!")
        logging.info(f"   📡 RSS jobs: {len(rss_jobs)}")
        logging.info(f"   🏢 Company jobs: {len(company_jobs)}")  
        logging.info(f"   📝 Total jobs: {len(all_jobs)}")
        logging.info(f"   ⚡ Total time: {total_time:.1f}s (was ~25+ minutes)")
    else:
        logging.warning("No jobs were fetched.")
            
    logging.info("--- Job Scraping Finished ---")
