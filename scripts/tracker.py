import pandas as pd
from datetime import datetime
import logging
from pathlib import Path

# --- Configuration ---
DATA_DIR = Path(__file__).parent.parent / "data"
APPLIED_LOG_PATH = DATA_DIR / "applied_log.csv"
ERROR_LOG_PATH = DATA_DIR / "errors.log"

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ERROR_LOG_PATH),
        logging.StreamHandler()
    ]
)

def track_application(title, company, link):
    """Appends a job application to the log file."""
    try:
        date_applied = datetime.now().strftime("%Y-%m-%d")
        new_entry = pd.DataFrame([{
            "title": title,
            "company": company,
            "link": link,
            "date": date_applied
        }])

        if APPLIED_LOG_PATH.exists():
            log_df = pd.read_csv(APPLIED_LOG_PATH)
            # Check if the job link already exists in the log
            if link in log_df['link'].values:
                logging.warning(f"Application for '{title}' at '{company}' already logged.")
                return
        else:
            log_df = pd.DataFrame(columns=["title", "company", "link", "date"])

        combined_df = pd.concat([log_df, new_entry], ignore_index=True)
        combined_df.to_csv(APPLIED_LOG_PATH, index=False)
        logging.info(f"Successfully logged application for: {title}")

    except Exception as e:
        logging.error(f"Failed to log application for {title}: {e}")

if __name__ == "__main__":
    # Example usage:
    # This allows the script to be run standalone for testing.
    logging.info("--- Testing Application Tracker ---")
    track_application(
        "Senior Python Developer",
        "Tech Innovations Inc.",
        "https://www.example.com/job/12345"
    )
    track_application(
        "Frontend Engineer",
        "Creative Solutions LLC",
        "https://www.example.com/job/67890"
    )
    # Test duplicate
    track_application(
        "Senior Python Developer",
        "Tech Innovations Inc.",
        "https://www.example.com/job/12345"
    )
    logging.info("--- Application Tracker Test Finished ---")
