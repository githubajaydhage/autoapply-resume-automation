#!/usr/bin/env python3
"""
HR Data Merger - Smart data preservation across workflow runs
Ensures no data is lost and all HR emails are consolidated
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

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
        return merged_df
        
    elif existing_df is not None:
        # Only existing data, copy to new path
        existing_df.to_csv(new_path, index=False)
        print(f"   📋 Restored {len(existing_df)} existing records")
        return existing_df
        
    elif new_df is not None:
        print(f"   ✨ Keeping {len(new_df)} new records (no existing data)")
        return new_df
    else:
        print(f"   ⚠️ No data found for {file_name}")
        return None
    
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


def create_master_hr_database():
    """
    Create a consolidated master HR database from all sources.
    This is the SMART part - combines everything for maximum coverage.
    """
    print("\n" + "=" * 60)
    print("🧠 CREATING MASTER HR DATABASE (Smart Consolidation)")
    print("=" * 60)
    
    master_df = pd.DataFrame()
    
    # Collect from all HR email sources
    hr_sources = [
        ("curated_hr_emails.csv", "curated"),
        ("all_hr_emails.csv", "scraped"),
        ("discovered_hr_emails.csv", "discovered"),
        ("verified_hr_emails.csv", "verified"),
    ]
    
    for file_name, source_type in hr_sources:
        file_path = DATA_DIR / file_name
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                df['source'] = source_type
                df['added_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Normalize email column
                email_col = None
                for col in ['email', 'hr_email', 'Email', 'HR_Email', 'recipient_email']:
                    if col in df.columns:
                        email_col = col
                        break
                
                if email_col and email_col != 'email':
                    df = df.rename(columns={email_col: 'email'})
                
                if 'email' in df.columns:
                    master_df = pd.concat([master_df, df], ignore_index=True)
                    print(f"   ✅ Added {len(df)} from {file_name}")
            except Exception as e:
                print(f"   ⚠️ Could not load {file_name}: {e}")
    
    if not master_df.empty:
        # Deduplicate by email, keeping the most recent/verified
        priority = {'verified': 4, 'curated': 3, 'discovered': 2, 'scraped': 1}
        master_df['priority'] = master_df['source'].map(priority).fillna(0)
        master_df = master_df.sort_values('priority', ascending=False)
        master_df = master_df.drop_duplicates(subset=['email'], keep='first')
        master_df = master_df.drop(columns=['priority'])
        
        # Save master database
        master_path = DATA_DIR / "master_hr_database.csv"
        master_df.to_csv(master_path, index=False)
        print(f"\n   🎯 MASTER DATABASE: {len(master_df)} unique HR emails")
        print(f"   💾 Saved to: {master_path}")
        
        # Also update all_hr_emails.csv for backward compatibility
        all_hr_path = DATA_DIR / "all_hr_emails.csv"
        master_df.to_csv(all_hr_path, index=False)
        print(f"   📋 Updated all_hr_emails.csv for compatibility")
    
    return master_df


def get_emails_not_contacted():
    """
    SMART: Get HR emails that haven't been contacted yet.
    This ensures we don't waste time on already-contacted companies.
    """
    print("\n" + "=" * 60)
    print("🎯 FINDING NEW CONTACTS (Smart Filtering)")
    print("=" * 60)
    
    # Load master database
    master_path = DATA_DIR / "master_hr_database.csv"
    if not master_path.exists():
        master_path = DATA_DIR / "all_hr_emails.csv"
    
    if not master_path.exists():
        print("   ⚠️ No HR database found")
        return None
    
    master_df = pd.read_csv(master_path)
    total_emails = len(master_df)
    
    # Load sent emails log
    sent_path = DATA_DIR / "sent_emails_log.csv"
    sent_emails = set()
    if sent_path.exists():
        try:
            sent_df = pd.read_csv(sent_path)
            for col in ['recipient_email', 'email', 'hr_email']:
                if col in sent_df.columns:
                    sent_emails.update(sent_df[col].dropna().str.lower().tolist())
        except:
            pass
    
    # Load bounced emails
    bounced_path = DATA_DIR / "bounced_emails.csv"
    bounced_emails = set()
    if bounced_path.exists():
        try:
            bounced_df = pd.read_csv(bounced_path)
            for col in ['email', 'bounced_email']:
                if col in bounced_df.columns:
                    bounced_emails.update(bounced_df[col].dropna().str.lower().tolist())
        except:
            pass
    
    # Filter out already contacted and bounced
    if 'email' in master_df.columns:
        master_df['email_lower'] = master_df['email'].str.lower()
        not_contacted = master_df[~master_df['email_lower'].isin(sent_emails)]
        not_bounced = not_contacted[~not_contacted['email_lower'].isin(bounced_emails)]
        not_bounced = not_bounced.drop(columns=['email_lower'])
        
        # Save fresh contacts
        fresh_path = DATA_DIR / "fresh_hr_contacts.csv"
        not_bounced.to_csv(fresh_path, index=False)
        
        print(f"   📊 Total HR emails: {total_emails}")
        print(f"   📧 Already contacted: {len(sent_emails)}")
        print(f"   ❌ Bounced: {len(bounced_emails)}")
        print(f"   ✨ Fresh contacts: {len(not_bounced)}")
        print(f"   💾 Saved to: {fresh_path}")
        
        return not_bounced
    
    return master_df


def main():
    print("=" * 60)
    print("🔄 HR DATA MERGER - Smart Data Preservation")
    print("=" * 60)
    print(f"📅 Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create data directory if needed
    DATA_DIR.mkdir(exist_ok=True)
    
    # Step 1: Merge HR email files (dedupe by email)
    for file_name in MERGE_FILES:
        if "email" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['email', 'Email', 'hr_email', 'recipient_email'])
        elif "compan" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['company', 'Company', 'company_name'])
        elif "employee" in file_name.lower():
            merge_csv_files(file_name, dedupe_columns=['email', 'Email', 'employee_email'])
        else:
            merge_csv_files(file_name)
    
    # Step 2: Append log files (keep all records)
    for file_name in APPEND_FILES:
        append_csv_files(file_name)
    
    # Step 3: Create master HR database (SMART consolidation)
    master_df = create_master_hr_database()
    
    # Step 4: Get fresh contacts (not yet contacted)
    fresh_df = get_emails_not_contacted()
    
    print("\n" + "=" * 60)
    print("✅ SMART DATA MERGE COMPLETE!")
    print("=" * 60)
    
    # Summary
    print("\n📊 CURRENT DATA SUMMARY:")
    for file_name in ['master_hr_database.csv', 'fresh_hr_contacts.csv'] + MERGE_FILES + APPEND_FILES:
        file_path = DATA_DIR / file_name
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                print(f"   {file_name}: {len(df)} records")
            except:
                pass


if __name__ == "__main__":
    main()
