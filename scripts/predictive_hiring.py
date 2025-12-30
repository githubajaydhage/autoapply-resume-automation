#!/usr/bin/env python3
"""
🔮 PREDICTIVE HIRING INTELLIGENCE
Predict which companies are likely to hire soon based on various signals.

Features:
- Track company hiring signals
- Funding announcements detection
- Job posting velocity analysis
- LinkedIn activity monitoring
- News & press release analysis
- Predict hiring probability
- Recommend companies to target
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import FreeAIManager
except ImportError:
    FreeAIManager = None


class PredictiveHiringIntelligence:
    """Predict which companies will hire soon"""
    
    # Hiring signals and their weights
    SIGNAL_WEIGHTS = {
        'recent_funding': 25,
        'job_posting_increase': 20,
        'leadership_hire': 15,
        'expansion_news': 15,
        'product_launch': 10,
        'partnership_announcement': 10,
        'positive_earnings': 10,
        'office_expansion': 10,
        'linkedin_followers_growth': 5,
        'tech_stack_change': 5,
    }
    
    # Negative signals
    NEGATIVE_SIGNALS = {
        'layoffs': -40,
        'hiring_freeze': -50,
        'revenue_decline': -20,
        'leadership_exit': -15,
        'bad_press': -10,
        'downsizing': -30,
    }
    
    def __init__(self):
        self.companies_file = Path("data/company_signals.json")
        self.predictions_file = Path("data/hiring_predictions.json")
        self.companies = self._load_companies()
        self.predictions = self._load_predictions()
        self.ai = FreeAIManager() if FreeAIManager else None
        
    def _load_companies(self) -> Dict:
        """Load company data"""
        if self.companies_file.exists():
            try:
                with open(self.companies_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'companies': {}}
    
    def _save_companies(self):
        """Save company data"""
        self.companies_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.companies_file, 'w') as f:
            json.dump(self.companies, f, indent=2)
    
    def _load_predictions(self) -> Dict:
        """Load predictions history"""
        if self.predictions_file.exists():
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'predictions': []}
    
    def _save_predictions(self):
        """Save predictions"""
        self.predictions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)
    
    def add_company(self, name: str, industry: str = "", 
                    website: str = "", linkedin: str = "") -> Dict:
        """Add a company to track"""
        
        company_id = name.lower().replace(' ', '_')
        
        company = {
            'id': company_id,
            'name': name,
            'industry': industry,
            'website': website,
            'linkedin': linkedin,
            'signals': [],
            'hiring_score': 50,
            'last_analyzed': None,
            'created_at': datetime.now().isoformat(),
            'job_posting_count': 0,
            'job_posting_history': []
        }
        
        self.companies['companies'][company_id] = company
        self._save_companies()
        
        return company
    
    def add_signal(self, company_name: str, signal_type: str, 
                   details: str = "", source: str = "") -> bool:
        """Add a hiring signal for a company"""
        
        company_id = company_name.lower().replace(' ', '_')
        
        if company_id not in self.companies['companies']:
            self.add_company(company_name)
        
        signal = {
            'type': signal_type,
            'details': details,
            'source': source,
            'date': datetime.now().isoformat(),
            'weight': self.SIGNAL_WEIGHTS.get(signal_type, 0) + self.NEGATIVE_SIGNALS.get(signal_type, 0)
        }
        
        self.companies['companies'][company_id]['signals'].append(signal)
        
        # Recalculate hiring score
        self._calculate_hiring_score(company_id)
        self._save_companies()
        
        return True
    
    def _calculate_hiring_score(self, company_id: str) -> int:
        """Calculate hiring probability score"""
        
        company = self.companies['companies'].get(company_id)
        if not company:
            return 0
        
        score = 50  # Base score
        
        # Process signals from last 90 days
        cutoff = (datetime.now() - timedelta(days=90)).isoformat()
        
        for signal in company.get('signals', []):
            if signal['date'] >= cutoff:
                # More recent signals have higher weight
                days_ago = (datetime.now() - datetime.fromisoformat(signal['date'])).days
                recency_factor = 1 - (days_ago / 90)  # 1.0 to 0.0
                
                weight = signal.get('weight', 0)
                score += weight * recency_factor
        
        # Adjust for job posting velocity
        posting_increase = self._calculate_posting_velocity(company_id)
        score += posting_increase * 2  # Up to 20 points for high velocity
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        company['hiring_score'] = int(score)
        company['last_analyzed'] = datetime.now().isoformat()
        
        return int(score)
    
    def _calculate_posting_velocity(self, company_id: str) -> int:
        """Calculate job posting velocity (rate of change)"""
        
        company = self.companies['companies'].get(company_id)
        if not company:
            return 0
        
        history = company.get('job_posting_history', [])
        if len(history) < 2:
            return 0
        
        # Compare last two data points
        recent = history[-1].get('count', 0)
        previous = history[-2].get('count', 0)
        
        if previous == 0:
            return 5 if recent > 0 else 0
        
        change_pct = ((recent - previous) / previous) * 100
        
        if change_pct >= 50:
            return 10  # Significant increase
        elif change_pct >= 20:
            return 5
        elif change_pct <= -30:
            return -5  # Significant decrease
        
        return 0
    
    def analyze_company_with_ai(self, company_name: str) -> Dict:
        """Use AI to analyze company hiring likelihood"""
        
        if not self.ai:
            return {}
        
        prompt = f"""
        Analyze the hiring outlook for "{company_name}" company.
        Based on general knowledge, estimate:
        
        1. Is this company likely hiring right now? (Yes/No/Maybe)
        2. Hiring probability score (0-100)
        3. Key hiring signals (positive or negative)
        4. Best departments/roles to apply for
        5. Best time to apply (if known)
        
        Return as JSON:
        {{
            "hiring_likely": "Yes/No/Maybe",
            "probability_score": 0,
            "positive_signals": ["signal1", "signal2"],
            "negative_signals": ["signal1"],
            "recommended_roles": ["role1", "role2"],
            "apply_timing": "now/wait/avoid",
            "analysis_summary": "brief summary"
        }}
        """
        
        try:
            response = self.ai.generate(prompt, max_tokens=400)
            if response:
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except:
            pass
        
        return {}
    
    def track_job_postings(self, company_name: str, current_count: int):
        """Track job posting count over time"""
        
        company_id = company_name.lower().replace(' ', '_')
        
        if company_id not in self.companies['companies']:
            self.add_company(company_name)
        
        self.companies['companies'][company_id]['job_posting_count'] = current_count
        self.companies['companies'][company_id]['job_posting_history'].append({
            'date': datetime.now().isoformat(),
            'count': current_count
        })
        
        # Keep only last 30 data points
        if len(self.companies['companies'][company_id]['job_posting_history']) > 30:
            self.companies['companies'][company_id]['job_posting_history'] = \
                self.companies['companies'][company_id]['job_posting_history'][-30:]
        
        self._save_companies()
    
    def search_funding_news(self) -> List[Dict]:
        """Search for recent funding announcements (using free APIs)"""
        
        funding_news = []
        
        # This would ideally use a news API or web scraping
        # For now, using AI to generate likely funding signals
        
        if self.ai:
            target_role = os.getenv('APPLICANT_TARGET_ROLE', 'software engineer')
            prompt = f"""
            List 5 companies in India that recently (last 3 months) raised funding 
            and are likely hiring for roles related to: {target_role}
            
            Return as JSON array:
            [
                {{
                    "company": "Company Name",
                    "funding_amount": "$X million",
                    "funding_round": "Series A/B/C",
                    "date": "Month Year",
                    "likely_hiring": ["role1", "role2"]
                }}
            ]
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=400)
                if response:
                    json_match = re.search(r'\[[^\[\]]*\]', response, re.DOTALL)
                    if json_match:
                        funding_news = json.loads(json_match.group())
            except:
                pass
        
        return funding_news
    
    def get_top_targets(self, limit: int = 20) -> List[Dict]:
        """Get top companies to target based on hiring probability"""
        
        targets = []
        
        for company_id, company in self.companies['companies'].items():
            # Recalculate score
            self._calculate_hiring_score(company_id)
            
            targets.append({
                'name': company['name'],
                'hiring_score': company['hiring_score'],
                'industry': company.get('industry', ''),
                'recent_signals': len([s for s in company.get('signals', []) 
                                       if s['date'] >= (datetime.now() - timedelta(days=30)).isoformat()]),
                'job_count': company.get('job_posting_count', 0),
                'recommendation': self._get_recommendation(company['hiring_score'])
            })
        
        targets.sort(key=lambda x: x['hiring_score'], reverse=True)
        return targets[:limit]
    
    def _get_recommendation(self, score: int) -> str:
        """Get recommendation based on score"""
        
        if score >= 80:
            return "🔥 HOT - Apply immediately!"
        elif score >= 60:
            return "✅ WARM - Great time to apply"
        elif score >= 40:
            return "👍 MODERATE - Worth applying"
        elif score >= 20:
            return "⚠️ COOL - Apply with caution"
        else:
            return "❄️ COLD - Consider waiting"
    
    def predict_hiring_surge(self, months_ahead: int = 3) -> List[Dict]:
        """Predict companies likely to have hiring surge"""
        
        predictions = []
        
        for company_id, company in self.companies['companies'].items():
            score = company.get('hiring_score', 50)
            signals = company.get('signals', [])
            
            # Check for leading indicators
            leading_indicators = {
                'recent_funding': 0,
                'leadership_hire': 0,
                'expansion_news': 0,
                'product_launch': 0
            }
            
            recent_cutoff = (datetime.now() - timedelta(days=60)).isoformat()
            
            for signal in signals:
                if signal['date'] >= recent_cutoff:
                    if signal['type'] in leading_indicators:
                        leading_indicators[signal['type']] += 1
            
            # Calculate surge probability
            surge_score = score
            surge_score += leading_indicators['recent_funding'] * 15
            surge_score += leading_indicators['leadership_hire'] * 10
            surge_score += leading_indicators['expansion_news'] * 10
            surge_score += leading_indicators['product_launch'] * 8
            
            if surge_score >= 70:
                predictions.append({
                    'company': company['name'],
                    'current_score': score,
                    'surge_probability': min(100, surge_score),
                    'key_indicators': [k for k, v in leading_indicators.items() if v > 0],
                    'recommended_action': 'Apply now and follow up in 2-4 weeks',
                    'confidence': 'High' if surge_score >= 85 else 'Medium'
                })
        
        predictions.sort(key=lambda x: x['surge_probability'], reverse=True)
        
        # Save predictions
        self.predictions['predictions'].append({
            'date': datetime.now().isoformat(),
            'months_ahead': months_ahead,
            'predictions': predictions[:10]
        })
        self._save_predictions()
        
        return predictions[:10]
    
    def discover_emerging_companies(self) -> List[Dict]:
        """Discover emerging companies in target industry"""
        
        if not self.ai:
            return []
        
        target_role = os.getenv('APPLICANT_TARGET_ROLE', 'software engineer')
        location = os.getenv('APPLICANT_CITY', 'Bangalore')
        
        prompt = f"""
        List 10 emerging/growing companies in {location}, India that are likely 
        hiring for {target_role} related roles.
        
        Focus on:
        - Startups that raised funding in last 6 months
        - Companies expanding their tech teams
        - Companies in growth mode
        
        Return as JSON array:
        [
            {{
                "company": "Company Name",
                "industry": "Industry",
                "why_hiring": "reason they're likely hiring",
                "company_stage": "Seed/Series A/B/Growth",
                "estimated_team_size": "50-100",
                "website": "website.com"
            }}
        ]
        """
        
        try:
            response = self.ai.generate(prompt, max_tokens=600)
            if response:
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    companies = json.loads(json_match.group())
                    
                    # Add to tracking
                    for company in companies:
                        self.add_company(
                            company.get('company', ''),
                            industry=company.get('industry', ''),
                            website=company.get('website', '')
                        )
                        self.add_signal(
                            company.get('company', ''),
                            'expansion_news',
                            company.get('why_hiring', ''),
                            'AI Discovery'
                        )
                    
                    return companies
        except:
            pass
        
        return []
    
    def get_industry_trends(self) -> Dict:
        """Get industry-wide hiring trends"""
        
        if not self.ai:
            return {}
        
        target_role = os.getenv('APPLICANT_TARGET_ROLE', 'software engineer')
        
        prompt = f"""
        Analyze current hiring trends for {target_role} roles in India (2024-2025).
        
        Return JSON:
        {{
            "overall_market": "hot/warm/cool/cold",
            "demand_trend": "increasing/stable/decreasing",
            "hot_skills": ["skill1", "skill2", "skill3"],
            "industries_hiring": ["industry1", "industry2"],
            "industries_slowing": ["industry1"],
            "salary_trend": "increasing/stable/decreasing",
            "remote_trend": "more remote/same/less remote",
            "best_companies_to_target": ["company1", "company2", "company3"],
            "hiring_outlook_6_months": "positive/neutral/negative"
        }}
        """
        
        try:
            response = self.ai.generate(prompt, max_tokens=400)
            if response:
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except:
            pass
        
        return {}
    
    def print_intelligence_report(self):
        """Print hiring intelligence report"""
        
        print(f"\n{'='*60}")
        print(f"🔮 PREDICTIVE HIRING INTELLIGENCE REPORT")
        print(f"{'='*60}")
        
        # Top targets
        targets = self.get_top_targets(10)
        
        print(f"\n🎯 TOP COMPANIES TO TARGET:")
        print(f"{'─'*60}")
        
        for i, target in enumerate(targets, 1):
            print(f"\n{i}. {target['name']}")
            print(f"   Score: {target['hiring_score']}/100 | {target['recommendation']}")
            print(f"   Industry: {target['industry']} | Active Jobs: {target['job_count']}")
        
        # Predictions
        predictions = self.predict_hiring_surge()
        
        if predictions:
            print(f"\n📈 HIRING SURGE PREDICTIONS (Next 3 Months):")
            print(f"{'─'*60}")
            
            for pred in predictions[:5]:
                print(f"\n   🔥 {pred['company']}")
                print(f"      Surge Probability: {pred['surge_probability']}%")
                print(f"      Key Indicators: {', '.join(pred['key_indicators'])}")
                print(f"      Confidence: {pred['confidence']}")
        
        # Industry trends
        trends = self.get_industry_trends()
        
        if trends:
            print(f"\n📊 INDUSTRY TRENDS:")
            print(f"{'─'*60}")
            print(f"   Market Status: {trends.get('overall_market', 'N/A')}")
            print(f"   Demand Trend: {trends.get('demand_trend', 'N/A')}")
            print(f"   Hot Skills: {', '.join(trends.get('hot_skills', []))}")
            print(f"   6-Month Outlook: {trends.get('hiring_outlook_6_months', 'N/A')}")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    intel = PredictiveHiringIntelligence()
    
    # Discover emerging companies
    print("🔍 Discovering emerging companies...")
    emerging = intel.discover_emerging_companies()
    print(f"   Found {len(emerging)} emerging companies")
    
    # Print intelligence report
    intel.print_intelligence_report()


if __name__ == "__main__":
    main()
