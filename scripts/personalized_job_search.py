#!/usr/bin/env python3
"""
Personalized Job Search System
Creates targeted search queries for different users based on their skills and preferences
"""

import csv
import os
import sys
import time
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class PersonalizedJobSearchSystem:
    """
    Creates personalized job searches for different users
    Integrates with existing HR email discovery system
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # User profiles with personalized search queries
        self.user_profiles = {
            'shweta': {
                'name': 'Shweta',
                'job_titles': [
                    'Data Analyst', 'SQL Developer', 'BI Analyst', 
                    'Power BI Developer', 'Reporting Analyst'
                ],
                'required_skills': [
                    'Power BI', 'SQL', 'SSMS', 'stored procedures', 
                    'data visualization', 'reporting'
                ],
                'preferred_location': 'Bangalore',
                'experience_level': 'mid-level',
                'search_query': '("Data Analyst" OR "SQL Developer" OR "BI Analyst" OR "Power BI Developer" OR "Reporting Analyst") ("Power BI" OR "SQL" OR "SSMS" OR "stored procedures") ("apply now" OR "job opening" OR "hiring" OR "send your resume") Bangalore -intern -internship -fresher',
                'exclude_keywords': ['intern', 'internship', 'fresher', 'senior manager', 'director', '7+ years']
            },
            'geeta': {
                'name': 'Yogeshwari Mane (Geeta)',
                'job_titles': [
                    'AutoCAD Designer', 'Interior Designer', 'Estimation Engineer',
                    'Quantity Surveyor', 'Architect', 'Design Engineer'
                ],
                'required_skills': [
                    'AutoCAD', 'SketchUp', '3Ds Max', 'Revit', 
                    'Interior Design', 'Estimation', 'Quantity Surveying'
                ],
                'preferred_location': 'Bangalore',
                'experience_level': 'mid-level', 
                'search_query': '("AutoCAD Designer" OR "Interior Designer" OR "Estimation Engineer" OR "Quantity Surveyor" OR "Architect" OR "Design Engineer") ("AutoCAD" OR "SketchUp" OR "3Ds Max" OR "Revit" OR "Interior Design" OR "Estimation") ("apply now" OR "job opening" OR "hiring" OR "send your resume") Bangalore -intern -internship -fresher',
                'exclude_keywords': ['intern', 'internship', 'fresher', 'senior architect', 'principal', '10+ years']
            }
        }
        
        # Output files
        self.jobs_file = self.data_dir / "personalized_jobs.csv"
        self.search_results_file = self.data_dir / "search_results.csv"
    
    def generate_search_query(self, user_profile: str) -> str:
        """Generate optimized search query for a specific user."""
        
        if user_profile not in self.user_profiles:
            logging.error(f"User profile '{user_profile}' not found!")
            return ""
        
        profile = self.user_profiles[user_profile]
        return profile['search_query']
    
    def search_jobs_for_user(self, user_profile: str) -> List[Dict]:
        """Search for jobs using user-specific criteria."""
        
        if user_profile not in self.user_profiles:
            logging.error(f"User profile '{user_profile}' not found!")
            return []
        
        profile = self.user_profiles[user_profile]
        logging.info(f"Searching jobs for {profile['name']}...")
        
        # Simulated job search results (replace with actual job board API calls)
        jobs_found = []
        
        # Example job data structure for demonstration
        sample_jobs = self.get_sample_jobs_for_user(user_profile)
        
        for job in sample_jobs:
            # Filter based on user criteria
            if self.matches_user_criteria(job, profile):
                jobs_found.append(job)
                logging.info(f"Found matching job: {job['title']} at {job['company']}")
        
        logging.info(f"Found {len(jobs_found)} jobs for {profile['name']}")
        return jobs_found
    
    def get_sample_jobs_for_user(self, user_profile: str) -> List[Dict]:
        """Get sample jobs tailored to user profile."""
        
        if user_profile == 'shweta':
            return [
                {
                    'title': 'Power BI Developer',
                    'company': 'Accenture',
                    'location': 'Bangalore',
                    'skills_required': ['Power BI', 'SQL', 'SSMS'],
                    'experience_required': '2-4 years',
                    'description': 'Looking for Power BI Developer with strong SQL skills',
                    'url': 'https://accenture.com/careers/powerbideveloper',
                    'posted_date': '2026-01-01'
                },
                {
                    'title': 'SQL Developer', 
                    'company': 'Infosys',
                    'location': 'Bangalore',
                    'skills_required': ['SQL', 'SSMS', 'stored procedures'],
                    'experience_required': '2-5 years',
                    'description': 'SQL Developer for data warehouse projects',
                    'url': 'https://infosys.com/careers/sqldeveloper',
                    'posted_date': '2025-12-30'
                },
                {
                    'title': 'BI Analyst',
                    'company': 'TCS',
                    'location': 'Bangalore', 
                    'skills_required': ['Power BI', 'SQL', 'data visualization'],
                    'experience_required': '1-3 years',
                    'description': 'BI Analyst for reporting and dashboards',
                    'url': 'https://tcs.com/careers/bianalyst',
                    'posted_date': '2026-01-01'
                },
                {
                    'title': 'Data Analyst',
                    'company': 'Wipro',
                    'location': 'Bangalore',
                    'skills_required': ['SQL', 'Power BI', 'Excel'],
                    'experience_required': '2-4 years', 
                    'description': 'Data Analyst for business intelligence',
                    'url': 'https://wipro.com/careers/dataanalyst',
                    'posted_date': '2025-12-31'
                },
                {
                    'title': 'Reporting Analyst',
                    'company': 'Cognizant',
                    'location': 'Bangalore',
                    'skills_required': ['Power BI', 'SQL', 'reporting'],
                    'experience_required': '2-5 years',
                    'description': 'Reporting Analyst for financial reports',
                    'url': 'https://cognizant.com/careers/reportinganalyst',
                    'posted_date': '2026-01-01'
                }
            ]
        
        elif user_profile == 'geeta':
            return [
                {
                    'title': 'AutoCAD Designer',
                    'company': 'L&T Construction',
                    'location': 'Bangalore', 
                    'skills_required': ['AutoCAD', '2D Drafting', 'Technical Drawing'],
                    'experience_required': '2-4 years',
                    'description': 'AutoCAD Designer for construction projects',
                    'url': 'https://lntecc.com/careers/autocaddesigner',
                    'posted_date': '2026-01-01'
                },
                {
                    'title': 'Interior Designer',
                    'company': 'Godrej Properties',
                    'location': 'Bangalore',
                    'skills_required': ['Interior Design', 'SketchUp', '3Ds Max', 'Space Planning'],
                    'experience_required': '2-5 years', 
                    'description': 'Interior Designer for residential projects',
                    'url': 'https://godrejproperties.com/careers/interiordesigner',
                    'posted_date': '2025-12-30'
                },
                {
                    'title': 'Estimation Engineer',
                    'company': 'Prestige Group',
                    'location': 'Bangalore',
                    'skills_required': ['Quantity Surveying', 'Estimation', 'AutoCAD'],
                    'experience_required': '3-5 years',
                    'description': 'Estimation Engineer for real estate projects',
                    'url': 'https://prestigeconstructions.com/careers/estimation',
                    'posted_date': '2026-01-01'
                },
                {
                    'title': 'Design Engineer', 
                    'company': 'Brigade Group',
                    'location': 'Bangalore',
                    'skills_required': ['Revit', 'AutoCAD', 'Structural Design'],
                    'experience_required': '2-4 years',
                    'description': 'Design Engineer for construction planning',
                    'url': 'https://brigadegroup.com/careers/designengineer', 
                    'posted_date': '2025-12-31'
                },
                {
                    'title': 'Quantity Surveyor',
                    'company': 'Sobha Limited',
                    'location': 'Bangalore',
                    'skills_required': ['Quantity Surveying', 'Cost Estimation', 'Project Planning'],
                    'experience_required': '2-5 years',
                    'description': 'Quantity Surveyor for residential projects',
                    'url': 'https://sobha.com/jobs/quantitysurveyor',
                    'posted_date': '2026-01-01'
                }
            ]
        
        return []
    
    def matches_user_criteria(self, job: Dict, profile: Dict) -> bool:
        """Check if job matches user's criteria."""
        
        # Check if job title matches
        title_match = any(title.lower() in job['title'].lower() 
                         for title in profile['job_titles'])
        
        # Check if required skills match
        skills_match = any(skill.lower() in str(job['skills_required']).lower() 
                          for skill in profile['required_skills'])
        
        # Check location
        location_match = profile['preferred_location'].lower() in job['location'].lower()
        
        # Check exclusion criteria
        exclude_match = any(exclude.lower() in job['title'].lower() or 
                           exclude.lower() in job['description'].lower()
                           for exclude in profile['exclude_keywords'])
        
        return title_match and skills_match and location_match and not exclude_match
    
    def save_personalized_jobs(self, user_profile: str, jobs: List[Dict]) -> None:
        """Save personalized job results to CSV."""
        
        if not jobs:
            logging.warning(f"No jobs to save for {user_profile}")
            return
        
        profile = self.user_profiles[user_profile]
        
        # Add user info to each job
        for job in jobs:
            job['target_user'] = profile['name']
            job['user_profile'] = user_profile
            job['search_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to CSV
        fieldnames = ['target_user', 'user_profile', 'title', 'company', 'location', 
                     'skills_required', 'experience_required', 'description', 'url', 
                     'posted_date', 'search_timestamp']
        
        file_exists = self.jobs_file.exists()
        
        with open(self.jobs_file, 'a' if file_exists else 'w', 
                 newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(jobs)
        
        logging.info(f"Saved {len(jobs)} jobs for {profile['name']} to {self.jobs_file}")
    
    def generate_search_report(self) -> Dict:
        """Generate comprehensive search report for all users."""
        
        report = {
            'search_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'users_searched': len(self.user_profiles),
            'total_jobs_found': 0,
            'user_results': {}
        }
        
        # Search for each user
        for user_profile in self.user_profiles:
            profile = self.user_profiles[user_profile]
            jobs = self.search_jobs_for_user(user_profile)
            
            report['user_results'][user_profile] = {
                'name': profile['name'],
                'jobs_found': len(jobs),
                'target_roles': profile['job_titles'],
                'key_skills': profile['required_skills'][:3],  # Top 3 skills
                'search_query': profile['search_query']
            }
            
            report['total_jobs_found'] += len(jobs)
            
            # Save jobs for this user
            if jobs:
                self.save_personalized_jobs(user_profile, jobs)
        
        return report

def main():
    """Run personalized job search for all users."""
    
    print("PERSONALIZED JOB SEARCH SYSTEM")
    print("=" * 50)
    print("Creating targeted searches for Shweta and Yogeshwari (Geeta)")
    print()
    
    searcher = PersonalizedJobSearchSystem()
    
    # Show search queries
    print("PERSONALIZED SEARCH QUERIES:")
    print("-" * 30)
    
    for user_profile in searcher.user_profiles:
        profile = searcher.user_profiles[user_profile]
        print(f"\n{profile['name'].upper()}:")
        print(f"Target Roles: {', '.join(profile['job_titles'])}")
        print(f"Key Skills: {', '.join(profile['required_skills'][:4])}")
        print(f"Location: {profile['preferred_location']}")
        print(f"\nSearch Query:")
        print(f'"{profile["search_query"]}"')
    
    print("\n" + "=" * 50)
    print("RUNNING PERSONALIZED JOB SEARCHES...")
    print("=" * 50)
    
    # Generate search report
    report = searcher.generate_search_report()
    
    print(f"\nSEARCH RESULTS SUMMARY:")
    print("-" * 30)
    print(f"Total jobs found: {report['total_jobs_found']}")
    print(f"Users searched: {report['users_searched']}")
    
    for user_profile, results in report['user_results'].items():
        print(f"\n{results['name'].upper()}:")
        print(f"  Jobs found: {results['jobs_found']}")
        print(f"  Target roles: {', '.join(results['target_roles'][:3])}")
        print(f"  Key skills: {', '.join(results['key_skills'])}")
    
    if report['total_jobs_found'] > 0:
        print(f"\nSUCCESS: Found {report['total_jobs_found']} personalized job matches!")
        print(f"Results saved to: {searcher.jobs_file}")
        print("\nNEXT STEPS:")
        print("1. Run HR email discovery on these jobs")
        print("2. Send personalized applications")
        print("3. Track responses for each user")
    else:
        print("\nNo jobs found. Try expanding search criteria.")

if __name__ == "__main__":
    main()