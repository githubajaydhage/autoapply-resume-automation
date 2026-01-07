"""
Add Bounced Emails to Database

This script allows you to manually add bounced email addresses to the database
so they will be skipped in future email campaigns.

Usage:
    python add_bounced_emails.py email1@example.com email2@example.com
    
    Or run interactively without arguments.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def add_bounced_emails(emails: list, reason: str = "Manually added - undeliverable"):
    """Add emails to the bounced emails database."""
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    bounce_file = os.path.join(data_dir, 'bounced_emails.csv')
    
    if not emails:
        print("❌ No emails provided!")
        return
    
    # Prepare records
    records = []
    for email in emails:
        email = email.strip().lower()
        if email and '@' in email:
            records.append({
                'email': email,
                'company': 'Unknown',
                'reason': reason,
                'bounce_date': datetime.now().strftime('%Y-%m-%d'),
                'detected_at': datetime.now().isoformat(),
                'source': 'manual_addition'
            })
    
    if not records:
        print("❌ No valid emails found!")
        return
    
    df_new = pd.DataFrame(records)
    
    # Load existing and merge
    if os.path.exists(bounce_file):
        df_existing = pd.read_csv(bounce_file)
        if not df_existing.empty:
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['email'], keep='last')
        else:
            df_combined = df_new
    else:
        df_combined = df_new
    
    df_combined.to_csv(bounce_file, index=False)
    
    print(f"✅ Added {len(records)} emails to bounced database")
    print(f"📄 Database location: {bounce_file}")
    print(f"📊 Total blocked emails: {len(df_combined)}")
    print("\nThese emails will be SKIPPED in future email campaigns:")
    for email in emails[:10]:
        print(f"   🚫 {email}")
    if len(emails) > 10:
        print(f"   ... and {len(emails) - 10} more")


def sync_from_sent_log():
    """Sync all bounced emails from sent_emails_log.csv"""
    from scripts.bounce_checker import BounceChecker
    
    checker = BounceChecker()
    synced = checker.sync_bounced_from_sent_log()
    print(f"✅ Synced {synced} bounced emails from sent log")


def show_bounced_emails():
    """Display all bounced emails in the database."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    bounce_file = os.path.join(data_dir, 'bounced_emails.csv')
    
    if not os.path.exists(bounce_file):
        print("❌ No bounced emails database found!")
        return
    
    df = pd.read_csv(bounce_file)
    print(f"\n📊 BOUNCED EMAILS DATABASE ({len(df)} emails)")
    print("="*60)
    
    for _, row in df.iterrows():
        print(f"🚫 {row['email']}")
        print(f"   Company: {row.get('company', 'Unknown')}")
        print(f"   Reason: {row.get('reason', 'Unknown')}")
        print(f"   Date: {row.get('bounce_date', 'Unknown')}")
        print()


def main():
    """Main function."""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--sync':
            sync_from_sent_log()
        elif sys.argv[1] == '--show':
            show_bounced_emails()
        else:
            # Add emails from command line
            emails = sys.argv[1:]
            add_bounced_emails(emails)
    else:
        # Interactive mode
        print("="*60)
        print("📧 BOUNCED EMAIL MANAGER")
        print("="*60)
        print("\nOptions:")
        print("  1. Add bounced emails manually")
        print("  2. Sync bounced emails from sent log")
        print("  3. Show all bounced emails")
        print("  4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\nEnter bounced email addresses (one per line, empty line to finish):")
            emails = []
            while True:
                email = input("> ").strip()
                if not email:
                    break
                emails.append(email)
            
            if emails:
                reason = input("\nEnter reason (or press Enter for default): ").strip()
                if not reason:
                    reason = "Mail Delivery Subsystem - Undeliverable"
                add_bounced_emails(emails, reason)
            else:
                print("No emails entered!")
                
        elif choice == '2':
            sync_from_sent_log()
            
        elif choice == '3':
            show_bounced_emails()
            
        elif choice == '4':
            print("Goodbye!")
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
