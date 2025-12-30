#!/usr/bin/env python3
"""
HR Data Merger - Merges new data with existing data
Ensures no data is lost between workflow runs
"""

import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# Files to merge (append new rows, remove duplicates)
MERGE_FILES = [
    "all_hr_emails.csv",
    "discovered_hr_emails.csv",
    "curated_hr_emails.csv",
    "verified_hr_emails.csv",
    "discovered_companies.csv",
    "discovered_employees.csv",
]

# Files to append (keep all rows, used for logging)
APPEND_FILES = [
    "sent_emails_log.csv",
    "applied_log.csv",
    "followup_log.csv",
    "referral_requests_log.csv",
    "bounced_emails.csv",
]

def merge_csv_files(file_name: str, dedupe_columns: list = None):
    """Merge existing and new data, removing duplicates."""
    existing_path = DATA_DIR / f"existing_{file_name}"
    new_path = DATA_DIR / file_name
    
    print(f"\n📁 Processing {file_name}...")
    
    # Load existing data (from previous runs)
    existing_df = None
    if existing_path.exists():
        try:
            existing_df = pd.read_csv(existing_path)
            print(f"   ✅ Loaded {len(existing_df)} existing records")
        except Exception as e:
            print(f"   ⚠️ Could not load existing: {e}")
    
    # Load new data (from current run)
    new_df = None
    if new_path.exists():
        try:
            new_df = pd.read_csv(new_path)
            print(f"   ✅ Loaded {len(new_df)} new records")
        except Exception as e:
            print(f"   ⚠️ Could not load new: {e}")
    
    # Merge
    if existing_df is not None and new_df is not None:
        # Combine both
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Remove duplicates if dedupe columns specified
        if dedupe_columns:
            # Filter to columns that exist
            valid_cols = [c for c in dedupe_columns if c in merged_df.columns]
            if valid_cols:
                before_count = len(merged_df)
                merged_df = merged_df.drop_duplicates(subset=valid_cols, keep='last')
                after_count = len(merged_df)
                print(f"   🔄 Merged: {before_count} → {after_count} (removed {before_count - after_count} duplicates)")
        
        merged_df.to_csv(new_path, index=False)
        print(f"   💾 Saved {len(merged_df)} total records")
        
    elif existing_df is not None:
        # Only existing data, copy to new path
        existing_df.to_csv(new_path, index=False)
        print(f"   📋 Restored {len(existing_df)} existing records")
        
    elif new_df is not None:
        print(f"   ✨ Keeping {len(new_df)} new records (no existing data)")
    else:
        print(f"   ⚠️ No data found for {file_name}")
    
    # Clean up existing file
    if existing_path.exists():
        existing_path.unlink()


def append_csv_files(file_name: str):
    """Append new data to existing data (for log files)."""
    existing_path = DATA_DIR / f"existing_{file_name}"
    new_path = DATA_DIR / file_name
    
    print(f"\n📁 Appending {file_name}...")
    
    # Load existing data
    existing_df = None
    if existing_path.exists():
        try:
            existing_df = pd.read_csv(existing_path)
            print(f"   ✅ Loaded {len(existing_df)} existing records")
        except Exception as e:
            print(f"   ⚠️ Could not load existing: {e}")
    
    # Load new data
    new_df = None
    if new_path.exists():
        try:
            new_df = pd.read_csv(new_path)
            print(f"   ✅ Loaded {len(new_df)} new records")
        except Exception as e:
            print(f"   ⚠️ Could not load new: {e}")
    
    # Append
    if existing_df is not None and new_df is not None:
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        merged_df.to_csv(new_path, index=False)
        print(f"   💾 Total: {len(merged_df)} records")
        
    elif existing_df is not None:
        existing_df.to_csv(new_path, index=False)
        print(f"   📋 Restored {len(existing_df)} existing records")
        
    elif new_df is not None:
        print(f"   ✨ Keeping {len(new_df)} new records")
    
    # Clean up
    if existing_path.exists():
        existing_path.unlink()


def main():
    print("=" * 60)
    print("🔄 HR DATA MERGER - Preserving all collected data")
    print("=" * 60)
    
    # Create data directory if needed
    DATA_DIR.mkdir(exist_ok=True)
    
    # Merge HR email files (dedupe by email)
    for file_name in MERGE_FILES:
        if "email" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['email', 'Email', 'hr_email', 'recipient_email'])
        elif "compan" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['company', 'Company', 'company_name'])
        elif "employee" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['email', 'Email', 'employee_email'])
        else:
            merge_csv_files(file_name)
    
    # Append log files (keep all records)
    for file_name in APPEND_FILES:
        append_csv_files(file_name)
    
    print("\n" + "=" * 60)
    print("✅ Data merge complete!")
    print("=" * 60)
    
    # Summary
    print("\n📊 CURRENT DATA SUMMARY:")
    for file_name in MERGE_FILES + APPEND_FILES:
        file_path = DATA_DIR / file_name
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                print(f"   {file_name}: {len(df)} records")
            except:
                pass


if __name__ == "__main__":
    main()
