#!/usr/bin/env python3
"""
Slack Notifier - Send job application updates to Slack
Sends alerts for: interviews, HR replies, daily summaries, errors
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class SlackNotifier:
    """Send notifications to Slack webhook."""
    
    def __init__(self):
        self.webhook_url = os.environ.get('SLACK_WEBHOOK_URL', '')
        self.enabled = bool(self.webhook_url)
        self.channel = os.environ.get('SLACK_CHANNEL', '#job-alerts')
        
        # GitHub Actions dashboard link
        self.github_repo = os.environ.get('GITHUB_REPOSITORY', 'githubajaydhage/autoapply-resume-automation')
        self.github_run_id = os.environ.get('GITHUB_RUN_ID', '')
        self.dashboard_url = f"https://github.com/{self.github_repo}/actions"
        if self.github_run_id:
            self.run_url = f"https://github.com/{self.github_repo}/actions/runs/{self.github_run_id}"
        else:
            self.run_url = self.dashboard_url
        
        if not self.enabled:
            logging.warning("⚠️ Slack webhook URL not configured. Notifications disabled.")
    
    def send_message(self, blocks: List[Dict], text: str = "Job Application Update") -> bool:
        """Send a message to Slack."""
        if not self.enabled:
            logging.info(f"[Slack Disabled] Would send: {text}")
            return False
        
        try:
            payload = {
                "text": text,
                "blocks": blocks
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"✅ Slack notification sent: {text}")
                return True
            else:
                logging.error(f"❌ Slack error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Slack notification failed: {e}")
            return False
    
    def notify_interview_request(self, company: str, email: str, subject: str, preview: str = ""):
        """🎯 Alert for interview request - HIGH PRIORITY."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎯 INTERVIEW REQUEST!", "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": f"*From:*\n{email}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Subject:*\n{subject}"}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} | Reply ASAP!"}
                ]
            },
            {"type": "divider"}
        ]
        
        if preview:
            blocks.insert(3, {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Preview:*\n_{preview[:200]}..._"}
            })
        
        return self.send_message(blocks, f"🎯 Interview Request from {company}!")
    
    def notify_hr_reply(self, company: str, email: str, subject: str, reply_type: str):
        """📬 Alert for HR reply."""
        emoji_map = {
            'interview': '🎯',
            'offer': '🏆',
            'positive': '✅',
            'acknowledgment': '📥',
            'rejection': '❌',
            'review': '📧'
        }
        emoji = emoji_map.get(reply_type, '📧')
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} HR Reply Received", "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": f"*Type:*\n{reply_type.title()}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Subject:*\n{subject}"}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]
            }
        ]
        
        return self.send_message(blocks, f"{emoji} HR Reply from {company}")
    
    def notify_daily_summary(self, stats: Dict):
        """📊 Daily run summary."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📊 Job Application Summary", "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🔍 Jobs Scraped:*\n{stats.get('jobs_scraped', 0)}"},
                    {"type": "mrkdwn", "text": f"*📧 Emails Sent:*\n{stats.get('emails_sent', 0)}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🤝 Referrals Sent:*\n{stats.get('referrals_sent', 0)}"},
                    {"type": "mrkdwn", "text": f"*🎯 Interview Requests:*\n{stats.get('interviews', 0)}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*📬 HR Replies:*\n{stats.get('hr_replies', 0)}"},
                    {"type": "mrkdwn", "text": f"*❌ Bounced:*\n{stats.get('bounced', 0)}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"📊 *<{self.run_url}|View Full Dashboard & Reports>*"}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🕐 Run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                ]
            }
        ]
        
        # Add interview alert if any
        if stats.get('interviews', 0) > 0:
            blocks.insert(1, {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🚨 *ACTION REQUIRED: You have interview requests!*"}
            })
        
        return self.send_message(blocks, f"📊 Daily Summary: {stats.get('emails_sent', 0)} sent, {stats.get('interviews', 0)} interviews")
    
    def notify_emails_sent(self, count: int, companies: List[str]):
        """✉️ Notification after sending emails."""
        company_list = ", ".join(companies[:5])
        if len(companies) > 5:
            company_list += f" +{len(companies) - 5} more"
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"✉️ *{count} application emails sent*\n\nCompanies: {company_list}"}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]
            }
        ]
        
        return self.send_message(blocks, f"✉️ {count} emails sent")
    
    def notify_error(self, phase: str, error: str):
        """🚨 Alert for errors."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🚨 Workflow Error", "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Phase:*\n{phase}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now().strftime('%H:%M:%S')}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error[:500]}```"}
            }
        ]
        
        return self.send_message(blocks, f"🚨 Error in {phase}")
    
    def notify_new_jobs(self, count: int, sources: Dict[str, int]):
        """🔍 New jobs found notification."""
        source_text = "\n".join([f"• {src}: {cnt}" for src, cnt in list(sources.items())[:6]])
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"🔍 *{count} new jobs scraped*\n\n{source_text}"}
            }
        ]
        
        return self.send_message(blocks, f"🔍 {count} jobs found")


def collect_stats(data_dir: str = "data") -> Dict:
    """Collect statistics from data files."""
    stats = {}
    
    def count_lines(filepath):
        try:
            if os.path.exists(filepath):
                return max(0, sum(1 for _ in open(filepath)) - 1)
        except:
            pass
        return 0
    
    stats['jobs_scraped'] = count_lines(f"{data_dir}/jobs_today.csv")
    stats['emails_sent'] = count_lines(f"{data_dir}/sent_emails_log.csv")
    stats['hr_replies'] = count_lines(f"{data_dir}/hr_replies.csv")
    stats['interviews'] = count_lines(f"{data_dir}/interview_requests.csv")
    stats['verified_emails'] = count_lines(f"{data_dir}/verified_hr_emails.csv")
    stats['bounced'] = count_lines(f"{data_dir}/bounced_emails.csv")
    stats['referrals_sent'] = count_lines(f"{data_dir}/referral_requests_log.csv")
    
    return stats


def notify_new_interviews(notifier: SlackNotifier, data_dir: str = "data"):
    """Check for new interview requests and notify."""
    interview_file = f"{data_dir}/interview_requests.csv"
    
    if not os.path.exists(interview_file):
        return
    
    try:
        df = pd.read_csv(interview_file)
        
        # Get interviews from last 24 hours
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Use timezone-naive comparison by removing timezone info
            df['date'] = df['date'].dt.tz_localize(None)
            cutoff = datetime.now() - pd.Timedelta(hours=24)
            recent = df[df['date'].notna() & (df['date'] > cutoff)]
        else:
            recent = df.tail(5)  # Just notify last 5
        
        for _, row in recent.iterrows():
            company = row.get('company', 'Unknown')
            email = row.get('from_email', row.get('email', ''))
            subject = row.get('subject', 'Interview Request')
            preview = row.get('preview', '')
            
            notifier.notify_interview_request(company, email, subject, preview)
            
    except Exception as e:
        logging.error(f"Error checking interviews: {e}")


def notify_hr_replies(notifier: SlackNotifier, data_dir: str = "data"):
    """Check for HR replies and notify."""
    replies_file = f"{data_dir}/hr_replies.csv"
    
    if not os.path.exists(replies_file):
        return
    
    try:
        df = pd.read_csv(replies_file)
        
        # Get recent replies
        recent = df.tail(10)
        
        for _, row in recent.iterrows():
            reply_type = row.get('type', 'review')
            
            # Only notify for important replies
            if reply_type in ['interview', 'offer', 'positive']:
                company = row.get('company', 'Unknown')
                email = row.get('from_email', row.get('email', ''))
                subject = row.get('subject', 'HR Reply')
                
                notifier.notify_hr_reply(company, email, subject, reply_type)
                
    except Exception as e:
        logging.error(f"Error checking replies: {e}")


def main():
    """Main function - send summary notification."""
    logging.info("=" * 60)
    logging.info("📢 SLACK NOTIFIER")
    logging.info("=" * 60)
    
    notifier = SlackNotifier()
    
    if not notifier.enabled:
        logging.info("Slack not configured. Set SLACK_WEBHOOK_URL to enable.")
        return
    
    # Collect stats
    stats = collect_stats()
    
    # Send daily summary
    notifier.notify_daily_summary(stats)
    
    # Check for interview requests
    notify_new_interviews(notifier)
    
    # Check for important HR replies
    notify_hr_replies(notifier)
    
    logging.info("=" * 60)
    logging.info("✅ Slack notifications sent!")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
