"""
🔍 AI HR EMAIL DISCOVERY - Smart HR Contact Finder

Uses FREE AI to:
1. Extract HR emails from company websites
2. Generate likely HR email patterns
3. Find hiring manager contacts from job posts
4. Discover recruiter emails from LinkedIn posts
5. Validate and verify email formats
6. Build company-specific email patterns

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import csv
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import get_ai, FreeAIManager
except ImportError:
    from free_ai_providers import get_ai, FreeAIManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class AIHREmailDiscovery:
    """
    🔍 AI-Powered HR Email Discovery
    
    Uses LLMs to intelligently find HR contact emails.
    """
    
    # Common HR email patterns
    HR_PATTERNS = [
        'hr@{domain}',
        'careers@{domain}',
        'jobs@{domain}',
        'hiring@{domain}',
        'recruitment@{domain}',
        'talent@{domain}',
        'people@{domain}',
        'join@{domain}',
        'work@{domain}',
        'team@{domain}',
        'apply@{domain}',
    ]
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # Initialize AI
        self.ai = get_ai()
        
        # Email database
        self.discovered_emails_path = os.path.join(self.data_path, 'ai_discovered_hr_emails.csv')
        self.email_patterns_path = os.path.join(self.data_path, 'company_email_patterns.json')
        
        # Load existing data
        self.known_emails = self._load_known_emails()
        self.email_patterns = self._load_email_patterns()
        
        logging.info(f"🔍 AI HR Email Discovery initialized ({len(self.known_emails)} known emails)")
    
    def _load_known_emails(self) -> Set[str]:
        """Load known HR emails."""
        emails = set()
        
        # Load from various sources
        email_files = [
            'ai_discovered_hr_emails.csv',
            'all_hr_emails.csv',
            'curated_hr_emails.csv',
            'verified_hr_emails.csv'
        ]
        
        for filename in email_files:
            filepath = os.path.join(self.data_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            email = row.get('email', row.get('Email', ''))
                            if email and '@' in email:
                                emails.add(email.lower().strip())
                except:
                    pass
        
        return emails
    
    def ai_research_company(self, company: str, job_description: str = None) -> Dict:
        """
        🤖 AI researches company for better email discovery.
        """
        try:
            prompt = f"""Research company: {company}
Job Context: {job_description[:500] if job_description else 'General inquiry'}

Provide company intelligence:
1. Industry and business type
2. Company size estimate
3. Likely email domain(s)
4. HR department structure
5. Hiring process style
6. Best contact timing

Respond in JSON:
{{
  "industry": "industry name",
  "size": "startup|small|medium|large|enterprise",
  "domains": ["primary.com", "alternate.com"],
  "hr_structure": "centralized|distributed|outsourced",
  "hiring_style": "fast|thorough|selective",
  "best_timing": "morning|afternoon|any"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=300)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        research = json.loads(json_match.group())
                        logging.info(f"🔍 AI research: {company} is {research.get('size', 'unknown')} {research.get('industry', 'company')}")
                        return research
                except:
                    pass
            
            return {"industry": "unknown", "size": "medium", "domains": [], "hr_structure": "centralized", "hiring_style": "standard", "best_timing": "morning"}
            
        except Exception as e:
            logging.warning(f"⚠️ AI company research failed: {e}")
            return {"industry": "unknown", "size": "medium", "domains": [], "hr_structure": "centralized", "hiring_style": "standard", "best_timing": "morning"}
    
    def _load_email_patterns(self) -> Dict:
        """Load company email patterns."""
        if os.path.exists(self.email_patterns_path):
            try:
                with open(self.email_patterns_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_email_patterns(self):
        """Save email patterns."""
        try:
            with open(self.email_patterns_path, 'w') as f:
                json.dump(self.email_patterns, f, indent=2)
        except:
            pass
    
    def extract_emails_from_text(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        # Email regex pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        
        # Filter and clean
        valid_emails = []
        for email in emails:
            email = email.lower().strip()
            # Skip common non-HR emails
            skip_patterns = ['noreply', 'no-reply', 'support@', 'info@', 'sales@', 'marketing@', 'admin@']
            if not any(pat in email for pat in skip_patterns):
                valid_emails.append(email)
        
        return list(set(valid_emails))
    
    def _ai_generate_smart_patterns(self, company: str, domain: str, industry: str = None, company_size: str = None) -> List[Dict]:
        """
        🤖 AI generates intelligent HR email patterns based on company profile.
        """
        try:
            prompt = f"""Company: {company}
Domain: {domain}
Industry: {industry or 'Unknown'}
Company Size: {company_size or 'Unknown'}

Generate the 8 most likely HR/recruiting email patterns for this company. Consider:
1. Industry standards and naming conventions
2. Company culture (startup vs enterprise)
3. Regional preferences
4. Common HR department structures

Respond with ONLY email patterns in this format:
hr@{domain}
careers@{domain}
jobs@{domain}
hiring@{domain}
talent@{domain}
recruitment@{domain}
people@{domain}
join@{domain}

No explanation, just the email patterns."""
            
            ai_response = self.ai.generate(prompt, max_tokens=200)
            if not ai_response:
                return self._fallback_patterns(domain)
            
            # Extract email patterns from AI response
            patterns = []
            for line in ai_response.strip().split('\n'):
                line = line.strip()
                if '@' in line and domain in line:
                    patterns.append({
                        'email': line,
                        'confidence': 'ai_high',
                        'source': 'ai_generated'
                    })
            
            # Store successful pattern for company
            if patterns:
                self.email_patterns[company.lower()] = patterns[0]['email'].replace(domain, '{domain}')
                self._save_email_patterns()
            
            logging.info(f"✅ AI generated {len(patterns)} patterns for {company}")
            return patterns[:5]  # Top 5 patterns
            
        except Exception as e:
            logging.warning(f"⚠️ AI pattern generation failed: {e}")
            return self._fallback_patterns(domain)
    
    def _fallback_patterns(self, domain: str) -> List[Dict]:
        """Fallback patterns when AI fails."""
        return [{'email': pattern.format(domain=domain), 'confidence': 'medium', 'source': 'fallback'} 
                for pattern in self.HR_PATTERNS[:5]]
    
    def ai_extract_hidden_emails(self, page_content: str, company_url: str = None) -> List[str]:
        """
        🤖 AI extracts hidden/obfuscated emails from webpage content.
        """
        try:
            prompt = f"""Webpage content from {company_url or 'unknown'}:
{page_content[:2500]}

Extract ALL possible contact emails, especially:
1. Hidden emails (JavaScript encoded, base64, HTML entities)
2. HR/recruiting contacts
3. Careers/jobs contacts
4. Contact form emails
5. Alternative contact methods

Find emails that regex might miss due to:
- JavaScript obfuscation
- CSS hiding
- Character encoding
- Split across elements
- Dynamic generation

Respond with ONLY email addresses, one per line. No explanations."""
            
            ai_response = self.ai.generate(prompt, max_tokens=300)
            if not ai_response:
                return []
            
            # Extract emails from AI response
            found_emails = []
            for line in ai_response.strip().split('\n'):
                line = line.strip()
                if '@' in line and '.' in line:
                    # Clean up the email
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                    if email_match:
                        email = email_match.group().lower()
                        # Skip obvious non-HR emails
                        skip_patterns = ['noreply', 'no-reply', 'support@', 'admin@', 'webmaster@', 'postmaster@']
                        if not any(pat in email for pat in skip_patterns):
                            found_emails.append(email)
            
            logging.info(f"🤖 AI extracted {len(found_emails)} hidden emails")
            return list(set(found_emails))
            
        except Exception as e:
            logging.warning(f"⚠️ AI email extraction failed: {e}")
            return []
    
    def ai_analyze_company_hiring_patterns(self, company: str, recent_job_posts: List[str] = None) -> Dict:
        """
        🤖 AI analyzes company hiring patterns and predicts best contact strategy.
        """
        try:
            job_context = '\n'.join(recent_job_posts[:3]) if recent_job_posts else 'No recent job posts available'
            
            prompt = f"""Company: {company}
Recent Job Posts:
{job_context}

Analyze hiring patterns and provide:
1. Best contact approach (email vs LinkedIn vs referral)
2. Optimal outreach timing
3. Preferred communication style
4. Response probability factors
5. Department structure insights

Respond in JSON format:
{{
  "best_approach": "email|linkedin|referral",
  "timing": "morning|afternoon|evening",
  "style": "formal|casual|technical",
  "response_probability": "high|medium|low",
  "insights": "key insights about this company"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=400)
            if ai_response:
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except:
                    pass
            
            # Fallback analysis
            return {
                "best_approach": "email",
                "timing": "morning", 
                "style": "professional",
                "response_probability": "medium",
                "insights": f"Standard outreach recommended for {company}"
            }
            
        except Exception as e:
            logging.warning(f"⚠️ AI company analysis failed: {e}")
            return {"best_approach": "email", "timing": "morning", "style": "professional", "response_probability": "medium", "insights": "Standard approach"}
    
    def generate_hr_emails_for_company(self, company: str, domain: str = None, industry: str = None, company_size: str = None) -> List[Dict]:
        """
        🏢 Use AI to generate likely HR email patterns for a company.
        """
        if not domain:
            domain = self._guess_domain(company)
        
        # Check if we already know this company's patterns
        if company.lower() in self.email_patterns:
            pattern = self.email_patterns[company.lower()]
            return [{'email': pattern.format(domain=domain), 'confidence': 'high', 'source': 'pattern_cache'}]
        
        logging.info(f"🔍 Generating AI-powered HR emails for {company}...")
        
        # Use AI to generate smart email patterns
        ai_patterns = self._ai_generate_smart_patterns(company, domain, industry, company_size)
        if ai_patterns:
            return ai_patterns
        
        prompt = f"""You are an HR email pattern expert. Generate likely HR email addresses for:

COMPANY: {company}
DOMAIN: {domain}

Based on common patterns, generate 5-8 likely HR email addresses.

Return JSON array:
[
  {{"email": "hr@{domain}", "role": "HR Team", "confidence": "high|medium|low"}},
  {{"email": "careers@{domain}", "role": "Careers", "confidence": "high|medium|low"}},
  ...
]

Consider:
1. Common HR email patterns (hr@, careers@, jobs@, hiring@, talent@, recruitment@)
2. Indian company patterns (if applicable)
3. Startup vs enterprise patterns
4. Industry-specific patterns

Return ONLY valid JSON array."""

        result = self.ai.generate(prompt, max_tokens=400)
        
        emails = []
        if result:
            try:
                json_match = re.search(r'\[[\s\S]*\]', result)
                if json_match:
                    emails = json.loads(json_match.group())
            except:
                pass
        
        # Fallback to default patterns
        if not emails:
            emails = self._generate_default_emails(domain)
        
        # Add source info
        for e in emails:
            e['company'] = company
            e['domain'] = domain
            e['source'] = 'ai_generated'
            e['discovered_at'] = datetime.now().isoformat()
        
        return emails
    
    def _guess_domain(self, company: str) -> str:
        """Guess domain from company name."""
        # Clean company name
        clean_name = company.lower()
        clean_name = re.sub(r'[^a-z0-9]', '', clean_name)
        clean_name = clean_name.replace('technologies', '').replace('solutions', '')
        clean_name = clean_name.replace('pvt', '').replace('ltd', '').replace('inc', '')
        clean_name = clean_name.replace('private', '').replace('limited', '')
        clean_name = clean_name.strip()
        
        # Common domain patterns
        domains = [
            f"{clean_name}.com",
            f"{clean_name}.io",
            f"{clean_name}.in",
            f"{clean_name}.co.in",
        ]
        
        return domains[0]
    
    def _generate_default_emails(self, domain: str) -> List[Dict]:
        """Generate default HR email patterns."""
        emails = []
        for pattern in self.HR_PATTERNS:
            emails.append({
                'email': pattern.format(domain=domain),
                'role': pattern.split('@')[0].title(),
                'confidence': 'medium'
            })
        return emails
    
    def analyze_job_post_for_contacts(self, job_post: str) -> Dict:
        """
        📋 Use AI to extract contact info from a job posting.
        """
        prompt = f"""Analyze this job posting and extract ALL contact information:

JOB POSTING:
{job_post[:2000]}

Return JSON with any found information:
{{
  "hr_email": "email if found",
  "hr_name": "HR person name if found",
  "hr_phone": "phone if found",
  "apply_link": "application URL if found",
  "company_email_pattern": "detected pattern like firstname.lastname@company.com",
  "linkedin_profiles": ["any LinkedIn URLs mentioned"],
  "other_contacts": ["any other contact info"]
}}

If something is not found, set it to null.
Return ONLY valid JSON."""

        result = self.ai.generate(prompt, max_tokens=400)
        
        if result:
            try:
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # Fallback: extract emails directly
        emails = self.extract_emails_from_text(job_post)
        return {
            'hr_email': emails[0] if emails else None,
            'other_contacts': emails[1:] if len(emails) > 1 else []
        }
    
    def discover_emails_for_companies(self, companies: List[str]) -> List[Dict]:
        """
        🏢 Bulk discover HR emails for multiple companies.
        """
        logging.info(f"🔍 Discovering HR emails for {len(companies)} companies...")
        
        all_emails = []
        
        for i, company in enumerate(companies):
            logging.info(f"  [{i+1}/{len(companies)}] Processing {company}...")
            
            emails = self.generate_hr_emails_for_company(company)
            all_emails.extend(emails)
            
            # Rate limiting
            if i % 5 == 4:
                time.sleep(1)
        
        # Save discovered emails
        self._save_discovered_emails(all_emails)
        
        logging.info(f"✅ Discovered {len(all_emails)} potential HR emails")
        return all_emails
    
    def _save_discovered_emails(self, emails: List[Dict]):
        """Save discovered emails to CSV."""
        os.makedirs(self.data_path, exist_ok=True)
        
        with open(self.discovered_emails_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['email', 'company', 'role', 'confidence', 'domain', 'source', 'discovered_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for email in emails:
                writer.writerow(email)
        
        logging.info(f"💾 Saved to {self.discovered_emails_path}")
    
    def find_hr_from_linkedin_post(self, post_text: str) -> Dict:
        """
        🔗 Extract HR info from a LinkedIn job post.
        """
        prompt = f"""Extract HR/recruiter information from this LinkedIn post:

POST:
{post_text[:1500]}

Return JSON:
{{
  "recruiter_name": "name if mentioned",
  "recruiter_title": "title like 'HR Manager'",
  "company": "company name",
  "email": "email if found",
  "linkedin_url": "LinkedIn profile URL if mentioned",
  "email_pattern_hint": "any hint about email format like 'reach me at name@company'"
}}

Return ONLY valid JSON."""

        result = self.ai.generate(prompt, max_tokens=300)
        
        if result:
            try:
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {}
    
    def generate_personalized_email_address(
        self,
        hr_name: str,
        company: str,
        domain: str = None
    ) -> List[str]:
        """
        👤 Generate personalized email from HR name.
        """
        if not domain:
            domain = self._guess_domain(company)
        
        # Parse name
        name_parts = hr_name.lower().split()
        if len(name_parts) < 2:
            return [f"hr@{domain}"]
        
        first = name_parts[0]
        last = name_parts[-1]
        
        # Common patterns
        patterns = [
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first}@{domain}",
            f"{last}@{domain}",
        ]
        
        # Store pattern for this company
        self.email_patterns[company.lower()] = f"{{first}}.{{last}}@{domain}"
        self._save_email_patterns()
        
        return patterns
    
    def validate_email_format(self, email: str) -> Dict:
        """
        ✅ Validate email format (without sending).
        """
        result = {
            'email': email,
            'valid_format': False,
            'issues': []
        }
        
        # Basic format check
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            result['issues'].append('Invalid format')
            return result
        
        result['valid_format'] = True
        
        # Check for common issues
        local, domain = email.split('@')
        
        if len(local) < 2:
            result['issues'].append('Local part too short')
        if '..' in email:
            result['issues'].append('Double dots')
        if domain.startswith('.') or domain.endswith('.'):
            result['issues'].append('Domain starts/ends with dot')
        
        # Check for disposable domains
        disposable_domains = ['mailinator.com', 'tempmail.com', 'throwaway.email']
        if domain in disposable_domains:
            result['issues'].append('Disposable email domain')
        
        return result
    
    def run_discovery_pipeline(self, companies: List[str] = None) -> Dict:
        """
        🚀 Run full HR email discovery pipeline.
        """
        logging.info("\n" + "="*60)
        logging.info("🔍 AI HR EMAIL DISCOVERY PIPELINE")
        logging.info("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'companies_processed': 0,
            'emails_discovered': 0,
            'emails': []
        }
        
        # If no companies provided, load from AI research
        if not companies:
            research_path = os.path.join(self.data_path, 'ai_job_research.json')
            if os.path.exists(research_path):
                with open(research_path, 'r') as f:
                    research = json.load(f)
                    companies = [c['company'] for c in research.get('companies', [])]
        
        if not companies:
            # Default companies
            companies = [
                'Infosys', 'TCS', 'Wipro', 'HCL Technologies', 'Tech Mahindra',
                'Accenture', 'Cognizant', 'Capgemini', 'IBM India', 'Microsoft India',
                'Google India', 'Amazon India', 'Flipkart', 'Swiggy', 'Zomato',
                'PhonePe', 'Paytm', 'CRED', 'Razorpay', 'Zerodha'
            ]
        
        # Discover emails
        emails = self.discover_emails_for_companies(companies)
        
        results['companies_processed'] = len(companies)
        results['emails_discovered'] = len(emails)
        results['emails'] = emails
        
        # Print summary
        print("\n" + "="*60)
        print("📊 DISCOVERY SUMMARY")
        print("="*60)
        print(f"🏢 Companies Processed: {results['companies_processed']}")
        print(f"📧 Emails Discovered: {results['emails_discovered']}")
        
        high_conf = len([e for e in emails if e.get('confidence') == 'high'])
        print(f"⭐ High Confidence: {high_conf}")
        
        return results


def main():
    """Run AI HR email discovery."""
    discovery = AIHREmailDiscovery()
    discovery.run_discovery_pipeline()


if __name__ == '__main__':
    main()
