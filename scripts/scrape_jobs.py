import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from pathlib import Path
import fitz # PyMuPDF
import re
import os

# --- Configuration ---
# Job roles to search for
JOB_ROLES = [
    "Data Analyst",
    "Business Intelligence Analyst",
    "BI Developer",
    "Business Analyst",
    "Data Engineer",
    "Analytics Engineer"
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
        # Main role query
        queries.append(role)
        # Role + skill queries
        for skill in skills[:3]: # Limit to top 3 skills to avoid overly specific searches
            queries.append(f'{role} {skill}')
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
            location_param = f"&l={mapped_location}"
        
        fromage_param = ""
        if fromage:
            fromage_param = f"&fromage={fromage}"

        feed_name = f"Indeed - {query} ({location})"
        feed_url = f"{INDEED_BASE_URL}?q={query.replace(' ', '+')}{location_param}{fromage_param}"
        feeds[feed_name] = feed_url
        
    return feeds

def clean_summary(summary_html):
    """Cleans HTML tags from the job summary."""
    soup = BeautifulSoup(summary_html, "lxml")
    return soup.get_text().strip()

def fetch_jobs(rss_feeds):
    """Fetches jobs from RSS feeds and returns a list of job dictionaries."""
    jobs_list = []
    for feed_name, feed_url in rss_feeds.items():
        try:
            logging.info(f"Fetching jobs from: {feed_name}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logging.warning(f"Could not parse feed {feed_name}: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                job = {
                    "title": entry.title,
                    "company": entry.get("author", "N/A"),
                    "link": entry.link,
                    "summary": clean_summary(entry.summary)
                }
                jobs_list.append(job)
            
            time.sleep(2)

        except Exception as e:
            logging.error(f"An error occurred while fetching from {feed_name}: {e}")
            
    return jobs_list

def save_jobs_to_csv(jobs_list):
    """Saves a list of jobs to a CSV file, avoiding duplicates."""
    if not jobs_list:
        logging.info("No new jobs found to save.")
        return

    new_jobs_df = pd.DataFrame(jobs_list)

    if os.path.exists(JOBS_CSV_PATH):
        try:
            existing_jobs_df = pd.read_csv(JOBS_CSV_PATH)
            new_jobs_df = new_jobs_df[~new_jobs_df['link'].isin(existing_jobs_df['link'])]
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
    
    resume_text = extract_text_from_pdf(BASE_RESUME_PATH)
    if not resume_text:
        logging.error("Could not read resume. Aborting job scrape.")
    else:
        skills = extract_skills_from_resume(resume_text)
        logging.info(f"Extracted skills from resume: {skills}")
        
        # Scrape from Indeed
        search_queries = construct_search_queries(skills)
        rss_feeds = get_rss_feeds(search_queries)
        jobs = fetch_jobs(rss_feeds)
        
        # Scrape from company career pages
        from scripts.scrape_company_jobs import scrape_company_jobs
        company_jobs = scrape_company_jobs(skills)
        
        # Convert company jobs to same format as Indeed jobs
        for job in company_jobs:
            jobs.append({
                "title": job["title"],
                "company": job["company"],
                "link": job["url"],
                "summary": f"Job from {job['company']} career page",
                "portal": job.get("portal", "company")
            })
        
        if jobs:
            save_jobs_to_csv(jobs)
        else:
            logging.warning("No jobs were fetched.")
            
    logging.info("--- Job Scraping Finished ---")
