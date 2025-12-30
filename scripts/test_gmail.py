#!/usr/bin/env python3
"""
Test Gmail SMTP connection
Run: python scripts/test_gmail.py
"""

import smtplib
import ssl
import os
import sys

def test_gmail_connection():
    """Test Gmail SMTP connection with app password."""
    
    # Get credentials from environment
    sender_email = os.getenv('SENDER_EMAIL') or os.getenv('GMAIL_USER') or os.getenv('APPLICANT_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    print("="*60)
    print("🔐 GMAIL SMTP CONNECTION TEST")
    print("="*60)
    
    # Check if credentials exist
    if not sender_email:
        print("❌ ERROR: No email found!")
        print("   Set SENDER_EMAIL or GMAIL_USER environment variable")
        return False
    
    if not sender_password:
        print("❌ ERROR: No password found!")
        print("   Set SENDER_PASSWORD or GMAIL_APP_PASSWORD environment variable")
        print("   Get App Password: https://myaccount.google.com/apppasswords")
        return False
    
    print(f"📧 Email: {sender_email}")
    print(f"🔑 Password: {'*' * (len(sender_password) - 4) + sender_password[-4:] if len(sender_password) > 4 else '***'}")
    print()
    
    # Test SMTP connection
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    print(f"🔌 Connecting to {smtp_server}:{smtp_port}...")
    
    try:
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            print("   ✅ Connected to SMTP server")
            
            server.starttls(context=context)
            print("   ✅ TLS started")
            
            server.login(sender_email, sender_password)
            print("   ✅ Login successful!")
            
        print()
        print("="*60)
        print("✅ GMAIL CONNECTION TEST PASSED!")
        print("   Your credentials are working correctly.")
        print("="*60)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print()
        print("="*60)
        print("❌ AUTHENTICATION FAILED!")
        print("="*60)
        print()
        print("Possible reasons:")
        print("1. ❌ Wrong App Password")
        print("   → Get new App Password: https://myaccount.google.com/apppasswords")
        print()
        print("2. ❌ Using regular password instead of App Password")
        print("   → Gmail requires 16-character App Password, NOT your regular password")
        print()
        print("3. ❌ 2-Factor Authentication not enabled")
        print("   → Enable 2FA first: https://myaccount.google.com/signinoptions/two-step-verification")
        print("   → Then create App Password")
        print()
        print(f"Error details: {e}")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


if __name__ == "__main__":
    # Allow passing credentials as arguments for testing
    if len(sys.argv) >= 3:
        os.environ['SENDER_EMAIL'] = sys.argv[1]
        os.environ['SENDER_PASSWORD'] = sys.argv[2]
    
    success = test_gmail_connection()
    sys.exit(0 if success else 1)
