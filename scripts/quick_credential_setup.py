#!/usr/bin/env python3
"""
Quick setup for LinkedIn and Naukri credentials testing
"""

import os
import logging

# Configure logging without emojis for Windows compatibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def setup_test_credentials():
    """Quick credential setup for local testing"""
    logger.info("CREDENTIAL SETUP FOR JOB APPLICATION TESTING")
    logger.info("=" * 55)
    logger.info("")
    
    logger.info("Enter your credentials for testing:")
    logger.info("(These will be set as environment variables for this session only)")
    logger.info("")
    
    # LinkedIn credentials
    logger.info("LINKEDIN CREDENTIALS:")
    linkedin_email = input("LinkedIn Email: ").strip()
    linkedin_password = input("LinkedIn Password: ").strip()  # Using input instead of getpass for simplicity
    
    logger.info("")
    logger.info("NAUKRI CREDENTIALS:")
    naukri_email = input("Naukri Email: ").strip()
    naukri_password = input("Naukri Password: ").strip()
    
    # Set environment variables
    os.environ['LINKEDIN_EMAIL'] = linkedin_email
    os.environ['LINKEDIN_PASSWORD'] = linkedin_password
    os.environ['NAUKRI_EMAIL'] = naukri_email
    os.environ['NAUKRI_PASSWORD'] = naukri_password
    
    # Optional Indeed credentials
    logger.info("")
    use_indeed = input("Also set up Indeed credentials? (y/n): ").strip().lower()
    if use_indeed == 'y':
        indeed_email = input("Indeed Email: ").strip()
        indeed_password = input("Indeed Password: ").strip()
        os.environ['INDEED_EMAIL'] = indeed_email
        os.environ['INDEED_PASSWORD'] = indeed_password
        logger.info("Indeed credentials set!")
    
    logger.info("")
    logger.info("CREDENTIALS SET FOR CURRENT SESSION!")
    logger.info("You can now run simultaneous applications")
    return True

def verify_and_run():
    """Verify credentials and run simultaneous test"""
    logger.info("")
    logger.info("VERIFYING CREDENTIALS...")
    
    # Check LinkedIn
    linkedin_ready = bool(os.getenv('LINKEDIN_EMAIL')) and bool(os.getenv('LINKEDIN_PASSWORD'))
    logger.info(f"LinkedIn Ready: {'YES' if linkedin_ready else 'NO'}")
    
    # Check Naukri
    naukri_ready = bool(os.getenv('NAUKRI_EMAIL')) and bool(os.getenv('NAUKRI_PASSWORD'))
    logger.info(f"Naukri Ready: {'YES' if naukri_ready else 'NO'}")
    
    # Check Indeed
    indeed_ready = bool(os.getenv('INDEED_EMAIL')) and bool(os.getenv('INDEED_PASSWORD'))
    logger.info(f"Indeed Ready: {'YES' if indeed_ready else 'NO (Optional)'}")
    
    if linkedin_ready and naukri_ready:
        logger.info("")
        logger.info("SUCCESS! Core credentials are ready")
        logger.info("Running simultaneous application test...")
        logger.info("")
        
        # Import and run the simulation
        import subprocess
        result = subprocess.run(['python', 'scripts/test_credentials_simulation.py'], 
                              capture_output=False, text=True)
        return result.returncode == 0
    else:
        logger.error("Missing required credentials. Please set LinkedIn and Naukri credentials.")
        return False

def main():
    """Main setup and test function"""
    logger.info("JOB APPLICATION AUTOMATION - CREDENTIAL SETUP & TEST")
    logger.info("=" * 60)
    logger.info("")
    
    # Check if credentials are already set
    linkedin_set = bool(os.getenv('LINKEDIN_EMAIL')) and bool(os.getenv('LINKEDIN_PASSWORD'))
    naukri_set = bool(os.getenv('NAUKRI_EMAIL')) and bool(os.getenv('NAUKRI_PASSWORD'))
    
    if linkedin_set and naukri_set:
        logger.info("Credentials already detected in environment!")
        run_test = input("Run simultaneous application test? (y/n): ").strip().lower()
        if run_test == 'y':
            return verify_and_run()
    else:
        logger.info("No credentials detected. Setting up for local testing...")
        logger.info("")
        logger.info("NOTE: In production, these should be set as GitHub repository secrets:")
        logger.info("  - LINKEDIN_EMAIL")
        logger.info("  - LINKEDIN_PASSWORD") 
        logger.info("  - NAUKRI_EMAIL")
        logger.info("  - NAUKRI_PASSWORD")
        logger.info("")
        
        setup_ok = setup_test_credentials()
        if setup_ok:
            return verify_and_run()
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("")
        logger.info("SETUP COMPLETE! System ready for simultaneous applications")
    else:
        logger.info("")
        logger.info("Setup incomplete. Please check credentials and try again.")