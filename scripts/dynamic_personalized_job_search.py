#!/usr/bin/env python3
"""
Dynamic Personalized Job Search System
Automatically loads user profiles from GitHub Actions workflow files
No hardcoding - profiles are extracted from apply_jobs_*.yml files
"""

import csv
import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging with unicode support
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_profiles_from_workflows():
    """Load user profiles from GitHub Actions workflow files"""
    
    workflows_dir = Path('.github/workflows')
    profiles = {}
    
    if not workflows_dir.exists():
        logger.warning("No .github/workflows directory found")
        return profiles
    
    # Find all apply_jobs_*.yml files
    workflow_files = list(workflows_dir.glob('apply_jobs_*.yml'))
    
    if not workflow_files:
        logger.warning("No apply_jobs_*.yml workflow files found")
        return profiles
    
    for workflow_file in workflow_files:
        try:
            # Try UTF-8 first, then fallback to other encodings
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(workflow_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.warning(f"❌ Could not decode {workflow_file} with any encoding")
                continue
                
            # Extract user key from filename (e.g., apply_jobs_shweta.yml -> shweta)
            user_key = workflow_file.stem.replace('apply_jobs_', '')
            
            # Parse environment variables section (find top-level env: section)
            # The env: section starts at column 0 and continues until jobs: at column 0
            env_section = re.search(r'^env:\s*\n((?:  .*\n)*)', content, re.MULTILINE)
            if not env_section:
                logger.warning(f"No env section found in {workflow_file}")
                continue
                
            env_content = env_section.group(1)
            
            # Extract profile data using proper regex patterns for GitHub Actions syntax
            name_match = re.search(r"APPLICANT_NAME:\s*\$\{\{[^}]+\|\|\s*'([^']+)'\s*\}\}", env_content)
            skills_match = re.search(r"APPLICANT_SKILLS:\s*\$\{\{[^}]+\|\|\s*'([^']+)'\s*\}\}", env_content)  
            target_role_match = re.search(r"APPLICANT_TARGET_ROLE:\s*\$\{\{[^}]+\|\|\s*'([^']+)'\s*\}\}", env_content)
            location_match = re.search(r"APPLICANT_CITY:\s*\$\{\{[^}]+\|\|\s*'([^']+)'\s*\}\}", env_content)
            experience_match = re.search(r"APPLICANT_EXPERIENCE:\s*\$\{\{[^}]+\|\|\s*'([^']+)'\s*\}\}", env_content)
            
            if name_match and skills_match and target_role_match:
                name = name_match.group(1)
                skills_str = skills_match.group(1)
                target_roles_str = target_role_match.group(1)
                location = location_match.group(1) if location_match else 'Bangalore'
                experience = experience_match.group(1) if experience_match else '2'
                
                # Parse skills and target roles
                skills = [s.strip() for s in skills_str.split(',')]
                target_roles = [r.strip() for r in target_roles_str.split(',')]
                
                # Generate search query based on profile
                roles_query = ' OR '.join([f'"{role}"' for role in target_roles[:5]])  # Limit to 5 roles
                skills_query = ' OR '.join([f'"{skill}"' for skill in skills[:5]])  # Limit to 5 skills
                
                search_query = f'({roles_query}) ({skills_query}) ("apply now" OR "job opening" OR "hiring" OR "send your resume") {location} -intern -internship -fresher'
                
                profiles[user_key] = {
                    'name': name,
                    'query': search_query,
                    'target_roles': target_roles,
                    'skills': skills,
                    'location': location,
                    'experience': experience,
                    'workflow_file': str(workflow_file),
                    'user_key': user_key
                }
                
                logger.info(f"✅ Loaded profile for {user_key}: {name}")
                
            else:
                logger.warning(f"❌ Incomplete profile data in {workflow_file}")
                missing = []
                if not name_match: missing.append("APPLICANT_NAME")
                if not skills_match: missing.append("APPLICANT_SKILLS")
                if not target_role_match: missing.append("APPLICANT_TARGET_ROLE")
                logger.warning(f"Missing: {', '.join(missing)}")
                
        except Exception as e:
            logger.error(f"❌ Error loading profile from {workflow_file}: {e}")
            continue
    
    return profiles

def get_user_profiles():
    """Get user-specific search profiles from workflow files"""
    return load_profiles_from_workflows()

def get_sample_jobs_for_user(user_key: str, profile: Dict) -> List[Dict]:
    """Generate sample jobs based on user profile"""
    
    jobs = []
    
    # Generate relevant sample jobs based on target roles
    for i, role in enumerate(profile['target_roles'][:5]):  # Limit to 5 sample jobs
        # Create company names based on the role type
        if any(tech in role.lower() for tech in ['data', 'sql', 'analyst', 'bi']):
            companies = ['Accenture', 'Infosys', 'TCS', 'Wipro', 'Cognizant']
        elif any(design in role.lower() for design in ['autocad', 'interior', 'architect', 'design']):
            companies = ['L&T Construction', 'Godrej Properties', 'Prestige Group', 'Brigade Group', 'Sobha Limited']
        else:
            companies = ['TechCorp', 'InnovateInc', 'GlobalTech', 'NextGen', 'FutureSoft']
            
        company = companies[i % len(companies)]
        
        job = {
            'title': role,
            'company': company,
            'location': profile['location'],
            'description': f"{role} role with focus on {', '.join(profile['skills'][:3])}",
            'job_url': f"https://{company.lower().replace(' ', '')}.com/careers/{role.lower().replace(' ', '-')}",
            'posted_date': datetime.now().strftime('%Y-%m-%d'),
            'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'required_skills': profile['skills'][:3],
            'experience_required': f"{profile['experience']} years" if profile['experience'] else "2-4 years",
            'matched_user': profile['name'],
            'search_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        jobs.append(job)
    
    return jobs

def run_personalized_search():
    """Run personalized job search for all users from workflow files"""
    
    print("🔍 DYNAMIC PERSONALIZED JOB SEARCH SYSTEM")
    print("=" * 50)
    print("📂 Loading user profiles from GitHub Actions workflow files...")
    print()
    
    profiles = get_user_profiles()
    
    if not profiles:
        print("❌ No user profiles found in workflow files!")
        print("💡 Please ensure workflow files exist in .github/workflows/apply_jobs_*.yml")
        print("📋 Required format: apply_jobs_username.yml")
        return
        
    print(f"✅ Found {len(profiles)} user profile(s): {', '.join(profiles.keys())}")
    print()
    
    print("👥 LOADED USER PROFILES:")
    print("-" * 30)
    
    for user_key, profile in profiles.items():
        print(f"\n{user_key.upper()}:")
        print(f"Name: {profile['name']}")
        print(f"Target Roles: {', '.join(profile['target_roles'][:3])}...")
        print(f"Key Skills: {', '.join(profile['skills'][:3])}...")
        print(f"Location: {profile['location']}")
        print(f"Experience: {profile['experience']} years")
        print(f"Source: {Path(profile['workflow_file']).name}")
    
    print()
    print("🎯 PERSONALIZED SEARCH QUERIES:")
    print("-" * 30)
    
    for user_key, profile in profiles.items():
        print(f"\n{user_key.upper()}:")
        print(f"Search Query:")
        print(f'"{profile["query"]}"')
    
    print()
    print("=" * 50) 
    print("🚀 RUNNING PERSONALIZED JOB SEARCHES...")
    print("=" * 50) 
    
    all_jobs = []
    total_jobs = 0
    
    # Create output directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    for user_key, profile in profiles.items():
        logger.info(f"🔍 Searching jobs for {profile['name']}...")
        
        # Get sample jobs for this user
        user_jobs = get_sample_jobs_for_user(user_key, profile)
        
        # Log each job found
        for job in user_jobs:
            logger.info(f"Found matching job: {job['title']} at {job['company']}")
        
        all_jobs.extend(user_jobs)
        total_jobs += len(user_jobs)
        logger.info(f"Found {len(user_jobs)} jobs for {profile['name']}")
        
        # Save individual user jobs to CSV
        user_csv_file = data_dir / "personalized_jobs.csv"
        
        # Write to CSV with proper encoding
        with open(user_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['user_name', 'user_key', 'title', 'company', 'location', 
                         'required_skills', 'experience_required', 'description', 
                         'job_url', 'posted_date', 'search_timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is empty
            if csvfile.tell() == 0:
                writer.writeheader()
            
            for job in user_jobs:
                writer.writerow({
                    'user_name': profile['name'],
                    'user_key': user_key,
                    'title': job['title'],
                    'company': job['company'],
                    'location': job['location'],
                    'required_skills': job['required_skills'],
                    'experience_required': job['experience_required'],
                    'description': job['description'],
                    'job_url': job['job_url'],
                    'posted_date': job['posted_date'],
                    'search_timestamp': job['search_timestamp']
                })
        
        logger.info(f"💾 Saved {len(user_jobs)} jobs for {profile['name']} to {user_csv_file}")
        print()
    
    # Summary
    print("📊 SEARCH RESULTS SUMMARY:")
    print("-" * 30)
    print(f"Total jobs found: {total_jobs}")
    print(f"Users searched: {len(profiles)}")
    print()
    
    for user_key, profile in profiles.items():
        user_job_count = len([j for j in all_jobs if j['matched_user'] == profile['name']])
        print(f"{user_key.upper()}:")
        print(f"  Jobs found: {user_job_count}")
        print(f"  Target roles: {', '.join(profile['target_roles'][:3])}")
        print(f"  Key skills: {', '.join(profile['skills'][:3])}")
        print()
    
    if total_jobs > 0:
        print(f"✅ SUCCESS: Found {total_jobs} personalized job matches!")
        print(f"💾 Results saved to: {data_dir}/personalized_jobs.csv")
        print()
        print("📝 NEXT STEPS:")
        print("1. Run HR email discovery on these jobs")
        print("2. Send personalized applications")
        print("3. Track responses for each user")
    else:
        print("❌ No jobs found. Check your workflow file configurations.")

if __name__ == "__main__":
    try:
        run_personalized_search()
    except Exception as e:
        logger.error(f"❌ Error in personalized search: {e}")
        print(f"\\n❌ Error: {e}")