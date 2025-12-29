#!/usr/bin/env python3
"""
Job Priority Intelligence System
Prioritizes jobs based on multiple factors to maximize interview chances:
- Posting freshness (newer = higher priority)
- Application deadline urgency
- Company response rate
- Role-candidate fit score
- Salary attractiveness
"""

import os
import sys
from datetime import datetime, timedelta
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
class JobPriority:
    """Represents job priority scoring."""
    job_id: str
    title: str
    company: str
    priority_score: float
    urgency_level: str
    factors: Dict[str, float]
    recommended_action: str


class PostingFreshnessScorer:
    """Score jobs based on how recently they were posted."""
    
    # Decay curve for posting freshness
    FRESHNESS_SCORES = {
        0: 100,    # Today
        1: 95,     # Yesterday
        2: 90,     # 2 days ago
        3: 85,     # 3 days ago
        7: 70,     # Week old
        14: 50,    # 2 weeks old
        30: 30,    # Month old
        60: 15,    # 2 months old
        90: 5,     # 3 months old
    }
    
    # Keywords indicating recently posted
    FRESH_KEYWORDS = [
        'just posted', 'posted today', 'new', 'urgent', 'immediate',
        'asap', 'quickly', 'fast hiring', 'rapid', 'hot job'
    ]
    
    # Keywords indicating old posting
    STALE_KEYWORDS = [
        'repost', 're-post', 'posting again', 'still looking',
        'extended', 'reopened'
    ]
    
    @classmethod
    def calculate_days_old(cls, posted_date: str) -> int:
        """
        Calculate days since posting from various date formats.
        
        Args:
            posted_date: Date string in various formats
            
        Returns:
            Number of days since posting
        """
        import pandas as pd
        if not posted_date or pd.isna(posted_date):
            return 30  # Default assumption
        
        posted_lower = str(posted_date).lower().strip()
        
        # Handle relative dates
        relative_patterns = [
            (r'today|just now|just posted|new', 0),
            (r'yesterday', 1),
            (r'(\d+)\s*hours?\s*ago', lambda m: 0 if int(m.group(1)) < 12 else 1),
            (r'(\d+)\s*days?\s*ago', lambda m: int(m.group(1))),
            (r'(\d+)\s*weeks?\s*ago', lambda m: int(m.group(1)) * 7),
            (r'(\d+)\s*months?\s*ago', lambda m: int(m.group(1)) * 30),
            (r'a\s*week\s*ago', 7),
            (r'a\s*month\s*ago', 30),
        ]
        
        for pattern, days in relative_patterns:
            match = re.search(pattern, posted_lower)
            if match:
                if callable(days):
                    return days(match)
                return days
        
        # Try parsing actual dates
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in date_formats:
            try:
                posted = datetime.strptime(posted_date.strip(), fmt)
                return (datetime.now() - posted).days
            except ValueError:
                continue
        
        return 14  # Default if can't parse
    
    @classmethod
    def score_freshness(cls, posted_date: str, description: str = "") -> Tuple[float, str]:
        """
        Score job freshness (0-100).
        
        Args:
            posted_date: When job was posted
            description: Job description for keyword analysis
            
        Returns:
            Tuple of (score, explanation)
        """
        days_old = cls.calculate_days_old(posted_date)
        
        # Get base score from days
        score = 100
        for threshold, threshold_score in sorted(cls.FRESHNESS_SCORES.items()):
            if days_old >= threshold:
                score = threshold_score
        
        explanation = f"{days_old} days old"
        
        # Adjust based on keywords
        import pandas as pd
        desc_lower = str(description).lower() if description and not pd.isna(description) else ""
        
        for keyword in cls.FRESH_KEYWORDS:
            if keyword in desc_lower:
                score = min(100, score + 10)
                explanation += f", has '{keyword}'"
                break
        
        for keyword in cls.STALE_KEYWORDS:
            if keyword in desc_lower:
                score = max(0, score - 20)
                explanation += f", has '{keyword}' (likely repost)"
                break
        
        return score, explanation


class ApplicationDeadlineScorer:
    """Score urgency based on application deadlines."""
    
    DEADLINE_KEYWORDS = [
        (r'deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'explicit'),
        (r'apply\s*by[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'explicit'),
        (r'closes?\s*on[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'explicit'),
        (r'last\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'explicit'),
        (r'(\d+)\s*positions?\s*(?:left|remaining|available)', 'positions'),
        (r'only\s*(\d+)\s*(?:spots?|openings?)', 'positions'),
        (r'filling\s*fast|limited\s*(?:spots?|openings?)', 'urgency_cue'),
        (r'immediate\s*(?:start|joining|hire)', 'immediate'),
        (r'urgent(?:ly)?\s*(?:hiring|looking|need)', 'urgent'),
    ]
    
    @classmethod
    def score_deadline_urgency(cls, description: str) -> Tuple[float, str]:
        """
        Score urgency based on deadlines (0-100).
        
        Args:
            description: Job description
            
        Returns:
            Tuple of (score, explanation)
        """
        import pandas as pd
        if not description or pd.isna(description):
            return 50, "No description available"
        desc_lower = str(description).lower()
        
        for pattern, urgency_type in cls.DEADLINE_KEYWORDS:
            match = re.search(pattern, desc_lower)
            if match:
                if urgency_type == 'explicit':
                    # Parse deadline date
                    try:
                        # Try to figure out days until deadline
                        return 90, f"Has explicit deadline: {match.group(1)}"
                    except:
                        return 85, "Has deadline mentioned"
                
                elif urgency_type == 'positions':
                    positions = int(match.group(1))
                    if positions <= 2:
                        return 95, f"Only {positions} position(s) remaining"
                    elif positions <= 5:
                        return 80, f"{positions} positions left"
                    else:
                        return 60, f"{positions} positions available"
                
                elif urgency_type == 'urgency_cue':
                    return 85, "Indicates 'filling fast' or limited openings"
                
                elif urgency_type == 'immediate':
                    return 90, "Needs immediate joining"
                
                elif urgency_type == 'urgent':
                    return 92, "Marked as urgent hiring"
        
        # No urgency signals
        return 50, "No specific deadline mentioned"


class CompanyResponseScorer:
    """Score based on company's known response patterns."""
    
    # Known responsive companies (based on Glassdoor/AmbitionBox data)
    RESPONSIVE_COMPANIES = {
        # Very responsive (often reply within days)
        'google': 90,
        'microsoft': 85,
        'amazon': 80,
        'flipkart': 85,
        'razorpay': 88,
        'phonepe': 85,
        'swiggy': 80,
        'zomato': 75,
        'cred': 90,
        'meesho': 82,
        'groww': 85,
        'zerodha': 88,
        'atlassian': 85,
        'salesforce': 80,
        
        # Moderately responsive
        'paytm': 70,
        'ola': 65,
        'uber': 75,
        'linkedin': 78,
        'adobe': 75,
        'oracle': 65,
        'walmart': 70,
        
        # Slower response (larger hiring volumes)
        'tcs': 50,
        'infosys': 55,
        'wipro': 50,
        'hcl': 52,
        'cognizant': 55,
        'accenture': 58,
        'capgemini': 55,
    }
    
    # Startup indicators (generally more responsive)
    STARTUP_INDICATORS = [
        'series a', 'series b', 'series c', 'seed funded',
        'yc', 'y combinator', 'sequoia', 'accel', 'tiger global',
        'startup', 'fast-growing', 'rapidly scaling'
    ]
    
    @classmethod
    def score_company_response(cls, company: str, description: str = "") -> Tuple[float, str]:
        """
        Score expected company responsiveness (0-100).
        
        Args:
            company: Company name
            description: Job description for context
            
        Returns:
            Tuple of (score, explanation)
        """
        import pandas as pd
        if not company or pd.isna(company):
            return 55, "Unknown company"
        company_lower = str(company).lower().strip()
        
        # Check known companies
        for known_company, score in cls.RESPONSIVE_COMPANIES.items():
            if known_company in company_lower:
                responsiveness = "high" if score >= 80 else "moderate" if score >= 60 else "standard"
                return score, f"{company} has {responsiveness} response rate"
        
        # Check for startup indicators
        desc_lower = str(description).lower() if description and not pd.isna(description) else ""
        for indicator in cls.STARTUP_INDICATORS:
            if indicator in desc_lower or indicator in company_lower:
                return 75, "Funded startup - typically responsive"
        
        # Default based on company name patterns
        if any(x in company_lower for x in ['labs', 'ai', 'tech', 'io']):
            return 70, "Tech company - likely responsive"
        
        return 55, "Unknown response pattern"


class RoleFitScorer:
    """Score how well the role matches candidate profile."""
    
    @classmethod
    def score_role_fit(
        cls,
        job_title: str,
        description: str,
        candidate_skills: List[str],
        candidate_experience: int,
        target_role: str = ""
    ) -> Tuple[float, str]:
        """
        Score role-candidate fit (0-100).
        
        Args:
            job_title: Job title
            description: Job description
            candidate_skills: Candidate's skills
            candidate_experience: Years of experience
            target_role: Candidate's target role
            
        Returns:
            Tuple of (score, explanation)
        """
        import pandas as pd
        score = 50  # Base score
        factors = []
        
        # Handle NaN values
        job_title = str(job_title) if job_title and not pd.isna(job_title) else ""
        description = str(description) if description and not pd.isna(description) else ""
        target_role = str(target_role) if target_role and not pd.isna(target_role) else ""
        
        title_lower = job_title.lower()
        desc_lower = description.lower()
        
        # Title match
        if target_role:
            target_words = set(target_role.lower().split())
            title_words = set(title_lower.split())
            title_overlap = len(target_words & title_words) / max(len(target_words), 1)
            title_score = title_overlap * 30
            score += title_score
            if title_overlap > 0.5:
                factors.append("Good title match")
        
        # Skill match
        skills_found = 0
        for skill in candidate_skills:
            if skill.lower() in desc_lower:
                skills_found += 1
        
        if candidate_skills:
            skill_ratio = skills_found / len(candidate_skills)
            skill_score = skill_ratio * 40
            score += skill_score
            if skill_ratio > 0.5:
                factors.append(f"{skills_found}/{len(candidate_skills)} skills matched")
        
        # Experience level check
        exp_patterns = [
            (r'(\d+)\+?\s*years?', lambda m: int(m.group(1))),
            (r'(\d+)\s*-\s*(\d+)\s*years?', lambda m: (int(m.group(1)) + int(m.group(2))) // 2),
        ]
        
        for pattern, extractor in exp_patterns:
            match = re.search(pattern, desc_lower)
            if match:
                required_exp = extractor(match)
                exp_diff = candidate_experience - required_exp
                
                if -1 <= exp_diff <= 3:
                    score += 10
                    factors.append("Experience level matches")
                elif exp_diff > 3:
                    score -= 5
                    factors.append("May be overqualified")
                elif exp_diff < -1:
                    score -= 10
                    factors.append("May need more experience")
                break
        
        score = max(0, min(100, score))
        explanation = ", ".join(factors) if factors else "Basic fit analysis"
        
        return score, explanation


class JobPriorityEngine:
    """Main engine to calculate overall job priority."""
    
    # Weight distribution for final score
    WEIGHTS = {
        'freshness': 0.25,
        'deadline_urgency': 0.20,
        'company_response': 0.20,
        'role_fit': 0.35,
    }
    
    URGENCY_THRESHOLDS = {
        85: ('🔴 URGENT', 'Apply immediately - high chance of quick response'),
        70: ('🟠 HIGH', 'Apply within 24 hours'),
        55: ('🟡 MEDIUM', 'Apply within 2-3 days'),
        40: ('🟢 NORMAL', 'Add to application queue'),
        0: ('⚪ LOW', 'Apply if time permits'),
    }
    
    @classmethod
    def calculate_priority(
        cls,
        job: Dict,
        candidate_skills: List[str] = None,
        candidate_experience: int = 5,
        target_role: str = ""
    ) -> JobPriority:
        """
        Calculate overall priority for a job.
        
        Args:
            job: Job dictionary with title, company, description, posted_date
            candidate_skills: Candidate's skills
            candidate_experience: Years of experience
            target_role: Target role
            
        Returns:
            JobPriority object with scores and recommendations
        """
        title = job.get('title', '')
        company = job.get('company', '')
        description = job.get('description', '')
        posted_date = job.get('posted_date', job.get('date', ''))
        
        if candidate_skills is None:
            candidate_skills = USER_DETAILS.get('key_skills', '').split(',')
        
        if not target_role:
            target_role = USER_DETAILS.get('target_role', '')
        
        # Calculate individual scores
        freshness_score, freshness_exp = PostingFreshnessScorer.score_freshness(
            posted_date, description
        )
        
        deadline_score, deadline_exp = ApplicationDeadlineScorer.score_deadline_urgency(
            description
        )
        
        response_score, response_exp = CompanyResponseScorer.score_company_response(
            company, description
        )
        
        fit_score, fit_exp = RoleFitScorer.score_role_fit(
            title, description, candidate_skills, candidate_experience, target_role
        )
        
        # Calculate weighted score
        factors = {
            'freshness': freshness_score,
            'deadline_urgency': deadline_score,
            'company_response': response_score,
            'role_fit': fit_score
        }
        
        priority_score = sum(
            factors[factor] * weight
            for factor, weight in cls.WEIGHTS.items()
        )
        
        # Determine urgency level
        urgency_level = '⚪ LOW'
        recommended_action = 'Apply if time permits'
        
        for threshold, (level, action) in sorted(cls.URGENCY_THRESHOLDS.items(), reverse=True):
            if priority_score >= threshold:
                urgency_level = level
                recommended_action = action
                break
        
        return JobPriority(
            job_id=job.get('id', f"{company}_{title}"[:50]),
            title=title,
            company=company,
            priority_score=round(priority_score, 1),
            urgency_level=urgency_level,
            factors={
                'freshness': f"{freshness_score:.0f} ({freshness_exp})",
                'deadline': f"{deadline_score:.0f} ({deadline_exp})",
                'response_rate': f"{response_score:.0f} ({response_exp})",
                'role_fit': f"{fit_score:.0f} ({fit_exp})"
            },
            recommended_action=recommended_action
        )


def prioritize_jobs(jobs_df, output_path: str = 'data/prioritized_jobs.csv') -> 'pd.DataFrame':
    """
    Prioritize all jobs and return sorted DataFrame.
    
    Args:
        jobs_df: DataFrame with job listings
        output_path: Where to save prioritized jobs
        
    Returns:
        Sorted DataFrame with priority scores
    """
    import pandas as pd
    
    priorities = []
    
    for idx, row in jobs_df.iterrows():
        job = row.to_dict()
        priority = JobPriorityEngine.calculate_priority(job)
        
        priorities.append({
            'title': priority.title,
            'company': priority.company,
            'priority_score': priority.priority_score,
            'urgency_level': priority.urgency_level,
            'recommended_action': priority.recommended_action,
            'freshness': priority.factors.get('freshness', ''),
            'role_fit': priority.factors.get('role_fit', ''),
            **{k: v for k, v in row.items() if k not in ['title', 'company']}
        })
    
    priority_df = pd.DataFrame(priorities)
    priority_df = priority_df.sort_values('priority_score', ascending=False)
    
    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    priority_df.to_csv(output_path, index=False)
    
    print(f"\n📊 Job Priority Report:")
    print(f"Total jobs analyzed: {len(priority_df)}")
    
    urgent = len(priority_df[priority_df['priority_score'] >= 85])
    high = len(priority_df[(priority_df['priority_score'] >= 70) & (priority_df['priority_score'] < 85)])
    medium = len(priority_df[(priority_df['priority_score'] >= 55) & (priority_df['priority_score'] < 70)])
    
    print(f"🔴 Urgent (85+): {urgent} jobs")
    print(f"🟠 High (70-84): {high} jobs")
    print(f"🟡 Medium (55-69): {medium} jobs")
    print(f"Saved prioritized jobs to: {output_path}")
    
    return priority_df


def get_top_priority_jobs(jobs_df, top_n: int = 10) -> List[JobPriority]:
    """
    Get top N highest priority jobs.
    
    Args:
        jobs_df: DataFrame with job listings
        top_n: Number of top jobs to return
        
    Returns:
        List of JobPriority objects
    """
    priorities = []
    
    for idx, row in jobs_df.iterrows():
        job = row.to_dict()
        priority = JobPriorityEngine.calculate_priority(job)
        priorities.append(priority)
    
    # Sort by priority score
    priorities.sort(key=lambda x: x.priority_score, reverse=True)
    
    return priorities[:top_n]


if __name__ == "__main__":
    # Example usage
    sample_jobs = [
        {
            'title': 'Senior Data Engineer',
            'company': 'Razorpay',
            'description': '''
            We are urgently looking for a Senior Data Engineer.
            Requirements: 5+ years experience, Python, Spark, AWS, Airflow.
            Only 2 positions remaining. Apply by 15/01/2025.
            ''',
            'posted_date': '2 days ago'
        },
        {
            'title': 'Software Developer',
            'company': 'TCS',
            'description': '''
            Looking for Software Developer with Java, Spring Boot experience.
            3-5 years experience required. Multiple openings.
            ''',
            'posted_date': '2 weeks ago'
        },
        {
            'title': 'ML Engineer',
            'company': 'Cred',
            'description': '''
            Immediate hiring for ML Engineer position.
            Required: Python, PyTorch, TensorFlow, MLOps.
            Series D funded startup, fast-growing team.
            ''',
            'posted_date': 'Posted today'
        }
    ]
    
    print("=" * 60)
    print("JOB PRIORITY ANALYSIS")
    print("=" * 60)
    
    for job in sample_jobs:
        priority = JobPriorityEngine.calculate_priority(
            job,
            candidate_skills=['Python', 'AWS', 'Spark', 'SQL', 'Airflow'],
            candidate_experience=5,
            target_role='Data Engineer'
        )
        
        print(f"\n{priority.urgency_level} {priority.title} at {priority.company}")
        print(f"Priority Score: {priority.priority_score}/100")
        print(f"Action: {priority.recommended_action}")
        print("Factors:")
        for factor, detail in priority.factors.items():
            print(f"  • {factor}: {detail}")
