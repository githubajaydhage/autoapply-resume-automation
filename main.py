import pandas as pd
import logging
import sys
from applicators.linkedin import LinkedInApplicator
from applicators.indeed import IndeedApplicator
from applicators.naukri import NaukriApplicator
from utils.config import JOBS_CSV_PATH, PORTAL_CONFIGS

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/main.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main orchestrator for the job application process."""
    logging.info("--- Starting Main Application Orchestrator ---")

    try:
        jobs_df = pd.read_csv(JOBS_CSV_PATH)
    except FileNotFoundError:
        logging.error(f"Jobs CSV not found at: {JOBS_CSV_PATH}. Please run scrape_jobs.py first.")
        return
    except pd.errors.EmptyDataError:
        logging.info("jobs_today.csv is empty. No jobs to apply for.")
        return

    # Group jobs by portal
    jobs_by_portal = {}
    for portal, config in PORTAL_CONFIGS.items():
        domain = config["domain"]
        portal_jobs = jobs_df[jobs_df['link'].str.contains(domain, na=False)]
        if not portal_jobs.empty:
            jobs_by_portal[portal] = portal_jobs.to_dict('records')

    if not jobs_by_portal:
        logging.info("No jobs found for the configured portals.")
        return

    # Instantiate and run applicators
    applicators = {
        "linkedin": LinkedInApplicator(),
        "indeed": IndeedApplicator(),
        "naukri": NaukriApplicator(),
    }

    for portal, jobs in jobs_by_portal.items():
        if portal in applicators:
            applicator = applicators[portal]
            applicator.run(jobs)
        else:
            logging.warning(f"No applicator found for portal: {portal}")

    logging.info("--- Main Application Orchestrator Finished ---")

if __name__ == "__main__":
    main()
