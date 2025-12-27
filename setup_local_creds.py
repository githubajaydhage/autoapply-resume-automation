#!/usr/bin/env python3
"""
Quick Local Credential Setup

This sets up your credentials locally to match your GitHub secrets
so you can run real applications and get email confirmations.
"""

import os
from pathlib import Path

def setup_local_credentials():
    """Setup credentials locally to match GitHub secrets"""
    print("🔐 LOCAL CREDENTIAL SETUP FOR EMAIL CONFIRMATIONS")
    print("=" * 55)
    print("Enter the same credentials you have in GitHub secrets:")
    print("")
    
    # LinkedIn credentials
    print("📧 LINKEDIN CREDENTIALS")
    print("-" * 25)
    linkedin_email = input("LinkedIn Email: ").strip()
    linkedin_password = input("LinkedIn Password: ").strip()
    
    # Naukri credentials  
    print("\n📧 NAUKRI CREDENTIALS")
    print("-" * 20)
    naukri_email = input("Naukri Email: ").strip()
    naukri_password = input("Naukri Password: ").strip()
    
    # Indeed credentials (optional)
    print("\n📧 INDEED CREDENTIALS (Optional)")
    print("-" * 30)
    indeed_email = input("Indeed Email (press enter to skip): ").strip()
    indeed_password = input("Indeed Password (press enter to skip): ").strip() if indeed_email else ""
    
    # Set environment variables for current session
    if linkedin_email and linkedin_password:
        os.environ['LINKEDIN_EMAIL'] = linkedin_email
        os.environ['LINKEDIN_PASSWORD'] = linkedin_password
        print("✅ LinkedIn credentials set")
    
    if naukri_email and naukri_password:
        os.environ['NAUKRI_EMAIL'] = naukri_email
        os.environ['NAUKRI_PASSWORD'] = naukri_password
        print("✅ Naukri credentials set")
    
    if indeed_email and indeed_password:
        os.environ['INDEED_EMAIL'] = indeed_email
        os.environ['INDEED_PASSWORD'] = indeed_password
        print("✅ Indeed credentials set")
    
    # Create batch file for Windows to persist environment variables
    batch_content = f"""@echo off
echo Setting up job application credentials...
set LINKEDIN_EMAIL={linkedin_email}
set LINKEDIN_PASSWORD={linkedin_password}
set NAUKRI_EMAIL={naukri_email}
set NAUKRI_PASSWORD={naukri_password}
"""
    
    if indeed_email and indeed_password:
        batch_content += f"""set INDEED_EMAIL={indeed_email}
set INDEED_PASSWORD={indeed_password}
"""
    
    batch_content += """
echo ✅ Credentials loaded!
echo Running real job applications...
python run_real_apps_simple.py
pause
"""
    
    with open("run_with_credentials.bat", 'w') as f:
        f.write(batch_content)
    
    print("\n✅ CREDENTIALS SETUP COMPLETE!")
    print("=" * 40)
    print("Credentials are now available for real applications")
    print("Run: python test_credentials.py to verify")
    
    return True

def test_loaded_credentials():
    """Test if credentials are loaded correctly"""
    print("\n🧪 TESTING CREDENTIALS")
    print("=" * 25)
    
    linkedin_ready = bool(os.getenv('LINKEDIN_EMAIL')) and bool(os.getenv('LINKEDIN_PASSWORD'))
    naukri_ready = bool(os.getenv('NAUKRI_EMAIL')) and bool(os.getenv('NAUKRI_PASSWORD'))
    indeed_ready = bool(os.getenv('INDEED_EMAIL')) and bool(os.getenv('INDEED_PASSWORD'))
    
    print(f"LinkedIn: {'✅ Ready' if linkedin_ready else '❌ Missing'}")
    print(f"Naukri:   {'✅ Ready' if naukri_ready else '❌ Missing'}")
    print(f"Indeed:   {'✅ Ready' if indeed_ready else '⚠️ Optional'}")
    
    if linkedin_ready or naukri_ready:
        print("\n🚀 READY FOR REAL APPLICATIONS!")
        print("Run: python run_real_apps_simple.py")
        return True
    else:
        print("\n❌ Credentials not properly loaded")
        return False

if __name__ == "__main__":
    setup_local_credentials()
    test_loaded_credentials()