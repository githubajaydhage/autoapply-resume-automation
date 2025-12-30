#!/usr/bin/env python3
"""
💰 SALARY NEGOTIATION AI
AI-powered salary research and negotiation assistance.

Features:
- Research market salary ranges
- Analyze compensation packages
- Generate negotiation scripts
- Counter-offer strategies
- Benefits comparison
- Total compensation calculator
- Red flags detection
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import FreeAIManager
except ImportError:
    FreeAIManager = None


class SalaryNegotiationAI:
    """AI-powered salary negotiation assistant"""
    
    # Salary data (India market - can be updated)
    INDIA_SALARY_DATA = {
        'data analyst': {'min': 400000, 'mid': 800000, 'max': 1500000, 'currency': 'INR'},
        'senior data analyst': {'min': 800000, 'mid': 1400000, 'max': 2500000, 'currency': 'INR'},
        'business analyst': {'min': 500000, 'mid': 1000000, 'max': 1800000, 'currency': 'INR'},
        'data scientist': {'min': 600000, 'mid': 1200000, 'max': 2500000, 'currency': 'INR'},
        'software engineer': {'min': 500000, 'mid': 1200000, 'max': 2500000, 'currency': 'INR'},
        'senior software engineer': {'min': 1200000, 'mid': 2400000, 'max': 4500000, 'currency': 'INR'},
        'frontend developer': {'min': 400000, 'mid': 1000000, 'max': 2000000, 'currency': 'INR'},
        'backend developer': {'min': 500000, 'mid': 1200000, 'max': 2500000, 'currency': 'INR'},
        'full stack developer': {'min': 600000, 'mid': 1400000, 'max': 3000000, 'currency': 'INR'},
        'devops engineer': {'min': 700000, 'mid': 1500000, 'max': 3000000, 'currency': 'INR'},
        'product manager': {'min': 1000000, 'mid': 2000000, 'max': 4000000, 'currency': 'INR'},
        'interior designer': {'min': 300000, 'mid': 600000, 'max': 1500000, 'currency': 'INR'},
        'senior interior designer': {'min': 600000, 'mid': 1200000, 'max': 2500000, 'currency': 'INR'},
    }
    
    # Common benefits in India
    COMMON_BENEFITS = {
        'health_insurance': {'typical_value': 50000, 'negotiable': False},
        'life_insurance': {'typical_value': 30000, 'negotiable': False},
        'pf_contribution': {'typical_value': '12% of basic', 'negotiable': False},
        'gratuity': {'typical_value': '4.81% of basic', 'negotiable': False},
        'food_allowance': {'typical_value': 3000, 'negotiable': True},
        'transport_allowance': {'typical_value': 3200, 'negotiable': True},
        'wfh_allowance': {'typical_value': 2000, 'negotiable': True},
        'learning_budget': {'typical_value': 25000, 'negotiable': True},
        'stock_options': {'typical_value': 'Variable', 'negotiable': True},
        'joining_bonus': {'typical_value': 'Variable', 'negotiable': True},
        'relocation_bonus': {'typical_value': 50000, 'negotiable': True},
        'annual_bonus': {'typical_value': '10-20% of CTC', 'negotiable': True},
    }
    
    def __init__(self):
        self.negotiations_file = Path("data/salary_negotiations.json")
        self.negotiations = self._load_negotiations()
        self.ai = FreeAIManager() if FreeAIManager else None
        
        # User's expectations
        self.current_salary = int(os.getenv('CURRENT_SALARY', '0'))
        self.expected_salary = int(os.getenv('EXPECTED_SALARY', '0'))
        self.years_experience = int(os.getenv('YEARS_EXPERIENCE', '3'))
        
    def _load_negotiations(self) -> Dict:
        """Load negotiation history"""
        if self.negotiations_file.exists():
            try:
                with open(self.negotiations_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'negotiations': []}
    
    def _save_negotiations(self):
        """Save negotiations"""
        self.negotiations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.negotiations_file, 'w') as f:
            json.dump(self.negotiations, f, indent=2)
    
    def research_salary(self, role: str, location: str = "Bangalore", 
                        experience_years: int = None) -> Dict:
        """Research market salary for a role"""
        
        exp = experience_years or self.years_experience
        role_lower = role.lower()
        
        # Check our data
        base_data = None
        for title, data in self.INDIA_SALARY_DATA.items():
            if title in role_lower or role_lower in title:
                base_data = data.copy()
                break
        
        if not base_data:
            # Default ranges
            base_data = {'min': 400000, 'mid': 800000, 'max': 1500000, 'currency': 'INR'}
        
        # Adjust for experience
        experience_multiplier = 1 + (exp - 3) * 0.15  # 15% per year above 3 years
        experience_multiplier = max(0.7, min(2.0, experience_multiplier))
        
        # Adjust for location
        location_multipliers = {
            'bangalore': 1.0,
            'mumbai': 1.05,
            'delhi': 0.95,
            'hyderabad': 0.95,
            'pune': 0.90,
            'chennai': 0.90,
            'remote': 1.0,
            'kolkata': 0.85,
        }
        location_mult = location_multipliers.get(location.lower(), 0.9)
        
        # Calculate ranges
        research = {
            'role': role,
            'location': location,
            'experience_years': exp,
            'currency': base_data['currency'],
            'market_range': {
                'min': int(base_data['min'] * experience_multiplier * location_mult),
                'mid': int(base_data['mid'] * experience_multiplier * location_mult),
                'max': int(base_data['max'] * experience_multiplier * location_mult),
            },
            'recommendation': '',
            'data_sources': ['Internal data', 'Market research'],
            'last_updated': datetime.now().isoformat()
        }
        
        # Use AI for additional insights
        if self.ai:
            prompt = f"""
            What is the typical salary range for a {role} with {exp} years of experience in {location}, India?
            
            Consider:
            - Current market conditions (2024-2025)
            - IT industry standards
            - Startup vs MNC differences
            
            Return JSON:
            {{
                "min_salary": 0,
                "median_salary": 0,
                "max_salary": 0,
                "currency": "INR",
                "factors": ["factor1", "factor2"],
                "tips": ["tip1", "tip2"]
            }}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=300)
                if response:
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                        research['ai_insights'] = {
                            'factors': ai_data.get('factors', []),
                            'tips': ai_data.get('tips', [])
                        }
            except:
                pass
        
        # Generate recommendation
        mid = research['market_range']['mid']
        if self.current_salary:
            expected_hike = (mid - self.current_salary) / self.current_salary * 100
            research['recommendation'] = f"Based on market data, aim for ₹{mid:,} ({expected_hike:.0f}% hike)"
        else:
            research['recommendation'] = f"Target salary: ₹{mid:,} (market median)"
        
        return research
    
    def analyze_offer(self, offer_details: Dict) -> Dict:
        """Analyze a job offer"""
        
        offered_ctc = offer_details.get('ctc', 0)
        role = offer_details.get('role', '')
        company = offer_details.get('company', '')
        
        # Research market rate
        market = self.research_salary(role)
        
        # Calculate percentile
        min_sal = market['market_range']['min']
        max_sal = market['market_range']['max']
        
        if max_sal > min_sal:
            percentile = (offered_ctc - min_sal) / (max_sal - min_sal) * 100
            percentile = max(0, min(100, percentile))
        else:
            percentile = 50
        
        # Determine verdict
        if percentile >= 70:
            verdict = "EXCELLENT OFFER ✅"
            negotiate = False
        elif percentile >= 50:
            verdict = "GOOD OFFER 👍"
            negotiate = True
        elif percentile >= 30:
            verdict = "BELOW AVERAGE ⚠️"
            negotiate = True
        else:
            verdict = "LOW OFFER ❌"
            negotiate = True
        
        # Calculate potential increase
        target = market['market_range']['mid']
        if offered_ctc < target:
            potential_increase = target - offered_ctc
            increase_percentage = (potential_increase / offered_ctc) * 100 if offered_ctc else 0
        else:
            potential_increase = 0
            increase_percentage = 0
        
        analysis = {
            'offered_ctc': offered_ctc,
            'market_range': market['market_range'],
            'percentile': round(percentile, 1),
            'verdict': verdict,
            'should_negotiate': negotiate,
            'target_salary': target,
            'potential_increase': potential_increase,
            'increase_percentage': round(increase_percentage, 1),
            'hike_from_current': round((offered_ctc - self.current_salary) / self.current_salary * 100, 1) if self.current_salary else 0
        }
        
        return analysis
    
    def generate_negotiation_script(self, offer_details: Dict, target_salary: int) -> Dict:
        """Generate negotiation talking points and scripts"""
        
        current = self.current_salary
        offered = offer_details.get('ctc', 0)
        role = offer_details.get('role', '')
        company = offer_details.get('company', '')
        
        scripts = {
            'opening': '',
            'justification': [],
            'counter_offer': '',
            'fallback_asks': [],
            'closing': '',
            'tips': []
        }
        
        # Calculate counter offer (10-15% above target)
        counter = int(target_salary * 1.1)
        
        if self.ai:
            prompt = f"""
            Generate salary negotiation scripts for:
            
            Context:
            - Current salary: ₹{current:,}
            - Offered salary: ₹{offered:,}
            - Target salary: ₹{target_salary:,}
            - Role: {role}
            - Company: {company}
            - Experience: {self.years_experience} years
            
            Return JSON:
            {{
                "opening_statement": "statement to open negotiation",
                "justification_points": ["point1", "point2", "point3"],
                "counter_offer_script": "how to present counter offer",
                "fallback_benefits": ["benefit1", "benefit2"],
                "closing_statement": "how to close positively",
                "dos": ["do1", "do2"],
                "donts": ["dont1", "dont2"]
            }}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=500)
                if response:
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        ai_scripts = json.loads(json_match.group())
                        scripts.update({
                            'opening': ai_scripts.get('opening_statement', ''),
                            'justification': ai_scripts.get('justification_points', []),
                            'counter_offer': ai_scripts.get('counter_offer_script', ''),
                            'fallback_asks': ai_scripts.get('fallback_benefits', []),
                            'closing': ai_scripts.get('closing_statement', ''),
                            'dos': ai_scripts.get('dos', []),
                            'donts': ai_scripts.get('donts', [])
                        })
            except:
                pass
        
        # Fallback scripts
        if not scripts['opening']:
            scripts['opening'] = f"Thank you for the offer. I'm very excited about the opportunity at {company}. I'd like to discuss the compensation package."
        
        if not scripts['justification']:
            scripts['justification'] = [
                f"Based on my {self.years_experience} years of experience",
                "Market research shows similar roles paying 15-20% higher",
                "My specific skills in [mention key skills] add significant value",
                "I've consistently exceeded targets in my current role"
            ]
        
        if not scripts['counter_offer']:
            scripts['counter_offer'] = f"Based on my research and experience, I was expecting something closer to ₹{target_salary:,}. Would you be able to meet at ₹{counter:,}?"
        
        if not scripts['fallback_asks']:
            scripts['fallback_asks'] = [
                "Signing bonus",
                "Additional stock options/RSUs",
                "Earlier salary review (6 months instead of 12)",
                "Additional leave days",
                "Learning & development budget",
                "Work from home flexibility"
            ]
        
        if not scripts['closing']:
            scripts['closing'] = "I'm committed to joining and contributing to the team. I'm confident we can find a number that works for both of us."
        
        scripts['tips'] = [
            "Never accept on the spot - always ask for 24-48 hours",
            "Get the offer in writing before negotiating",
            "Focus on value you bring, not personal needs",
            "Be enthusiastic but firm",
            "Have a walkaway number in mind",
            "Consider the full package, not just base salary"
        ]
        
        return scripts
    
    def generate_counter_email(self, offer_details: Dict, target_salary: int) -> str:
        """Generate counter-offer email"""
        
        name = os.getenv('APPLICANT_NAME', '')
        offered = offer_details.get('ctc', 0)
        role = offer_details.get('role', '')
        company = offer_details.get('company', '')
        
        if self.ai:
            prompt = f"""
            Write a professional salary negotiation email:
            
            Context:
            - My name: {name}
            - Offered: ₹{offered:,}
            - Target: ₹{target_salary:,}
            - Role: {role}
            - Company: {company}
            - Experience: {self.years_experience} years
            
            Requirements:
            - Professional and respectful tone
            - Express enthusiasm for the role
            - Justify the counter-offer briefly
            - Leave room for discussion
            - Under 200 words
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=400)
                if response:
                    return response.strip()
            except:
                pass
        
        # Fallback template
        return f"""Dear Hiring Team,

Thank you for extending the offer for the {role} position. I'm genuinely excited about the opportunity to join {company} and contribute to the team.

After careful consideration, I would like to discuss the compensation package. Based on my {self.years_experience} years of experience and the current market rates for similar positions, I was hoping for a salary closer to ₹{target_salary:,}.

I believe my skills and experience would bring significant value to the team, and I'm confident we can find a mutually agreeable number.

I'm very enthusiastic about this opportunity and look forward to your response.

Best regards,
{name}"""
    
    def calculate_total_compensation(self, base_salary: int, benefits: Dict) -> Dict:
        """Calculate total compensation value"""
        
        total = base_salary
        breakdown = {'base_salary': base_salary}
        
        for benefit, value in benefits.items():
            if isinstance(value, int):
                total += value
                breakdown[benefit] = value
            elif isinstance(value, str) and '%' in value:
                # Calculate percentage-based benefits
                pct = float(re.search(r'(\d+)', value).group(1))
                amount = int(base_salary * pct / 100)
                total += amount
                breakdown[benefit] = amount
        
        breakdown['total'] = total
        breakdown['monthly_take_home_approx'] = int(total * 0.7 / 12)  # Rough estimate
        
        return breakdown
    
    def compare_offers(self, offers: List[Dict]) -> Dict:
        """Compare multiple job offers"""
        
        comparisons = []
        
        for offer in offers:
            analysis = self.analyze_offer(offer)
            total_comp = self.calculate_total_compensation(
                offer.get('ctc', 0),
                offer.get('benefits', {})
            )
            
            comparisons.append({
                'company': offer.get('company', 'Unknown'),
                'role': offer.get('role', 'Unknown'),
                'ctc': offer.get('ctc', 0),
                'total_compensation': total_comp.get('total', offer.get('ctc', 0)),
                'percentile': analysis['percentile'],
                'verdict': analysis['verdict'],
                'monthly_take_home': total_comp.get('monthly_take_home_approx', 0),
                'growth_potential': offer.get('growth_potential', 'Unknown'),
                'wlb_score': offer.get('work_life_balance', 5)
            })
        
        # Sort by total compensation
        comparisons.sort(key=lambda x: x['total_compensation'], reverse=True)
        
        # Determine recommendation
        if comparisons:
            best = comparisons[0]
            recommendation = f"Best offer: {best['company']} with ₹{best['total_compensation']:,} total compensation"
        else:
            recommendation = "No offers to compare"
        
        return {
            'offers': comparisons,
            'recommendation': recommendation,
            'compared_at': datetime.now().isoformat()
        }
    
    def detect_red_flags(self, offer_details: Dict) -> List[str]:
        """Detect red flags in job offer"""
        
        red_flags = []
        
        # Check CTC breakdown
        if not offer_details.get('ctc_breakdown'):
            red_flags.append("⚠️ No CTC breakdown provided - ask for detailed structure")
        
        # Check variable component
        variable = offer_details.get('variable_pay', 0)
        ctc = offer_details.get('ctc', 0)
        if ctc and variable / ctc > 0.3:
            red_flags.append("⚠️ High variable component (>30%) - actual take-home may be lower")
        
        # Check joining bonus clawback
        if offer_details.get('joining_bonus') and not offer_details.get('clawback_terms'):
            red_flags.append("⚠️ Joining bonus - clarify clawback terms if you leave early")
        
        # Check notice period
        notice = offer_details.get('notice_period_days', 0)
        if notice > 60:
            red_flags.append(f"⚠️ Long notice period ({notice} days) - may affect future opportunities")
        
        # Check bond/agreement
        if offer_details.get('bond_period'):
            red_flags.append(f"⚠️ Bond/Service agreement - review terms carefully")
        
        # Check probation terms
        if offer_details.get('probation_months', 0) > 6:
            red_flags.append("⚠️ Long probation period - clarify terms and confirmation process")
        
        return red_flags
    
    def print_analysis_report(self, analysis: Dict, scripts: Dict = None):
        """Print formatted analysis report"""
        
        print(f"\n{'='*60}")
        print(f"💰 SALARY ANALYSIS REPORT")
        print(f"{'='*60}")
        
        print(f"\n📊 OFFER ANALYSIS:")
        print(f"   Offered CTC: ₹{analysis['offered_ctc']:,}")
        print(f"   Market Range: ₹{analysis['market_range']['min']:,} - ₹{analysis['market_range']['max']:,}")
        print(f"   Percentile: {analysis['percentile']}%")
        print(f"   Verdict: {analysis['verdict']}")
        
        if analysis.get('hike_from_current'):
            print(f"   Hike from current: {analysis['hike_from_current']}%")
        
        print(f"\n🎯 RECOMMENDATION:")
        if analysis['should_negotiate']:
            print(f"   Target: ₹{analysis['target_salary']:,}")
            print(f"   Potential increase: ₹{analysis['potential_increase']:,} ({analysis['increase_percentage']}%)")
        else:
            print(f"   This is a strong offer - you may accept or negotiate slightly")
        
        if scripts:
            print(f"\n📝 NEGOTIATION SCRIPT:")
            print(f"\n   Opening:")
            print(f"   \"{scripts['opening']}\"")
            
            print(f"\n   Key Points:")
            for point in scripts['justification'][:3]:
                print(f"   • {point}")
            
            print(f"\n   Counter Offer:")
            print(f"   \"{scripts['counter_offer']}\"")
            
            print(f"\n   Fallback Asks:")
            for ask in scripts['fallback_asks'][:4]:
                print(f"   • {ask}")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    negotiator = SalaryNegotiationAI()
    
    print(f"\n💰 SALARY NEGOTIATION AI")
    print(f"{'='*50}")
    
    # Research salary
    research = negotiator.research_salary("Data Analyst", "Bangalore", 3)
    print(f"\n📊 Market Research for Data Analyst:")
    print(f"   Range: ₹{research['market_range']['min']:,} - ₹{research['market_range']['max']:,}")
    print(f"   Median: ₹{research['market_range']['mid']:,}")
    
    # Analyze an offer
    offer = {
        'ctc': 1000000,
        'role': 'Data Analyst',
        'company': 'Example Corp'
    }
    
    analysis = negotiator.analyze_offer(offer)
    scripts = negotiator.generate_negotiation_script(offer, analysis['target_salary'])
    
    negotiator.print_analysis_report(analysis, scripts)
    
    # Show counter email
    print(f"📧 COUNTER OFFER EMAIL:")
    print(f"{'─'*50}")
    email = negotiator.generate_counter_email(offer, analysis['target_salary'])
    print(email)


if __name__ == "__main__":
    main()
