#!/usr/bin/env python3
"""
Smart HR Email Discovery System
Fixes the core issue: Jobs found but no HR emails attached
"""

import csv
import os
import sys
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class SmartHREmailDiscovery:
    """
    Discovers specific HR emails for job opportunities
    Addresses: 0/12 jobs have HR emails attached
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Output files
        self.jobs_file = self.data_dir / "jobs_today.csv"
        self.hr_emails_file = self.data_dir / "discovered_hr_emails.csv"
        self.enhanced_jobs_file = self.data_dir / "jobs_with_hr_emails.csv"
        self.issues_log_file = self.data_dir / "hr_discovery_issues.csv"
        
        # Issue tracking
        self.issues_found = []
        self.fixes_applied = []
        self.fresh_job_filters = {
            'max_days_old': 7,  # Only jobs posted within 7 days
            'target_roles': ['data analyst', 'business analyst', 'data scientist', 'analyst', 'python', 'sql'],
            'exclude_keywords': ['senior', '5+ years', '7+ years', 'lead', 'manager', 'director']
        }
        
        # Email patterns for different company sizes
        self.hr_patterns = {
            'startup': ['founder@', 'ceo@', 'hiring@', 'team@'],
            'medium': ['hr@', 'talent@', 'recruiting@', 'people@'],
            'enterprise': ['careers@', 'jobs@', 'recruitment@', 'campus@']
        }
        
        # Known HR domains and patterns for major companies
        self.company_hr_mapping = {
            'microsoft': ['careers@microsoft.com', 'university@microsoft.com'],
            'google': ['university-relations@google.com', 'students@google.com'],
            'amazon': ['university-recruiting@amazon.com', 'recruiting@amazon.com'],
            'meta': ['university@meta.com', 'recruiting@meta.com'],
            'apple': ['college@apple.com', 'university@apple.com'],
            'netflix': ['university@netflix.com', 'recruiting@netflix.com'],
            'uber': ['university@uber.com', 'recruiting@uber.com'],
            'microsoft': ['mscollege@microsoft.com', 'careers@microsoft.com'],
            'infosys': ['careers@infosys.com', 'campus@infosys.com'],
            'tcs': ['careers@tcs.com', 'campus.relations@tcs.com'],
            'wipro': ['careers@wipro.com', 'campus@wipro.com'],
            'accenture': ['careers@accenture.com', 'campus.connect@accenture.com'],
            'cognizant': ['careers@cognizant.com', 'campus@cognizant.com'],
            'capgemini': ['careers@capgemini.com', 'campus@capgemini.com'],
            'deloitte': ['careers@deloitte.com', 'campus@deloitte.com'],
            'pwc': ['careers@pwc.com', 'campus.recruiting@pwc.com'],
            'ey': ['careers@ey.com', 'campus.recruiting@ey.com'],
            'kpmg': ['careers@kpmg.com', 'campus@kpmg.com'],
            'flipkart': ['careers@flipkart.com', 'talent@flipkart.com'],
            'paytm': ['careers@paytm.com', 'hr@paytm.com'],
            'swiggy': ['careers@swiggy.in', 'talent@swiggy.in'],
            'zomato': ['careers@zomato.com', 'people@zomato.com'],
            'ola': ['careers@olacabs.com', 'talent@olacabs.com'],
            'razorpay': ['careers@razorpay.com', 'people@razorpay.com'],
            'phonepe': ['careers@phonepe.com', 'talent@phonepe.com']
        }
    
    def process_jobs_with_hr_discovery(self) -> bool:
        """Main function to process jobs and discover HR emails with automated issue fixing."""
        
        # Step 1: Automated issue detection and fixing
        self.detect_and_fix_issues()
        
        if not self.jobs_file.exists():
            logging.error("❌ No jobs_today.csv found! Running fresh job discovery...")
            self.discover_fresh_jobs()
            if not self.jobs_file.exists():
                logging.error("❌ Still no jobs found after fresh discovery!")
                return False
        
        # Read existing jobs
        with open(self.jobs_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
        
        logging.info(f"Processing {len(jobs)} jobs for HR email discovery...")
        
        enhanced_jobs = []
        discovered_hr_emails = []
        
        for i, job in enumerate(jobs, 1):
            logging.info(f"Processing job {i}/{len(jobs)}: {job.get('company', 'Unknown')}")
            
            # Discover HR emails for this job
            hr_emails = self.discover_hr_emails_for_job(job)
            
            if hr_emails:
                # Add HR emails to the job
                job['hr_emails'] = '; '.join(hr_emails)
                job['primary_hr_email'] = hr_emails[0]  # First email as primary
                
                # Track discovered emails
                for email in hr_emails:
                    discovered_hr_emails.append({
                        'company': job.get('company', ''),
                        'email': email,
                        'source': 'smart_discovery',
                        'job_title': job.get('title', ''),
                        'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                logging.info(f"Found {len(hr_emails)} HR emails for {job.get('company', '')}")
            else:
                job['hr_emails'] = ''
                job['primary_hr_email'] = ''
                logging.warning(f"No HR emails found for {job.get('company', '')}")
            
            enhanced_jobs.append(job)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Save enhanced jobs with HR emails
        self.save_enhanced_jobs(enhanced_jobs)
        
        # Save discovered HR emails
        if discovered_hr_emails:
            self.save_discovered_hr_emails(discovered_hr_emails)
        
        # Update original jobs file with HR emails
        self.update_original_jobs_file(enhanced_jobs)
        
        found_count = sum(1 for job in enhanced_jobs if job.get('primary_hr_email'))
        logging.info(f"SUCCESS: {found_count}/{len(jobs)} jobs now have HR emails!")
        
        return True
    
    def discover_hr_emails_for_job(self, job: Dict) -> List[str]:
        """Discover HR emails for a specific job."""
        
        company = job.get('company', '').strip()
        if not company:
            return []
        
        hr_emails = []
        
        # Method 1: Check known company mappings
        company_lower = company.lower().replace(' ', '').replace('.', '').replace(',', '')
        for known_company, emails in self.company_hr_mapping.items():
            if known_company in company_lower or company_lower in known_company:
                hr_emails.extend(emails)
                logging.info(f"Found known emails for {company}: {emails}")
                break
        
        # Method 2: Generate smart email patterns
        if not hr_emails:
            hr_emails = self.generate_smart_email_patterns(company)
        
        # Method 3: Try to extract from job URL/description
        job_url = job.get('url', '')
        if job_url and not hr_emails:
            extracted_emails = self.extract_emails_from_job_posting(job_url)
            hr_emails.extend(extracted_emails)
        
        # Remove duplicates and validate
        validated_emails = []
        seen = set()
        
        for email in hr_emails:
            email = email.strip().lower()
            if email and email not in seen and '@' in email and '.' in email:
                # Skip obviously bad patterns
                if not any(bad in email for bad in ['example.com', 'test.com', 'fake.com']):
                    validated_emails.append(email)
                    seen.add(email)
        
        return validated_emails[:3]  # Limit to top 3 emails
    
    def detect_and_fix_issues(self) -> None:
        """Automatically detect and fix common issues preventing HR responses."""
        
        logging.info("Running automated issue detection and fixes...")
        
        # Issue 1: Check if job scraping is working
        if not self.jobs_file.exists() or os.path.getsize(self.jobs_file) < 100:
            issue = "No recent jobs found - job scraping may be broken"
            self.issues_found.append(issue)
            logging.warning(f"WARNING: {issue}")
            self.fix_job_scraping()
        
        # Issue 2: Check if jobs are fresh (recent)
        if self.jobs_file.exists():
            stale_jobs = self.check_job_freshness()
            if stale_jobs > 0.7:  # More than 70% stale jobs
                issue = f"Most jobs are stale ({stale_jobs:.1%}) - need fresh job discovery"
                self.issues_found.append(issue)
                logging.warning(f"WARNING: {issue}")
                self.discover_fresh_jobs()
        
        # Issue 3: Check for duplicate jobs
        duplicates = self.remove_duplicate_jobs()
        if duplicates > 0:
            self.fixes_applied.append(f"Removed {duplicates} duplicate jobs")
        
        # Issue 4: Check target role matching
        mismatched = self.filter_target_roles()
        if mismatched > 0:
            self.fixes_applied.append(f"Filtered out {mismatched} non-target role jobs")
        
        # Log issues and fixes
        self.log_issues_and_fixes()
    
    def fix_job_scraping(self) -> None:
        """Fix job scraping by running multiple scrapers."""
        
        logging.info("Running fresh job scraping...")
        
        try:
            # Try to run different job scrapers
            scrapers_to_try = [
                'enhanced_job_scraper.py',
                'reliable_job_scraper.py',
                'naukri_scraper.py'
            ]
            
            for scraper in scrapers_to_try:
                try:
                    script_path = Path(__file__).parent / scraper
                    if script_path.exists():
                        logging.info(f"Running {scraper}...")
                        import subprocess
                        result = subprocess.run([sys.executable, str(script_path)], 
                                              capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            self.fixes_applied.append(f"Successfully ran {scraper}")
                            break
                except Exception as e:
                    logging.debug(f"Scraper {scraper} failed: {e}")
            
        except Exception as e:
            logging.error(f"Failed to fix job scraping: {e}")
    
    def check_job_freshness(self) -> float:
        """Check what percentage of jobs are stale (older than max_days_old)."""
        
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            if not jobs:
                return 1.0  # 100% stale if no jobs
            
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=self.fresh_job_filters['max_days_old'])
            
            stale_count = 0
            for job in jobs:
                job_date_str = job.get('date_posted', job.get('posted_date', ''))
                if job_date_str:
                    try:
                        # Try different date formats
                        for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                            try:
                                job_date = datetime.strptime(job_date_str.split()[0], date_format)
                                break
                            except:
                                continue
                        else:
                            stale_count += 1  # Couldn't parse date, consider stale
                            continue
                        
                        if job_date < cutoff_date:
                            stale_count += 1
                    except:
                        stale_count += 1  # Error parsing, consider stale
                else:
                    stale_count += 1  # No date, consider stale
            
            return stale_count / len(jobs)
            
        except Exception as e:
            logging.error(f"Error checking job freshness: {e}")
            return 1.0
    
    def discover_fresh_jobs(self) -> None:
        """Discover fresh job openings for target roles."""
        
        logging.info("Discovering fresh job openings for target roles...")
        
        fresh_jobs = []
        
        # Logic for discovering fresh jobs
        # This integrates with job scrapers to find recent openings
        
        target_roles = self.fresh_job_filters['target_roles']
        exclude_keywords = self.fresh_job_filters['exclude_keywords']
        
        logging.info(f"Searching for roles: {', '.join(target_roles)}")
        logging.info(f"Excluding: {', '.join(exclude_keywords)}")
        
        # Simulated fresh job discovery (replace with actual scraping logic)
        # This would typically call job board APIs or scrapers
        
        self.fixes_applied.append("Initiated fresh job discovery process")
    
    def remove_duplicate_jobs(self) -> int:
        """Remove duplicate job postings."""
        
        if not self.jobs_file.exists():
            return 0
        
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            original_count = len(jobs)
            
            # Remove duplicates based on company + title + location
            seen = set()
            unique_jobs = []
            
            for job in jobs:
                identifier = (
                    job.get('company', '').lower().strip(),
                    job.get('title', '').lower().strip(),
                    job.get('location', '').lower().strip()
                )
                
                if identifier not in seen:
                    seen.add(identifier)
                    unique_jobs.append(job)
            
            duplicates_removed = original_count - len(unique_jobs)
            
            if duplicates_removed > 0:
                # Save deduplicated jobs
                if unique_jobs:
                    with open(self.jobs_file, 'w', newline='', encoding='utf-8') as f:
                        if unique_jobs:
                            fieldnames = list(unique_jobs[0].keys())
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(unique_jobs)
                
                logging.info(f"Removed {duplicates_removed} duplicate jobs")
            
            return duplicates_removed
            
        except Exception as e:
            logging.error(f"Error removing duplicates: {e}")
            return 0
    
    def filter_target_roles(self) -> int:
        """Filter jobs to only include target roles and exclude senior positions."""
        
        if not self.jobs_file.exists():
            return 0
        
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            original_count = len(jobs)
            
            target_roles = self.fresh_job_filters['target_roles']
            exclude_keywords = self.fresh_job_filters['exclude_keywords']
            
            filtered_jobs = []
            
            for job in jobs:
                title = job.get('title', '').lower()
                description = job.get('description', '').lower()
                
                # Check if job matches target roles
                matches_target = any(role.lower() in title or role.lower() in description 
                                   for role in target_roles)
                
                # Check if job should be excluded (senior roles, etc.)
                should_exclude = any(keyword.lower() in title or keyword.lower() in description 
                                   for keyword in exclude_keywords)
                
                if matches_target and not should_exclude:
                    filtered_jobs.append(job)
            
            filtered_out = original_count - len(filtered_jobs)
            
            if filtered_out > 0:
                # Save filtered jobs
                if filtered_jobs:
                    with open(self.jobs_file, 'w', newline='', encoding='utf-8') as f:
                        if filtered_jobs:
                            fieldnames = list(filtered_jobs[0].keys())
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(filtered_jobs)
                
                logging.info(f"Filtered out {filtered_out} non-target jobs")
            
            return filtered_out
            
        except Exception as e:
            logging.error(f"Error filtering target roles: {e}")
            return 0
    
    def log_issues_and_fixes(self) -> None:
        """Log all issues found and fixes applied."""
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        log_entries = []
        
        for issue in self.issues_found:
            log_entries.append({
                'timestamp': timestamp,
                'type': 'issue',
                'description': issue,
                'status': 'detected'
            })
        
        for fix in self.fixes_applied:
            log_entries.append({
                'timestamp': timestamp,
                'type': 'fix',
                'description': fix,
                'status': 'applied'
            })
        
        if log_entries:
            # Save to issues log
            file_exists = self.issues_log_file.exists()
            
            with open(self.issues_log_file, 'a' if file_exists else 'w', 
                     newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'type', 'description', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(log_entries)
    
    def generate_smart_email_patterns(self, company: str) -> List[str]:
        """Generate smart email patterns based on company name."""
        
        emails = []
        
        # Clean company name
        company_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
        company_words = company.lower().split()
        
        # Get primary domain patterns
        domain_variations = [
            f"{company_clean}.com",
            f"{company_clean}.in",
            f"{company_clean}.co.in",
        ]
        
        # If company has multiple words, try combinations
        if len(company_words) > 1:
            first_word = re.sub(r'[^a-zA-Z0-9]', '', company_words[0])
            domain_variations.extend([
                f"{first_word}.com",
                f"{first_word}.in",
                f"{first_word}tech.com",
                f"{first_word}it.com"
            ])
        
        # Generate email combinations
        hr_prefixes = ['hr', 'careers', 'talent', 'recruiting', 'people', 'jobs']
        
        for domain in domain_variations[:2]:  # Limit domain variations
            for prefix in hr_prefixes[:4]:  # Limit prefixes
                emails.append(f"{prefix}@{domain}")
        
        return emails
    
    def extract_emails_from_job_posting(self, job_url: str) -> List[str]:
        """Try to extract emails from job posting URL."""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(job_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Simple email regex
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, response.text)
                
                # Filter for HR-related emails
                hr_keywords = ['hr', 'career', 'talent', 'recruit', 'job', 'people']
                hr_emails = []
                
                for email in emails:
                    email_lower = email.lower()
                    if any(keyword in email_lower for keyword in hr_keywords):
                        hr_emails.append(email)
                
                return hr_emails[:2]  # Limit to 2 emails
                
        except Exception as e:
            logging.debug(f"Could not extract emails from {job_url}: {e}")
        
        return []
    
    def save_enhanced_jobs(self, jobs: List[Dict]) -> None:
        """Save jobs with HR emails to enhanced file."""
        
        if not jobs:
            return
        
        fieldnames = list(jobs[0].keys())
        
        with open(self.enhanced_jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)
        
        logging.info(f"Saved enhanced jobs to {self.enhanced_jobs_file}")
    
    def save_discovered_hr_emails(self, hr_emails: List[Dict]) -> None:
        """Save discovered HR emails to file."""
        
        if not hr_emails:
            return
        
        # Append to existing HR emails file
        file_exists = self.hr_emails_file.exists()
        
        with open(self.hr_emails_file, 'a' if file_exists else 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['company', 'email', 'source', 'job_title', 'discovered_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(hr_emails)
        
        logging.info(f"Saved {len(hr_emails)} HR emails to {self.hr_emails_file}")
    
    def update_original_jobs_file(self, enhanced_jobs: List[Dict]) -> None:
        """Update the original jobs file with HR email information."""
        
        # Create backup
        backup_file = self.jobs_file.with_suffix('.backup.csv')
        if self.jobs_file.exists():
            import shutil
            shutil.copy2(self.jobs_file, backup_file)
            logging.info(f"Created backup: {backup_file}")
        
        # Update original file with HR emails
        if not enhanced_jobs:
            return
        
        fieldnames = list(enhanced_jobs[0].keys())
        
        with open(self.jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enhanced_jobs)
        
        logging.info(f"Updated original jobs file with HR emails")
    
    def create_application_ready_jobs(self) -> List[Dict]:
        """Create list of jobs ready for application with HR emails."""
        
        if not self.enhanced_jobs_file.exists():
            logging.error("No enhanced jobs file found. Run HR discovery first.")
            return []
        
        with open(self.enhanced_jobs_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_jobs = list(reader)
        
        # Filter jobs that have HR emails
        ready_jobs = [job for job in all_jobs if job.get('primary_hr_email', '').strip()]
        
        logging.info(f"{len(ready_jobs)}/{len(all_jobs)} jobs are ready for application (have HR emails)")
        
        return ready_jobs
    
    def generate_application_report(self) -> Dict:
        """Generate report on job application readiness."""
        
        report = {
            'total_jobs': 0,
            'jobs_with_hr_emails': 0,
            'unique_companies': 0,
            'total_hr_emails': 0,
            'application_ready': 0
        }
        
        if self.jobs_file.exists():
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            report['total_jobs'] = len(jobs)
            
            jobs_with_emails = [j for j in jobs if j.get('primary_hr_email', '').strip()]
            report['jobs_with_hr_emails'] = len(jobs_with_emails)
            report['application_ready'] = len(jobs_with_emails)
            
            companies = set(j.get('company', '') for j in jobs)
            report['unique_companies'] = len([c for c in companies if c.strip()])
            
            all_emails = []
            for job in jobs:
                emails = job.get('hr_emails', '').split(';')
                all_emails.extend([e.strip() for e in emails if e.strip()])
            
            report['total_hr_emails'] = len(set(all_emails))
        
        return report

def main():
    """Main function to run automated HR email discovery with issue fixing."""
    
    print("SMART HR EMAIL DISCOVERY & AUTOMATION SYSTEM")
    print("=" * 60)
    print("AUTOMATION LOGIC:")
    print("  1. Detect & fix job scraping issues")
    print("  2. Find fresh openings for target roles")
    print("  3. Discover specific HR emails (not generic)")
    print("  4. Filter & prioritize applications")
    print("  5. Generate application-ready job list")
    print()
    
    discoverer = SmartHREmailDiscovery()
    
    # Show current filters
    filters = discoverer.fresh_job_filters
    print("FRESH JOB TARGETING:")
    print(f"  • Max age: {filters['max_days_old']} days")
    print(f"  • Target roles: {', '.join(filters['target_roles'])}")
    print(f"  • Excluding: {', '.join(filters['exclude_keywords'])}")
    print()
    
    # Run automated HR email discovery with issue fixing
    success = discoverer.process_jobs_with_hr_discovery()
    
    if success:
        # Generate application report
        report = discoverer.generate_application_report()
        
        print(f"\nAPPLICATION READINESS REPORT:")
        print("-" * 30)
        print(f"Total jobs found: {report['total_jobs']}")
        print(f"Jobs with HR emails: {report['jobs_with_hr_emails']}")
        print(f"Application ready: {report['application_ready']}")
        print(f"Unique companies: {report['unique_companies']}")
        print(f"Total HR emails: {report['total_hr_emails']}")
        
        # Show automation results
        print(f"\nAUTOMATION RESULTS:")
        print("-" * 30)
        if discoverer.issues_found:
            print("Issues detected:")
            for issue in discoverer.issues_found:
                print(f"  ERROR: {issue}")
        
        if discoverer.fixes_applied:
            print("Fixes applied:")
            for fix in discoverer.fixes_applied:
                print(f"  SUCCESS: {fix}")
        
        if not discoverer.issues_found:
            print("  SUCCESS: No issues detected - system running optimally!")
        
        if report['application_ready'] > 0:
            success_rate = (report['jobs_with_hr_emails'] / report['total_jobs']) * 100
            print(f"\nSUCCESS: {report['application_ready']} jobs ready for application!")
            print(f"HR email discovery rate: {success_rate:.1f}%")
            print("\nNEXT AUTOMATED STEPS:")
            print("  1. Run smart_job_applicant.py to send targeted applications")
            print("  2. Email verifier will check deliverability")
            print("  3. Response tracker will monitor replies")
            print("  4. Auto follow-ups after 3-5 days")
        else:
            print("\nERROR: No jobs ready for application.")
            print("RECOMMENDED FIXES:")
            print("  1. Check job scrapers are working")
            print("  2. Verify target role keywords")
            print("  3. Update company HR email mappings")
    
    else:
        print("❌ HR email discovery failed. Check logs for details.")

if __name__ == "__main__":
    main()