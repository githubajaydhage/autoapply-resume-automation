try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    
import logging
import sys
import csv
from applicators.linkedin import LinkedInApplicator
from applicators.indeed import IndeedApplicator
from applicators.naukri import NaukriApplicator
from applicators.company_careers import CompanyCareersApplicator
from scripts.intelligent_job_research import IntelligentJobResearcher
from utils.config import JOBS_CSV_PATH, PORTAL_CONFIGS, COMPANY_CAREERS

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/main.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main orchestrator with intelligent job research and prioritization."""
    logging.info("🚀 Starting Intelligent Job Application System")
    
    # STEP 1: Research Latest Openings Intelligently
    logging.info("🔍 Phase 1: Researching latest job openings...")
    researcher = IntelligentJobResearcher()
    prioritized_opportunities = researcher.research_and_prioritize()
    
    if not prioritized_opportunities:
        logging.warning("No opportunities found during intelligent research")
        return
        
    # Save research results
    researcher.save_research_results(prioritized_opportunities, "data/intelligent_research_results.json")
    
    # STEP 2: Convert opportunities to jobs data structure
    logging.info(f"📊 Phase 2: Converting {len(prioritized_opportunities)} opportunities to application format")
    
    jobs_data = []
    for opp in prioritized_opportunities:
        job_record = {
            'title': opp.title,
            'company': opp.company,
            'location': opp.location,
            'link': opp.url,
            'posted_date': opp.posted_date,
            'source': opp.source,
            'portal': opp.source,
            'priority_score': opp.priority_score,
            'company_tier': opp.company_tier,
            'keywords_match': ','.join(opp.keywords_match),
            'fresh_score': opp.fresh_score
        }
        jobs_data.append(job_record)
    
    # Save to CSV for backup
    if HAS_PANDAS:
        jobs_df = pd.DataFrame(jobs_data)
        jobs_df.to_csv("data/prioritized_jobs_today.csv", index=False)
    else:
        # Save using csv module
        with open("data/prioritized_jobs_today.csv", 'w', newline='', encoding='utf-8') as f:
            if jobs_data:
                fieldnames = jobs_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs_data)
                
    logging.info("💾 Saved prioritized jobs to data/prioritized_jobs_today.csv")
    
    # STEP 3: Group by portal and apply intelligently
    logging.info("🎯 Phase 3: Applying to prioritized opportunities")
    
    jobs_by_portal = {}
    
    # Group by source/portal
    for job in jobs_data:
        portal = job['portal']
        if portal not in jobs_by_portal:
            jobs_by_portal[portal] = []
        jobs_by_portal[portal].append(job)
    
    # Sort each portal's jobs by priority score (highest first)
    for portal in jobs_by_portal:
        jobs_by_portal[portal] = sorted(jobs_by_portal[portal], 
                                       key=lambda x: x['priority_score'], 
                                       reverse=True)
    
    if not jobs_by_portal:
        logging.info("No jobs found after intelligent research.")
        return

    # STEP 4: Apply with prioritization
    total_applications = 0
    
    # Instantiate applicators
    applicators = {
        "linkedin": LinkedInApplicator(),
        "indeed": IndeedApplicator(),
        "naukri": NaukriApplicator(),
    }

    # Apply to jobs in priority order
    for portal, jobs in jobs_by_portal.items():
        logging.info(f"📋 Processing {portal}: {len(jobs)} prioritized opportunities")
        
        if portal in applicators:
            applicator = applicators[portal]
            applied_count = applicator.run(jobs)
            total_applications += applied_count or 0
            
        elif portal.startswith("company_") or "_careers" in portal:
            # Handle company career pages
            company_key = portal.replace("company_", "").replace("_careers", "")
            logging.info(f"🏢 Processing company career page: {company_key}")
            
            from utils.browser_manager import BrowserManager
            import os
            user_data_dir = os.path.join(os.getcwd(), "browser_data", company_key)
            os.makedirs(user_data_dir, exist_ok=True)
            
            with BrowserManager(user_data_dir, headless=True) as page:
                applicator = CompanyCareersApplicator(page, company_key)
                applied_count = applicator.run(jobs)
                total_applications += applied_count or 0
                
        else:
            logging.warning(f"⚠️  No applicator found for portal: {portal}")

    # STEP 5: Summary Report
    logging.info(f"✅ INTELLIGENT APPLICATION SESSION COMPLETE")
    logging.info(f"📊 Total opportunities researched: {len(prioritized_opportunities)}")
    logging.info(f"🎯 Total applications submitted: {total_applications}")
    logging.info(f"📈 Success rate: {(total_applications/len(prioritized_opportunities)*100):.1f}%")
    
    # Show top applications
    logging.info("🏆 Top applications submitted:")
    for i, job in enumerate(jobs_data[:10]):
        tier_emoji = "🥇" if job['company_tier'] == 'tier1' else "🥈" if job['company_tier'] == 'tier2' else "🥉"
        logging.info(f"  {i+1:2d}. {tier_emoji} {job['company']:15s} - {job['title']:30s} (Score: {job['priority_score']:5.1f})")

    logging.info("🚀 Intelligent Job Application System Complete!")

if __name__ == "__main__":
    main()
