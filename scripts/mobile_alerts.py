#!/usr/bin/env python3
"""
Mobile Alerts - WhatsApp & Telegram notifications for job applications
Sends instant alerts for interviews, offers, and important updates
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class WhatsAppNotifier:
    """
    Send WhatsApp notifications via various providers.
    
    Supported providers:
    1. Twilio WhatsApp API (paid, reliable)
    2. WhatsApp Business API (requires business account)
    3. CallMeBot (free, limited)
    4. WhatsMate (freemium)
    """
    
    def __init__(self):
        self.enabled = os.environ.get('ENABLE_WHATSAPP', 'false').lower() == 'true'
        self.provider = os.environ.get('WHATSAPP_PROVIDER', 'callmebot')
        
        # CallMeBot (Free option)
        self.callmebot_phone = os.environ.get('WHATSAPP_PHONE', '')  # With country code: +919876543210
        self.callmebot_apikey = os.environ.get('CALLMEBOT_API_KEY', '')
        
        # Twilio (Paid option)
        self.twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.twilio_from = os.environ.get('TWILIO_WHATSAPP_FROM', '')
        self.twilio_to = os.environ.get('TWILIO_WHATSAPP_TO', '')
        
        if self.enabled:
            logging.info(f"📱 WhatsApp notifications enabled via {self.provider}")
        else:
            logging.info("📱 WhatsApp notifications disabled")
    
    def send_message(self, message: str) -> bool:
        """Send WhatsApp message using configured provider."""
        if not self.enabled:
            logging.debug(f"[WhatsApp Disabled] Would send: {message[:50]}...")
            return False
        
        if self.provider == 'callmebot':
            return self._send_callmebot(message)
        elif self.provider == 'twilio':
            return self._send_twilio(message)
        else:
            logging.error(f"Unknown WhatsApp provider: {self.provider}")
            return False
    
    def _send_callmebot(self, message: str) -> bool:
        """Send via CallMeBot (free service)."""
        if not self.callmebot_phone or not self.callmebot_apikey:
            logging.warning("CallMeBot not configured. Set WHATSAPP_PHONE and CALLMEBOT_API_KEY")
            return False
        
        try:
            url = "https://api.callmebot.com/whatsapp.php"
            params = {
                'phone': self.callmebot_phone,
                'text': message,
                'apikey': self.callmebot_apikey
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                logging.info("✅ WhatsApp message sent via CallMeBot")
                return True
            else:
                logging.error(f"CallMeBot error: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"WhatsApp send failed: {e}")
            return False
    
    def _send_twilio(self, message: str) -> bool:
        """Send via Twilio WhatsApp API (paid)."""
        if not all([self.twilio_sid, self.twilio_token, self.twilio_from, self.twilio_to]):
            logging.warning("Twilio not fully configured")
            return False
        
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            
            msg = client.messages.create(
                body=message,
                from_=f'whatsapp:{self.twilio_from}',
                to=f'whatsapp:{self.twilio_to}'
            )
            
            logging.info(f"✅ WhatsApp sent via Twilio: {msg.sid}")
            return True
            
        except ImportError:
            logging.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logging.error(f"Twilio error: {e}")
            return False
    
    def send_interview_alert(self, company: str, email: str, subject: str) -> bool:
        """Send urgent interview alert."""
        message = f"""🎯 *INTERVIEW REQUEST!*

📍 Company: {company}
📧 From: {email}
📋 Subject: {subject}

⚡ Reply ASAP!
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return self.send_message(message)
    
    def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily summary."""
        message = f"""📊 *Job Application Summary*

🔍 Jobs Scraped: {stats.get('jobs_scraped', 0)}
📧 Emails Sent: {stats.get('emails_sent', 0)}
📬 HR Replies: {stats.get('hr_replies', 0)}
🎯 Interviews: {stats.get('interviews', 0)}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return self.send_message(message)


class TelegramNotifier:
    """
    Send Telegram notifications via Bot API.
    
    Setup:
    1. Create bot with @BotFather
    2. Get bot token
    3. Get your chat ID (message the bot, check updates API)
    """
    
    def __init__(self):
        self.enabled = os.environ.get('ENABLE_TELEGRAM', 'false').lower() == 'true'
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        if self.enabled and self.bot_token and self.chat_id:
            logging.info("📱 Telegram notifications enabled")
        else:
            logging.info("📱 Telegram notifications disabled")
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send Telegram message."""
        if not self.enabled or not self.bot_token or not self.chat_id:
            logging.debug(f"[Telegram Disabled] Would send: {message[:50]}...")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logging.info("✅ Telegram message sent")
                return True
            else:
                logging.error(f"Telegram error: {result}")
                return False
                
        except Exception as e:
            logging.error(f"Telegram send failed: {e}")
            return False
    
    def send_interview_alert(self, company: str, email: str, subject: str) -> bool:
        """Send urgent interview alert."""
        message = f"""🎯 *INTERVIEW REQUEST!*

📍 *Company:* {company}
📧 *From:* {email}
📋 *Subject:* {subject}

⚡ *Reply ASAP!*
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return self.send_message(message)
    
    def send_hr_reply_alert(self, company: str, reply_type: str, subject: str) -> bool:
        """Send HR reply notification."""
        emoji_map = {
            'interview': '🎯',
            'offer': '🏆',
            'positive': '✅',
            'rejection': '❌'
        }
        emoji = emoji_map.get(reply_type, '📧')
        
        message = f"""{emoji} *HR Reply - {reply_type.title()}*

📍 *Company:* {company}
📋 *Subject:* {subject}
🕐 {datetime.now().strftime('%H:%M')}"""
        
        return self.send_message(message)
    
    def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily summary."""
        message = f"""📊 *Job Application Summary*

🔍 Jobs Scraped: `{stats.get('jobs_scraped', 0)}`
📧 Emails Sent: `{stats.get('emails_sent', 0)}`
📬 HR Replies: `{stats.get('hr_replies', 0)}`
🎯 Interviews: `{stats.get('interviews', 0)}`
✅ Verified Emails: `{stats.get('verified_emails', 0)}`
❌ Bounced: `{stats.get('bounced', 0)}`

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return self.send_message(message)


class MobileAlerts:
    """Unified mobile alerts manager."""
    
    def __init__(self):
        self.whatsapp = WhatsAppNotifier()
        self.telegram = TelegramNotifier()
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    def send_interview_alert(self, company: str, email: str, subject: str):
        """Send interview alert to all enabled channels."""
        logging.info(f"🚨 Sending interview alert: {company}")
        
        if self.whatsapp.enabled:
            self.whatsapp.send_interview_alert(company, email, subject)
        
        if self.telegram.enabled:
            self.telegram.send_interview_alert(company, email, subject)
    
    def send_daily_summary(self, stats: Dict):
        """Send daily summary to all enabled channels."""
        logging.info("📊 Sending daily summary to mobile")
        
        if self.whatsapp.enabled:
            self.whatsapp.send_daily_summary(stats)
        
        if self.telegram.enabled:
            self.telegram.send_daily_summary(stats)
    
    def check_and_alert_interviews(self):
        """Check for new interviews and send alerts."""
        interview_file = os.path.join(self.data_dir, 'interview_requests.csv')
        
        if not os.path.exists(interview_file):
            return
        
        try:
            df = pd.read_csv(interview_file)
            
            # Get interviews from last hour (to avoid duplicate alerts)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                recent = df[df['date'] > (datetime.now() - pd.Timedelta(hours=1))]
            else:
                recent = df.tail(3)
            
            for _, row in recent.iterrows():
                company = row.get('company', 'Unknown')
                email = row.get('from_email', row.get('email', ''))
                subject = row.get('subject', 'Interview Request')
                
                self.send_interview_alert(company, email, subject)
                
        except Exception as e:
            logging.error(f"Error checking interviews: {e}")


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
    
    return stats


def main():
    """Main function - send mobile alerts."""
    logging.info("=" * 60)
    logging.info("📱 MOBILE ALERTS (WhatsApp/Telegram)")
    logging.info("=" * 60)
    
    alerts = MobileAlerts()
    
    # Check if any channel is enabled
    if not alerts.whatsapp.enabled and not alerts.telegram.enabled:
        logging.info("No mobile alerts configured.")
        logging.info("Set ENABLE_WHATSAPP=true or ENABLE_TELEGRAM=true to enable")
        logging.info("")
        logging.info("📱 WHATSAPP SETUP (Free - CallMeBot):")
        logging.info("   1. Add +34 644 51 95 23 to contacts as 'CallMeBot'")
        logging.info("   2. Send 'I allow callmebot to send me messages' to this number")
        logging.info("   3. You'll receive an API key")
        logging.info("   4. Set secrets: WHATSAPP_PHONE, CALLMEBOT_API_KEY")
        logging.info("")
        logging.info("📱 TELEGRAM SETUP:")
        logging.info("   1. Message @BotFather to create a bot")
        logging.info("   2. Get your chat ID from @userinfobot")
        logging.info("   3. Set secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        return
    
    # Collect stats
    stats = collect_stats()
    
    # Send daily summary
    alerts.send_daily_summary(stats)
    
    # Check for interview alerts
    alerts.check_and_alert_interviews()
    
    logging.info("=" * 60)
    logging.info("✅ Mobile alerts sent!")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
