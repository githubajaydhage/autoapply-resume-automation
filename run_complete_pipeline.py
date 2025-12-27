#!/usr/bin/env python3
"""
Run Complete Job Application Pipeline with Proof Tracking

This script executes the full automation pipeline:
1. Job scraping from multiple sources
2. Resume tailoring for each job
3. Simultaneous applications across platforms  
4. Application proof documentation

Usage: python run_complete_pipeline.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.production_app_runner import main
import logging

def setup_logging():
    """Setup enhanced logging for complete pipeline execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)8s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/complete_pipeline_execution.log')
        ]
    )

if __name__ == "__main__":
    print("🚀 STARTING COMPLETE JOB APPLICATION PIPELINE")
    print("=" * 60)
    print("This will execute:")
    print("  1️⃣ Job Scraping (Indeed RSS + Company careers)")
    print("  2️⃣ Resume Tailoring (AI-powered customization)")  
    print("  3️⃣ Simultaneous Applications (LinkedIn + Naukri + Companies)")
    print("  4️⃣ Application Proof Documentation")
    print("")
    print("Expected results: 50-150+ job applications with proof")
    print("Estimated time: 5-10 minutes for complete pipeline")
    print("")
    
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Pipeline cancelled.")
        sys.exit(0)
    
    print("\n🔄 INITIATING COMPLETE PIPELINE EXECUTION...")
    print("=" * 50)
    
    setup_logging()
    
    try:
        success = main()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ COMPLETE PIPELINE EXECUTION SUCCESSFUL!")
            print("")
            print("📋 Check these files for proof:")
            print("  • data/application_proof.json - Detailed application proof")
            print("  • data/complete_pipeline_execution.log - Full execution log")
            print("  • data/jobs_today.csv - Scraped jobs")
            print("  • resumes/tailored/ - Tailored resumes")
            print("")
            print("🎯 All applications have been documented with timestamps and proof!")
        else:
            print("❌ Pipeline execution encountered issues")
            print("Check logs for details: data/complete_pipeline_execution.log")
            
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline execution interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}")
        logging.error(f"Pipeline execution failed: {e}")