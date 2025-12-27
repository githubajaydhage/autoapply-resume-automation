#!/usr/bin/env python3
"""
Real Credentials Setup for Email Confirmations

This sets up your actual job portal credentials so the system can:
1. Submit REAL applications to LinkedIn, Naukri, Company portals
2. You'll receive EMAIL CONFIRMATIONS from each portal
3. Get actual interview calls and responses

IMPORTANT: This submits REAL applications with your profile!
"""

import os
from pathlib import Path

def setup_real_credentials():
    """Setup real job portal credentials for actual applications"""
    print("🔐 REAL CREDENTIALS SETUP FOR EMAIL CONFIRMATIONS")
    print("=" * 55)
    print("⚠️  WARNING: This will submit REAL applications!")
    print("⚠️  You will receive EMAIL confirmations from job portals")
    print("⚠️  Companies may contact you for interviews")
    print("")
    
    # Get credentials
    credentials = {}
    
    print("📧 LINKEDIN CREDENTIALS (Required)")
    print("-" * 30)
    linkedin_email = input("LinkedIn Email: ").strip()
    linkedin_password = input("LinkedIn Password: ").strip()
    
    if linkedin_email and linkedin_password:
        credentials['LINKEDIN_EMAIL'] = linkedin_email
        credentials['LINKEDIN_PASSWORD'] = linkedin_password
        print("✅ LinkedIn credentials saved")
    else:
        print("❌ LinkedIn credentials required for email confirmations")
        return False
    
    print("\n📧 NAUKRI CREDENTIALS (Required)")  
    print("-" * 30)
    naukri_email = input("Naukri Email: ").strip()
    naukri_password = input("Naukri Password: ").strip()
    
    if naukri_email and naukri_password:
        credentials['NAUKRI_EMAIL'] = naukri_email
        credentials['NAUKRI_PASSWORD'] = naukri_password
        print("✅ Naukri credentials saved")
    else:
        print("⚠️ Naukri credentials recommended for more email confirmations")
    
    print("\n📧 INDEED CREDENTIALS (Optional)")
    print("-" * 30)
    indeed_email = input("Indeed Email (optional): ").strip()
    indeed_password = input("Indeed Password (optional): ").strip()
    
    if indeed_email and indeed_password:
        credentials['INDEED_EMAIL'] = indeed_email
        credentials['INDEED_PASSWORD'] = indeed_password
        print("✅ Indeed credentials saved")
    else:
        print("ℹ️ Indeed credentials skipped (optional)")
    
    # Save to environment file
    env_file = Path(".env")
    with open(env_file, 'w') as f:
        f.write("# Real Job Portal Credentials for Email Confirmations\\n")
        f.write("# IMPORTANT: These will submit REAL applications!\\n\\n")
        
        for key, value in credentials.items():
            f.write(f"{key}={value}\\n")
    
    print(f"\n✅ Credentials saved to {env_file}")
    print("\n📧 EMAIL CONFIRMATION SETUP COMPLETE!")
    print("=" * 45)
    print("When you run the real system:")
    print("  ✅ Applications will be ACTUALLY submitted")
    print("  ✅ You'll get EMAIL confirmations from portals")
    print("  ✅ Companies will contact you for interviews")
    print("  ✅ Real responses from hiring managers")
    print("")
    print("Next: Run 'python run_real_applications.py'")
    
    return True

def load_credentials_to_environment():
    """Load credentials from .env file to environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    return True

if __name__ == "__main__":
    print("🎯 SETUP FOR REAL EMAIL CONFIRMATIONS")
    print("This will configure the system to submit ACTUAL applications")
    print("and receive EMAIL confirmations from job portals.")
    print("")
    
    confirm = input("Continue with REAL applications setup? (y/N): ").lower()
    if confirm == 'y':
        success = setup_real_credentials()
        if success:
            print("\\n🚀 Ready to submit REAL applications!")
            print("Run: python run_real_applications.py")
    else:
        print("Setup cancelled.")