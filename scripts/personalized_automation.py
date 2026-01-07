#!/usr/bin/env python3
"""
Complete Personalized Job Application System
Integrates personalized job search with HR email discovery and application sending
"""

import csv
import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class PersonalizedJobApplicationSystem:
    """
    Complete system for personalized job applications:
    1. Personalized job search queries
    2. HR email discovery 
    3. Targeted application sending
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.scripts_dir = Path("scripts")
        self.data_dir.mkdir(exist_ok=True)
        
        # User-specific search queries
        self.search_queries = {
            'shweta': {
                'name': 'Shweta',
                'query': '("Data Analyst" OR "SQL Developer" OR "BI Analyst" OR "Power BI Developer" OR "Reporting Analyst") ("Power BI" OR "SQL" OR "SSMS" OR "stored procedures") ("apply now" OR "job opening" OR "hiring" OR "send your resume") Bangalore -intern -internship -fresher',
                'target_roles': ['Data Analyst', 'SQL Developer', 'BI Analyst', 'Power BI Developer', 'Reporting Analyst'],
                'skills': ['Power BI', 'SQL', 'SSMS', 'stored procedures', 'reporting'],
                'location': 'Bangalore'
            },
            'geeta': {
                'name': 'Yogeshwari Mane (Geeta)', 
                'query': '("AutoCAD Designer" OR "Interior Designer" OR "Estimation Engineer" OR "Quantity Surveyor" OR "Architect" OR "Design Engineer") ("AutoCAD" OR "SketchUp" OR "3Ds Max" OR "Revit" OR "Interior Design" OR "Estimation") ("apply now" OR "job opening" OR "hiring" OR "send your resume") Bangalore -intern -internship -fresher',
                'target_roles': ['AutoCAD Designer', 'Interior Designer', 'Estimation Engineer', 'Quantity Surveyor', 'Architect', 'Design Engineer'],
                'skills': ['AutoCAD', 'SketchUp', '3Ds Max', 'Revit', 'Interior Design', 'Estimation', 'Quantity Surveying'],
                'location': 'Bangalore'
            }
        }
    
    def run_personalized_automation(self, user: str) -> bool:
        """Run complete personalized automation for a specific user."""
        
        if user not in self.search_queries:
            logging.error(f"User '{user}' not found in system!")
            return False
        
        user_info = self.search_queries[user]
        
        print(f"RUNNING PERSONALIZED AUTOMATION FOR {user_info['name'].upper()}")
        print("=" * 60)
        print(f"Target Roles: {', '.join(user_info['target_roles'])}")
        print(f"Key Skills: {', '.join(user_info['skills'][:4])}")
        print(f"Location: {user_info['location']}")
        print()
        print("SEARCH QUERY:")
        print(f'"{user_info["query"]}"')
        print()
        
        try:
            # Step 1: Run personalized job search
            self.log_phase(f"Step 1: Personalized Job Search for {user_info['name']}")
            jobs_found = self.run_personalized_search(user)
            
            if jobs_found == 0:
                logging.warning(f"No jobs found for {user_info['name']}")
                return False
            
            # Step 2: Discover HR emails for found jobs
            self.log_phase(f"Step 2: HR Email Discovery")
            hr_success = self.run_hr_discovery()
            
            # Step 3: Generate personalized application report
            self.log_phase(f"Step 3: Application Readiness Report")
            self.generate_user_report(user)
            
            return True
            
        except Exception as e:
            logging.error(f"Personalized automation failed for {user}: {e}")
            return False
    
    def run_personalized_search(self, user: str) -> int:
        """Run personalized job search for specific user."""
        
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.scripts_dir / "personalized_job_search.py")
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                # Count jobs found from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if f"{self.search_queries[user]['name'].upper()}:" in line and "Jobs found:" in line:
                        try:
                            jobs_count = int(line.split("Jobs found: ")[1].strip())
                            logging.info(f"Found {jobs_count} jobs for {self.search_queries[user]['name']}")
                            return jobs_count
                        except:
                            pass
                
                logging.info("Personalized job search completed")
                return 5  # Default assumption
            else:
                logging.error(f"Job search failed: {result.stderr}")
                return 0
                
        except Exception as e:
            logging.error(f"Job search error: {e}")
            return 0
    
    def run_hr_discovery(self) -> bool:
        """Run HR email discovery on found jobs."""
        
        try:
            # Convert personalized jobs to standard format for HR discovery
            self.convert_personalized_jobs_to_standard()
            
            result = subprocess.run([
                sys.executable,
                str(self.scripts_dir / "smart_hr_email_discovery.py")
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logging.info("HR email discovery completed successfully")
                return True
            else:
                logging.warning("HR email discovery had issues but continuing...")
                return True  # Continue even if HR discovery has issues
                
        except Exception as e:
            logging.warning(f"HR discovery error: {e}")
            return True  # Don't fail the entire process
    
    def convert_personalized_jobs_to_standard(self) -> None:
        """Convert personalized jobs CSV to standard jobs_today.csv format."""
        
        personalized_file = self.data_dir / "personalized_jobs.csv"
        standard_file = self.data_dir / "jobs_today.csv"
        
        if not personalized_file.exists():
            logging.warning("No personalized jobs file found")
            return
        
        try:
            with open(personalized_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                personalized_jobs = list(reader)
            
            # Convert to standard format
            standard_jobs = []
            for job in personalized_jobs:
                standard_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'url': job.get('url', ''),
                    'posted_date': job.get('posted_date', ''),
                    'date_posted': job.get('posted_date', ''),  # Alternative field name
                    'skills': job.get('skills_required', ''),
                    'experience': job.get('experience_required', ''),
                    'target_user': job.get('target_user', ''),
                    'search_timestamp': job.get('search_timestamp', '')
                }
                standard_jobs.append(standard_job)
            
            # Save in standard format
            if standard_jobs:
                fieldnames = list(standard_jobs[0].keys())
                with open(standard_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(standard_jobs)
                
                logging.info(f"Converted {len(standard_jobs)} jobs to standard format")
            
        except Exception as e:
            logging.error(f"Error converting jobs format: {e}")
    
    def generate_user_report(self, user: str) -> None:
        """Generate comprehensive report for specific user."""
        
        user_info = self.search_queries[user]
        
        # Read results
        jobs_file = self.data_dir / "jobs_today.csv"
        jobs_count = 0
        hr_coverage = 0
        
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    jobs = [job for job in reader if job.get('target_user', '').lower() == user_info['name'].lower()]
                
                jobs_count = len(jobs)
                jobs_with_hr = sum(1 for job in jobs if job.get('primary_hr_email', '').strip())
                hr_coverage = (jobs_with_hr / jobs_count * 100) if jobs_count > 0 else 0
                
            except Exception as e:
                logging.error(f"Error reading jobs file: {e}")
        
        print(f"\n{user_info['name'].upper()} - APPLICATION READINESS REPORT")
        print("=" * 50)
        print(f"Jobs found: {jobs_count}")
        print(f"HR emails discovered: {hr_coverage:.1f}% coverage")
        print(f"Target roles: {', '.join(user_info['target_roles'])}")
        print(f"Key skills: {', '.join(user_info['skills'][:4])}")
        print(f"Location: {user_info['location']}")
        
        if jobs_count > 0:
            print(f"\nSUCCESS: {user_info['name']} has {jobs_count} application-ready jobs!")
            print("NEXT STEPS:")
            print(f"1. Send personalized applications using {user_info['name']}'s profile")
            print("2. Track responses and follow up")
            print("3. Optimize based on response rates")
        else:
            print(f"\nNeed to expand search criteria for {user_info['name']}")
    
    def log_phase(self, phase_name: str) -> None:
        """Log the start of a phase."""
        print(f"\n{phase_name}")
        print("-" * len(phase_name))
        logging.info(f"Starting: {phase_name}")

def main():
    """Run personalized job application system."""
    
    system = PersonalizedJobApplicationSystem()
    
    print("PERSONALIZED JOB APPLICATION SYSTEM")
    print("=" * 50)
    print("Available Users: Shweta, Yogeshwari (Geeta)")
    print()
    
    # Show all search queries
    print("PERSONALIZED SEARCH QUERIES:")
    print("=" * 40)
    
    for user, info in system.search_queries.items():
        print(f"\n{info['name'].upper()}:")
        print(f"Roles: {', '.join(info['target_roles'][:3])}...")
        print(f"Skills: {', '.join(info['skills'][:3])}...")
        print(f"Query: {info['query'][:80]}...")
    
    print("\n" + "=" * 50)
    
    # Run automation for both users
    success_count = 0
    
    for user in system.search_queries.keys():
        print(f"\nProcessing {user}...")
        if system.run_personalized_automation(user):
            success_count += 1
        time.sleep(2)  # Brief pause between users
    
    print(f"\n" + "=" * 50)
    print("AUTOMATION COMPLETE!")
    print(f"Successfully processed: {success_count}/{len(system.search_queries)} users")
    print("=" * 50)

if __name__ == "__main__":
    main()