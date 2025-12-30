#!/usr/bin/env python3
"""
Quick Gmail SMTP Test - Minimal test for GitHub Actions
Tests Gmail connection without complex logging
"""

import smtplib
import ssl
import os

def test_gmail():
    email = os.getenv('SENDER_EMAIL')
    password = os.getenv('SENDER_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD') or os.getenv('SENDER_PASSWORD_YOGESHWARI', '')
    
    if not email:
        print("❌ SENDER_EMAIL environment variable is required")
        return False
        
    print(f"📧 Testing: {email}")
    
    if not password:
        print("❌ No password found in SENDER_PASSWORD/GMAIL_APP_PASSWORD/SENDER_PASSWORD_YOGESHWARI")
        return False
    
    try:
        # Create secure connection
        context = ssl.create_default_context()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(context=context)
        
        # Test login
        server.login(email, password)
        server.quit()
        
        print("✅ Gmail authentication SUCCESS!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail authentication FAILED: {e}")
        print("🔧 Fix: Generate new App Password at https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gmail()
    exit(0 if success else 1)