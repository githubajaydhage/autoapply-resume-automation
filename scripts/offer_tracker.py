"""
Offer Comparison Tool - Compare and track job offers
Track salary, equity, benefits, and make informed decisions
"""

import pandas as pd
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class OfferTracker:
    """Track and compare job offers received"""
    
    def __init__(self):
        self.offers_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'offers.csv'
        )
        self.offers_df = self._load_offers()
    
    def _load_offers(self) -> pd.DataFrame:
        """Load offers from CSV"""
        if os.path.exists(self.offers_file):
            return pd.read_csv(self.offers_file)
        return pd.DataFrame(columns=[
            'company', 'job_title', 'hr_email', 'offer_date', 'base_salary',
            'equity_percent', 'signing_bonus', 'joining_date', 'status', 'user', 'notes'
        ])
    
    def add_offer(self, company: str, job_title: str, hr_email: str, base_salary: int,
                  equity_percent: float = 0, signing_bonus: int = 0, joining_date: str = '',
                  user: str = '', notes: str = ''):
        """Add a new offer"""
        new_offer = {
            'company': company,
            'job_title': job_title,
            'hr_email': hr_email,
            'offer_date': datetime.now().strftime('%Y-%m-%d'),
            'base_salary': base_salary,
            'equity_percent': equity_percent,
            'signing_bonus': signing_bonus,
            'joining_date': joining_date,
            'status': 'received',
            'user': user,
            'notes': notes
        }
        
        self.offers_df = pd.concat([
            self.offers_df,
            pd.DataFrame([new_offer])
        ], ignore_index=True)
        
        self.save()
        logging.info(f"✅ Offer added: {company} - {job_title} (${base_salary:,})")
    
    def update_status(self, company: str, status: str, notes: str = ''):
        """Update offer status (accepted, rejected, negotiating)"""
        mask = self.offers_df['company'].str.lower() == company.lower()
        if mask.any():
            self.offers_df.loc[mask, 'status'] = status
            if notes:
                self.offers_df.loc[mask, 'notes'] = notes
            self.save()
            logging.info(f"✅ Updated {company} status to: {status}")
    
    def get_comparison(self, user: str = None) -> pd.DataFrame:
        """Get comparison of all offers"""
        df = self.offers_df.copy()
        
        if user:
            df = df[df['user'].str.lower() == user.lower()]
        
        # Calculate total compensation (base + signing bonus for year 1)
        df['total_year1'] = df['base_salary'] + df['signing_bonus']
        df['salary_rank'] = df['base_salary'].rank(ascending=False)
        
        return df[['company', 'job_title', 'base_salary', 'equity_percent', 
                   'signing_bonus', 'total_year1', 'joining_date', 'status']]
    
    def show_summary(self, user: str = None):
        """Display offer summary"""
        logging.info("="*80)
        logging.info("💼 JOB OFFERS SUMMARY")
        logging.info("="*80)
        
        comparison = self.get_comparison(user)
        
        if comparison.empty:
            logging.info("No offers yet")
            return
        
        # Display table
        logging.info("\n📊 OFFERS COMPARISON:")
        for idx, row in comparison.iterrows():
            logging.info(f"\n{idx + 1}. {row['company']} - {row['job_title']}")
            logging.info(f"   💰 Base Salary: ${row['base_salary']:,}")
            logging.info(f"   📈 Equity: {row['equity_percent']}%")
            logging.info(f"   🎁 Signing Bonus: ${row['signing_bonus']:,}")
            logging.info(f"   💵 Total Year 1: ${row['total_year1']:,}")
            logging.info(f"   📅 Joining: {row['joining_date']}")
            logging.info(f"   ✅ Status: {row['status']}")
        
        # Best offer
        if not comparison.empty:
            best_idx = comparison['total_year1'].idxmax()
            best_offer = comparison.loc[best_idx]
            logging.info(f"\n🏆 HIGHEST OFFER: {best_offer['company']}")
            logging.info(f"   Total Year 1 Compensation: ${best_offer['total_year1']:,}")
        
        logging.info("="*80)
    
    def save(self):
        """Save offers to CSV"""
        self.offers_df.to_csv(self.offers_file, index=False)


def main():
    """Main function"""
    tracker = OfferTracker()
    
    # Show current offers
    tracker.show_summary()
    
    # Example: Add new offer
    # tracker.add_offer(
    #     company='Google',
    #     job_title='Senior Data Analyst',
    #     hr_email='careers@google.com',
    #     base_salary=180000,
    #     equity_percent=1.5,
    #     signing_bonus=50000,
    #     joining_date='2026-03-01',
    #     user='shweta',
    #     notes='Great offer with good growth'
    # )


if __name__ == "__main__":
    main()
