# Production-Grade Job Application Automation

This framework automates the process of applying for jobs on portals like **LinkedIn, Indeed, Naukri**, and **company career pages** (Google, Microsoft, Amazon, and more). It is designed for full, headless automation within a GitHub Actions environment.

**Disclaimer:** This tool is for personal use only. The user is responsible for all actions performed.

## Architecture

The framework has been refactored to a production-grade architecture with a focus on maintainability, scalability, and robustness.

-   **`main.py`**: The central orchestrator that reads scraped jobs and delegates them to the appropriate applicator.
-   **`applicators/`**: Contains portal-specific logic. Each applicator inherits from a `BaseApplicator` to reduce code duplication.
    -   `base.py`: Abstract base class defining the standard interface for all applicators.
    -   `linkedin.py`, `indeed.py`, `naukri.py`: Implementations for each job portal.
    -   `company_careers.py`: Generic applicator for company career pages (Google, Microsoft, Amazon, etc.).
-   **`utils/`**: Contains shared, reusable components.
    -   `browser_manager.py`: A class to manage the Playwright browser instance.
    -   `config.py`: Centralized configuration for portal URLs, credentials, and CSS selectors. This makes updating selectors easy when websites change.
-   **`scripts/`**: Contains standalone scripts for scraping and resume tailoring.
    -   `scrape_jobs.py`: Dynamically generates job search queries based on your resume's skills and applies filters for location and freshness.
    -   `scrape_company_jobs.py`: Scrapes jobs directly from company career pages (Google, Microsoft, Amazon).
    -   `tailor_resume.py`: Customizes your PDF resume with job-specific keywords.

## How It Works

1.  **Dynamic Job Scraping:** The GitHub Actions workflow triggers `scrape_jobs.py`. This script reads your `base_resume.pdf`, extracts your skills, and generates targeted search queries for Indeed and company career pages. It filters by location and freshness based on your workflow inputs.
2.  **Resume Tailoring:** `tailor_resume.py` reads the scraped jobs and your base PDF resume. It injects relevant keywords into the resume, creating a tailored PDF for each application.
3.  **Automated Application:** The main orchestrator (`main.py`) runs, delegating jobs to the correct applicator based on the job link. Each applicator logs in automatically using credentials from GitHub Secrets and submits the application.
4.  **Logging and Artifacts:** All actions are logged. The final application log is uploaded as a GitHub Actions artifact.

## Adding More Companies

To apply to additional company career pages:

1. Open [utils/config.py](utils/config.py)
2. Add a new entry to the `COMPANY_CAREERS` dictionary with:
   - `name`: Company name
   - `careers_url`: Base URL for their careers page
   - `search_params`: URL parameters for job search
   - `selectors`: CSS selectors for job cards, titles, links, and apply buttons

Example:
```python
"meta": {
    "name": "Meta",
    "careers_url": "https://www.metacareers.com/jobs/",
    "search_params": {"q": ""},  # Keywords will be auto-filled
    "selectors": {
        "job_card": "._9ata",
        "job_title": "._8esa",
        "job_link": "a[href*='/jobs/']",
        "apply_button": "button:has-text('Apply now')"
    }
}
```

## Step-by-Step Execution

### 1. Prerequisites

-   A PDF resume file named `base_resume.pdf` located in `resumes/`.
-   This resume **must** contain the placeholder `[KEYWORDS]` where you want tailored skills to be inserted.

### 2. Configure GitHub Secrets

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add the following secrets:

-   `LINKEDIN_EMAIL`
-   `LINKEDIN_PASSWORD`
-   `INDEED_EMAIL`
-   `INDEED_PASSWORD`
-   `NAUKRI_EMAIL`
-   `NAUKRI_PASSWORD`

### 3. Running the Automation

The automation is designed to run via GitHub Actions.

1.  Navigate to the **Actions** tab in your repository.
2.  Select the **Scheduled Job Application** workflow.
3.  The workflow runs automatically on a daily schedule. You can also trigger it manually by clicking **Run workflow**.
4.  When running manually, you can configure the **Job Location** and **Job Freshness** for that specific run.

After the workflow completes, you can download the `application-logs` artifact to see which jobs were applied to.
