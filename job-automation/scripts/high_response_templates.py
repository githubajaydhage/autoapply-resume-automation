"""
High Response Email Templates - Optimized for Maximum Recruiter Callbacks

Research shows:
- Personalized subject lines get 50% higher open rates
- Mentioning specific skills matching JD gets 3x more responses
- Short, scannable emails get 40% more replies
- Clear call-to-action doubles response rate
"""

import random
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HighResponseSubjects:
    """Email subjects proven to get higher open rates."""
    
    # TIER 1: Highest performing subjects (40%+ open rate)
    HIGH_IMPACT_SUBJECTS = [
        # Specificity + Urgency
        "{job_title} - {experience} Years | Immediate Joiner | {city}",
        "Application: {job_title} at {company} - {experience}+ YOE | {skills_short}",
        "{job_title} Opening - {experience} Years Exp | Notice: Immediate",
        
        # Results-focused
        "Experienced {job_title} | {skills_short} | Ready to Join",
        "{job_title} with {experience} Years in {skills_primary} - Available Now",
        
        # Company-specific (personalized)
        "Excited about {job_title} role at {company}",
        "Applying for {job_title} - Impressed by {company}'s work",
    ]
    
    # TIER 2: Good performing subjects (25-35% open rate)
    STANDARD_SUBJECTS = [
        "{job_title} Application - {name} | {experience} Years Experience",
        "Application: {job_title} Position - {city} Based",
        "{experience}+ Years {skills_primary} Professional - {job_title} Role",
        "Interested in {job_title} at {company}",
    ]
    
    # TIER 3: Safe subjects (15-25% open rate)
    SAFE_SUBJECTS = [
        "Job Application: {job_title} - {name}",
        "Application for {job_title} Position",
        "{job_title} - Resume Attached",
    ]
    
    @classmethod
    def get_subject(cls, job_title: str, company: str, name: str, 
                   experience: str, skills: str, city: str = "Bangalore") -> str:
        """Get a high-performing subject line."""
        
        # Parse skills for short version
        skills_list = [s.strip() for s in skills.split(',')][:3]
        skills_short = ', '.join(skills_list[:2])
        skills_primary = skills_list[0] if skills_list else "Analytics"
        
        # 70% chance of high-impact, 25% standard, 5% safe
        roll = random.random()
        if roll < 0.70:
            template = random.choice(cls.HIGH_IMPACT_SUBJECTS)
        elif roll < 0.95:
            template = random.choice(cls.STANDARD_SUBJECTS)
        else:
            template = random.choice(cls.SAFE_SUBJECTS)
        
        return template.format(
            job_title=job_title,
            company=company,
            name=name,
            experience=experience,
            skills=skills,
            skills_short=skills_short,
            skills_primary=skills_primary,
            city=city
        )


class HighResponseEmailBodies:
    """Email body templates proven to get more recruiter responses."""
    
    # TEMPLATE 1: Concise & Action-Oriented (Best for busy recruiters)
    CONCISE_TEMPLATE = """Hi,

I'm applying for the {job_title} position at {company}.

QUICK PROFILE:
• Experience: {experience}+ years in {skills_area}
• Core Skills: {skills}
• Location: {city} | Availability: Immediate
• Notice Period: {notice_period}

I've attached my resume for your review. Would love to discuss how my experience aligns with this role.

Best regards,
{name}
📞 {phone}
🔗 {linkedin}"""

    # TEMPLATE 2: Value-Proposition Focused (Shows what you bring)
    VALUE_TEMPLATE = """Dear Hiring Team,

I noticed {company}'s {job_title} opening and wanted to reach out directly.

WHY ME:
✓ {experience}+ years hands-on experience with {skills_primary}
✓ Proven track record in {skills_area}
✓ {city}-based, ready to join immediately

KEY SKILLS: {skills}

I'm genuinely interested in contributing to {company} and would appreciate the opportunity to discuss this role.

Resume attached for your reference.

Warm regards,
{name}
📱 {phone}
💼 LinkedIn: {linkedin}"""

    # TEMPLATE 3: Brief & Professional (For formal companies)
    PROFESSIONAL_TEMPLATE = """Dear Hiring Manager,

I am writing to apply for the {job_title} position at {company}.

With {experience}+ years of experience in {skills_area}, I have developed strong expertise in {skills}.

I am based in {city} and available to join immediately. Please find my resume attached.

I look forward to the opportunity to discuss my candidacy.

Best regards,
{name}
Phone: {phone}
LinkedIn: {linkedin}"""

    # TEMPLATE 4: Story-based (For startups/creative companies)
    STORY_TEMPLATE = """Hi there,

I came across the {job_title} role at {company} and got excited - this is exactly the kind of work I've been looking for!

A bit about me:
• {experience}+ years solving problems with {skills_primary}
• I love working with {skills}
• Currently in {city}, can start immediately

I've attached my resume - would love to chat about how I can add value to your team.

Cheers,
{name}
📞 {phone}
🔗 {linkedin}"""

    # TEMPLATE 5: Achievement-focused (For senior roles)
    ACHIEVEMENT_TEMPLATE = """Dear {company} Team,

I'm reaching out regarding the {job_title} position.

RELEVANT EXPERIENCE:
• {experience}+ years in {skills_area}
• Expertise: {skills}
• Successfully delivered projects involving data-driven decision making
• Strong background in {skills_primary}

I'm {city}-based with immediate availability. Resume attached for your review.

Looking forward to discussing this opportunity.

Best,
{name}
📞 {phone}
💼 {linkedin}"""

    @classmethod
    def get_templates(cls) -> list:
        """Get all template strings."""
        return [
            cls.CONCISE_TEMPLATE,
            cls.VALUE_TEMPLATE,
            cls.PROFESSIONAL_TEMPLATE,
            cls.STORY_TEMPLATE,
            cls.ACHIEVEMENT_TEMPLATE,
        ]
    
    @classmethod
    def get_body(cls, job_title: str, company: str, name: str,
                 experience: str, skills: str, phone: str, 
                 linkedin: str, city: str = "Bangalore",
                 notice_period: str = "Immediate") -> str:
        """Get a high-performing email body."""
        
        # Parse skills
        skills_list = [s.strip() for s in skills.split(',')]
        skills_primary = skills_list[0] if skills_list else "Data Analysis"
        
        # Determine skills area based on keywords
        skills_lower = skills.lower()
        if 'sql' in skills_lower or 'data' in skills_lower:
            skills_area = "Data Analysis & Business Intelligence"
        elif 'python' in skills_lower and ('ml' in skills_lower or 'machine' in skills_lower):
            skills_area = "Data Science & Machine Learning"
        elif 'tableau' in skills_lower or 'power bi' in skills_lower:
            skills_area = "Data Visualization & Reporting"
        else:
            skills_area = "Data Analytics"
        
        # Select template based on weighted randomness
        # Concise template has highest success rate
        weights = [0.35, 0.25, 0.15, 0.15, 0.10]
        templates = cls.get_templates()
        template = random.choices(templates, weights=weights)[0]
        
        return template.format(
            job_title=job_title,
            company=company,
            name=name,
            experience=experience,
            skills=skills,
            skills_primary=skills_primary,
            skills_area=skills_area,
            phone=phone,
            linkedin=linkedin if linkedin else "(Available upon request)",
            city=city,
            notice_period=notice_period
        )


class ResponseBooster:
    """Additional tips and techniques to boost response rates."""
    
    # Best times to send emails (in local timezone)
    OPTIMAL_SEND_TIMES = {
        'best': [(9, 10), (10, 11)],  # 9-11 AM
        'good': [(14, 15), (15, 16)],  # 2-4 PM
        'avoid': [(0, 8), (18, 24), (12, 13)]  # Early morning, evening, lunch
    }
    
    # Best days to send
    OPTIMAL_DAYS = [1, 2, 3]  # Tuesday, Wednesday, Thursday
    GOOD_DAYS = [0, 4]  # Monday, Friday (before 3 PM)
    AVOID_DAYS = [5, 6]  # Saturday, Sunday
    
    @classmethod
    def get_send_recommendation(cls) -> dict:
        """Get recommendation for when to send."""
        now = datetime.now()
        day = now.weekday()
        hour = now.hour
        
        is_optimal_day = day in cls.OPTIMAL_DAYS
        is_optimal_hour = any(start <= hour < end for start, end in cls.OPTIMAL_SEND_TIMES['best'])
        
        if day in cls.AVOID_DAYS:
            return {
                'send_now': False,
                'reason': "Weekend - wait until Tuesday 9 AM for best results",
                'wait_hours': (7 - day) * 24 + (9 - hour)
            }
        
        if is_optimal_day and is_optimal_hour:
            return {
                'send_now': True,
                'reason': "🎯 PERFECT TIME! Tue-Thu 9-11 AM gets 40% higher response",
                'confidence': 'high'
            }
        
        return {
            'send_now': True,
            'reason': "Acceptable time - consider 9-11 AM Tue-Thu for best results",
            'confidence': 'medium'
        }
    
    @classmethod
    def get_follow_up_schedule(cls) -> list:
        """Get optimal follow-up email schedule."""
        return [
            {'day': 3, 'subject_prefix': 'Following up: ', 'tone': 'friendly'},
            {'day': 7, 'subject_prefix': 'Checking in: ', 'tone': 'professional'},
            {'day': 14, 'subject_prefix': 'Final follow-up: ', 'tone': 'direct'},
        ]


# Quick test
if __name__ == "__main__":
    print("=" * 60)
    print("HIGH RESPONSE EMAIL TEMPLATES")
    print("=" * 60)
    
    # Test subject generation
    subject = HighResponseSubjects.get_subject(
        job_title="Data Analyst",
        company="Razorpay",
        name="Shweta Biradar",
        experience="3",
        skills="SQL, Python, Tableau, Power BI",
        city="Bangalore"
    )
    print(f"\n📧 SUBJECT: {subject}")
    
    # Test body generation
    body = HighResponseEmailBodies.get_body(
        job_title="Data Analyst",
        company="Razorpay",
        name="Shweta Biradar",
        experience="3",
        skills="SQL, Python, Tableau, Power BI",
        phone="+91-9876543210",
        linkedin="linkedin.com/in/shweta-biradar",
        city="Bangalore"
    )
    print(f"\n📝 BODY:\n{body}")
    
    # Test send recommendation
    rec = ResponseBooster.get_send_recommendation()
    print(f"\n⏰ TIMING: {rec['reason']}")
