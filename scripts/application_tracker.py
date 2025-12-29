"""
Application Status Tracker - Centralized tracking of all job applications
Tracks: Applied → Acknowledged → Interviewing → Offered → Rejected
"""

import pandas as pd
import os
import sys
import logging
from datetime import datetime, timedelta
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ApplicationStatus(Enum):
    """Application status stages."""
    IDENTIFIED = "identified"           # Job identified, not yet applied
    APPLIED = "applied"                  # Application sent
    ACKNOWLEDGED = "acknowledged"        # Received acknowledgment
    INTERVIEWING = "interviewing"        # Interview scheduled/in progress
    OFFERED = "offered"                  # Received offer
    REJECTED = "rejected"                # Application rejected
    NO_RESPONSE = "no_response"          # No response after X days
    WITHDRAWN = "withdrawn"              # Candidate withdrew


class ApplicationTracker:
    """Tracks all job applications and their statuses."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Main tracking file
        self.tracker_path = os.path.join(self.data_path, 'application_tracker.csv')
        
        # Source files
        self.sent_log_path = os.path.join(self.data_path, 'sent_emails_log.csv')
        self.replies_path = os.path.join(self.data_path, 'hr_replies.csv')
        self.bounced_path = os.path.join(self.data_path, 'bounced_emails.csv')
        self.followup_path = os.path.join(self.data_path, 'followup_log.csv')
        
        # Load or create tracker
        self.tracker_df = self._load_tracker()
    
    def _load_tracker(self) -> pd.DataFrame:
        """Load existing tracker or create new one."""
        if os.path.exists(self.tracker_path):
            return pd.read_csv(self.tracker_path)
        
        return pd.DataFrame(columns=[
            'application_id', 'company', 'job_title', 'hr_email', 'job_url',
            'status', 'applied_date', 'last_updated', 'last_action',
            'followup_count', 'response_date', 'response_type', 'notes',
            'match_score', 'priority'
        ])
    
    def _generate_application_id(self, company: str, email: str) -> str:
        """Generate unique application ID."""
        company_short = ''.join(c for c in company[:10] if c.isalnum()).upper()
        email_hash = hash(email) % 10000
        return f"{company_short}_{email_hash}"
    
    def sync_from_sent_log(self):
        """Import applications from sent emails log."""
        if not os.path.exists(self.sent_log_path):
            logging.info("No sent emails log found")
            return 0
        
        sent_df = pd.read_csv(self.sent_log_path)
        new_count = 0
        
        for _, row in sent_df.iterrows():
            email = row.get('recipient_email', '')
            company = row.get('company', '')
            
            if not email or pd.isna(email):
                continue
            
            # Check if already tracked
            existing = self.tracker_df[
                self.tracker_df['hr_email'].str.lower() == email.lower()
            ]
            
            if existing.empty:
                # Add new application
                new_app = {
                    'application_id': self._generate_application_id(company, email),
                    'company': company,
                    'job_title': row.get('job_title', 'Open Position'),
                    'hr_email': email,
                    'job_url': row.get('job_url', ''),
                    'status': ApplicationStatus.APPLIED.value,
                    'applied_date': row.get('sent_at', datetime.now().isoformat()),
                    'last_updated': datetime.now().isoformat(),
                    'last_action': 'Initial application sent',
                    'followup_count': 0,
                    'response_date': None,
                    'response_type': None,
                    'notes': f"Status: {row.get('status', 'sent')}",
                    'match_score': row.get('match_score', 50),
                    'priority': row.get('priority', 3)
                }
                
                self.tracker_df = pd.concat([
                    self.tracker_df, 
                    pd.DataFrame([new_app])
                ], ignore_index=True)
                new_count += 1
        
        logging.info(f"📥 Imported {new_count} new applications from sent log")
        return new_count
    
    def sync_from_replies(self):
        """Update statuses based on detected replies."""
        if not os.path.exists(self.replies_path):
            logging.info("No replies log found")
            return 0
        
        replies_df = pd.read_csv(self.replies_path)
        update_count = 0
        
        for _, reply in replies_df.iterrows():
            from_email = str(reply.get('from_email', '')).lower()
            category = reply.get('category', '')
            
            # Find matching applications by email domain
            domain = from_email.split('@')[1] if '@' in from_email else ''
            
            if not domain:
                continue
            
            # Match by domain
            matches = self.tracker_df[
                self.tracker_df['hr_email'].str.contains(domain, case=False, na=False)
            ]
            
            for idx in matches.index:
                current_status = self.tracker_df.loc[idx, 'status']
                new_status = current_status
                
                # Update status based on reply category
                if category == 'INTERVIEW_REQUEST':
                    new_status = ApplicationStatus.INTERVIEWING.value
                elif category == 'OFFER':
                    new_status = ApplicationStatus.OFFERED.value
                elif category == 'POSITIVE_RESPONSE':
                    if current_status == ApplicationStatus.APPLIED.value:
                        new_status = ApplicationStatus.ACKNOWLEDGED.value
                elif category == 'REJECTION':
                    new_status = ApplicationStatus.REJECTED.value
                elif category == 'ACKNOWLEDGMENT':
                    if current_status == ApplicationStatus.APPLIED.value:
                        new_status = ApplicationStatus.ACKNOWLEDGED.value
                
                if new_status != current_status:
                    self.tracker_df.loc[idx, 'status'] = new_status
                    self.tracker_df.loc[idx, 'last_updated'] = datetime.now().isoformat()
                    self.tracker_df.loc[idx, 'response_date'] = reply.get('date', '')
                    self.tracker_df.loc[idx, 'response_type'] = category
                    update_count += 1
        
        logging.info(f"📬 Updated {update_count} application statuses from replies")
        return update_count
    
    def sync_from_bounces(self):
        """Mark bounced applications."""
        if not os.path.exists(self.bounced_path):
            return 0
        
        bounced_df = pd.read_csv(self.bounced_path)
        update_count = 0
        
        bounced_emails = set()
        for col in ['email', 'bounced_email', 'recipient_email']:
            if col in bounced_df.columns:
                bounced_emails.update(bounced_df[col].str.lower().dropna())
        
        for idx, row in self.tracker_df.iterrows():
            email = str(row['hr_email']).lower()
            if email in bounced_emails:
                self.tracker_df.loc[idx, 'status'] = 'bounced'
                self.tracker_df.loc[idx, 'notes'] = 'Email bounced - invalid address'
                update_count += 1
        
        logging.info(f"🚫 Marked {update_count} applications as bounced")
        return update_count
    
    def mark_no_response(self, days_threshold: int = 14):
        """Mark applications with no response after X days."""
        update_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        for idx, row in self.tracker_df.iterrows():
            status = row['status']
            applied_date = row.get('applied_date', '')
            
            # Only update if still in 'applied' status
            if status != ApplicationStatus.APPLIED.value:
                continue
            
            try:
                app_date = datetime.fromisoformat(applied_date.replace('Z', '+00:00'))
                if app_date.replace(tzinfo=None) < cutoff_date:
                    self.tracker_df.loc[idx, 'status'] = ApplicationStatus.NO_RESPONSE.value
                    self.tracker_df.loc[idx, 'notes'] = f'No response after {days_threshold} days'
                    update_count += 1
            except:
                continue
        
        logging.info(f"⏰ Marked {update_count} applications as no-response")
        return update_count
    
    def sync_all(self):
        """Sync from all sources and update tracker."""
        logging.info("="*60)
        logging.info("📊 APPLICATION STATUS TRACKER")
        logging.info("="*60)
        
        # Import new applications
        self.sync_from_sent_log()
        
        # Update from replies
        self.sync_from_replies()
        
        # Mark bounced
        self.sync_from_bounces()
        
        # Mark no-response
        self.mark_no_response(days_threshold=14)
        
        # Save tracker
        self.save()
        
        return self.get_summary()
    
    def save(self):
        """Save tracker to CSV."""
        self.tracker_df.to_csv(self.tracker_path, index=False)
        logging.info(f"💾 Saved tracker with {len(self.tracker_df)} applications")
    
    def get_summary(self) -> dict:
        """Get status summary."""
        summary = {
            'total': len(self.tracker_df),
            'by_status': {}
        }
        
        if not self.tracker_df.empty:
            status_counts = self.tracker_df['status'].value_counts().to_dict()
            summary['by_status'] = status_counts
        
        return summary
    
    def get_applications_by_status(self, status: str) -> pd.DataFrame:
        """Get applications with specific status."""
        return self.tracker_df[self.tracker_df['status'] == status]
    
    def get_pending_followups(self, days_since_apply: int = 3) -> pd.DataFrame:
        """Get applications that need follow-up."""
        cutoff_date = datetime.now() - timedelta(days=days_since_apply)
        
        pending = self.tracker_df[
            (self.tracker_df['status'] == ApplicationStatus.APPLIED.value) &
            (self.tracker_df['followup_count'] < 3)  # Max 3 follow-ups
        ].copy()
        
        # Filter by date
        result = []
        for _, row in pending.iterrows():
            try:
                app_date = datetime.fromisoformat(row['applied_date'].replace('Z', '+00:00'))
                if app_date.replace(tzinfo=None) <= cutoff_date:
                    result.append(row)
            except:
                continue
        
        return pd.DataFrame(result)
    
    def update_application(self, email: str, status: str, notes: str = None):
        """Manually update an application status."""
        mask = self.tracker_df['hr_email'].str.lower() == email.lower()
        
        if mask.any():
            self.tracker_df.loc[mask, 'status'] = status
            self.tracker_df.loc[mask, 'last_updated'] = datetime.now().isoformat()
            if notes:
                self.tracker_df.loc[mask, 'notes'] = notes
            self.save()
            return True
        return False
    
    def export_report(self) -> str:
        """Generate a text report of application status."""
        summary = self.get_summary()
        
        report = []
        report.append("="*60)
        report.append("📊 JOB APPLICATION STATUS REPORT")
        report.append(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("="*60)
        report.append(f"\n📈 TOTAL APPLICATIONS: {summary['total']}\n")
        
        # Status breakdown
        status_icons = {
            'applied': '📤',
            'acknowledged': '📥',
            'interviewing': '🎯',
            'offered': '🏆',
            'rejected': '❌',
            'no_response': '⏰',
            'bounced': '🚫',
            'withdrawn': '🚪'
        }
        
        report.append("📊 STATUS BREAKDOWN:")
        for status, count in summary['by_status'].items():
            icon = status_icons.get(status, '📋')
            report.append(f"   {icon} {status.upper()}: {count}")
        
        # Highlight positive outcomes
        interviewing = summary['by_status'].get('interviewing', 0)
        offered = summary['by_status'].get('offered', 0)
        
        if interviewing > 0 or offered > 0:
            report.append(f"\n🎉 POSITIVE OUTCOMES: {interviewing + offered}")
            
            if not self.tracker_df.empty:
                positive = self.tracker_df[
                    self.tracker_df['status'].isin(['interviewing', 'offered'])
                ]
                for _, row in positive.iterrows():
                    report.append(f"   • {row['company']} - {row['job_title']}")
        
        # Response rate
        total = summary['total']
        responses = summary['by_status'].get('acknowledged', 0) + \
                   summary['by_status'].get('interviewing', 0) + \
                   summary['by_status'].get('offered', 0) + \
                   summary['by_status'].get('rejected', 0)
        
        if total > 0:
            response_rate = (responses / total) * 100
            report.append(f"\n📬 RESPONSE RATE: {response_rate:.1f}%")
        
        report.append("="*60)
        
        return '\n'.join(report)


def main():
    """Main function to sync and display tracker."""
    tracker = ApplicationTracker()
    summary = tracker.sync_all()
    
    # Print report
    print(tracker.export_report())
    
    # Show pending follow-ups
    pending = tracker.get_pending_followups(days_since_apply=3)
    if not pending.empty:
        print(f"\n📨 PENDING FOLLOW-UPS ({len(pending)}):")
        for _, row in pending.head(10).iterrows():
            print(f"   • {row['company']} ({row['hr_email']})")


if __name__ == "__main__":
    main()
