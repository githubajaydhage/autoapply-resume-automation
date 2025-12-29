#!/usr/bin/env python3
"""
Email Open Tracking - Track if HR opened your email
Uses a tracking pixel approach with webhook callbacks
"""

import os
import json
import logging
import hashlib
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class EmailOpenTracker:
    """
    Track email opens using tracking pixels.
    
    How it works:
    1. Generate unique tracking ID for each email
    2. Insert invisible 1x1 pixel in email HTML
    3. When HR opens email, pixel loads and logs the open
    
    Options for tracking:
    - Self-hosted: Use your own server endpoint
    - Free services: Use tracking services like Mailtrack pixel
    - GitHub Pages: Host a simple tracking pixel
    """
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.tracking_log = os.path.join(self.data_dir, 'email_opens_log.csv')
        self.tracking_enabled = os.environ.get('ENABLE_OPEN_TRACKING', 'true').lower() == 'true'
        
        # Tracking pixel URL (can be customized)
        # Default: Using a simple redirect tracker or your own endpoint
        self.tracking_base_url = os.environ.get(
            'TRACKING_PIXEL_URL', 
            ''  # Set your tracking endpoint URL
        )
        
        self._init_tracking_log()
    
    def _init_tracking_log(self):
        """Initialize tracking log file."""
        if not os.path.exists(self.tracking_log):
            df = pd.DataFrame(columns=[
                'tracking_id', 'recipient_email', 'company', 'job_title',
                'sent_at', 'first_opened', 'open_count', 'last_opened',
                'user_agent', 'ip_location'
            ])
            os.makedirs(self.data_dir, exist_ok=True)
            df.to_csv(self.tracking_log, index=False)
    
    def generate_tracking_id(self, email: str, company: str, timestamp: str) -> str:
        """Generate unique tracking ID for an email."""
        unique_string = f"{email}_{company}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def create_tracking_pixel(self, tracking_id: str) -> str:
        """
        Create HTML tracking pixel.
        
        Returns HTML snippet to insert in email body.
        """
        if not self.tracking_enabled or not self.tracking_base_url:
            return ""
        
        # Create invisible 1x1 pixel
        pixel_url = f"{self.tracking_base_url}?tid={tracking_id}"
        
        tracking_html = f'''
<img src="{pixel_url}" width="1" height="1" style="display:none;visibility:hidden;" alt="" />
'''
        return tracking_html
    
    def create_tracking_link(self, tracking_id: str, original_url: str, link_name: str = "link") -> str:
        """
        Create a tracked link that redirects to original URL.
        
        This tracks link clicks in addition to opens.
        """
        if not self.tracking_enabled or not self.tracking_base_url:
            return original_url
        
        # Create redirect URL
        redirect_url = f"{self.tracking_base_url}/click?tid={tracking_id}&url={original_url}&name={link_name}"
        return redirect_url
    
    def log_email_sent(self, tracking_id: str, recipient_email: str, 
                       company: str, job_title: str) -> None:
        """Log when a tracked email is sent."""
        try:
            df = pd.read_csv(self.tracking_log)
            
            new_entry = {
                'tracking_id': tracking_id,
                'recipient_email': recipient_email,
                'company': company,
                'job_title': job_title,
                'sent_at': datetime.now().isoformat(),
                'first_opened': '',
                'open_count': 0,
                'last_opened': '',
                'user_agent': '',
                'ip_location': ''
            }
            
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            df.to_csv(self.tracking_log, index=False)
            
            logging.info(f"📧 Tracking enabled for {recipient_email} (ID: {tracking_id})")
            
        except Exception as e:
            logging.error(f"Error logging tracked email: {e}")
    
    def record_open(self, tracking_id: str, user_agent: str = "", 
                    ip_address: str = "") -> bool:
        """
        Record when an email is opened.
        
        Called by your tracking endpoint when pixel is loaded.
        """
        try:
            df = pd.read_csv(self.tracking_log)
            
            mask = df['tracking_id'] == tracking_id
            if not mask.any():
                logging.warning(f"Unknown tracking ID: {tracking_id}")
                return False
            
            now = datetime.now().isoformat()
            
            # Update first open if not set
            if pd.isna(df.loc[mask, 'first_opened'].values[0]) or df.loc[mask, 'first_opened'].values[0] == '':
                df.loc[mask, 'first_opened'] = now
            
            # Increment open count
            df.loc[mask, 'open_count'] = df.loc[mask, 'open_count'].fillna(0).astype(int) + 1
            df.loc[mask, 'last_opened'] = now
            df.loc[mask, 'user_agent'] = user_agent
            df.loc[mask, 'ip_location'] = ip_address
            
            df.to_csv(self.tracking_log, index=False)
            
            # Get email details for notification
            email_info = df[mask].iloc[0]
            logging.info(f"📬 EMAIL OPENED! {email_info['company']} ({email_info['recipient_email']})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error recording open: {e}")
            return False
    
    def get_open_stats(self) -> Dict:
        """Get email open statistics."""
        try:
            df = pd.read_csv(self.tracking_log)
            
            total_sent = len(df)
            total_opened = len(df[df['open_count'] > 0])
            
            # Calculate open rate
            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            
            # Get recently opened
            df_opened = df[df['open_count'] > 0].copy()
            if not df_opened.empty:
                df_opened['first_opened'] = pd.to_datetime(df_opened['first_opened'])
                recent_opens = df_opened.nlargest(5, 'first_opened')
            else:
                recent_opens = pd.DataFrame()
            
            return {
                'total_tracked': total_sent,
                'total_opened': total_opened,
                'open_rate': round(open_rate, 1),
                'recent_opens': recent_opens.to_dict('records') if not recent_opens.empty else []
            }
            
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {'total_tracked': 0, 'total_opened': 0, 'open_rate': 0, 'recent_opens': []}
    
    def get_unopened_emails(self, days_old: int = 3) -> List[Dict]:
        """Get list of emails that haven't been opened after X days."""
        try:
            df = pd.read_csv(self.tracking_log)
            
            df['sent_at'] = pd.to_datetime(df['sent_at'])
            cutoff = datetime.now() - pd.Timedelta(days=days_old)
            
            # Emails sent before cutoff with 0 opens
            unopened = df[(df['sent_at'] < cutoff) & (df['open_count'] == 0)]
            
            return unopened.to_dict('records')
            
        except Exception as e:
            logging.error(f"Error getting unopened: {e}")
            return []
    
    def generate_report(self) -> str:
        """Generate open tracking report."""
        stats = self.get_open_stats()
        unopened = self.get_unopened_emails(days_old=5)
        
        report = []
        report.append("=" * 60)
        report.append("📊 EMAIL OPEN TRACKING REPORT")
        report.append("=" * 60)
        report.append(f"\n📈 STATISTICS:")
        report.append(f"   Total Tracked Emails: {stats['total_tracked']}")
        report.append(f"   Emails Opened: {stats['total_opened']}")
        report.append(f"   Open Rate: {stats['open_rate']}%")
        
        if stats['recent_opens']:
            report.append(f"\n📬 RECENTLY OPENED:")
            for email in stats['recent_opens'][:5]:
                report.append(f"   ✅ {email.get('company', 'Unknown')} - {email.get('recipient_email', '')}")
        
        if unopened:
            report.append(f"\n⚠️ NOT OPENED (5+ days):")
            for email in unopened[:10]:
                report.append(f"   ❌ {email.get('company', 'Unknown')} - {email.get('recipient_email', '')}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


def generate_simple_tracking_html() -> str:
    """
    Generate a simple tracking solution using free services.
    
    Alternative approach without needing your own server:
    Uses email read receipts or simple beacon services.
    """
    # This provides instructions for setting up tracking
    instructions = """
    # EMAIL OPEN TRACKING SETUP OPTIONS:
    
    ## Option 1: Gmail Read Receipts (Simple)
    - Enable "Request read receipt" in Gmail settings
    - Note: Recipients can decline
    
    ## Option 2: Mailtrack Extension
    - Install Mailtrack browser extension
    - Automatically tracks opens in Gmail
    
    ## Option 3: Self-Hosted Tracking Pixel
    - Set up a simple endpoint (e.g., on Vercel/Netlify)
    - Returns 1x1 transparent GIF
    - Logs requests with tracking ID
    
    ## Option 4: GitHub Pages Tracking
    - Host a simple tracking page on GitHub Pages
    - Use query parameters for tracking IDs
    
    Set TRACKING_PIXEL_URL environment variable to your endpoint.
    """
    return instructions


def main():
    """Main function - generate tracking report."""
    logging.info("=" * 60)
    logging.info("📊 EMAIL OPEN TRACKER")
    logging.info("=" * 60)
    
    tracker = EmailOpenTracker()
    
    if not tracker.tracking_enabled:
        logging.info("Open tracking is disabled. Set ENABLE_OPEN_TRACKING=true to enable.")
        return
    
    # Generate and print report
    report = tracker.generate_report()
    print(report)
    
    # Save report
    report_path = os.path.join(tracker.data_dir, 'open_tracking_report.txt')
    with open(report_path, 'w') as f:
        f.write(report)
    
    logging.info(f"💾 Report saved to {report_path}")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
