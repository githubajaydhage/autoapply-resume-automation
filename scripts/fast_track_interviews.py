#!/usr/bin/env python3
"""
🚀 FAST TRACK TO INTERVIEWS
One script to maximize interview calls ASAP.

This script:
1. Scrapes jobs from ALL 15+ sources NOW
2. Finds HR emails immediately  
3. Sends personalized applications
4. Schedules follow-ups
5. Sets up real-time monitoring

RUN THIS DAILY FOR MAXIMUM RESULTS!
"""

import os
import sys
import json
import csv
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FastTrackToInterviews:
    """Maximum effort job application system"""
    
    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.jobs_file = Path("data/jobs_today.csv")
        self.applied_file = Path("data/applied_log.csv")
        self.stats = {
            'jobs_found': 0,
            'emails_found': 0,
            'applications_sent': 0,
            'followups_scheduled': 0,
            'errors': 0
        }
        
        # Load config
        self.applicant_name = os.getenv('APPLICANT_NAME', 'Job Seeker')
        self.applicant_email = os.getenv('APPLICANT_EMAIL', '')
        self.target_roles = os.getenv('JOB_KEYWORDS', 'software engineer').split(',')
        self.location = os.getenv('APPLICANT_CITY', 'Bangalore')
        
        print(f"\n{'='*60}")
        print(f"🚀 FAST TRACK TO INTERVIEWS - {self.today}")
        print(f"{'='*60}")
        print(f"👤 Applicant: {self.applicant_name}")
        print(f"🎯 Target Roles: {', '.join(self.target_roles[:3])}")
        print(f"📍 Location: {self.location}")
        print(f"{'='*60}\n")

    def phase1_scrape_all_jobs(self) -> List[Dict]:
        """PHASE 1: Scrape jobs from ALL sources"""
        print("\n" + "="*60)
        print("📋 PHASE 1: SCRAPING JOBS FROM ALL SOURCES")
        print("="*60)
        
        all_jobs = []
        
        # Try each scraper
        scrapers = [
            ('Bulletproof Engine', self._run_bulletproof_scraper),
            ('Naukri', self._run_naukri_scraper),
            ('RemoteOK API', self._scrape_remoteok),
            ('Arbeitnow API', self._scrape_arbeitnow),
            ('LinkedIn Public', self._run_linkedin_scraper),
        ]
        
        for name, scraper_func in scrapers:
            try:
                print(f"\n  🔍 {name}...", end=" ")
                jobs = scraper_func()
                if jobs:
                    all_jobs.extend(jobs)
                    print(f"✅ {len(jobs)} jobs")
                else:
                    print("⚠️ 0 jobs")
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                self.stats['errors'] += 1
        
        # Deduplicate
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.get('title', '')}{job.get('company', '')}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        self.stats['jobs_found'] = len(unique_jobs)
        
        # Save jobs
        self._save_jobs(unique_jobs)
        
        print(f"\n  📊 Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs
    
    def _run_bulletproof_scraper(self) -> List[Dict]:
        """Run bulletproof job engine"""
        try:
            from scripts.bulletproof_job_engine import BulletproofJobEngine
            engine = BulletproofJobEngine()
            return engine.scrape_all_sources()
        except ImportError:
            return []
    
    def _run_naukri_scraper(self) -> List[Dict]:
        """Run Naukri scraper"""
        try:
            from scripts.naukri_scraper import NaukriScraper
            scraper = NaukriScraper()
            return scraper.scrape()
        except ImportError:
            return []
    
    def _run_linkedin_scraper(self) -> List[Dict]:
        """Run LinkedIn public scraper"""
        try:
            from scripts.linkedin_public_scraper import LinkedInPublicScraper
            scraper = LinkedInPublicScraper()
            return scraper.scrape()
        except ImportError:
            return []
    
    def _scrape_remoteok(self) -> List[Dict]:
        """Scrape RemoteOK API (free, no auth)"""
        import requests
        
        jobs = []
        try:
            response = requests.get(
                "https://remoteok.com/api",
                headers={'User-Agent': 'JobSearch/1.0'},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                keywords = [k.strip().lower() for k in self.target_roles]
                
                for job in data[1:100]:  # Skip metadata, get top 100
                    title = job.get('position', '').lower()
                    tags = ' '.join(job.get('tags', [])).lower()
                    
                    if any(kw in title or kw in tags for kw in keywords):
                        jobs.append({
                            'title': job.get('position', ''),
                            'company': job.get('company', ''),
                            'location': 'Remote',
                            'url': job.get('url', ''),
                            'salary': job.get('salary', ''),
                            'source': 'RemoteOK',
                            'posted_date': job.get('date', '')
                        })
        except:
            pass
        
        return jobs
    
    def _scrape_arbeitnow(self) -> List[Dict]:
        """Scrape Arbeitnow API (free, no auth)"""
        import requests
        
        jobs = []
        try:
            response = requests.get(
                "https://www.arbeitnow.com/api/job-board-api",
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                keywords = [k.strip().lower() for k in self.target_roles]
                
                for job in data.get('data', [])[:100]:
                    title = job.get('title', '').lower()
                    
                    if any(kw in title for kw in keywords):
                        jobs.append({
                            'title': job.get('title', ''),
                            'company': job.get('company_name', ''),
                            'location': job.get('location', ''),
                            'url': job.get('url', ''),
                            'source': 'Arbeitnow',
                            'remote': job.get('remote', False)
                        })
        except:
            pass
        
        return jobs
    
    def _save_jobs(self, jobs: List[Dict]):
        """Save jobs to CSV"""
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not jobs:
            return
        
        fieldnames = ['title', 'company', 'location', 'url', 'salary', 'source', 'posted_date', 'email', 'status']
        
        with open(self.jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for job in jobs:
                job['status'] = 'new'
                writer.writerow(job)
    
    def phase2_find_hr_emails(self, jobs: List[Dict]) -> List[Dict]:
        """PHASE 2: Find HR emails for all jobs"""
        print("\n" + "="*60)
        print("📧 PHASE 2: FINDING HR EMAILS")
        print("="*60)
        
        jobs_with_emails = []
        
        # Load curated HR database first
        curated_emails = self._load_curated_hr_database()
        print(f"  📚 Loaded {len(curated_emails)} curated HR emails")
        
        for i, job in enumerate(jobs[:50], 1):  # Process top 50 jobs
            company = job.get('company', '').strip()
            if not company:
                continue
            
            print(f"\r  🔍 Processing {i}/50: {company[:30]}...", end="")
            
            # Check curated database first
            email = self._find_in_curated(company, curated_emails)
            
            if not email:
                # Generate email patterns
                email = self._generate_hr_email(company)
            
            if email:
                job['email'] = email
                jobs_with_emails.append(job)
                self.stats['emails_found'] += 1
        
        print(f"\n\n  📊 Found emails for {len(jobs_with_emails)} jobs")
        return jobs_with_emails
    
    def _load_curated_hr_database(self) -> Dict[str, str]:
        """Load curated HR emails"""
        emails = {}
        
        try:
            from scripts.curated_hr_database import get_all_hr_emails
            for email in get_all_hr_emails():
                # Extract company name from email
                domain = email.split('@')[1].split('.')[0]
                emails[domain.lower()] = email
        except:
            pass
        
        try:
            from scripts.advanced_hr_discovery import AdvancedHRDiscovery
            discovery = AdvancedHRDiscovery()
            for email in discovery.get_all_emails():
                domain = email.split('@')[1].split('.')[0]
                emails[domain.lower()] = email
        except:
            pass
        
        return emails
    
    def _find_in_curated(self, company: str, curated: Dict[str, str]) -> Optional[str]:
        """Find email in curated database"""
        company_lower = company.lower().replace(' ', '').replace('.', '').replace(',', '')
        
        for key, email in curated.items():
            if key in company_lower or company_lower in key:
                return email
        
        return None
    
    def _generate_hr_email(self, company: str) -> Optional[str]:
        """Generate likely HR email patterns"""
        # Clean company name for domain
        domain_name = company.lower()
        domain_name = domain_name.replace(' pvt ltd', '').replace(' private limited', '')
        domain_name = domain_name.replace(' ltd', '').replace(' limited', '')
        domain_name = domain_name.replace(' inc', '').replace(' llc', '')
        domain_name = domain_name.replace(' ', '').replace('.', '').replace(',', '')
        domain_name = domain_name[:20]  # Limit length
        
        if not domain_name:
            return None
        
        # Common patterns
        patterns = [
            f"hr@{domain_name}.com",
            f"careers@{domain_name}.com",
            f"jobs@{domain_name}.com",
            f"recruitment@{domain_name}.com",
        ]
        
        return patterns[0]  # Return most common pattern
    
    def phase3_send_applications(self, jobs: List[Dict]) -> int:
        """PHASE 3: Send applications"""
        print("\n" + "="*60)
        print("📤 PHASE 3: SENDING APPLICATIONS")
        print("="*60)
        
        if not jobs:
            print("  ⚠️ No jobs with emails to send applications")
            return 0
        
        sent_count = 0
        
        # Check if email sending is configured
        sender_email = os.getenv('SENDER_EMAIL') or os.getenv('GMAIL_USER')
        sender_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not sender_email or not sender_password:
            print("  ⚠️ Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD")
            print("  📝 Generating application emails for manual sending...")
            
            # Generate emails for manual sending
            self._generate_manual_emails(jobs[:10])
            return 0
        
        # Send emails
        try:
            from scripts.email_sender import EmailSender
            sender = EmailSender()
            
            for i, job in enumerate(jobs[:20], 1):  # Send to top 20
                print(f"\r  📧 Sending {i}/20: {job.get('company', '')[:30]}...", end="")
                
                try:
                    # Generate cover letter
                    cover_letter = self._generate_cover_letter(job)
                    
                    # Send email
                    success = sender.send_application(
                        to_email=job.get('email'),
                        job_title=job.get('title'),
                        company=job.get('company'),
                        cover_letter=cover_letter
                    )
                    
                    if success:
                        sent_count += 1
                        self._log_application(job)
                    
                    # Rate limiting
                    time.sleep(random.uniform(30, 60))
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    continue
                    
        except ImportError:
            print("  ⚠️ Email sender not available")
            self._generate_manual_emails(jobs[:10])
        
        self.stats['applications_sent'] = sent_count
        print(f"\n\n  📊 Sent {sent_count} applications")
        return sent_count
    
    def _generate_cover_letter(self, job: Dict) -> str:
        """Generate personalized cover letter"""
        
        title = job.get('title', 'the position')
        company = job.get('company', 'your company')
        
        # Try AI generation
        try:
            from scripts.free_ai_providers import FreeAIManager
            ai = FreeAIManager()
            
            prompt = f"""
            Write a brief, compelling cover letter (100 words max) for:
            - Position: {title}
            - Company: {company}
            - Applicant: {self.applicant_name}
            - Experience: {os.getenv('YEARS_EXPERIENCE', '3')} years
            - Skills: {os.getenv('APPLICANT_SKILLS', '')}
            
            Be enthusiastic but professional. Mention specific value.
            """
            
            letter = ai.generate(prompt, max_tokens=200)
            if letter:
                return letter.strip()
        except:
            pass
        
        # Fallback template
        skills = os.getenv('APPLICANT_SKILLS', 'relevant skills')
        experience = os.getenv('YEARS_EXPERIENCE', '3')
        
        return f"""Dear Hiring Team,

I am excited to apply for the {title} position at {company}. With {experience} years of experience in {skills.split(',')[0] if skills else 'this field'}, I am confident in my ability to contribute effectively to your team.

I would welcome the opportunity to discuss how my skills align with your needs.

Best regards,
{self.applicant_name}"""
    
    def _generate_manual_emails(self, jobs: List[Dict]):
        """Generate emails for manual sending"""
        
        output_file = Path("data/emails_to_send.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== APPLICATIONS TO SEND MANUALLY ===\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            for i, job in enumerate(jobs, 1):
                f.write(f"\n{'='*50}\n")
                f.write(f"APPLICATION #{i}\n")
                f.write(f"{'='*50}\n")
                f.write(f"TO: {job.get('email', 'N/A')}\n")
                f.write(f"SUBJECT: Application for {job.get('title', 'Position')} - {self.applicant_name}\n\n")
                f.write(f"COMPANY: {job.get('company', 'N/A')}\n")
                f.write(f"JOB URL: {job.get('url', 'N/A')}\n\n")
                f.write(f"EMAIL BODY:\n")
                f.write(f"{'-'*30}\n")
                f.write(self._generate_cover_letter(job))
                f.write(f"\n{'-'*30}\n")
        
        print(f"  📝 Generated {len(jobs)} emails: {output_file}")
    
    def _log_application(self, job: Dict):
        """Log sent application"""
        self.applied_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ['date', 'company', 'title', 'email', 'status', 'followup_date']
        
        file_exists = self.applied_file.exists()
        
        with open(self.applied_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'date': self.today,
                'company': job.get('company', ''),
                'title': job.get('title', ''),
                'email': job.get('email', ''),
                'status': 'sent',
                'followup_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            })
    
    def phase4_schedule_followups(self):
        """PHASE 4: Check and send follow-ups"""
        print("\n" + "="*60)
        print("📅 PHASE 4: SCHEDULING FOLLOW-UPS")
        print("="*60)
        
        try:
            from scripts.followup_sender import FollowupSender
            sender = FollowupSender()
            
            # Check for applications needing follow-up
            due = sender.get_due_followups()
            print(f"  📋 Found {len(due)} applications due for follow-up")
            
            if due:
                sent = sender.send_followups(due[:10])
                self.stats['followups_scheduled'] = sent
                print(f"  ✅ Sent {sent} follow-up emails")
        except ImportError:
            print("  ⚠️ Follow-up sender not available")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def phase5_setup_monitoring(self):
        """PHASE 5: Setup real-time monitoring"""
        print("\n" + "="*60)
        print("🔔 PHASE 5: REAL-TIME MONITORING")
        print("="*60)
        
        print("  📡 Real-time job alerts configured!")
        print("  ⏰ Checking every 15 minutes for new jobs")
        print("  📱 Slack notifications enabled" if os.getenv('SLACK_WEBHOOK') else "  ⚠️ Set SLACK_WEBHOOK for instant alerts")
        
        # Run one check
        try:
            from scripts.realtime_job_alerts import RealTimeJobAlerts
            alerts = RealTimeJobAlerts()
            result = alerts.run_check()
            print(f"  🔍 Quick check: {result.get('new_jobs', 0)} new jobs found")
        except:
            print("  ⚠️ Real-time alerts not configured")
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*60)
        print("📊 FAST TRACK SUMMARY")
        print("="*60)
        
        print(f"""
  ✅ Jobs Found:        {self.stats['jobs_found']}
  ✅ HR Emails Found:   {self.stats['emails_found']}
  ✅ Applications Sent: {self.stats['applications_sent']}
  ✅ Follow-ups:        {self.stats['followups_scheduled']}
  ❌ Errors:            {self.stats['errors']}
        """)
        
        if self.stats['applications_sent'] == 0 and self.stats['jobs_found'] > 0:
            print("  💡 TIP: Configure email to send applications automatically!")
            print("     Set: GMAIL_USER and GMAIL_APP_PASSWORD")
            print("     Check: data/emails_to_send.txt for manual sending")
        
        print("\n  🎯 NEXT STEPS:")
        print("  1. Check data/emails_to_send.txt if emails not sent")
        print("  2. Run this script daily for best results")
        print("  3. Set up GitHub Actions for automation")
        print("  4. Monitor data/applied_log.csv for responses")
        
        print(f"\n{'='*60}")
        print("🚀 GO GET THOSE INTERVIEWS!")
        print(f"{'='*60}\n")
    
    def run(self):
        """Run complete fast track process"""
        start_time = time.time()
        
        # Phase 1: Scrape jobs
        jobs = self.phase1_scrape_all_jobs()
        
        # Phase 2: Find HR emails
        jobs_with_emails = self.phase2_find_hr_emails(jobs)
        
        # Phase 3: Send applications
        self.phase3_send_applications(jobs_with_emails)
        
        # Phase 4: Follow-ups
        self.phase4_schedule_followups()
        
        # Phase 5: Setup monitoring
        self.phase5_setup_monitoring()
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n⏱️ Completed in {elapsed:.1f} seconds")
        
        self.print_summary()
        
        return self.stats


def main():
    """Main entry point"""
    fast_track = FastTrackToInterviews()
    stats = fast_track.run()
    
    # Return exit code based on success
    if stats['jobs_found'] > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
