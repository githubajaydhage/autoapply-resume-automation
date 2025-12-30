"""
🔍 AI JOB RESEARCH ENGINE - Find Latest Openings Using AI

Uses FREE AI to:
1. Discover trending job sources and portals
2. Generate smart search queries for each role
3. Extract job requirements from descriptions
4. Find hidden job boards and company career pages
5. Analyze job market trends
6. Identify emerging companies hiring

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import csv
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import get_ai, FreeAIManager
except ImportError:
    from free_ai_providers import get_ai, FreeAIManager

from utils.config import USER_DETAILS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AIJobResearcher:
    """
    🔍 AI-Powered Job Research Engine
    
    Uses LLMs to intelligently find and analyze job opportunities.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Initialize AI
        self.ai = get_ai()
        
        # User info
        self.role = USER_DETAILS.get('specific_role') or os.getenv('JOB_TITLE', os.getenv('APPLICANT_ROLE', 'Software Engineer'))
        self.skills = USER_DETAILS.get('key_skills') or os.getenv('JOB_KEYWORDS', 'Python, SQL, Data Analysis')
        self.location = os.getenv('JOB_LOCATION', 'India')
        self.experience = USER_DETAILS.get('years_experience') or os.getenv('YEARS_EXPERIENCE', '3')
        
        # Research cache
        self.cache_path = os.path.join(self.data_path, 'ai_research_cache.json')
        self.cache = self._load_cache()
        
        logging.info(f"🔍 AI Job Researcher initialized for: {self.role}")
    
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'job_sources': [], 'search_queries': [], 'last_updated': ''}
    
    def _save_cache(self):
        self.cache['last_updated'] = datetime.now().isoformat()
        try:
            os.makedirs(self.data_path, exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logging.warning(f"Cache save failed: {e}")
    
    def discover_job_sources(self) -> List[Dict]:
        """
        🌐 Use AI to discover job sources specific to the role.
        """
        logging.info("🔍 Discovering job sources with AI...")
        
        prompt = f"""You are a job search expert. Find the BEST job sources for this role:

ROLE: {self.role}
SKILLS: {self.skills}
LOCATION: {self.location}
EXPERIENCE: {self.experience} years

List 15 job sources in this exact JSON format (no other text):
[
  {{"name": "Source Name", "url": "https://...", "type": "job_board|company_careers|aggregator|niche", "relevance": "high|medium", "has_api": true|false}},
  ...
]

Include:
1. Major job boards (LinkedIn, Indeed, Naukri)
2. Niche job boards for this specific role
3. Tech company career pages if relevant
4. Startup job platforms
5. Remote work platforms
6. India-specific platforms if location is India

IMPORTANT: Return ONLY valid JSON array, no explanation."""

        result = self.ai.generate(prompt, max_tokens=1000)
        
        sources = []
        if result:
            try:
                # Extract JSON from response
                json_match = re.search(r'\[[\s\S]*\]', result)
                if json_match:
                    sources = json.loads(json_match.group())
                    logging.info(f"✅ Discovered {len(sources)} job sources")
            except json.JSONDecodeError as e:
                logging.warning(f"JSON parse error: {e}")
        
        # Add default sources if AI fails
        if not sources:
            sources = self._get_default_sources()
        
        self.cache['job_sources'] = sources
        self._save_cache()
        
        return sources
    
    def _get_default_sources(self) -> List[Dict]:
        """Default job sources as fallback."""
        return [
            {'name': 'LinkedIn Jobs', 'url': 'https://www.linkedin.com/jobs/', 'type': 'job_board', 'relevance': 'high', 'has_api': False},
            {'name': 'Indeed India', 'url': 'https://www.indeed.co.in/', 'type': 'job_board', 'relevance': 'high', 'has_api': True},
            {'name': 'Naukri', 'url': 'https://www.naukri.com/', 'type': 'job_board', 'relevance': 'high', 'has_api': False},
            {'name': 'RemoteOK', 'url': 'https://remoteok.com/', 'type': 'aggregator', 'relevance': 'high', 'has_api': True},
            {'name': 'Wellfound (AngelList)', 'url': 'https://wellfound.com/', 'type': 'startup', 'relevance': 'high', 'has_api': False},
            {'name': 'Instahyre', 'url': 'https://www.instahyre.com/', 'type': 'job_board', 'relevance': 'high', 'has_api': False},
            {'name': 'Cutshort', 'url': 'https://cutshort.io/', 'type': 'niche', 'relevance': 'high', 'has_api': False},
            {'name': 'Hirist', 'url': 'https://www.hirist.tech/', 'type': 'niche', 'relevance': 'medium', 'has_api': False},
            {'name': 'Arbeitnow', 'url': 'https://arbeitnow.com/', 'type': 'aggregator', 'relevance': 'medium', 'has_api': True},
            {'name': 'Jobicy', 'url': 'https://jobicy.com/', 'type': 'remote', 'relevance': 'medium', 'has_api': True},
        ]
    
    def generate_search_queries(self) -> List[Dict]:
        """
        🔎 Use AI to generate optimized search queries.
        """
        logging.info("🔎 Generating AI-optimized search queries...")
        
        prompt = f"""You are a job search optimization expert. Generate search queries for:

ROLE: {self.role}
SKILLS: {self.skills}
LOCATION: {self.location}
EXPERIENCE: {self.experience} years

Generate 20 search query variations in JSON format:
[
  {{"query": "search string", "platform": "linkedin|indeed|naukri|google|all", "intent": "exact_role|related_role|skill_based|company_type"}},
  ...
]

Include:
1. Exact role title variations
2. Related roles they might list under
3. Skill-based searches (e.g., "Python developer")
4. Company type searches (e.g., "startup data analyst")
5. Seniority variations (junior, mid, senior)
6. Industry-specific queries

Return ONLY valid JSON array."""

        result = self.ai.generate(prompt, max_tokens=1000)
        
        queries = []
        if result:
            try:
                json_match = re.search(r'\[[\s\S]*\]', result)
                if json_match:
                    queries = json.loads(json_match.group())
                    logging.info(f"✅ Generated {len(queries)} search queries")
            except:
                pass
        
        # Default queries
        if not queries:
            queries = [
                {'query': self.role, 'platform': 'all', 'intent': 'exact_role'},
                {'query': f'{self.role} {self.location}', 'platform': 'all', 'intent': 'exact_role'},
                {'query': self.skills.split(',')[0].strip(), 'platform': 'all', 'intent': 'skill_based'},
            ]
        
        self.cache['search_queries'] = queries
        self._save_cache()
        
        return queries
    
    def analyze_job_description(self, job_description: str) -> Dict:
        """
        📊 Use AI to deeply analyze a job description.
        """
        prompt = f"""Analyze this job description and extract structured information:

JOB DESCRIPTION:
{job_description[:3000]}

Return JSON with:
{{
  "title": "exact job title",
  "company": "company name if mentioned",
  "location": "location or remote",
  "experience_required": "X-Y years",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "responsibilities": ["resp1", "resp2"],
  "benefits": ["benefit1", "benefit2"],
  "salary_range": "if mentioned",
  "job_type": "full-time|part-time|contract",
  "urgency": "high|medium|low",
  "match_score_for_you": 0-100,
  "missing_skills": ["skills you might need to learn"],
  "application_tips": ["tip1", "tip2"]
}}

MY PROFILE:
- Skills: {self.skills}
- Experience: {self.experience} years
- Target Role: {self.role}

Return ONLY valid JSON."""

        result = self.ai.generate(prompt, max_tokens=800)
        
        if result:
            try:
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {'error': 'Analysis failed'}
    
    def find_emerging_companies(self) -> List[Dict]:
        """
        🚀 Use AI to find companies actively hiring for this role.
        """
        logging.info("🚀 Finding emerging companies with AI...")
        
        prompt = f"""You are a tech industry analyst. Find companies ACTIVELY HIRING for:

ROLE: {self.role}
LOCATION: {self.location}
SKILLS: {self.skills}

List 20 companies in JSON format:
[
  {{
    "company": "Company Name",
    "industry": "Tech/Finance/etc",
    "size": "startup|mid|enterprise",
    "hiring_intensity": "high|medium",
    "career_page": "https://...",
    "why_good_fit": "brief reason",
    "glassdoor_rating": "4.2"
  }},
  ...
]

Focus on:
1. Companies known to be actively hiring in {datetime.now().strftime('%B %Y')}
2. Startups with recent funding
3. Tech giants with constant openings
4. Companies in {self.location}
5. Remote-friendly companies

Return ONLY valid JSON array."""

        result = self.ai.generate(prompt, max_tokens=1500)
        
        companies = []
        if result:
            try:
                json_match = re.search(r'\[[\s\S]*\]', result)
                if json_match:
                    companies = json.loads(json_match.group())
                    logging.info(f"✅ Found {len(companies)} hiring companies")
            except:
                pass
        
        # Save to file
        if companies:
            output_path = os.path.join(self.data_path, 'ai_discovered_companies.json')
            with open(output_path, 'w') as f:
                json.dump(companies, f, indent=2)
            logging.info(f"💾 Saved to {output_path}")
        
        return companies
    
    def get_market_insights(self) -> Dict:
        """
        📈 Get AI-powered job market insights.
        """
        logging.info("📈 Getting market insights...")
        
        prompt = f"""You are a job market analyst. Provide insights for:

ROLE: {self.role}
LOCATION: {self.location}
SKILLS: {self.skills}

Return JSON with current market insights (December 2025):
{{
  "demand_level": "high|medium|low",
  "salary_range_india": "₹X-Y LPA",
  "salary_range_remote": "$X-Y/year",
  "trending_skills": ["skill1", "skill2", "skill3"],
  "declining_skills": ["skill1", "skill2"],
  "hot_industries": ["industry1", "industry2"],
  "remote_availability": "percentage of jobs that are remote",
  "competition_level": "high|medium|low",
  "best_time_to_apply": "recommendation",
  "tips_for_success": ["tip1", "tip2", "tip3"],
  "certifications_that_help": ["cert1", "cert2"]
}}

Be specific and actionable. Return ONLY valid JSON."""

        result = self.ai.generate(prompt, max_tokens=600)
        
        if result:
            try:
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    insights = json.loads(json_match.group())
                    
                    # Save insights
                    output_path = os.path.join(self.data_path, 'market_insights.json')
                    with open(output_path, 'w') as f:
                        json.dump(insights, f, indent=2)
                    
                    return insights
            except:
                pass
        
        return {'error': 'Could not generate insights'}
    
    def run_full_research(self) -> Dict:
        """
        🎯 Run complete AI-powered job research.
        """
        logging.info("\n" + "="*60)
        logging.info("🔍 STARTING AI-POWERED JOB RESEARCH")
        logging.info("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'role': self.role,
            'sources': [],
            'queries': [],
            'companies': [],
            'insights': {}
        }
        
        # 1. Discover job sources
        print("\n📡 Step 1: Discovering job sources...")
        results['sources'] = self.discover_job_sources()
        
        # 2. Generate search queries
        print("\n🔎 Step 2: Generating search queries...")
        results['queries'] = self.generate_search_queries()
        
        # 3. Find hiring companies
        print("\n🚀 Step 3: Finding hiring companies...")
        results['companies'] = self.find_emerging_companies()
        
        # 4. Get market insights
        print("\n📈 Step 4: Analyzing market trends...")
        results['insights'] = self.get_market_insights()
        
        # Save complete research
        output_path = os.path.join(self.data_path, 'ai_job_research.json')
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict):
        """Print research summary."""
        print("\n" + "="*60)
        print("🎯 AI JOB RESEARCH COMPLETE")
        print("="*60)
        
        print(f"\n📡 Job Sources Found: {len(results.get('sources', []))}")
        for s in results.get('sources', [])[:5]:
            print(f"   • {s.get('name', 'Unknown')} ({s.get('relevance', 'unknown')} relevance)")
        
        print(f"\n🔎 Search Queries Generated: {len(results.get('queries', []))}")
        for q in results.get('queries', [])[:3]:
            print(f"   • \"{q.get('query', '')}\" ({q.get('intent', 'general')})")
        
        print(f"\n🚀 Companies Identified: {len(results.get('companies', []))}")
        for c in results.get('companies', [])[:5]:
            print(f"   • {c.get('company', 'Unknown')} ({c.get('size', 'unknown')})")
        
        insights = results.get('insights', {})
        if insights and 'error' not in insights:
            print(f"\n📈 Market Insights:")
            print(f"   • Demand Level: {insights.get('demand_level', 'unknown')}")
            print(f"   • Salary Range (India): {insights.get('salary_range_india', 'N/A')}")
            print(f"   • Competition: {insights.get('competition_level', 'unknown')}")
        
        print("\n💾 Full results saved to data/ai_job_research.json")


def main():
    """Run AI job research."""
    researcher = AIJobResearcher()
    researcher.run_full_research()


if __name__ == '__main__':
    main()
