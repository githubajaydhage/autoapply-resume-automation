#!/usr/bin/env python3
"""
Run Phase 8-10 analysis scripts for the workflow.
This wrapper handles optional features that may fail gracefully.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_job_priority():
    """Phase 8: Job Priority Analysis"""
    print("📊 Running job priority analysis...")
    try:
        import pandas as pd
        if os.path.exists('data/jobs_today.csv'):
            from scripts.job_priority_engine import prioritize_jobs
            jobs_df = pd.read_csv('data/jobs_today.csv')
            prioritize_jobs(jobs_df)
            print("✅ Job priority analysis complete")
        else:
            print("⚠️ No jobs file found, skipping priority analysis")
    except Exception as e:
        print(f"⚠️ Job priority analysis skipped: {e}")

def run_linkedin_warmup():
    """Phase 9: LinkedIn Warm-Up Plans"""
    print("🔗 Generating LinkedIn warm-up plans...")
    try:
        import pandas as pd
        if os.path.exists('data/jobs_today.csv'):
            from scripts.linkedin_warmup import generate_linkedin_search_targets
            jobs_df = pd.read_csv('data/jobs_today.csv')
            generate_linkedin_search_targets(jobs_df)
            print("✅ LinkedIn search targets generated")
        else:
            print("⚠️ No jobs file found, skipping LinkedIn warmup")
    except Exception as e:
        print(f"⚠️ LinkedIn warmup skipped: {e}")

def run_analytics_dashboard():
    """Phase 10: Multi-Channel Analytics"""
    print("📈 Generating analytics dashboard...")
    try:
        from scripts.multi_channel_analytics import AnalyticsDashboard, integrate_existing_logs
        integrate_existing_logs()
        dashboard = AnalyticsDashboard()
        dashboard.generate_dashboard_report()
        print("✅ Analytics dashboard generated")
    except Exception as e:
        print(f"⚠️ Analytics dashboard skipped: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("RUNNING ANALYSIS PHASES (8-10)")
    print("=" * 50)
    
    run_job_priority()
    print()
    run_linkedin_warmup()
    print()
    run_analytics_dashboard()
    
    print()
    print("=" * 50)
    print("ANALYSIS PHASES COMPLETE")
    print("=" * 50)
