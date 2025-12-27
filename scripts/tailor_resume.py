import pandas as pd
import fitz  # PyMuPDF
import re
import logging
import os
from pathlib import Path
from utils.config import JOBS_CSV_PATH, BASE_RESUME_PATH, TAILORED_RESUMES_DIR, ERROR_LOG_PATH
from utils.resume_naming import get_resume_naming_manager

# --- Configuration ---
KEYWORDS_PLACEHOLDER = "[KEYWORDS]"
STOP_WORDS = set([
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", 
    "for", "with", "about", "to", "from", "of", "job", "experience", "required", 
    "skills", "responsibilities", "qualifications", "company", "team", "work", "role"
])

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ERROR_LOG_PATH),
        logging.StreamHandler()
    ]
)

def extract_keywords_from_summary(text):
    """Extracts potential keywords from job summary text."""
    if not isinstance(text, str):
        return []
    
    potential_keywords = re.findall(r'\b[A-Z][a-zA-Z\d\+\#\.]+\b', text)
    keywords = [kw for kw in potential_keywords if kw.lower() not in STOP_WORDS and len(kw) > 1]
    return sorted(list(set(keywords)), key=lambda x: x.lower())

def tailor_resume_pdf(job, base_doc, naming_manager):
    """Injects keywords into a PDF resume and saves a tailored version."""
    try:
        keywords = extract_keywords_from_summary(job["summary"])
        if not keywords:
            logging.warning(f"No keywords found for job: {job['title']} at {job['company']}")
            return None

        keyword_str = ", ".join(keywords)
        
        # Use standardized naming
        tailored_resume_path = naming_manager.get_tailored_resume_path(job, use_standardized_title=True)
        
        # Log both original and standardized titles for debugging
        standardized_title = naming_manager.title_standardizer.standardize_title(job["title"])
        logging.info(f"Tailoring resume: '{job['title']}' -> '{standardized_title}' for {job['company']}")

        # Replace placeholder in the PDF
        for page in base_doc:
            text_instances = page.search_for(KEYWORDS_PLACEHOLDER)
            for inst in text_instances:
                page.draw_rect(inst, color=(1, 1, 1), fill=(1, 1, 1)) # Cover old text
                page.insert_text(inst.tl, keyword_str, fontsize=10, fontname="helv")

        base_doc.save(tailored_resume_path)
        logging.info(f"Saved tailored PDF resume: {tailored_resume_path}")
        return str(tailored_resume_path)

    except Exception as e:
        logging.error(f"Failed to tailor PDF resume for {job['title']}: {e}")
        return None

def main():
    """Main function to process jobs and tailor resumes."""
    logging.info("--- Starting PDF Resume Tailoring ---")

    if not os.path.exists(BASE_RESUME_PATH):
        logging.error(f"Base resume not found at: {BASE_RESUME_PATH}")
        return

    if not os.path.exists(JOBS_CSV_PATH):
        logging.error(f"Jobs CSV not found at: {JOBS_CSV_PATH}")
        return

    Path(TAILORED_RESUMES_DIR).mkdir(exist_ok=True)
    
    # Initialize resume naming manager
    naming_manager = get_resume_naming_manager(TAILORED_RESUMES_DIR)

    try:
        jobs_df = pd.read_csv(JOBS_CSV_PATH)
    except pd.errors.EmptyDataError:
        logging.info("jobs_today.csv is empty. No resumes to tailor.")
        return

    for index, job in jobs_df.iterrows():
        base_doc = fitz.open(BASE_RESUME_PATH) # Re-open for each job to start fresh
        tailor_resume_pdf(job, base_doc, naming_manager)
        base_doc.close()

    logging.info("--- Resume Tailoring Finished ---")

if __name__ == "__main__":
    main()
