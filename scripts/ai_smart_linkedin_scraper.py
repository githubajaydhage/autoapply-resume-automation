"""
🤖 AI-Powered LinkedIn Scraper - Intelligent Hiring Manager Discovery

Uses AI to:
1. Find hiring managers from LinkedIn company pages
2. Analyze job post engagement and competition
3. Extract company hiring insights and patterns
4. Predict best outreach timing and approach
5. Identify key employees for referrals

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import get_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AILinkedInScraper:
    """
    🤖 AI-powered LinkedIn scraper for intelligent hiring manager discovery.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Initialize AI
        self.ai = get_ai() if AI_AVAILABLE else None
        if not self.ai:
            logging.warning("⚠️ AI not available - using fallback methods")
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Output files
        self.hiring_managers_path = os.path.join(self.data_path, 'ai_linkedin_hiring_managers.csv')
        self.company_insights_path = os.path.join(self.data_path, 'ai_company_hiring_insights.json')
        
        logging.info("🤖 AI LinkedIn Scraper initialized")
    
    def ai_find_hiring_managers(self, company_name: str, job_title: str = None, department: str = None) -> List[Dict]:
        """
        🤖 AI identifies likely hiring managers for a company.
        """
        if not self.ai:
            return self._fallback_hiring_roles(company_name)
        
        try:
            prompt = f"""Company: {company_name}
Job Title: {job_title or 'Software Engineer'}
Department: {department or 'Engineering'}

Based on this company and role, identify the most likely hiring managers and decision makers:

1. Who would typically hire for this role?
2. What job titles would these people have?
3. What departments would they be in?
4. How should I prioritize outreach?

Respond in JSON format:
{{
  "primary_hiring_roles": [
    {{"title": "Engineering Manager", "department": "Engineering", "priority": 1}},
    {{"title": "Head of Engineering", "department": "Engineering", "priority": 2}}
  ],
  "secondary_contacts": [
    {{"title": "HR Business Partner", "department": "HR", "priority": 3}},
    {{"title": "Technical Recruiter", "department": "HR", "priority": 4}}
  ],
  "outreach_strategy": "Start with direct managers, then HR",
  "best_approach": "LinkedIn message with technical project mention"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=500)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        hiring_info = json.loads(json_match.group())
                        logging.info(f"🎯 AI identified {len(hiring_info.get('primary_hiring_roles', []))} primary hiring roles for {company_name}")
                        return hiring_info
                except:
                    pass
            
            return self._fallback_hiring_roles(company_name)
            
        except Exception as e:
            logging.warning(f"⚠️ AI hiring manager analysis failed: {e}")
            return self._fallback_hiring_roles(company_name)
    
    def _fallback_hiring_roles(self, company_name: str) -> Dict:
        """Fallback hiring roles when AI fails."""
        return {
            "primary_hiring_roles": [
                {"title": "Engineering Manager", "department": "Engineering", "priority": 1},
                {"title": "Senior Software Engineer", "department": "Engineering", "priority": 2},
                {"title": "Tech Lead", "department": "Engineering", "priority": 3}
            ],
            "secondary_contacts": [
                {"title": "Technical Recruiter", "department": "HR", "priority": 4},
                {"title": "HR Manager", "department": "HR", "priority": 5}
            ],
            "outreach_strategy": "Direct technical contacts first",
            "best_approach": "LinkedIn message"
        }
    
    def ai_analyze_job_post_engagement(self, job_post_content: str, company: str) -> Dict:
        """
        🤖 AI predicts job post response rate and competition level.
        """
        if not self.ai:
            return {'competition': 'medium', 'response_rate': 'medium', 'insights': 'AI not available'}
        
        try:
            prompt = f"""Job Post Analysis:
Company: {company}
Content: {job_post_content[:2000]}

Analyze this job posting for:
1. Competition level (how many people will apply)
2. Expected response rate if I apply
3. Urgency indicators
4. Quality indicators
5. Red flags or positives

Respond in JSON:
{{
  "competition_level": "low|medium|high",
  "expected_response_rate": "low|medium|high", 
  "urgency_score": 7,
  "quality_indicators": ["clear requirements", "growth opportunities"],
  "red_flags": ["unrealistic expectations"],
  "best_application_timing": "immediately|within_week|no_rush",
  "application_advice": "specific advice for this job",
  "estimated_applicants": 50
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=400)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        logging.info(f"📊 AI job analysis: {analysis.get('competition_level')} competition, {analysis.get('expected_response_rate')} response rate")
                        return analysis
                except:
                    pass
            
            return {'competition_level': 'medium', 'expected_response_rate': 'medium', 'urgency_score': 5, 'insights': 'Standard job posting'}
            
        except Exception as e:
            logging.warning(f"⚠️ AI job engagement analysis failed: {e}")
            return {'competition_level': 'medium', 'expected_response_rate': 'medium', 'error': str(e)}
    
    def ai_extract_company_insights(self, company_linkedin_url: str, company_name: str) -> Dict:
        """
        🤖 AI extracts hiring patterns and company insights.
        """
        try:
            # Try to scrape company page (public info only)
            company_info = self._scrape_company_public_info(company_linkedin_url)
            
            if not self.ai:
                return company_info
            
            prompt = f"""Company Analysis:
Company: {company_name}
LinkedIn URL: {company_linkedin_url}
Available Info: {json.dumps(company_info, indent=2)}

Analyze hiring patterns and provide insights:
1. Company growth stage
2. Hiring frequency and patterns
3. Employee satisfaction indicators  
4. Best times to apply
5. Company culture insights
6. Typical hiring process

Respond in JSON:
{{
  "growth_stage": "startup|growth|mature|enterprise",
  "hiring_frequency": "high|medium|low",
  "best_application_months": ["January", "September"],
  "avg_hiring_process_days": 21,
  "company_culture": "fast-paced|collaborative|traditional",
  "employee_satisfaction": "high|medium|low",
  "hiring_challenges": ["high competition", "specific skills needed"],
  "success_tips": ["mention specific technologies", "show portfolio"],
  "contact_preferences": "email|linkedin|referral"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=600)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        insights = json.loads(json_match.group())
                        insights.update(company_info)  # Merge with scraped data
                        
                        # Save insights
                        self._save_company_insights(company_name, insights)
                        
                        logging.info(f"🏢 AI company insights: {insights.get('growth_stage')} stage, {insights.get('hiring_frequency')} hiring")
                        return insights
                except:
                    pass
            
            return company_info
            
        except Exception as e:
            logging.warning(f"⚠️ AI company insights failed: {e}")
            return {'company': company_name, 'error': str(e)}
    
    def _scrape_company_public_info(self, linkedin_url: str) -> Dict:
        """Scrape basic public company information."""
        try:
            # This would scrape public company info
            # For now, return basic structure
            return {
                'url': linkedin_url,
                'scraped_at': datetime.now().isoformat(),
                'employee_count': 'unknown',
                'industry': 'unknown',
                'founded': 'unknown'
            }
        except:
            return {}
    
    def _save_company_insights(self, company_name: str, insights: Dict):
        """Save company insights to JSON file."""
        try:
            # Load existing insights
            existing_insights = {}
            if os.path.exists(self.company_insights_path):
                with open(self.company_insights_path, 'r', encoding='utf-8') as f:
                    existing_insights = json.load(f)
            
            # Update with new insights
            existing_insights[company_name.lower()] = {
                **insights,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save back
            with open(self.company_insights_path, 'w', encoding='utf-8') as f:
                json.dump(existing_insights, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.warning(f"Failed to save insights for {company_name}: {e}")
    
    def ai_generate_outreach_strategy(self, company: str, job_title: str, hiring_manager_info: Dict) -> Dict:
        """
        🤖 AI generates personalized outreach strategy.
        """
        if not self.ai:
            return {'approach': 'standard', 'message': 'Standard LinkedIn message recommended'}
        
        try:
            prompt = f"""Outreach Strategy Planning:
Company: {company}
Job: {job_title}
Hiring Manager Info: {json.dumps(hiring_manager_info, indent=2)}

Create a personalized outreach strategy:
1. Best contact method
2. Optimal timing
3. Message tone and content
4. Follow-up schedule
5. Value proposition to highlight

Respond in JSON:
{{
  "best_method": "linkedin|email|referral",
  "optimal_timing": "morning|afternoon|evening",
  "message_tone": "professional|casual|technical",
  "key_points": ["point1", "point2"],
  "subject_line": "Great subject line",
  "follow_up_days": [3, 7, 14],
  "success_probability": 65,
  "personalization_tips": ["tip1", "tip2"]
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=500)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        strategy = json.loads(json_match.group())
                        logging.info(f"📝 AI outreach strategy: {strategy.get('success_probability', 'unknown')}% success probability")
                        return strategy
                except:
                    pass
            
            return {
                'best_method': 'linkedin',
                'optimal_timing': 'morning',
                'message_tone': 'professional',
                'key_points': ['Relevant experience', 'Interest in role'],
                'success_probability': 50
            }
            
        except Exception as e:
            logging.warning(f"⚠️ AI outreach strategy failed: {e}")
            return {'approach': 'standard', 'error': str(e)}
    
    def process_companies_for_hiring_insights(self, companies: List[str], job_titles: List[str] = None) -> pd.DataFrame:
        """
        Process multiple companies to extract hiring insights and manager info.
        """
        if not job_titles:
            job_titles = ['Software Engineer', 'Data Analyst', 'Product Manager']
        
        all_insights = []
        
        logging.info(f"🔍 Processing {len(companies)} companies for AI hiring insights...")
        
        for company in companies:
            for job_title in job_titles:
                try:
                    # Get hiring manager info
                    hiring_info = self.ai_find_hiring_managers(company, job_title)
                    
                    # Get company insights
                    company_url = f"https://linkedin.com/company/{company.lower().replace(' ', '-')}"
                    company_insights = self.ai_extract_company_insights(company_url, company)
                    
                    # Generate outreach strategy
                    outreach_strategy = self.ai_generate_outreach_strategy(company, job_title, hiring_info)
                    
                    # Combine all insights
                    insight_record = {
                        'company': company,
                        'job_title': job_title,
                        'primary_hiring_roles': len(hiring_info.get('primary_hiring_roles', [])),
                        'growth_stage': company_insights.get('growth_stage', 'unknown'),
                        'hiring_frequency': company_insights.get('hiring_frequency', 'unknown'),
                        'best_contact_method': outreach_strategy.get('best_method', 'linkedin'),
                        'success_probability': outreach_strategy.get('success_probability', 50),
                        'optimal_timing': outreach_strategy.get('optimal_timing', 'morning'),
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
                    all_insights.append(insight_record)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logging.warning(f"Failed to process {company} - {job_title}: {e}")
                    continue
        
        # Create DataFrame
        insights_df = pd.DataFrame(all_insights)
        
        # Save results
        if not insights_df.empty:
            output_path = os.path.join(self.data_path, 'ai_linkedin_insights.csv')
            insights_df.to_csv(output_path, index=False)
            logging.info(f"💾 Saved {len(insights_df)} AI insights to {output_path}")
        
        return insights_df


def main():
    """Main function for testing AI LinkedIn scraper."""
    scraper = AILinkedInScraper()
    
    # Test companies
    test_companies = ['Microsoft', 'Google', 'Amazon', 'Meta', 'Apple']
    test_jobs = ['Software Engineer', 'Data Scientist']
    
    # Process companies
    results_df = scraper.process_companies_for_hiring_insights(test_companies, test_jobs)
    
    if not results_df.empty:
        print(f"\n🎯 AI LinkedIn Analysis Results:")
        print(f"   Companies analyzed: {results_df['company'].nunique()}")
        print(f"   Job titles: {results_df['job_title'].nunique()}")
        print(f"   Average success probability: {results_df['success_probability'].mean():.1f}%")
        print(f"\n📊 Best contact methods:")
        print(results_df['best_contact_method'].value_counts())


if __name__ == "__main__":
    main()