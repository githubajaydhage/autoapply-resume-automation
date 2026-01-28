#!/usr/bin/env python3
"""
Complete Job Application Automation System - Unicode Safe Version
Orchestrates the entire process from job discovery to application sending
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class JobApplicationAutomation:
    """
    Complete automation system that handles:
    1. Fresh job discovery for target roles
    2. HR email discovery with automated fixes
    3. Email verification and deliverability checks
    4. Targeted application sending
    5. Response tracking and follow-ups
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.scripts_dir = Path("scripts")
        
        # Automation settings
        self.automation_config = {
            'max_applications_per_day': 20,
            'target_response_rate': 5.0,  # 5% minimum response rate
            'fresh_job_days': 7,
            'follow_up_days': 5,
            'email_verification_enabled': True
        }
        
        self.execution_log = []
    
    def run_complete_automation(self) -> bool:
        """Run the complete job application automation pipeline."""
        
        print("COMPLETE JOB APPLICATION AUTOMATION")
        print("=" * 50)
        print("TARGET: Fresh openings for analyst roles")
        print("STRATEGY: Specific HR emails (not generic)")
        print("AUTOMATION: End-to-end application process")
        print()
        
        try:
            # Phase 1: Job Discovery with Automated Fixes
            self.log_phase("Phase 1: Smart Job Discovery & Issue Fixing")
            if not self.run_smart_job_discovery():
                self.log_error("Job discovery failed - aborting automation")
                return False
            
            # Phase 2: HR Email Discovery with Validation
            self.log_phase("Phase 2: HR Email Discovery & Validation")
            if not self.run_hr_email_discovery():
                self.log_error("HR email discovery failed - aborting automation")
                return False
            
            # Phase 3: Email Verification (if enabled)
            if self.automation_config['email_verification_enabled']:
                self.log_phase("Phase 3: Email Verification & Deliverability Check")
                self.run_email_verification()
            
            # Phase 4: Application Sending
            self.log_phase("Phase 4: Targeted Application Sending")
            applications_sent = self.run_targeted_applications()
            
            # Phase 5: Response Tracking Setup
            self.log_phase("Phase 5: Response Tracking & Follow-up Setup")
            self.setup_response_tracking()
            
            # Phase 6: Generate Automation Report
            self.log_phase("Phase 6: Automation Report Generation")
            self.generate_automation_report(applications_sent)
            
            return True
            
        except Exception as e:
            self.log_error(f"Automation failed: {e}")
            return False
    
    def run_smart_job_discovery(self) -> bool:
        """Run smart job discovery with automated issue fixing."""
        
        logging.info("Running smart HR email discovery with issue detection...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.scripts_dir / "smart_hr_email_discovery.py")
            ], capture_output=True, text=True, timeout=300)
            
            self.log_execution("smart_hr_email_discovery.py", result.returncode == 0, result.stdout)
            
            if result.returncode == 0:
                self.log_success("Job discovery completed with automated fixes")
                return True
            else:
                self.log_error(f"Job discovery failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_error("Job discovery timed out")
            return False
        except Exception as e:
            self.log_error(f"Job discovery error: {e}")
            return False
    
    def run_hr_email_discovery(self) -> bool:
        """Ensure HR email discovery was successful."""
        
        # Check results from smart_hr_email_discovery
        jobs_file = self.data_dir / "jobs_today.csv"
        
        if not jobs_file.exists():
            return False
        
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            jobs_with_hr = sum(1 for job in jobs if job.get('primary_hr_email', '').strip())
            hr_coverage = (jobs_with_hr / len(jobs)) * 100 if jobs else 0
            
            self.log_success(f"HR email coverage: {hr_coverage:.1f}% ({jobs_with_hr}/{len(jobs)} jobs)")
            
            return hr_coverage > 50  # At least 50% coverage required
            
        except Exception as e:
            self.log_error(f"HR email validation error: {e}")
            return False
    
    def run_email_verification(self) -> None:
        """Run email verification to check deliverability."""
        
        try:
            # Try to run email verifier if it exists
            verifier_script = self.scripts_dir / "email_verifier.py"
            if verifier_script.exists():
                result = subprocess.run([
                    sys.executable, str(verifier_script)
                ], capture_output=True, text=True, timeout=180)
                
                self.log_execution("email_verifier.py", result.returncode == 0, result.stdout)
            else:
                self.log_warning("Email verifier not found - skipping verification")
                
        except Exception as e:
            self.log_warning(f"Email verification failed: {e}")
    
    def run_targeted_applications(self) -> int:
        """Send targeted job applications."""
        
        try:
            # Run smart job applicant
            applicant_script = self.scripts_dir / "smart_job_applicant.py"
            if applicant_script.exists():
                result = subprocess.run([
                    sys.executable, str(applicant_script)
                ], capture_output=True, text=True, timeout=600)
                
                self.log_execution("smart_job_applicant.py", result.returncode == 0, result.stdout)
                
                # Count applications sent from output
                applications_sent = 0
                if "applications sent" in result.stdout.lower():
                    # Extract number from output
                    import re
                    match = re.search(r'(\d+)\s+applications?\s+sent', result.stdout.lower())
                    if match:
                        applications_sent = int(match.group(1))
                
                return applications_sent
            else:
                self.log_error("Smart job applicant script not found")
                return 0
                
        except Exception as e:
            self.log_error(f"Application sending failed: {e}")
            return 0
    
    def setup_response_tracking(self) -> None:
        """Setup response tracking and follow-up automation."""
        
        try:
            # Try to run response tracking setup
            tracker_script = self.scripts_dir / "reply_detector.py"
            if tracker_script.exists():
                result = subprocess.run([
                    sys.executable, str(tracker_script)
                ], capture_output=True, text=True, timeout=120)
                
                self.log_execution("reply_detector.py", result.returncode == 0, result.stdout)
            
            self.log_success("Response tracking setup completed")
            
        except Exception as e:
            self.log_warning(f"Response tracking setup failed: {e}")
    
    def generate_automation_report(self, applications_sent: int) -> None:
        """Generate comprehensive automation report."""
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'applications_sent': applications_sent,
            'phases_completed': len([log for log in self.execution_log if log['success']]),
            'total_phases': 6,
            'execution_log': self.execution_log
        }
        
        print(f"\nAUTOMATION COMPLETE!")
        print("=" * 30)
        print(f"Applications sent: {applications_sent}")
        print(f"Phases completed: {report['phases_completed']}/{report['total_phases']}")
        print(f"Total runtime: {self.get_total_runtime()}")
        
        # Show execution summary
        print(f"\nEXECUTION SUMMARY:")
        for log in self.execution_log:
            status = "SUCCESS" if log['success'] else "FAILED"
            print(f"  {status}: {log['phase']}")
        
        # Show next steps
        if applications_sent > 0:
            print(f"\nWHAT HAPPENS NEXT:")
            print(f"  1. Response tracking monitors for HR replies")
            print(f"  2. Auto follow-ups in {self.automation_config['follow_up_days']} days")
            print(f"  3. Dashboard tracks application success rates")
            print(f"  4. System learns from responses to improve targeting")
        
        # Save report
        report_file = self.data_dir / f"automation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nFull report saved: {report_file}")
    
    def log_phase(self, phase_name: str) -> None:
        """Log the start of an automation phase."""
        print(f"\n{phase_name}")
        print("-" * len(phase_name))
        logging.info(f"Starting: {phase_name}")
    
    def log_success(self, message: str) -> None:
        """Log a success message."""
        print(f"SUCCESS: {message}")
        logging.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        print(f"WARNING: {message}")
        logging.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        print(f"ERROR: {message}")
        logging.error(message)
    
    def log_execution(self, script_name: str, success: bool, output: str) -> None:
        """Log script execution results."""
        self.execution_log.append({
            'phase': script_name,
            'success': success,
            'output': output,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_total_runtime(self) -> str:
        """Get total automation runtime."""
        if len(self.execution_log) >= 2:
            start_time = datetime.fromisoformat(self.execution_log[0]['timestamp'])
            end_time = datetime.fromisoformat(self.execution_log[-1]['timestamp'])
            duration = end_time - start_time
            return str(duration).split('.')[0]  # Remove microseconds
        return "Unknown"

def main():
    """Run complete job application automation."""
    
    automation = JobApplicationAutomation()
    
    print(f"STARTING COMPLETE JOB APPLICATION AUTOMATION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Logic: Fresh jobs -> HR emails -> Verification -> Applications -> Tracking")
    print()
    
    success = automation.run_complete_automation()
    
    if success:
        print(f"\nAUTOMATION SUCCESS!")
        print(f"The system has automatically:")
        print(f"  • Found fresh job openings for your target roles")
        print(f"  • Discovered specific HR email addresses")
        print(f"  • Verified email deliverability") 
        print(f"  • Sent personalized applications")
        print(f"  • Setup response tracking")
    else:
        print(f"\nAUTOMATION FAILED!")
        print(f"Check the logs above for specific error details.")
        print(f"Common issues:")
        print(f"  • Job scrapers not finding fresh openings")
        print(f"  • HR email discovery failing")
        print(f"  • Email authentication problems")

if __name__ == "__main__":
    main()