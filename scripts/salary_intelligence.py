#!/usr/bin/env python3
"""
Salary Intelligence System - Data-Driven Salary Negotiation
Provides market salary insights and negotiation strategies based on role, location, and experience.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.config import USER_DETAILS
except ImportError:
    USER_DETAILS = {}


@dataclass
class SalaryRange:
    """Represents a salary range for a position."""
    min_salary: int
    median_salary: int
    max_salary: int
    currency: str = "INR"
    
    def __str__(self):
        if self.currency == "INR":
            return f"₹{self.min_salary/100000:.1f}L - ₹{self.max_salary/100000:.1f}L (Median: ₹{self.median_salary/100000:.1f}L)"
        else:
            return f"${self.min_salary:,} - ${self.max_salary:,} (Median: ${self.median_salary:,})"


class IndianSalaryDatabase:
    """
    Salary data for Indian tech market based on 2024 market research.
    Sources: Glassdoor, AmbitionBox, Levels.fyi, LinkedIn Salary Insights
    """
    
    # Base salaries by role and experience (in INR LPA)
    BASE_SALARIES = {
        # Software Engineering
        'software_engineer': {
            'fresher': (4, 8, 12),      # 0-1 years
            'junior': (8, 12, 18),       # 1-3 years
            'mid': (15, 22, 30),         # 3-5 years
            'senior': (25, 35, 50),      # 5-8 years
            'staff': (40, 55, 80),       # 8-12 years
            'principal': (60, 80, 120),  # 12+ years
        },
        'data_scientist': {
            'fresher': (6, 10, 15),
            'junior': (12, 18, 25),
            'mid': (20, 30, 40),
            'senior': (35, 50, 70),
            'staff': (55, 75, 100),
            'principal': (80, 110, 150),
        },
        'data_engineer': {
            'fresher': (5, 9, 14),
            'junior': (10, 16, 22),
            'mid': (18, 26, 35),
            'senior': (30, 42, 55),
            'staff': (45, 60, 80),
            'principal': (65, 85, 110),
        },
        'machine_learning_engineer': {
            'fresher': (8, 12, 18),
            'junior': (15, 22, 30),
            'mid': (25, 35, 48),
            'senior': (40, 55, 75),
            'staff': (60, 80, 110),
            'principal': (90, 120, 160),
        },
        'devops_engineer': {
            'fresher': (5, 8, 12),
            'junior': (10, 15, 20),
            'mid': (18, 25, 35),
            'senior': (30, 40, 55),
            'staff': (45, 58, 75),
            'principal': (60, 80, 100),
        },
        'frontend_developer': {
            'fresher': (4, 7, 10),
            'junior': (8, 12, 16),
            'mid': (14, 20, 28),
            'senior': (24, 32, 45),
            'staff': (38, 50, 65),
            'principal': (55, 70, 90),
        },
        'backend_developer': {
            'fresher': (5, 8, 12),
            'junior': (10, 14, 18),
            'mid': (16, 22, 30),
            'senior': (26, 36, 48),
            'staff': (42, 55, 70),
            'principal': (58, 75, 95),
        },
        'product_manager': {
            'fresher': (8, 12, 16),
            'junior': (14, 20, 26),
            'mid': (22, 30, 40),
            'senior': (35, 48, 65),
            'staff': (55, 72, 90),
            'principal': (75, 95, 130),
        },
        'engineering_manager': {
            'junior': (25, 35, 45),
            'mid': (40, 52, 68),
            'senior': (55, 75, 95),
            'staff': (80, 100, 130),
            'principal': (110, 140, 180),
        },
    }
    
    # Company tier multipliers
    COMPANY_MULTIPLIERS = {
        'tier1_faang': 1.8,      # Google, Meta, Apple, Amazon, Netflix
        'tier1_india': 1.5,      # Flipkart, PhonePe, Razorpay, Swiggy
        'tier2_product': 1.3,    # Atlassian, Adobe, Uber, etc.
        'tier2_india': 1.2,      # Paytm, Zomato, CRED, etc.
        'tier3_funded': 1.1,     # Well-funded startups
        'service_mnc': 0.9,      # TCS, Infosys, Wipro (product roles higher)
        'startup_early': 0.85,   # Early-stage startups (equity heavy)
        'default': 1.0,
    }
    
    # City cost-of-living adjustments
    CITY_MULTIPLIERS = {
        'bangalore': 1.0,        # Base (highest tech salaries)
        'bengaluru': 1.0,
        'mumbai': 0.95,
        'delhi': 0.92,
        'gurgaon': 0.95,
        'gurugram': 0.95,
        'noida': 0.88,
        'hyderabad': 0.92,
        'pune': 0.88,
        'chennai': 0.85,
        'kolkata': 0.80,
        'ahmedabad': 0.78,
        'remote': 0.95,
        'default': 0.85,
    }
    
    # Top-paying companies in India
    TOP_COMPANIES = {
        'google': 'tier1_faang',
        'meta': 'tier1_faang',
        'facebook': 'tier1_faang',
        'apple': 'tier1_faang',
        'amazon': 'tier1_faang',
        'microsoft': 'tier1_faang',
        'netflix': 'tier1_faang',
        'flipkart': 'tier1_india',
        'phonepe': 'tier1_india',
        'razorpay': 'tier1_india',
        'swiggy': 'tier1_india',
        'cred': 'tier1_india',
        'meesho': 'tier1_india',
        'atlassian': 'tier2_product',
        'uber': 'tier2_product',
        'adobe': 'tier2_product',
        'salesforce': 'tier2_product',
        'oracle': 'tier2_product',
        'linkedin': 'tier2_product',
        'walmart': 'tier2_product',
        'paytm': 'tier2_india',
        'zomato': 'tier2_india',
        'ola': 'tier2_india',
        'dream11': 'tier2_india',
        'groww': 'tier2_india',
        'zerodha': 'tier2_india',
        'tcs': 'service_mnc',
        'infosys': 'service_mnc',
        'wipro': 'service_mnc',
        'hcl': 'service_mnc',
        'cognizant': 'service_mnc',
        'accenture': 'service_mnc',
    }
    
    @classmethod
    def get_role_category(cls, job_title: str) -> str:
        """Map job title to role category."""
        title_lower = job_title.lower()
        
        mappings = [
            (['machine learning', 'ml engineer', 'ai engineer', 'deep learning'], 'machine_learning_engineer'),
            (['data scientist', 'data science'], 'data_scientist'),
            (['data engineer', 'data engineering', 'analytics engineer'], 'data_engineer'),
            (['devops', 'sre', 'site reliability', 'platform engineer', 'infrastructure'], 'devops_engineer'),
            (['frontend', 'front-end', 'react', 'angular', 'vue', 'ui developer'], 'frontend_developer'),
            (['backend', 'back-end', 'api developer', 'server side'], 'backend_developer'),
            (['product manager', 'product owner', 'pm'], 'product_manager'),
            (['engineering manager', 'eng manager', 'tech lead manager'], 'engineering_manager'),
            (['software', 'developer', 'engineer', 'programmer', 'sde', 'full stack'], 'software_engineer'),
        ]
        
        for keywords, category in mappings:
            if any(kw in title_lower for kw in keywords):
                return category
        
        return 'software_engineer'  # Default
    
    @classmethod
    def get_experience_level(cls, years: int) -> str:
        """Map years of experience to level."""
        if years < 1:
            return 'fresher'
        elif years < 3:
            return 'junior'
        elif years < 5:
            return 'mid'
        elif years < 8:
            return 'senior'
        elif years < 12:
            return 'staff'
        else:
            return 'principal'
    
    @classmethod
    def get_company_tier(cls, company_name: str) -> str:
        """Get company tier for salary multiplier."""
        company_lower = company_name.lower().strip()
        
        # Check exact matches first
        for company, tier in cls.TOP_COMPANIES.items():
            if company in company_lower or company_lower in company:
                return tier
        
        # Check for patterns
        if any(x in company_lower for x in ['startup', 'labs', 'tech', 'ai']):
            return 'tier3_funded'
        
        return 'default'
    
    @classmethod
    def estimate_salary(
        cls,
        job_title: str,
        company: str,
        location: str,
        years_experience: int
    ) -> SalaryRange:
        """
        Estimate salary range for a position.
        
        Args:
            job_title: Job title
            company: Company name
            location: City/location
            years_experience: Years of experience
            
        Returns:
            SalaryRange with min, median, max
        """
        role = cls.get_role_category(job_title)
        level = cls.get_experience_level(years_experience)
        
        # Get base salary
        role_salaries = cls.BASE_SALARIES.get(role, cls.BASE_SALARIES['software_engineer'])
        if level not in role_salaries:
            level = 'mid'  # Default fallback
        
        min_sal, median_sal, max_sal = role_salaries[level]
        
        # Apply company multiplier
        company_tier = cls.get_company_tier(company)
        company_mult = cls.COMPANY_MULTIPLIERS.get(company_tier, 1.0)
        
        # Apply city multiplier
        city_lower = location.lower().strip()
        city_mult = cls.CITY_MULTIPLIERS.get(city_lower, cls.CITY_MULTIPLIERS['default'])
        
        # Calculate final range (convert LPA to actual INR)
        final_mult = company_mult * city_mult
        
        return SalaryRange(
            min_salary=int(min_sal * final_mult * 100000),
            median_salary=int(median_sal * final_mult * 100000),
            max_salary=int(max_sal * final_mult * 100000),
            currency="INR"
        )


class SalaryNegotiator:
    """Provides salary negotiation strategies and scripts."""
    
    NEGOTIATION_PRINCIPLES = [
        "Never give a number first - let them make the first offer",
        "Research market rates before any salary discussion",
        "Consider total compensation (base + bonus + equity + benefits)",
        "Have a walk-away number in mind before negotiating",
        "Use silence as a negotiation tool after they make an offer",
        "Always negotiate - 84% of employers expect it",
        "Get the offer in writing before accepting",
        "Negotiate other benefits if salary is capped (WFH, leave, learning budget)",
    ]
    
    COUNTER_OFFER_SCRIPTS = {
        'initial_response': """
Thank you for the offer of {offered_amount}. I'm very excited about this opportunity 
at {company} and believe I can add significant value to the team.

Based on my research of market rates for this role and my {years} years of experience 
with {key_skills}, I was expecting a base salary in the range of {expected_range}.

Would you be able to revisit the compensation package to better align with the 
market rate for someone with my background?
""",
        'competing_offer': """
I genuinely want to join {company} as I believe in the mission and team. However, 
I've received a competing offer at {competing_amount} that I need to consider.

Is there flexibility to match or come closer to this figure? I'd prefer to 
make my decision based on the role fit rather than just compensation.
""",
        'equity_focus': """
I understand the base salary constraints. Would it be possible to discuss 
additional equity or a signing bonus to bridge the gap? 

Given the growth trajectory of {company}, I'd be open to a compensation 
structure that has more upside through equity.
""",
        'benefits_focus': """
If the base salary is firm at {offered_amount}, I'd like to discuss other 
aspects of the package:
- Additional paid time off
- Flexible work arrangements  
- Learning & development budget
- Performance-based bonus structure

These would help make the overall package more competitive.
""",
    }
    
    @classmethod
    def generate_negotiation_strategy(
        cls,
        offered_salary: int,
        market_rate: SalaryRange,
        company: str,
        years_experience: int,
        key_skills: List[str]
    ) -> Dict:
        """
        Generate a personalized negotiation strategy.
        
        Args:
            offered_salary: The salary offered
            market_rate: Market salary range
            company: Company name
            years_experience: Years of experience
            key_skills: Key skills to highlight
            
        Returns:
            Dictionary with negotiation strategy
        """
        strategy = {
            'situation_analysis': '',
            'recommended_counter': 0,
            'negotiation_approach': '',
            'talking_points': [],
            'scripts': {}
        }
        
        # Analyze the offer
        offer_percentile = (offered_salary - market_rate.min_salary) / (market_rate.max_salary - market_rate.min_salary) * 100
        
        if offer_percentile >= 75:
            strategy['situation_analysis'] = (
                f"🟢 STRONG OFFER - At {offer_percentile:.0f}th percentile of market. "
                "Small negotiation room, focus on benefits."
            )
            strategy['recommended_counter'] = int(market_rate.max_salary * 0.95)
            strategy['negotiation_approach'] = 'benefits_focus'
        elif offer_percentile >= 50:
            strategy['situation_analysis'] = (
                f"🟡 FAIR OFFER - At {offer_percentile:.0f}th percentile. "
                "Reasonable room for 10-15% increase."
            )
            strategy['recommended_counter'] = int(market_rate.median_salary * 1.15)
            strategy['negotiation_approach'] = 'initial_response'
        elif offer_percentile >= 25:
            strategy['situation_analysis'] = (
                f"🟠 BELOW MARKET - At {offer_percentile:.0f}th percentile. "
                "Strong case for 20-30% increase."
            )
            strategy['recommended_counter'] = int(market_rate.median_salary * 1.1)
            strategy['negotiation_approach'] = 'initial_response'
        else:
            strategy['situation_analysis'] = (
                f"🔴 LOW OFFER - At {offer_percentile:.0f}th percentile. "
                "Significant gap from market. Counter aggressively or walk away."
            )
            strategy['recommended_counter'] = market_rate.median_salary
            strategy['negotiation_approach'] = 'competing_offer'
        
        # Generate talking points
        strategy['talking_points'] = [
            f"Your {years_experience} years of experience commands a premium",
            f"Skills in {', '.join(key_skills[:3])} are in high demand",
            f"Market median for this role is ₹{market_rate.median_salary/100000:.1f}L",
            "Your track record of delivering results justifies higher compensation",
            f"Similar roles at comparable companies pay ₹{market_rate.median_salary/100000:.1f}L-₹{market_rate.max_salary/100000:.1f}L",
        ]
        
        # Generate personalized scripts
        for script_name, template in cls.COUNTER_OFFER_SCRIPTS.items():
            strategy['scripts'][script_name] = template.format(
                offered_amount=f"₹{offered_salary/100000:.1f}L",
                company=company,
                years=years_experience,
                key_skills=', '.join(key_skills[:3]),
                expected_range=f"₹{market_rate.median_salary/100000:.1f}L - ₹{market_rate.max_salary/100000:.1f}L",
                competing_amount=f"₹{strategy['recommended_counter']/100000:.1f}L"
            )
        
        return strategy


class SalaryExtractor:
    """Extract salary information from job descriptions."""
    
    # Patterns for Indian salary formats
    INR_PATTERNS = [
        r'(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)\s*(?:l(?:acs?|akhs?)?|lpa|lac)',
        r'(\d+(?:\.\d+)?)\s*(?:l(?:acs?|akhs?)?|lpa)\s*(?:per\s*(?:annum|year))?',
        r'ctc[:\s]*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:l(?:acs?|akhs?)?)?',
        r'(\d+)\s*-\s*(\d+)\s*(?:l(?:acs?|akhs?)?|lpa)',
        r'salary[:\s]*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*)',
    ]
    
    USD_PATTERNS = [
        r'\$\s*(\d+(?:,\d+)*)\s*(?:k)?\s*(?:-|to)\s*\$?\s*(\d+(?:,\d+)*)\s*(?:k)?',
        r'\$(\d+(?:,\d+)*)\s*(?:per\s*(?:year|annum))?',
    ]
    
    @classmethod
    def extract_salary_from_jd(cls, job_description: str) -> Optional[Dict]:
        """
        Extract salary information from job description.
        
        Args:
            job_description: Full job description text
            
        Returns:
            Dictionary with salary info or None
        """
        text = job_description.lower()
        
        # Try INR patterns first
        for pattern in cls.INR_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:  # Range
                    return {
                        'min': float(groups[0].replace(',', '')) * 100000,
                        'max': float(groups[1].replace(',', '')) * 100000,
                        'currency': 'INR',
                        'raw_text': match.group(0)
                    }
                elif len(groups) == 1:
                    value = float(groups[0].replace(',', ''))
                    if value < 100:  # Likely in LPA
                        value = value * 100000
                    return {
                        'min': value * 0.9,
                        'max': value * 1.1,
                        'currency': 'INR',
                        'raw_text': match.group(0)
                    }
        
        # Try USD patterns
        for pattern in cls.USD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    min_val = int(groups[0].replace(',', ''))
                    max_val = int(groups[1].replace(',', ''))
                    if min_val < 500:  # Likely in K
                        min_val *= 1000
                        max_val *= 1000
                    return {
                        'min': min_val,
                        'max': max_val,
                        'currency': 'USD',
                        'raw_text': match.group(0)
                    }
        
        return None


def generate_salary_report(
    job_title: str,
    company: str,
    location: str,
    years_experience: int,
    job_description: str = "",
    offered_salary: int = None
) -> str:
    """
    Generate a comprehensive salary intelligence report.
    
    Args:
        job_title: Target job title
        company: Company name
        location: Job location
        years_experience: Years of experience
        job_description: Optional job description
        offered_salary: Optional offered salary to analyze
        
    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "SALARY INTELLIGENCE REPORT",
        "=" * 60,
        "",
        f"Role: {job_title}",
        f"Company: {company}",
        f"Location: {location}",
        f"Experience: {years_experience} years",
        "",
    ]
    
    # Get market rate
    market_rate = IndianSalaryDatabase.estimate_salary(
        job_title, company, location, years_experience
    )
    
    lines.extend([
        "-" * 40,
        "MARKET SALARY RANGE",
        "-" * 40,
        f"Minimum: ₹{market_rate.min_salary/100000:.1f} LPA",
        f"Median:  ₹{market_rate.median_salary/100000:.1f} LPA",
        f"Maximum: ₹{market_rate.max_salary/100000:.1f} LPA",
        "",
    ])
    
    # Company tier info
    tier = IndianSalaryDatabase.get_company_tier(company)
    tier_mult = IndianSalaryDatabase.COMPANY_MULTIPLIERS.get(tier, 1.0)
    lines.extend([
        f"Company Tier: {tier.replace('_', ' ').title()}",
        f"Tier Multiplier: {tier_mult}x",
        "",
    ])
    
    # Extract salary from JD if provided
    if job_description:
        extracted = SalaryExtractor.extract_salary_from_jd(job_description)
        if extracted:
            lines.extend([
                "-" * 40,
                "SALARY FROM JOB DESCRIPTION",
                "-" * 40,
                f"Mentioned: {extracted['raw_text']}",
                f"Range: ₹{extracted['min']/100000:.1f}L - ₹{extracted['max']/100000:.1f}L",
                "",
            ])
    
    # Negotiation strategy if offer provided
    if offered_salary:
        key_skills = USER_DETAILS.get('key_skills', 'Python,SQL,AWS').split(',')
        strategy = SalaryNegotiator.generate_negotiation_strategy(
            offered_salary, market_rate, company, years_experience, key_skills
        )
        
        lines.extend([
            "-" * 40,
            "NEGOTIATION STRATEGY",
            "-" * 40,
            f"Offered: ₹{offered_salary/100000:.1f} LPA",
            "",
            strategy['situation_analysis'],
            "",
            f"Recommended Counter: ₹{strategy['recommended_counter']/100000:.1f} LPA",
            "",
            "Talking Points:",
        ])
        
        for point in strategy['talking_points']:
            lines.append(f"  • {point}")
        
        lines.extend([
            "",
            "Counter Offer Script:",
            "-" * 30,
            strategy['scripts']['initial_response'],
        ])
    
    # General tips
    lines.extend([
        "",
        "=" * 60,
        "NEGOTIATION TIPS",
        "=" * 60,
    ])
    
    for i, tip in enumerate(SalaryNegotiator.NEGOTIATION_PRINCIPLES, 1):
        lines.append(f"{i}. {tip}")
    
    lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    report = generate_salary_report(
        job_title="Senior Data Engineer",
        company="Razorpay",
        location="Bangalore",
        years_experience=5,
        offered_salary=3500000  # 35 LPA
    )
    print(report)
    
    # Test salary extraction
    sample_jd = """
    We are looking for a Senior Software Engineer.
    CTC: 25-35 LPA based on experience.
    Location: Bangalore
    """
    
    extracted = SalaryExtractor.extract_salary_from_jd(sample_jd)
    if extracted:
        print(f"\nExtracted salary: {extracted}")
