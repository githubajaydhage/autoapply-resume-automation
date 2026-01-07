#!/usr/bin/env python3
"""
Dynamic Configuration Validator
Ensures all environment variables are properly set from workflow inputs
"""

import os
import sys

def validate_user_config():
    """Validate that all required user configuration is provided via env vars"""
    
    required_fields = {
        'APPLICANT_NAME': 'Full name of the applicant',
        'APPLICANT_EMAIL': 'Email address', 
        'APPLICANT_PHONE': 'Phone number',
        'APPLICANT_LOCATION': 'Location (city, state, country)',
        'APPLICANT_LINKEDIN': 'LinkedIn URL',
        'APPLICANT_EXPERIENCE': 'Years of experience',
        'APPLICANT_TARGET_ROLE': 'Target job roles',
        'APPLICANT_SKILLS': 'Key skills',
        'RESUME_FILENAME': 'Resume filename',
        'JOB_KEYWORDS': 'Job search keywords'
    }
    
    missing_fields = []
    provided_fields = {}
    
    print("🔍 DYNAMIC CONFIGURATION VALIDATION")
    print("=" * 50)
    
    for field, description in required_fields.items():
        value = os.getenv(field, '').strip()
        if not value:
            missing_fields.append(f"  ❌ {field}: {description}")
        else:
            provided_fields[field] = value
            print(f"✅ {field}: {value}")
    
    if missing_fields:
        print("\n❌ MISSING REQUIRED CONFIGURATION:")
        for field in missing_fields:
            print(field)
        print("\nPlease provide all required workflow inputs!")
        return False
    
    # Validate email format
    email = provided_fields.get('APPLICANT_EMAIL', '')
    if '@' not in email or '.' not in email:
        print(f"❌ Invalid email format: {email}")
        return False
    
    # Validate experience is numeric
    try:
        int(provided_fields.get('APPLICANT_EXPERIENCE', '0'))
    except ValueError:
        print(f"❌ Experience must be numeric: {provided_fields.get('APPLICANT_EXPERIENCE')}")
        return False
    
    print("\n✅ ALL CONFIGURATION VALID!")
    print("🚀 Ready to proceed with job applications")
    return True

if __name__ == "__main__":
    success = validate_user_config()
    sys.exit(0 if success else 1)