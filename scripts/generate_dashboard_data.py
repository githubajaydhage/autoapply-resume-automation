#!/usr/bin/env python3
"""
Multi-User Dashboard Data Generator
Generates JSON data for GitHub Pages dashboard from CSV files across multiple users/branches.
"""

import json
import csv
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


# Configuration - Add or modify users here
USERS = ['ajay', 'shweta', 'yogeshwari']

# Branch mapping (user -> branch name pattern)
BRANCH_PATTERNS = {
    'ajay': ['main', 'master', 'ajay', 'v.1.2.0-ajay'],
    'shweta': ['shweta', 'v.1.2.0-shweta'],
    'yogeshwari': ['yogeshwari', 'v.1.2.0-yogeshwari']
}


class MultiUserDashboardGenerator:
    """Generate dashboard data from CSV files for multiple users."""
    
    def __init__(self, base_dir: str = ".", output_dir: str = "docs/data"):
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.base_dir / "data"
    
    def read_csv(self, filename: str, user_data_dir: Path = None) -> list:
        """Read CSV file and return list of dictionaries."""
        data_dir = user_data_dir or self.data_dir
        filepath = data_dir / filename
        if not filepath.exists():
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return []
    
    def get_user_data_from_branch(self, user: str, branch: str) -> dict:
        """Fetch data from a specific branch for a user."""
        # This is a placeholder - in actual GitHub Actions, each branch's data
        # would be collected during the workflow run
        return {}
    
    def calculate_stats(self, data_dir: Path = None) -> dict:
        """Calculate dashboard statistics."""
        jobs = self.read_csv("jobs_today.csv", data_dir)
        applications = self.read_csv("applied_log.csv", data_dir)
        emails = self.read_csv("sent_emails_log.csv", data_dir)
        companies = self.read_csv("discovered_companies.csv", data_dir)
        hr_emails = self.read_csv("discovered_hr_emails.csv", data_dir)
        employees = self.read_csv("discovered_employees.csv", data_dir)
        
        hr_contacts = hr_emails + employees
        
        # Calculate response rate
        replied_count = sum(1 for e in emails if e.get('replied', '').lower() == 'true')
        response_rate = round((replied_count / len(emails) * 100) if emails else 0, 1)
        
        return {
            "jobsToday": len(jobs),
            "totalApplications": len(applications),
            "emailsSent": len(emails),
            "companiesFound": len(companies),
            "hrContacts": len(hr_contacts),
            "responseRate": response_rate
        }
    
    def get_applications_over_time(self, data_dir: Path = None, days: int = 7) -> list:
        """Get application counts over the last N days."""
        applications = self.read_csv("applied_log.csv", data_dir)
        
        date_counts = defaultdict(int)
        for app in applications:
            date_str = app.get('date', app.get('applied_date', ''))
            if date_str:
                try:
                    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            date = datetime.strptime(date_str.split()[0], fmt)
                            date_counts[date.strftime('%b %d')] += 1
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        result = []
        for i in range(days - 1, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_key = date.strftime('%b %d')
            result.append({
                "date": date_key,
                "count": date_counts.get(date_key, 0)
            })
        
        return result
    
    def get_application_status(self, data_dir: Path = None) -> dict:
        """Get application status breakdown."""
        applications = self.read_csv("applied_log.csv", data_dir)
        
        status_counts = {
            "applied": 0,
            "contacted": 0,
            "interviewing": 0,
            "rejected": 0,
            "offered": 0
        }
        
        for app in applications:
            status = app.get('status', 'applied').lower()
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts['applied'] += 1
        
        return status_counts
    
    def get_recent_jobs(self, user: str, data_dir: Path = None, limit: int = 10) -> list:
        """Get most recent jobs."""
        jobs = self.read_csv("jobs_today.csv", data_dir)
        
        result = []
        for job in jobs[:limit]:
            result.append({
                "title": job.get('title', job.get('job_title', 'Unknown')),
                "company": job.get('company', job.get('company_name', 'Unknown')),
                "location": job.get('location', 'Remote'),
                "source": job.get('source', job.get('platform', 'Job Board')),
                "user": user
            })
        
        return result
    
    def get_recent_emails(self, user: str, data_dir: Path = None, limit: int = 10) -> list:
        """Get most recent emails."""
        emails = self.read_csv("sent_emails_log.csv", data_dir)
        
        result = []
        for email in emails[-limit:]:
            result.append({
                "recipient": email.get('to', email.get('recipient', 'Unknown')),
                "company": email.get('company', 'Unknown'),
                "date": email.get('date', email.get('sent_date', 'Unknown')),
                "opened": email.get('opened', 'false').lower() == 'true',
                "user": user
            })
        
        return result[::-1]
    
    def get_companies_data(self, user: str, data_dir: Path = None, limit: int = 20) -> list:
        """Get companies with HR contact info."""
        companies = self.read_csv("discovered_companies.csv", data_dir)
        hr_emails = self.read_csv("discovered_hr_emails.csv", data_dir)
        employees = self.read_csv("discovered_employees.csv", data_dir)
        
        hr_contacts = {
            c.get('company', ''): c 
            for c in (hr_emails + employees)
        }
        
        result = []
        for company in companies[:limit]:
            company_name = company.get('company', company.get('name', 'Unknown'))
            hr = hr_contacts.get(company_name, {})
            
            result.append({
                "name": company_name,
                "hrContact": hr.get('name', hr.get('contact_name', '-')),
                "email": hr.get('email', company.get('email', '-')),
                "status": company.get('status', 'Discovered'),
                "user": user
            })
        
        return result
    
    def get_user_data(self, user: str) -> dict:
        """Get all data for a specific user."""
        # Check for user-specific data directory
        user_data_dir = self.base_dir / f"data_{user}"
        if not user_data_dir.exists():
            user_data_dir = self.data_dir
        
        return {
            "stats": self.calculate_stats(user_data_dir),
            "applicationsOverTime": self.get_applications_over_time(user_data_dir),
            "applicationStatus": self.get_application_status(user_data_dir)
        }
    
    def generate(self) -> dict:
        """Generate complete dashboard data for all users."""
        print("Generating multi-user dashboard data...")
        
        # Collect data for each user
        users_data = {}
        all_jobs = []
        all_emails = []
        all_companies = []
        
        for user in USERS:
            print(f"  Processing user: {user}")
            
            # Check for user-specific data directory
            user_data_dir = self.base_dir / f"data_{user}"
            if not user_data_dir.exists():
                # Fall back to main data directory if no user-specific one exists
                user_data_dir = self.data_dir
                print(f"    Using main data directory for {user}")
            else:
                print(f"    Found user-specific data directory: {user_data_dir}")
            
            users_data[user] = self.get_user_data(user)
            
            # Collect recent items with user tag
            all_jobs.extend(self.get_recent_jobs(user, user_data_dir))
            all_emails.extend(self.get_recent_emails(user, user_data_dir))
            all_companies.extend(self.get_companies_data(user, user_data_dir))
        
        data = {
            "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "users": users_data,
            "recentJobs": all_jobs[:20],
            "recentEmails": all_emails[:20],
            "companies": all_companies[:30]
        }
        
        # Save to JSON file
        output_path = self.output_dir / "dashboard_data.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Dashboard data saved to: {output_path}")
        
        # Print summary
        print("\n📊 Summary:")
        for user, user_data in users_data.items():
            stats = user_data.get('stats', {})
            print(f"  {user.capitalize()}: {stats.get('totalApplications', 0)} applications, "
                  f"{stats.get('emailsSent', 0)} emails")
        
        return data


def main():
    """Main entry point."""
    # Get the script's directory and navigate to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Change to project root
    os.chdir(project_root)
    
    generator = MultiUserDashboardGenerator()
    generator.generate()
    
    print("\n🎯 View your dashboard at: https://<username>.github.io/<repo>/")


if __name__ == "__main__":
    main()
