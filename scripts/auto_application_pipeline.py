"""
🚀 AUTO-APPLICATION PIPELINE - Bulletproof Job Application System

This pipeline ensures every discovered job gets an application:
1. Finds HR emails for each job
2. Generates personalized cover letters
3. Sends applications with retry logic
4. Tracks all applications and responses
5. Self-healing: retries failed applications

Author: AutoApply Automation
"""

import os
import sys
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AutoApplicationPipeline:
    """
    🚀 Bulletproof Application Pipeline
    
    Phases:
    1. DISCOVER - Find new jobs from all sources
    2. ENRICH - Find HR emails for each job
    3. PERSONALIZE - Generate tailored cover letters
    4. APPLY - Send applications with retry
    5. TRACK - Monitor responses and follow up
    6. HEAL - Retry failed applications
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        os.makedirs(self.data_path, exist_ok=True)
        
        # File paths
        self.jobs_path = os.path.join(self.data_path, 'jobs_today.csv')
        self.applied_path = os.path.join(self.data_path, 'applied_log.csv')
        self.failed_path = os.path.join(self.data_path, 'failed_applications.csv')
        self.queue_path = os.path.join(self.data_path, 'application_queue.csv')
        self.sent_log_path = os.path.join(self.data_path, 'sent_emails_log.csv')
        
        # Load pipeline state
        self.application_queue = self._load_queue()
        self.failed_applications = self._load_failed()
        
        # Config
        self.max_daily_emails = int(os.getenv('MAX_DAILY_EMAILS', '50'))
        self.retry_failed_after_hours = 24
        
        logging.info("="*60)
        logging.info("🚀 AUTO-APPLICATION PIPELINE INITIALIZED")
        logging.info(f"📋 Queue size: {len(self.application_queue)}")
        logging.info(f"❌ Failed (pending retry): {len(self.failed_applications)}")
        logging.info("="*60)
    
    def _load_queue(self) -> pd.DataFrame:
        """Load application queue."""
        if os.path.exists(self.queue_path):
            return pd.read_csv(self.queue_path)
        return pd.DataFrame(columns=[
            'job_id', 'company', 'job_title', 'job_url', 'hr_email',
            'status', 'priority', 'added_at', 'attempts', 'last_attempt'
        ])
    
    def _load_failed(self) -> pd.DataFrame:
        """Load failed applications for retry."""
        if os.path.exists(self.failed_path):
            return pd.read_csv(self.failed_path)
        return pd.DataFrame(columns=[
            'job_id', 'company', 'job_title', 'hr_email',
            'failure_reason', 'failed_at', 'retry_count'
        ])
    
    def _save_queue(self):
        """Save application queue."""
        self.application_queue.to_csv(self.queue_path, index=False)
    
    def _save_failed(self):
        """Save failed applications."""
        self.failed_applications.to_csv(self.failed_path, index=False)
    
    # =========================================================================
    # PHASE 1: DISCOVER - Find new jobs
    # =========================================================================
    
    def phase_discover(self) -> int:
        """
        Phase 1: Discover new jobs from all sources.
        Uses the BulletproofJobEngine.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("🔍 PHASE 1: DISCOVER NEW JOBS")
        logging.info("="*60)
        
        try:
            from bulletproof_job_engine import BulletproofJobEngine
            
            engine = BulletproofJobEngine()
            total, new = engine.run_full_scrape()
            
            logging.info(f"✅ Discovery complete: {new} new jobs found")
            return new
            
        except Exception as e:
            logging.error(f"Discovery phase failed: {e}")
            traceback.print_exc()
            
            # Fallback to existing scraper
            try:
                from reliable_job_scraper import ReliableJobScraper
                scraper = ReliableJobScraper()
                jobs = scraper.scrape_all_sources()
                logging.info(f"✅ Fallback discovery: {len(jobs)} jobs found")
                return len(jobs)
            except:
                return 0
    
    # =========================================================================
    # PHASE 2: ENRICH - Find HR emails
    # =========================================================================
    
    def phase_enrich(self) -> int:
        """
        Phase 2: Find HR emails for discovered jobs.
        Uses multiple email discovery methods.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("📧 PHASE 2: ENRICH WITH HR EMAILS")
        logging.info("="*60)
        
        if not os.path.exists(self.jobs_path):
            logging.warning("No jobs file found")
            return 0
        
        jobs_df = pd.read_csv(self.jobs_path)
        enriched_count = 0
        
        # Load existing applied log to skip
        applied_companies = set()
        if os.path.exists(self.applied_path):
            applied_df = pd.read_csv(self.applied_path)
            applied_companies = set(applied_df.get('company', []).str.lower().dropna())
        
        try:
            from curated_hr_database import get_hr_emails_for_company
            from hr_email_finder import HREmailFinder
            from advanced_hr_discovery import AdvancedHRDiscovery
            
            hr_finder = HREmailFinder()
            adv_discovery = AdvancedHRDiscovery()
            
        except ImportError as e:
            logging.warning(f"Some HR modules not available: {e}")
            return 0
        
        for idx, job in jobs_df.iterrows():
            company = str(job.get('company', '')).strip()
            
            if not company or company.lower() in applied_companies:
                continue
            
            # Try multiple sources for HR email
            hr_email = None
            
            # 1. Try curated database first (fastest)
            try:
                emails = get_hr_emails_for_company(company)
                if emails:
                    hr_email = emails[0].get('email')
            except:
                pass
            
            # 2. Try HR finder
            if not hr_email:
                try:
                    emails = hr_finder.find_hr_emails(company)
                    if emails:
                        hr_email = emails[0] if isinstance(emails[0], str) else emails[0].get('email')
                except:
                    pass
            
            # 3. Try advanced discovery
            if not hr_email:
                try:
                    emails = adv_discovery.discover_hr_for_company(company)
                    if emails:
                        hr_email = emails[0].get('email')
                except:
                    pass
            
            if hr_email:
                # Add to queue
                self._add_to_queue(job, hr_email)
                enriched_count += 1
                logging.info(f"   ✅ {company}: {hr_email}")
            else:
                logging.debug(f"   ⚠️ No email found for {company}")
        
        self._save_queue()
        logging.info(f"✅ Enrichment complete: {enriched_count} jobs with HR emails")
        return enriched_count
    
    def _add_to_queue(self, job: pd.Series, hr_email: str):
        """Add job to application queue."""
        job_id = f"{job.get('company', '')}_{hash(hr_email) % 10000}"
        
        # Check if already in queue
        if not self.application_queue.empty:
            existing = self.application_queue[
                self.application_queue['hr_email'].str.lower() == hr_email.lower()
            ]
            if not existing.empty:
                return
        
        new_entry = {
            'job_id': job_id,
            'company': job.get('company', ''),
            'job_title': job.get('title', ''),
            'job_url': job.get('url', ''),
            'hr_email': hr_email,
            'status': 'pending',
            'priority': job.get('priority', 5),
            'added_at': datetime.now().isoformat(),
            'attempts': 0,
            'last_attempt': None
        }
        
        self.application_queue = pd.concat([
            self.application_queue,
            pd.DataFrame([new_entry])
        ], ignore_index=True)
    
    # =========================================================================
    # PHASE 3: APPLY - Send applications
    # =========================================================================
    
    def phase_apply(self, max_applications: int = None) -> Tuple[int, int]:
        """
        Phase 3: Send applications for queued jobs.
        
        Returns: (sent_count, failed_count)
        """
        logging.info("")
        logging.info("="*60)
        logging.info("📤 PHASE 3: SEND APPLICATIONS")
        logging.info("="*60)
        
        if max_applications is None:
            max_applications = self.max_daily_emails
        
        # Get pending applications
        pending = self.application_queue[
            self.application_queue['status'] == 'pending'
        ].head(max_applications)
        
        if pending.empty:
            logging.info("No pending applications in queue")
            return 0, 0
        
        logging.info(f"📋 Processing {len(pending)} applications...")
        
        sent_count = 0
        failed_count = 0
        
        try:
            from email_sender import send_job_application_email
            from cover_letter_generator import CoverLetterGenerator
            
            cover_gen = CoverLetterGenerator()
            
        except ImportError as e:
            logging.error(f"Email modules not available: {e}")
            return 0, 0
        
        for idx, app in pending.iterrows():
            try:
                company = app['company']
                job_title = app['job_title']
                hr_email = app['hr_email']
                job_url = app.get('job_url', '')
                
                logging.info(f"   📧 Applying to {company} ({job_title})...")
                
                # Generate cover letter
                try:
                    cover_letter = cover_gen.generate_cover_letter(
                        company=company,
                        role=job_title,
                        job_description=f"Position at {company}"
                    )
                except:
                    cover_letter = self._generate_basic_cover_letter(company, job_title)
                
                # Send application
                success = send_job_application_email(
                    recipient_email=hr_email,
                    company_name=company,
                    job_title=job_title,
                    cover_letter=cover_letter,
                    job_url=job_url
                )
                
                if success:
                    self.application_queue.loc[idx, 'status'] = 'sent'
                    self.application_queue.loc[idx, 'last_attempt'] = datetime.now().isoformat()
                    sent_count += 1
                    logging.info(f"      ✅ Sent!")
                    
                    # Log to applied
                    self._log_applied(app)
                else:
                    self._handle_failed(app, "Send failed")
                    failed_count += 1
                    logging.warning(f"      ❌ Failed")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                self._handle_failed(app, str(e))
                failed_count += 1
                logging.error(f"      ❌ Error: {e}")
        
        self._save_queue()
        self._save_failed()
        
        logging.info(f"✅ Application phase complete: {sent_count} sent, {failed_count} failed")
        return sent_count, failed_count
    
    def _generate_basic_cover_letter(self, company: str, job_title: str) -> str:
        """Generate basic cover letter if generator fails."""
        applicant_name = USER_DETAILS.get('full_name', os.getenv('APPLICANT_NAME', 'Candidate'))
        experience = USER_DETAILS.get('years_experience', os.getenv('YEARS_EXPERIENCE', '3'))
        skills = USER_DETAILS.get('key_skills', os.getenv('JOB_KEYWORDS', 'relevant skills'))
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}.

With {experience}+ years of experience in {skills}, I am confident in my ability to contribute effectively to your team. I am particularly drawn to {company}'s reputation and would be excited to bring my expertise to your organization.

I would welcome the opportunity to discuss how my background aligns with your team's needs.

Thank you for considering my application.

Best regards,
{applicant_name}"""
    
    def _handle_failed(self, app: pd.Series, reason: str):
        """Handle failed application."""
        # Update queue
        idx = self.application_queue[
            self.application_queue['job_id'] == app['job_id']
        ].index
        if not idx.empty:
            self.application_queue.loc[idx[0], 'status'] = 'failed'
            self.application_queue.loc[idx[0], 'attempts'] = app.get('attempts', 0) + 1
            self.application_queue.loc[idx[0], 'last_attempt'] = datetime.now().isoformat()
        
        # Add to failed log
        failed_entry = {
            'job_id': app['job_id'],
            'company': app['company'],
            'job_title': app['job_title'],
            'hr_email': app['hr_email'],
            'failure_reason': reason,
            'failed_at': datetime.now().isoformat(),
            'retry_count': app.get('attempts', 0) + 1
        }
        
        self.failed_applications = pd.concat([
            self.failed_applications,
            pd.DataFrame([failed_entry])
        ], ignore_index=True)
    
    def _log_applied(self, app: pd.Series):
        """Log successful application."""
        applied_entry = {
            'company': app['company'],
            'job_title': app['job_title'],
            'hr_email': app['hr_email'],
            'job_url': app.get('job_url', ''),
            'applied_at': datetime.now().isoformat(),
            'status': 'applied'
        }
        
        if os.path.exists(self.applied_path):
            applied_df = pd.read_csv(self.applied_path)
            applied_df = pd.concat([applied_df, pd.DataFrame([applied_entry])], ignore_index=True)
        else:
            applied_df = pd.DataFrame([applied_entry])
        
        applied_df.to_csv(self.applied_path, index=False)
    
    # =========================================================================
    # PHASE 4: HEAL - Retry failed applications
    # =========================================================================
    
    def phase_heal(self) -> int:
        """
        Phase 4: Self-healing - retry failed applications.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("🔧 PHASE 4: SELF-HEALING (RETRY FAILED)")
        logging.info("="*60)
        
        if self.failed_applications.empty:
            logging.info("No failed applications to retry")
            return 0
        
        # Find applications that failed > 24 hours ago and have < 3 retries
        retry_candidates = []
        cutoff_time = datetime.now() - timedelta(hours=self.retry_failed_after_hours)
        
        for idx, app in self.failed_applications.iterrows():
            failed_at = app.get('failed_at', '')
            retry_count = app.get('retry_count', 0)
            
            if retry_count >= 3:
                continue  # Max retries reached
            
            try:
                failed_time = datetime.fromisoformat(failed_at)
                if failed_time < cutoff_time:
                    retry_candidates.append(app)
            except:
                pass
        
        if not retry_candidates:
            logging.info("No applications ready for retry")
            return 0
        
        logging.info(f"🔄 Retrying {len(retry_candidates)} failed applications...")
        
        # Re-add to queue with pending status
        for app in retry_candidates[:10]:  # Limit retries per run
            new_entry = {
                'job_id': app['job_id'],
                'company': app['company'],
                'job_title': app['job_title'],
                'job_url': '',
                'hr_email': app['hr_email'],
                'status': 'pending',
                'priority': 1,  # High priority for retries
                'added_at': datetime.now().isoformat(),
                'attempts': app.get('retry_count', 0),
                'last_attempt': None
            }
            
            self.application_queue = pd.concat([
                self.application_queue,
                pd.DataFrame([new_entry])
            ], ignore_index=True)
            
            # Remove from failed
            self.failed_applications = self.failed_applications[
                self.failed_applications['job_id'] != app['job_id']
            ]
        
        self._save_queue()
        self._save_failed()
        
        logging.info(f"✅ Added {len(retry_candidates[:10])} applications for retry")
        return len(retry_candidates[:10])
    
    # =========================================================================
    # PHASE 5: MONITOR - Track responses
    # =========================================================================
    
    def phase_monitor(self) -> Dict:
        """
        Phase 5: Monitor application responses.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("📊 PHASE 5: MONITOR RESPONSES")
        logging.info("="*60)
        
        stats = {
            'total_applied': 0,
            'responses': 0,
            'interviews': 0,
            'rejections': 0,
            'pending': 0
        }
        
        try:
            from reply_detector import ReplyDetector
            from bounce_checker import BounceChecker
            
            # Check for replies
            detector = ReplyDetector()
            replies = detector.check_for_replies()
            stats['responses'] = len(replies) if replies else 0
            
            # Check for bounces
            checker = BounceChecker()
            bounces = checker.check_bounces()
            
            logging.info(f"   📨 Replies detected: {stats['responses']}")
            
        except ImportError:
            logging.info("   Reply detector not available")
        
        # Count applied
        if os.path.exists(self.applied_path):
            applied_df = pd.read_csv(self.applied_path)
            stats['total_applied'] = len(applied_df)
            stats['pending'] = stats['total_applied'] - stats['responses']
        
        logging.info(f"   📈 Total applied: {stats['total_applied']}")
        logging.info(f"   ⏳ Awaiting response: {stats['pending']}")
        
        return stats
    
    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================
    
    def run_full_pipeline(self) -> Dict:
        """
        🚀 Run the complete application pipeline.
        
        Returns: Pipeline execution stats
        """
        logging.info("")
        logging.info("="*70)
        logging.info("🚀 BULLETPROOF AUTO-APPLICATION PIPELINE - STARTING")
        logging.info("="*70)
        
        start_time = time.time()
        stats = {
            'jobs_discovered': 0,
            'jobs_enriched': 0,
            'applications_sent': 0,
            'applications_failed': 0,
            'retries_queued': 0,
            'responses': 0,
            'execution_time': 0
        }
        
        try:
            # Phase 1: Discover jobs
            stats['jobs_discovered'] = self.phase_discover()
            
            # Phase 2: Enrich with HR emails
            stats['jobs_enriched'] = self.phase_enrich()
            
            # Phase 3: Send applications
            sent, failed = self.phase_apply()
            stats['applications_sent'] = sent
            stats['applications_failed'] = failed
            
            # Phase 4: Self-healing
            stats['retries_queued'] = self.phase_heal()
            
            # Phase 5: Monitor
            monitor_stats = self.phase_monitor()
            stats['responses'] = monitor_stats.get('responses', 0)
            
        except Exception as e:
            logging.error(f"Pipeline error: {e}")
            traceback.print_exc()
        
        stats['execution_time'] = time.time() - start_time
        
        # Print summary
        logging.info("")
        logging.info("="*70)
        logging.info("📊 PIPELINE EXECUTION SUMMARY")
        logging.info("="*70)
        logging.info(f"   🔍 Jobs discovered: {stats['jobs_discovered']}")
        logging.info(f"   📧 Jobs with HR emails: {stats['jobs_enriched']}")
        logging.info(f"   ✅ Applications sent: {stats['applications_sent']}")
        logging.info(f"   ❌ Applications failed: {stats['applications_failed']}")
        logging.info(f"   🔄 Retries queued: {stats['retries_queued']}")
        logging.info(f"   📨 Responses detected: {stats['responses']}")
        logging.info(f"   ⏱️ Execution time: {stats['execution_time']:.1f}s")
        logging.info("="*70)
        
        return stats
    
    def run_quick_apply(self, max_applications: int = 10) -> Dict:
        """
        Quick application run - skip discovery, just apply from queue.
        """
        logging.info("")
        logging.info("="*70)
        logging.info("⚡ QUICK APPLY MODE - Processing existing queue")
        logging.info("="*70)
        
        sent, failed = self.phase_apply(max_applications)
        
        return {
            'applications_sent': sent,
            'applications_failed': failed
        }


def main():
    """Run the auto-application pipeline."""
    pipeline = AutoApplicationPipeline()
    
    # Check command line args
    import argparse
    parser = argparse.ArgumentParser(description='Auto-Application Pipeline')
    parser.add_argument('--quick', action='store_true', help='Quick apply from existing queue')
    parser.add_argument('--max', type=int, default=50, help='Max applications to send')
    parser.add_argument('--discover-only', action='store_true', help='Only discover jobs')
    parser.add_argument('--enrich-only', action='store_true', help='Only enrich with emails')
    
    args = parser.parse_args()
    
    if args.discover_only:
        pipeline.phase_discover()
    elif args.enrich_only:
        pipeline.phase_enrich()
    elif args.quick:
        pipeline.run_quick_apply(args.max)
    else:
        pipeline.run_full_pipeline()


if __name__ == '__main__':
    main()
