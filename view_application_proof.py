#!/usr/bin/env python3
"""
Application Proof Viewer

This script displays detailed proof of all job applications with:
- Application timestamps and success rates
- Platform-wise breakdown
- Company and job title details
- Evidence tracking (confirmations and errors)

Usage: python view_application_proof.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_proof_data():
    """Load application proof data"""
    # Try the complete pipeline proof file first
    proof_files = [
        Path("data/complete_pipeline_proof.json"),
        Path("data/application_proof.json")
    ]
    
    for proof_file in proof_files:
        if proof_file.exists():
            with open(proof_file, 'r') as f:
                return json.load(f)
    
    return None

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def display_proof_summary(data):
    """Display comprehensive proof summary"""
    session = data.get('session_info', {})
    summary = data.get('summary', {})
    
    print("📋 APPLICATION PROOF REPORT")
    print("=" * 50)
    print(f"Session ID:     {session.get('session_id', 'N/A')}")
    print(f"System:         {session.get('system_version', 'N/A')}")
    print(f"Timestamp:      {format_timestamp(session.get('timestamp', ''))}")
    print("")
    
    print("📊 SUMMARY STATISTICS")
    print("-" * 30)
    print(f"Total Applications:      {summary.get('total_applications', 0)}")
    print(f"Successful Applications:  {summary.get('successful_applications', 0)}")
    print(f"Failed Applications:      {summary.get('failed_applications', 0)}")
    
    if summary.get('total_applications', 0) > 0:
        success_rate = (summary.get('successful_applications', 0) / summary.get('total_applications', 1)) * 100
        print(f"Success Rate:            {success_rate:.1f}%")
    
    platforms = summary.get('platforms_used', [])
    if platforms:
        print(f"Platforms Used:          {', '.join(platforms)}")
    print("")

def display_application_details(data):
    """Display detailed application proof"""
    applications = data.get('applications', [])
    if not applications:
        print("❌ No application records found")
        return
    
    print("📝 DETAILED APPLICATION RECORDS")
    print("=" * 60)
    
    # Group by platform
    platform_apps = {}
    for app in applications:
        platform = app.get('platform', 'Unknown')
        if platform not in platform_apps:
            platform_apps[platform] = []
        platform_apps[platform].append(app)
    
    for platform, apps in platform_apps.items():
        successful_apps = [app for app in apps if app.get('success', False)]
        failed_apps = [app for app in apps if not app.get('success', False)]
        
        print(f"\n🌐 {platform.upper()} PLATFORM")
        print(f"   Applications: {len(apps)} | Success: {len(successful_apps)} | Failed: {len(failed_apps)}")
        print("-" * 50)
        
        for i, app in enumerate(apps, 1):
            status = "✅ SUCCESS" if app.get('success') else "❌ FAILED"
            timestamp = format_timestamp(app.get('timestamp', ''))
            company = app.get('company', 'Unknown Company')
            job_title = app.get('job_title', 'Unknown Position')
            
            print(f"  {i:2d}. {status} | {timestamp}")
            print(f"      Company: {company}")
            print(f"      Position: {job_title}")
            
            if app.get('details'):
                print(f"      Details: {app.get('details')}")
            print("")

def display_evidence_log(data):
    """Display evidence and proof tracking"""
    evidence = data.get('evidence', {})
    
    print("🔍 EVIDENCE & PROOF TRACKING")
    print("=" * 40)
    
    confirmations = evidence.get('confirmations', [])
    errors = evidence.get('errors', [])
    
    print(f"Confirmations: {len(confirmations)}")
    print(f"Error Records: {len(errors)}")
    
    if confirmations:
        print("\n✅ SUCCESSFUL APPLICATION CONFIRMATIONS")
        print("-" * 40)
        for conf in confirmations[:5]:  # Show first 5
            timestamp = format_timestamp(conf.get('timestamp', ''))
            method = conf.get('confirmation_method', 'Unknown')
            print(f"  • {timestamp} - {method}")
        
        if len(confirmations) > 5:
            print(f"  ... and {len(confirmations) - 5} more confirmations")
    
    if errors:
        print("\n❌ ERROR RECORDS")
        print("-" * 20)
        for error in errors[:3]:  # Show first 3
            timestamp = format_timestamp(error.get('timestamp', ''))
            error_type = error.get('error_type', 'Unknown error')
            print(f"  • {timestamp} - {error_type}")
        
        if len(errors) > 3:
            print(f"  ... and {len(errors) - 3} more errors")

def main():
    """Main proof viewer function"""
    print("🔍 APPLICATION PROOF VIEWER")
    print("=" * 40)
    print("Loading application proof data...")
    print("")
    
    data = load_proof_data()
    if not data:
        print("❌ No proof data found!")
        print("")
        print("To generate proof data:")
        print("  1. Run: python run_complete_pipeline.py")
        print("  2. Or run: python scripts/production_app_runner.py")
        return
    
    display_proof_summary(data)
    display_application_details(data)
    display_evidence_log(data)
    
    print("\n" + "=" * 60)
    print("📋 PROOF VERIFICATION COMPLETE")
    print("This report provides comprehensive evidence of all job applications")
    print("submitted through the automated system with timestamps and success tracking.")

if __name__ == "__main__":
    main()