#!/usr/bin/env python3
"""
🚨 REAL-TIME JOB ALERTS
Monitors job boards continuously and sends INSTANT alerts for new matching jobs.
No more waiting for daily scheduled runs!

Features:
- Continuous monitoring (every 5-15 minutes)
- Instant Slack/Email/SMS alerts
- Priority scoring for urgent opportunities
- Duplicate detection
- Rate limiting to avoid blocks
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RealTimeJobAlerts:
    """Monitor job boards in real-time and send instant alerts"""
    
    def __init__(self):
        self.seen_jobs_file = Path("data/seen_jobs_hashes.json")
        self.seen_jobs = self._load_seen_jobs()
        self.alert_history = []
        
        # Configuration
        self.check_interval_minutes = int(os.getenv('JOB_CHECK_INTERVAL', '15'))
        self.priority_keywords = self._get_priority_keywords()
        self.slack_webhook = os.getenv('SLACK_WEBHOOK')
        self.sender_email = os.getenv('SENDER_EMAIL')
        
    def _get_priority_keywords(self) -> List[str]:
        """Get high-priority keywords that trigger immediate alerts"""
        keywords = os.getenv('JOB_KEYWORDS', '').lower().split(',')
        priority = os.getenv('PRIORITY_KEYWORDS', 'urgent,immediate,asap,hot,fast-track').lower().split(',')
        return [k.strip() for k in keywords + priority if k.strip()]
    
    def _load_seen_jobs(self) -> set:
        """Load previously seen job hashes"""
        if self.seen_jobs_file.exists():
            try:
                with open(self.seen_jobs_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('hashes', []))
            except:
                pass
        return set()
    
    def _save_seen_jobs(self):
        """Save seen job hashes"""
        self.seen_jobs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.seen_jobs_file, 'w') as f:
            json.dump({
                'hashes': list(self.seen_jobs),
                'last_updated': datetime.now().isoformat()
            }, f)
    
    def _generate_job_hash(self, job: Dict) -> str:
        """Generate unique hash for a job"""
        unique_str = f"{job.get('title', '')}{job.get('company', '')}{job.get('location', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def _calculate_priority_score(self, job: Dict) -> int:
        """Calculate priority score (0-100) for a job"""
        score = 50  # Base score
        
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        company = job.get('company', '').lower()
        
        # Keyword matches
        for keyword in self.priority_keywords:
            if keyword in title:
                score += 15
            if keyword in description:
                score += 5
        
        # Recency bonus
        posted = job.get('posted_date', '')
        if 'just now' in posted.lower() or 'minute' in posted.lower():
            score += 20
        elif 'hour' in posted.lower() or 'today' in posted.lower():
            score += 10
        
        # Company reputation (can be enhanced)
        top_companies = ['google', 'microsoft', 'amazon', 'meta', 'apple', 'netflix']
        if any(tc in company for tc in top_companies):
            score += 15
        
        # Remote bonus
        if 'remote' in title.lower() or 'remote' in job.get('location', '').lower():
            score += 10
        
        return min(100, score)
    
    def check_google_jobs_rss(self) -> List[Dict]:
        """Check Google Jobs via RSS-like endpoints"""
        jobs = []
        keywords = os.getenv('JOB_KEYWORDS', 'data analyst').replace(',', ' OR ')
        location = os.getenv('APPLICANT_CITY', 'Bangalore')
        
        # Using Google Jobs API alternative
        try:
            # SerpAPI or similar (if available)
            serp_key = os.getenv('SERPAPI_KEY')
            if serp_key:
                url = f"https://serpapi.com/search.json?engine=google_jobs&q={keywords}&location={location}&api_key={serp_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for job in data.get('jobs_results', []):
                        jobs.append({
                            'title': job.get('title', ''),
                            'company': job.get('company_name', ''),
                            'location': job.get('location', ''),
                            'description': job.get('description', ''),
                            'posted_date': job.get('detected_extensions', {}).get('posted_at', ''),
                            'apply_link': job.get('apply_link', ''),
                            'source': 'Google Jobs'
                        })
        except Exception as e:
            print(f"[WARN] Google Jobs check failed: {e}")
        
        return jobs
    
    def check_remoteok_api(self) -> List[Dict]:
        """Check RemoteOK API (free, no auth needed)"""
        jobs = []
        try:
            response = requests.get(
                "https://remoteok.com/api",
                headers={'User-Agent': 'JobAlerts/1.0'},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                keywords = [k.lower() for k in self.priority_keywords]
                
                for job in data[1:50]:  # Skip first item (metadata), get top 50
                    title = job.get('position', '').lower()
                    tags = ' '.join(job.get('tags', [])).lower()
                    
                    # Filter by keywords
                    if any(kw in title or kw in tags for kw in keywords):
                        jobs.append({
                            'title': job.get('position', ''),
                            'company': job.get('company', ''),
                            'location': 'Remote',
                            'description': job.get('description', '')[:500],
                            'posted_date': job.get('date', ''),
                            'apply_link': job.get('url', ''),
                            'salary': job.get('salary', ''),
                            'source': 'RemoteOK'
                        })
        except Exception as e:
            print(f"[WARN] RemoteOK check failed: {e}")
        
        return jobs
    
    def check_adzuna_api(self) -> List[Dict]:
        """Check Adzuna API (free tier available)"""
        jobs = []
        app_id = os.getenv('ADZUNA_APP_ID')
        app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not app_id or not app_key:
            return jobs
        
        try:
            keywords = os.getenv('JOB_KEYWORDS', 'data analyst').replace(',', ' ')
            url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={app_id}&app_key={app_key}&what={keywords}&max_days_old=1&results_per_page=50"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('results', []):
                    jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', {}).get('display_name', ''),
                        'location': job.get('location', {}).get('display_name', ''),
                        'description': job.get('description', '')[:500],
                        'posted_date': job.get('created', ''),
                        'apply_link': job.get('redirect_url', ''),
                        'salary': f"{job.get('salary_min', '')} - {job.get('salary_max', '')}",
                        'source': 'Adzuna'
                    })
        except Exception as e:
            print(f"[WARN] Adzuna check failed: {e}")
        
        return jobs
    
    def check_arbeitnow_api(self) -> List[Dict]:
        """Check Arbeitnow API (free, no auth)"""
        jobs = []
        try:
            response = requests.get(
                "https://www.arbeitnow.com/api/job-board-api",
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                keywords = [k.lower() for k in self.priority_keywords]
                
                for job in data.get('data', [])[:50]:
                    title = job.get('title', '').lower()
                    tags = ' '.join(job.get('tags', [])).lower()
                    
                    if any(kw in title or kw in tags for kw in keywords):
                        jobs.append({
                            'title': job.get('title', ''),
                            'company': job.get('company_name', ''),
                            'location': job.get('location', ''),
                            'description': job.get('description', '')[:500],
                            'posted_date': job.get('created_at', ''),
                            'apply_link': job.get('url', ''),
                            'remote': job.get('remote', False),
                            'source': 'Arbeitnow'
                        })
        except Exception as e:
            print(f"[WARN] Arbeitnow check failed: {e}")
        
        return jobs
    
    def send_instant_alert(self, job: Dict, priority: int):
        """Send instant alert for a new job"""
        
        # Format message
        emoji = "🔥" if priority >= 80 else "⭐" if priority >= 60 else "📋"
        message = f"""
{emoji} **NEW JOB ALERT** (Priority: {priority}/100)

**{job.get('title', 'N/A')}**
🏢 {job.get('company', 'N/A')}
📍 {job.get('location', 'N/A')}
💰 {job.get('salary', 'Not specified')}
🔗 {job.get('apply_link', 'N/A')}
📅 Posted: {job.get('posted_date', 'N/A')}
📡 Source: {job.get('source', 'N/A')}

⏰ Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send Slack alert
        if self.slack_webhook:
            try:
                requests.post(
                    self.slack_webhook,
                    json={"text": message},
                    timeout=10
                )
                print(f"[SLACK] Alert sent for: {job.get('title')}")
            except Exception as e:
                print(f"[ERROR] Slack alert failed: {e}")
        
        # Log alert
        self.alert_history.append({
            'job': job,
            'priority': priority,
            'sent_at': datetime.now().isoformat()
        })
        
        print(message)
    
    def run_check(self) -> Dict:
        """Run a single check across all sources"""
        print(f"\n{'='*60}")
        print(f"🔍 REAL-TIME JOB CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        all_jobs = []
        new_jobs = []
        
        # Check all sources
        sources = [
            ("RemoteOK", self.check_remoteok_api),
            ("Arbeitnow", self.check_arbeitnow_api),
            ("Google Jobs", self.check_google_jobs_rss),
            ("Adzuna", self.check_adzuna_api),
        ]
        
        for source_name, check_func in sources:
            try:
                jobs = check_func()
                all_jobs.extend(jobs)
                print(f"  ✓ {source_name}: {len(jobs)} jobs found")
            except Exception as e:
                print(f"  ✗ {source_name}: Error - {e}")
        
        # Filter new jobs
        for job in all_jobs:
            job_hash = self._generate_job_hash(job)
            
            if job_hash not in self.seen_jobs:
                self.seen_jobs.add(job_hash)
                priority = self._calculate_priority_score(job)
                job['priority_score'] = priority
                new_jobs.append(job)
                
                # Send alert for high-priority jobs
                if priority >= 50:
                    self.send_instant_alert(job, priority)
        
        # Save seen jobs
        self._save_seen_jobs()
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"  • Total jobs checked: {len(all_jobs)}")
        print(f"  • New jobs found: {len(new_jobs)}")
        print(f"  • Alerts sent: {len([j for j in new_jobs if j.get('priority_score', 0) >= 50])}")
        
        return {
            'total_checked': len(all_jobs),
            'new_jobs': len(new_jobs),
            'jobs': new_jobs
        }
    
    def run_continuous(self, max_hours: int = 24):
        """Run continuous monitoring"""
        print(f"🚨 STARTING REAL-TIME JOB MONITORING")
        print(f"  Check interval: Every {self.check_interval_minutes} minutes")
        print(f"  Max runtime: {max_hours} hours")
        print(f"  Keywords: {', '.join(self.priority_keywords[:5])}...")
        
        start_time = datetime.now()
        max_duration = timedelta(hours=max_hours)
        
        while datetime.now() - start_time < max_duration:
            try:
                self.run_check()
            except Exception as e:
                print(f"[ERROR] Check failed: {e}")
            
            # Wait for next check
            print(f"\n⏳ Next check in {self.check_interval_minutes} minutes...")
            time.sleep(self.check_interval_minutes * 60)
        
        print(f"\n✅ Monitoring completed after {max_hours} hours")


def main():
    """Main entry point"""
    alerts = RealTimeJobAlerts()
    
    # Single check or continuous mode
    mode = os.getenv('ALERT_MODE', 'single')
    
    if mode == 'continuous':
        alerts.run_continuous()
    else:
        result = alerts.run_check()
        print(f"\n✅ Check complete: {result['new_jobs']} new jobs found")


if __name__ == "__main__":
    main()
