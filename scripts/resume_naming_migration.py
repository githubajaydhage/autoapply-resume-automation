"""
Utility script to migrate existing tailored resumes to standardized naming
and analyze title mapping patterns.
"""

import os
import shutil
import logging
from pathlib import Path
from utils.config import TAILORED_RESUMES_DIR
from utils.resume_naming import get_resume_naming_manager, JobTitleStandardizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def analyze_existing_resumes():
    """Analyze existing tailored resumes and show naming patterns."""
    if not os.path.exists(TAILORED_RESUMES_DIR):
        logging.warning(f"Tailored resumes directory not found: {TAILORED_RESUMES_DIR}")
        return
    
    resume_files = [f for f in os.listdir(TAILORED_RESUMES_DIR) if f.endswith('.pdf')]
    
    if not resume_files:
        logging.info("No existing tailored resumes found.")
        return
    
    logging.info(f"Found {len(resume_files)} existing tailored resumes:")
    
    naming_manager = get_resume_naming_manager(TAILORED_RESUMES_DIR)
    
    for resume_file in sorted(resume_files):
        # Parse filename to extract company and title
        base_name = resume_file[:-4]  # Remove .pdf
        
        # Handle different possible formats
        if '_' in base_name:
            parts = base_name.split('_', 1)
            company = parts[0]
            original_title = parts[1] if len(parts) > 1 else "Unknown"
            
            # Check if title has " - Company" suffix (the issue you mentioned)
            if ' - ' in original_title:
                title_parts = original_title.split(' - ')
                if len(title_parts) >= 2:
                    clean_title = title_parts[0]
                    suffix = ' - '.join(title_parts[1:])
                    logging.info(f"  📁 {resume_file}")
                    logging.info(f"     Company: {company}")
                    logging.info(f"     Original title: {clean_title}")
                    logging.info(f"     Suffix found: {suffix}")
                    
                    standardized = naming_manager.title_standardizer.standardize_title(clean_title)
                    logging.info(f"     Standardized: {standardized}")
                    
                    expected_filename = f"{company}_{standardized}.pdf"
                    if expected_filename != resume_file:
                        logging.info(f"     Expected filename: {expected_filename}")
                    logging.info("")
            else:
                standardized = naming_manager.title_standardizer.standardize_title(original_title)
                logging.info(f"  📁 {resume_file}")
                logging.info(f"     Company: {company}, Title: {original_title}")
                logging.info(f"     Standardized: {standardized}")
                
                expected_filename = f"{company}_{standardized}.pdf"
                if expected_filename != resume_file:
                    logging.info(f"     Expected filename: {expected_filename}")
                logging.info("")


def show_title_mappings():
    """Show all configured title mappings."""
    mappings = JobTitleStandardizer.TITLE_MAPPINGS
    
    logging.info("=== Job Title Standardization Mappings ===")
    logging.info("Original Title -> Standardized Title")
    logging.info("-" * 50)
    
    for original, standardized in sorted(mappings.items()):
        logging.info(f"{original:30} -> {standardized}")
    
    logging.info("")


def migrate_resumes(dry_run: bool = True):
    """
    Migrate existing resumes to standardized naming.
    
    Args:
        dry_run: If True, only show what would be done without making changes
    """
    if not os.path.exists(TAILORED_RESUMES_DIR):
        logging.warning(f"Tailored resumes directory not found: {TAILORED_RESUMES_DIR}")
        return
    
    resume_files = [f for f in os.listdir(TAILORED_RESUMES_DIR) if f.endswith('.pdf')]
    
    if not resume_files:
        logging.info("No existing tailored resumes found.")
        return
    
    naming_manager = get_resume_naming_manager(TAILORED_RESUMES_DIR)
    migrations = []
    
    for resume_file in resume_files:
        # Parse filename
        base_name = resume_file[:-4]
        
        if '_' in base_name:
            parts = base_name.split('_', 1)
            company = parts[0]
            original_title = parts[1] if len(parts) > 1 else "Unknown"
            
            # Clean title (remove company suffix if present)
            clean_title = original_title
            if ' - ' in original_title:
                clean_title = original_title.split(' - ')[0]
            
            # Create job dict for standardization
            job = {'company': company, 'title': clean_title}
            expected_filename = naming_manager.get_tailored_resume_filename(job, use_standardized_title=True)
            
            if expected_filename != resume_file:
                migrations.append({
                    'old_file': resume_file,
                    'new_file': expected_filename,
                    'old_path': os.path.join(TAILORED_RESUMES_DIR, resume_file),
                    'new_path': os.path.join(TAILORED_RESUMES_DIR, expected_filename),
                    'company': company,
                    'original_title': original_title,
                    'clean_title': clean_title,
                    'standardized_title': naming_manager.title_standardizer.standardize_title(clean_title)
                })
    
    if not migrations:
        logging.info("All resumes already follow standardized naming.")
        return
    
    logging.info(f"Found {len(migrations)} resumes that need migration:")
    logging.info("")
    
    for i, migration in enumerate(migrations, 1):
        logging.info(f"{i}. {migration['old_file']}")
        logging.info(f"   Company: {migration['company']}")
        logging.info(f"   Original: {migration['original_title']}")
        logging.info(f"   Clean: {migration['clean_title']}")
        logging.info(f"   Standardized: {migration['standardized_title']}")
        logging.info(f"   New filename: {migration['new_file']}")
        logging.info("")
    
    if dry_run:
        logging.info("DRY RUN: No files were actually moved. Set dry_run=False to perform migration.")
        return
    
    # Perform actual migration
    logging.info("Starting migration...")
    
    for migration in migrations:
        try:
            if os.path.exists(migration['new_path']):
                logging.warning(f"Target file already exists: {migration['new_file']}")
                continue
            
            shutil.move(migration['old_path'], migration['new_path'])
            logging.info(f"✓ Migrated: {migration['old_file']} -> {migration['new_file']}")
            
        except Exception as e:
            logging.error(f"✗ Failed to migrate {migration['old_file']}: {e}")
    
    logging.info("Migration completed.")


def test_title_standardization():
    """Test title standardization with various examples."""
    test_titles = [
        "Data Engineer - Amazon",
        "Senior Data Analyst - Google", 
        "Business Intelligence Analyst",
        "Data Scientist",
        "Power BI Specialist",
        "SQL Developer - Microsoft",
        "Analytics Consultant",
        "BI Analyst",
        "Data Analyst - Cloud Platform",
        "Senior Business Analyst"
    ]
    
    standardizer = JobTitleStandardizer()
    
    logging.info("=== Title Standardization Tests ===")
    logging.info("Original Title -> Standardized Title")
    logging.info("-" * 60)
    
    for title in test_titles:
        standardized = standardizer.standardize_title(title)
        logging.info(f"{title:35} -> {standardized}")


def main():
    """Main function to run all analyses."""
    logging.info("=== Resume Naming Analysis and Migration Tool ===")
    logging.info("")
    
    # Show current title mappings
    show_title_mappings()
    
    # Test title standardization
    test_title_standardization()
    logging.info("")
    
    # Analyze existing resumes
    analyze_existing_resumes()
    
    # Show migration plan (dry run)
    migrate_resumes(dry_run=True)
    
    logging.info("=== Analysis Complete ===")
    logging.info("")
    logging.info("To perform actual migration, run:")
    logging.info("from scripts.resume_naming_migration import migrate_resumes")
    logging.info("migrate_resumes(dry_run=False)")


if __name__ == "__main__":
    main()