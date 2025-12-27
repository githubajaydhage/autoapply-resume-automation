import pandas as pd
import fitz  # PyMuPDF
import re
import logging
import os
from pathlib import Path
from utils.config import JOBS_CSV_PATH, BASE_RESUME_PATH, TAILORED_RESUMES_DIR, ERROR_LOG_PATH

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

def tailor_resume_pdf(job, base_doc):
    """Injects keywords into a PDF resume and saves a tailored version."""
    try:
        keywords = extract_keywords_from_summary(job["summary"])
        if not keywords:
            logging.warning(f"No keywords found for job: {job['title']} at {job['company']}")
            return None

        keyword_str = ", ".join(keywords)
        
        # Create a clean filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", job["title"])
        safe_company = re.sub(r'[\\/*?:"<>|]', "", job["company"])
        tailored_resume_filename = f"{safe_company}_{safe_title}.pdf"
        tailored_resume_path = os.path.join(TAILORED_RESUMES_DIR, tailored_resume_filename)

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

    try:
        jobs_df = pd.read_csv(JOBS_CSV_PATH)
    except pd.errors.EmptyDataError:
        logging.info("jobs_today.csv is empty. No resumes to tailor.")
        return

    for index, job in jobs_df.iterrows():
        base_doc = fitz.open(BASE_RESUME_PATH) # Re-open for each job to start fresh
        tailor_resume_pdf(job, base_doc)
        base_doc.close()

    logging.info("--- Resume Tailoring Finished ---")

if __name__ == "__main__":
    main()
