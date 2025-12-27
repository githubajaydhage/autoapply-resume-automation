#!/usr/bin/env python3
"""
Setup and test local credentials for job applications
"""

import os
import logging
import getpass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def setup_local_credentials():
    """Interactive setup for local credentials"""
    logger.info("🔐 LOCAL CREDENTIAL SETUP")
    logger.info("=" * 50)
    logger.info("This will help you set up credentials for testing")
    logger.info("Note: In production, use GitHub repository secrets")
    logger.info("")
    
    credentials = {}
    
    # LinkedIn credentials
    logger.info("📱 LinkedIn Credentials:")
    linkedin_email = input("LinkedIn Email: ").strip()
    linkedin_password = getpass.getpass("LinkedIn Password: ")
    credentials['LINKEDIN_EMAIL'] = linkedin_email
    credentials['LINKEDIN_PASSWORD'] = linkedin_password
    
    # Naukri credentials  
    logger.info("\n🇮🇳 Naukri Credentials:")
    naukri_email = input("Naukri Email: ").strip()
    naukri_password = getpass.getpass("Naukri Password: ")
    credentials['NAUKRI_EMAIL'] = naukri_email
    credentials['NAUKRI_PASSWORD'] = naukri_password
    
    # Indeed credentials
    logger.info("\n🌐 Indeed Credentials:")
    indeed_email = input("Indeed Email: ").strip()
    indeed_password = getpass.getpass("Indeed Password: ")
    credentials['INDEED_EMAIL'] = indeed_email
    credentials['INDEED_PASSWORD'] = indeed_password
    
    # Set environment variables for current session
    for key, value in credentials.items():
        os.environ[key] = value
    
    logger.info("")
    logger.info("✅ Credentials set for current session")
    logger.info("💡 For persistent setup, add these to your system environment variables")
    
    return credentials

def verify_credentials():
    """Verify credentials are accessible"""
    logger.info("\n🔍 VERIFYING CREDENTIALS")
    logger.info("-" * 30)
    
    required_vars = [
        'LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD',
        'NAUKRI_EMAIL', 'NAUKRI_PASSWORD',
        'INDEED_EMAIL', 'INDEED_PASSWORD'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                logger.info(f"✅ {var}: {'*' * len(value)}")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: NOT SET")
            all_present = False
    
    return all_present

def create_env_file(credentials):
    """Create a .env file for easy loading"""
    env_path = Path(".env")
    
    with open(env_path, 'w') as f:
        f.write("# Local Environment Variables for Job Application Automation\\n")
        f.write("# DO NOT commit this file to version control\\n\\n")
        
        for key, value in credentials.items():
            f.write(f"{key}={value}\\n")
    
    logger.info(f"💾 Created .env file: {env_path.absolute()}")
    logger.info("⚠️  Remember to add .env to .gitignore")

def main():
    """Main setup function"""
    logger.info("🚀 CREDENTIAL SETUP FOR JOB APPLICATION AUTOMATION")
    logger.info("=" * 60)
    
    # Check if credentials already exist
    if verify_credentials():
        logger.info("🎯 All credentials already configured!")
        response = input("\\nDo you want to reconfigure? (y/n): ").strip().lower()
        if response != 'y':
            logger.info("✅ Using existing credentials")
            return True
    
    # Setup credentials interactively
    credentials = setup_local_credentials()
    
    # Verify setup
    if verify_credentials():
        logger.info("\\n🎯 CREDENTIAL SETUP COMPLETE!")
        
        # Ask if user wants to save to .env file
        save_env = input("\\nSave to .env file for future use? (y/n): ").strip().lower()
        if save_env == 'y':
            create_env_file(credentials)
        
        logger.info("\\n🚀 Ready to test applications!")
        logger.info("Run: python scripts/test_credentials_and_apply.py")
        return True
    else:
        logger.error("❌ Credential setup failed")
        return False

if __name__ == "__main__":
    main()