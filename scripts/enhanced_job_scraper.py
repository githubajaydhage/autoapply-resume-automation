"""
Enhanced Job Scraper - Adds more job sources including AngelList, Instahyre, and more
Uses multiple APIs and scraping techniques for comprehensive job coverage
"""

import requests
import pandas as pd
import os
import sys
import logging
import time
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# AI integration
try:
    from scripts.free_ai_providers import get_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class EnhancedJobScraper:
    """Scrapes jobs from multiple additional sources."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        self.output_path = os.path.join(self.data_path, 'enhanced_jobs.csv')
        
        # Initialize AI if available
        self.ai = get_ai() if AI_AVAILABLE else None
        if self.ai:
            logging.info("🤖 AI-powered job analysis enabled")
        
        # Default search parameters
        self.keywords = ['data analyst', 'business analyst', 'data scientist', 'analytics']
        self.locations = ['bangalore', 'india', 'remote']
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        self.all_jobs = []
    
    def scrape_wellfound_api(self) -> list:
        """
        Scrape from Wellfound (formerly AngelList Talent) API.
        Uses public GraphQL API endpoints.
        """
        logging.info("🚀 Scraping Wellfound (AngelList)...")
        jobs = []
        
        # Wellfound uses GraphQL, we'll use their public search endpoint
        base_url = "https://wellfound.com/api/v1/jobs/search"
        
        try:
            for keyword in self.keywords[:2]:  # Limit queries
                params = {
                    'query': keyword,
                    'location': 'india',
                    'remote': 'true',
                    'page': 1,
                    'per_page': 50
                }
                
                response = requests.get(
                    base_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        listings = data.get('jobs', data.get('results', []))
                        
                        for job in listings:
                            parsed = {
                                'title': job.get('title', ''),
                                'company': job.get('company', {}).get('name', job.get('company_name', '')),
                                'location': job.get('location', 'Remote'),
                                'url': job.get('url', f"https://wellfound.com/jobs/{job.get('id', '')}"),
                                'source': 'Wellfound',
                                'scraped_at': datetime.now().isoformat(),
                                'remote': job.get('remote', True),
                                'salary': job.get('salary', '')
                            }
                            
                            if parsed['title'] and parsed['company']:
                                jobs.append(parsed)
                    except json.JSONDecodeError:
                        pass
                
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            logging.warning(f"Wellfound API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Wellfound")
        return jobs
    
    def scrape_instahyre_api(self) -> list:
        """
        Scrape from Instahyre - popular Indian job portal.
        Uses their public API endpoints.
        """
        logging.info("🏢 Scraping Instahyre...")
        jobs = []
        
        base_url = "https://www.instahyre.com/api/v1/job-listings/"
        
        try:
            params = {
                'query': 'data analyst',
                'location': 'bangalore',
                'page': 1,
                'page_size': 50
            }
            
            response = requests.get(
                base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('results', data.get('jobs', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', job.get('job_title', '')),
                            'company': job.get('company', {}).get('name', job.get('company_name', '')),
                            'location': job.get('location', job.get('city', 'India')),
                            'url': job.get('url', f"https://www.instahyre.com/job/{job.get('id', '')}"),
                            'source': 'Instahyre',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': 'remote' in str(job).lower(),
                            'salary': job.get('salary_range', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                
        except Exception as e:
            logging.warning(f"Instahyre API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Instahyre")
        return jobs
    
    def scrape_cutshort(self) -> list:
        """
        Scrape from Cutshort - Indian startup job platform.
        """
        logging.info("✂️ Scraping Cutshort...")
        jobs = []
        
        base_url = "https://cutshort.io/api/jobs/search"
        
        try:
            payload = {
                'query': 'data analyst',
                'location': 'bangalore',
                'experience': {'min': 0, 'max': 5}
            }
            
            response = requests.post(
                base_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('jobs', data.get('results', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', ''),
                            'company': job.get('company', {}).get('name', job.get('company_name', '')),
                            'location': job.get('location', 'India'),
                            'url': job.get('url', f"https://cutshort.io/job/{job.get('id', '')}"),
                            'source': 'Cutshort',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': job.get('remote', False),
                            'salary': job.get('salary', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logging.warning(f"Cutshort API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Cutshort")
        return jobs
    
    def scrape_linkedin_rss(self) -> list:
        """
        Scrape from LinkedIn RSS feeds (publicly available).
        Note: Limited data but legitimate access.
        """
        logging.info("🔗 Scraping LinkedIn RSS...")
        jobs = []
        
        # LinkedIn provides RSS feeds for job searches
        rss_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        
        try:
            params = {
                'keywords': 'data analyst',
                'location': 'India',
                'geoId': '102713980',  # India
                'start': 0
            }
            
            response = requests.get(
                rss_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for card in soup.find_all('div', class_='base-card'):
                    try:
                        title_elem = card.find('h3', class_='base-search-card__title')
                        company_elem = card.find('h4', class_='base-search-card__subtitle')
                        location_elem = card.find('span', class_='job-search-card__location')
                        link_elem = card.find('a', class_='base-card__full-link')
                        
                        parsed = {
                            'title': title_elem.get_text(strip=True) if title_elem else '',
                            'company': company_elem.get_text(strip=True) if company_elem else '',
                            'location': location_elem.get_text(strip=True) if location_elem else 'India',
                            'url': link_elem['href'] if link_elem and link_elem.get('href') else '',
                            'source': 'LinkedIn',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': False,
                            'salary': ''
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"LinkedIn RSS error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from LinkedIn")
        return jobs
    
    def scrape_glassdoor_api(self) -> list:
        """
        Scrape from Glassdoor public listings.
        """
        logging.info("🪟 Scraping Glassdoor...")
        jobs = []
        
        # Glassdoor's public API endpoint
        base_url = "https://www.glassdoor.co.in/Job/jobs.htm"
        
        try:
            params = {
                'sc.keyword': 'data analyst',
                'locT': 'C',
                'locId': '2906753',  # Bangalore
                'jobType': 'all',
            }
            
            response = requests.get(
                base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find job cards
                for card in soup.find_all(['li', 'div'], class_=re.compile(r'job.*card|react-job')):
                    try:
                        title_elem = card.find(['a', 'span'], class_=re.compile(r'job.*title'))
                        company_elem = card.find(['a', 'span'], class_=re.compile(r'employer'))
                        location_elem = card.find(['span'], class_=re.compile(r'location'))
                        
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        company = company_elem.get_text(strip=True) if company_elem else ''
                        
                        if title and company:
                            parsed = {
                                'title': title,
                                'company': company,
                                'location': location_elem.get_text(strip=True) if location_elem else 'India',
                                'url': title_elem.get('href', '') if title_elem and title_elem.name == 'a' else '',
                                'source': 'Glassdoor',
                                'scraped_at': datetime.now().isoformat(),
                                'remote': False,
                                'salary': ''
                            }
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"Glassdoor error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Glassdoor")
        return jobs
    
    def scrape_indeed_rss(self) -> list:
        """
        Scrape from Indeed RSS feeds.
        """
        logging.info("📋 Scraping Indeed...")
        jobs = []
        
        rss_url = "https://www.indeed.co.in/rss"
        
        try:
            params = {
                'q': 'data analyst',
                'l': 'bangalore',
                'sort': 'date'
            }
            
            response = requests.get(
                rss_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                
                for item in soup.find_all('item'):
                    try:
                        title = item.find('title')
                        link = item.find('link')
                        
                        # Parse company from title (format: "Title - Company")
                        title_text = title.get_text() if title else ''
                        parts = title_text.split(' - ')
                        job_title = parts[0] if parts else title_text
                        company = parts[1] if len(parts) > 1 else ''
                        
                        parsed = {
                            'title': job_title.strip(),
                            'company': company.strip(),
                            'location': 'Bangalore',
                            'url': link.get_text() if link else '',
                            'source': 'Indeed',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': 'remote' in title_text.lower(),
                            'salary': ''
                        }
                        
                        if parsed['title']:
                            jobs.append(parsed)
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.warning(f"Indeed RSS error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Indeed")
        return jobs
    
    def scrape_foundit(self) -> list:
        """
        Scrape from Foundit (formerly Monster India).
        """
        logging.info("👹 Scraping Foundit (Monster)...")
        jobs = []
        
        api_url = "https://www.foundit.in/middleware/jobsearch"
        
        try:
            payload = {
                'query': 'data analyst',
                'locations': ['bangalore'],
                'experience': {'min': 0, 'max': 5},
                'page': 1,
                'limit': 50
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    listings = data.get('jobs', data.get('jobDetails', []))
                    
                    for job in listings:
                        parsed = {
                            'title': job.get('title', job.get('designationName', '')),
                            'company': job.get('companyName', job.get('company', {}).get('name', '')),
                            'location': job.get('locations', job.get('location', 'India')),
                            'url': job.get('url', f"https://www.foundit.in/job/{job.get('jobId', '')}"),
                            'source': 'Foundit',
                            'scraped_at': datetime.now().isoformat(),
                            'remote': job.get('isRemote', False),
                            'salary': job.get('salary', '')
                        }
                        
                        if parsed['title'] and parsed['company']:
                            jobs.append(parsed)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logging.warning(f"Foundit API error: {e}")
        
        logging.info(f"   Found {len(jobs)} jobs from Foundit")
        return jobs
    
    def scrape_all(self) -> pd.DataFrame:
        """Scrape from all enhanced sources."""
        logging.info("="*60)
        logging.info("🔍 ENHANCED JOB SCRAPER")
        logging.info("="*60)
        
        all_jobs = []
        
        # Scrape from all sources
        scrapers = [
            self.scrape_wellfound_api,
            self.scrape_instahyre_api,
            self.scrape_cutshort,
            self.scrape_linkedin_rss,
            self.scrape_glassdoor_api,
            self.scrape_indeed_rss,
            self.scrape_foundit,
        ]
        
        for scraper in scrapers:
            try:
                jobs = scraper()
                all_jobs.extend(jobs)
            except Exception as e:
                logging.warning(f"Scraper error: {e}")
            time.sleep(2)  # Be polite between scrapers
        
        # Create DataFrame
        df = pd.DataFrame(all_jobs)
        
        if not df.empty:
            # Clean data
            df['title'] = df['title'].str.strip()
            df['company'] = df['company'].str.strip()
            df = df[df['title'] != '']
            df = df[df['company'] != '']
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['title', 'company'], keep='first')
            
            # Save
            df.to_csv(self.output_path, index=False)
            
            # 🤖 AI ENHANCEMENT: Analyze jobs with AI
            if self.ai and not df.empty:
                logging.info("🤖 Running AI analysis on scraped jobs...")
                df = self.ai_enhance_job_data(df, max_jobs=30)  # Analyze top 30 jobs
                # Save enhanced data
                df.to_csv(self.output_path, index=False)
            
            logging.info("="*60)
            logging.info(f"✅ ENHANCED SCRAPING COMPLETE")
            logging.info(f"   Total jobs: {len(df)}")
            logging.info(f"   Sources: {df['source'].nunique()}")
            if self.ai:
                ai_analyzed = len(df[df['ai_relevance_score'] != ''])
                logging.info(f"   AI analyzed: {ai_analyzed} jobs")
                if ai_analyzed > 0:
                    avg_score = df[df['ai_relevance_score'] != '']['ai_relevance_score'].astype(float).mean()
                    logging.info(f"   Avg relevance: {avg_score:.1f}/100")
            logging.info(f"   Saved to: {self.output_path}")
            logging.info("="*60)
        else:
            logging.warning("No jobs scraped from enhanced sources")
        
        return df
    
    def ai_analyze_job_relevance(self, job_description: str, job_title: str, company: str, user_profile: dict = None) -> dict:
        """
        🤖 AI analyzes job relevance and extracts hidden insights.
        """
        if not self.ai:
            return {'score': 50, 'insights': 'AI not available', 'confidence': 'low'}
        
        try:
            # Default user profile if not provided
            if not user_profile:
                user_profile = {
                    'skills': 'data analysis, python, sql, business intelligence',
                    'experience': '3-5 years',
                    'preferences': 'remote work, growth opportunities'
                }
            
            prompt = f"""Job Analysis Request:
Title: {job_title}
Company: {company}
Description: {job_description[:2000]}

User Profile:
Skills: {user_profile.get('skills', 'general')}
Experience: {user_profile.get('experience', '3+ years')}
Preferences: {user_profile.get('preferences', 'career growth')}

Analyze and respond in JSON:
{{
  "relevance_score": 85,
  "match_reasons": ["reason1", "reason2"],
  "missing_skills": ["skill1", "skill2"],
  "salary_estimate": "80k-120k",
  "remote_possible": true,
  "growth_potential": "high|medium|low",
  "application_difficulty": "easy|medium|hard",
  "best_application_approach": "direct|referral|linkedin",
  "key_requirements": ["req1", "req2"],
  "hidden_insights": "insights about company/role"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=600)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        analysis['ai_analyzed'] = True
                        return analysis
                except:
                    pass
            
            # Fallback analysis
            return {
                'relevance_score': 50,
                'match_reasons': ['Standard match'],
                'missing_skills': [],
                'salary_estimate': 'Not specified',
                'remote_possible': 'remote' in job_description.lower(),
                'growth_potential': 'medium',
                'application_difficulty': 'medium',
                'best_application_approach': 'direct',
                'key_requirements': [],
                'hidden_insights': 'Basic job posting',
                'ai_analyzed': False
            }
            
        except Exception as e:
            logging.warning(f"⚠️ AI job analysis failed: {e}")
            return {'relevance_score': 50, 'insights': f'Analysis error: {e}', 'confidence': 'low', 'ai_analyzed': False}
    
    def ai_extract_contact_info(self, job_description: str, company: str) -> dict:
        """
        🤖 AI extracts contact information from job descriptions.
        """
        if not self.ai:
            return {'contacts': [], 'application_method': 'unknown'}
        
        try:
            prompt = f"""Job Posting Analysis:
Company: {company}
Description: {job_description}

Extract contact information:
1. Hiring manager names
2. HR contact emails
3. Application instructions
4. Referral contacts
5. Application deadlines
6. Interview process details

Respond in JSON:
{{
  "contacts": [
    {{"type": "email", "value": "hr@company.com", "role": "HR Manager"}},
    {{"type": "name", "value": "John Smith", "role": "Hiring Manager"}}
  ],
  "application_method": "email|website|linkedin",
  "application_url": "url-if-specified",
  "deadline": "date-if-mentioned",
  "process_insights": "insights about interview process"
}}"""
            
            ai_response = self.ai.generate(prompt, max_tokens=400)
            if ai_response:
                try:
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        contacts = json.loads(json_match.group())
                        return contacts
                except:
                    pass
            
            return {'contacts': [], 'application_method': 'website', 'process_insights': 'Standard application process'}
            
        except Exception as e:
            logging.warning(f"⚠️ AI contact extraction failed: {e}")
            return {'contacts': [], 'application_method': 'unknown', 'error': str(e)}
    
    def ai_enhance_job_data(self, jobs_df: pd.DataFrame, max_jobs: int = 20) -> pd.DataFrame:
        """
        🤖 AI enhances job dataframe with relevance scores and insights.
        """
        if not self.ai or jobs_df.empty:
            return jobs_df
        
        logging.info(f"🤖 AI analyzing top {min(max_jobs, len(jobs_df))} jobs for relevance...")
        
        # Add new columns for AI insights
        ai_columns = ['ai_relevance_score', 'ai_salary_estimate', 'ai_remote_possible', 
                     'ai_growth_potential', 'ai_application_approach', 'ai_insights']
        for col in ai_columns:
            if col not in jobs_df.columns:
                jobs_df[col] = ''
        
        # Analyze top jobs
        for idx, row in jobs_df.head(max_jobs).iterrows():
            try:
                job_desc = str(row.get('description', ''))
                job_title = str(row.get('title', ''))
                company = str(row.get('company', ''))
                
                if job_desc and len(job_desc) > 50:  # Only analyze jobs with good descriptions
                    analysis = self.ai_analyze_job_relevance(job_desc, job_title, company)
                    
                    # Update dataframe with AI insights
                    jobs_df.at[idx, 'ai_relevance_score'] = analysis.get('relevance_score', 50)
                    jobs_df.at[idx, 'ai_salary_estimate'] = analysis.get('salary_estimate', '')
                    jobs_df.at[idx, 'ai_remote_possible'] = analysis.get('remote_possible', False)
                    jobs_df.at[idx, 'ai_growth_potential'] = analysis.get('growth_potential', 'medium')
                    jobs_df.at[idx, 'ai_application_approach'] = analysis.get('best_application_approach', 'direct')
                    jobs_df.at[idx, 'ai_insights'] = analysis.get('hidden_insights', '')
                    
                    # Extract contacts
                    contacts = self.ai_extract_contact_info(job_desc, company)
                    if contacts.get('contacts'):
                        contact_info = '; '.join([f"{c.get('role', '')}: {c.get('value', '')}" 
                                                for c in contacts['contacts']])
                        jobs_df.at[idx, 'ai_contacts'] = contact_info
                
                # Small delay to respect rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logging.warning(f"⚠️ AI analysis failed for job {idx}: {e}")
                continue
        
        # Sort by AI relevance score (highest first)
        try:
            jobs_df['ai_relevance_score'] = pd.to_numeric(jobs_df['ai_relevance_score'], errors='coerce').fillna(50)
            jobs_df = jobs_df.sort_values('ai_relevance_score', ascending=False)
        except:
            pass
        
        ai_analyzed_count = jobs_df[jobs_df['ai_relevance_score'] != ''].shape[0]
        logging.info(f"✅ AI analyzed {ai_analyzed_count} jobs with relevance scoring")
        
        return jobs_df
    
    def merge_with_existing(self) -> pd.DataFrame:
        """Merge enhanced jobs with existing jobs_today.csv."""
        existing_path = os.path.join(self.data_path, 'jobs_today.csv')
        
        enhanced_df = self.scrape_all()
        
        if os.path.exists(existing_path):
            existing_df = pd.read_csv(existing_path)
            
            # Ensure same columns
            for col in ['source', 'scraped_at', 'remote', 'salary']:
                if col not in existing_df.columns:
                    existing_df[col] = ''
            
            # Merge - handle empty DataFrames
            if existing_df.empty:
                merged = enhanced_df
            elif enhanced_df.empty:
                merged = existing_df
            else:
                merged = pd.concat([existing_df, enhanced_df], ignore_index=True)
            merged = merged.drop_duplicates(subset=['title', 'company'], keep='first')
            
            # Save back
            merged.to_csv(existing_path, index=False)
            logging.info(f"📊 Merged: {len(existing_df)} existing + {len(enhanced_df)} enhanced = {len(merged)} total")
            
            return merged
        
        # No existing file, save enhanced as jobs_today
        enhanced_df.to_csv(existing_path, index=False)
        return enhanced_df


def main():
    """Main function to run enhanced job scraping."""
    scraper = EnhancedJobScraper()
    jobs_df = scraper.merge_with_existing()
    
    if not jobs_df.empty:
        print(f"\n📊 Job Sources Summary:")
        print(jobs_df['source'].value_counts())


if __name__ == "__main__":
    main()
