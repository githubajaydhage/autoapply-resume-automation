"""
🔧 SELF-HEALING JOB MONITOR - Never Miss an Opportunity!

This module provides:
1. Health monitoring for all job sources
2. Automatic recovery from failures
3. Gap detection (jobs that slipped through)
4. Alert system for critical issues
5. Performance analytics

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class SelfHealingMonitor:
    """
    🔧 Self-Healing Job Monitor
    
    Monitors the entire automation pipeline and:
    - Detects failures and gaps
    - Triggers automatic recovery
    - Sends alerts for critical issues
    - Provides performance analytics
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        os.makedirs(self.data_path, exist_ok=True)
        
        # Monitoring data
        self.health_log_path = os.path.join(self.data_path, 'pipeline_health.json')
        self.source_health_path = os.path.join(self.data_path, 'source_health.json')
        self.metrics_path = os.path.join(self.data_path, 'daily_metrics.csv')
        
        # Load health data
        self.health_data = self._load_health_data()
        
        logging.info("🔧 Self-Healing Monitor initialized")
    
    def _load_health_data(self) -> Dict:
        """Load pipeline health data."""
        if os.path.exists(self.health_log_path):
            try:
                with open(self.health_log_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_run': None,
            'last_success': None,
            'consecutive_failures': 0,
            'total_runs': 0,
            'total_jobs_found': 0,
            'total_applications_sent': 0,
            'total_responses': 0,
            'source_status': {},
            'issues': [],
            'recovery_actions': []
        }
    
    def _save_health_data(self):
        """Save pipeline health data."""
        try:
            with open(self.health_log_path, 'w') as f:
                json.dump(self.health_data, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save health data: {e}")
    
    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================
    
    def check_pipeline_health(self) -> Dict:
        """
        Comprehensive health check of the entire pipeline.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("🔧 PIPELINE HEALTH CHECK")
        logging.info("="*60)
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check 1: Data files exist and are recent
        data_check = self._check_data_files()
        health_report['data_files'] = data_check
        if data_check['issues']:
            health_report['issues'].extend(data_check['issues'])
        
        # Check 2: Job sources are working
        source_check = self._check_job_sources()
        health_report['job_sources'] = source_check
        if source_check['issues']:
            health_report['issues'].extend(source_check['issues'])
        
        # Check 3: Email system is working
        email_check = self._check_email_system()
        health_report['email_system'] = email_check
        if email_check['issues']:
            health_report['issues'].extend(email_check['issues'])
        
        # Check 4: Application success rate
        success_check = self._check_success_rate()
        health_report['success_rate'] = success_check
        if success_check['issues']:
            health_report['issues'].extend(success_check['issues'])
        
        # Check 5: Gap detection
        gap_check = self._detect_gaps()
        health_report['gaps'] = gap_check
        if gap_check['issues']:
            health_report['issues'].extend(gap_check['issues'])
        
        # Determine overall status
        if health_report['issues']:
            critical_issues = [i for i in health_report['issues'] if i.get('severity') == 'critical']
            if critical_issues:
                health_report['overall_status'] = 'critical'
            else:
                health_report['overall_status'] = 'degraded'
        
        # Log summary
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '❌'
        }
        
        logging.info(f"{status_emoji[health_report['overall_status']]} Overall Status: {health_report['overall_status'].upper()}")
        
        if health_report['issues']:
            logging.info(f"   Issues found: {len(health_report['issues'])}")
            for issue in health_report['issues'][:5]:
                logging.info(f"   - {issue.get('description', 'Unknown issue')}")
        
        return health_report
    
    def _check_data_files(self) -> Dict:
        """Check if required data files exist and are recent."""
        result = {'status': 'ok', 'issues': [], 'files': {}}
        
        required_files = {
            'jobs_today.csv': 24,  # Max hours old
            'applied_log.csv': 168,  # 1 week
            'sent_emails_log.csv': 168,
        }
        
        optional_files = [
            'all_jobs_database.csv',
            'application_queue.csv',
            'hr_replies.csv'
        ]
        
        for filename, max_age_hours in required_files.items():
            filepath = os.path.join(self.data_path, filename)
            
            if not os.path.exists(filepath):
                result['files'][filename] = 'missing'
                result['issues'].append({
                    'type': 'missing_file',
                    'description': f"Required file missing: {filename}",
                    'severity': 'warning',
                    'recommendation': f"Run job discovery to create {filename}"
                })
            else:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_hours = (datetime.now() - mtime).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    result['files'][filename] = f'stale ({age_hours:.0f}h old)'
                    result['issues'].append({
                        'type': 'stale_file',
                        'description': f"File is {age_hours:.0f} hours old: {filename}",
                        'severity': 'warning',
                        'recommendation': "Run pipeline to refresh data"
                    })
                else:
                    result['files'][filename] = 'ok'
        
        if not result['issues']:
            result['status'] = 'ok'
            logging.info("   📁 Data files: OK")
        else:
            result['status'] = 'degraded'
            logging.info(f"   📁 Data files: {len(result['issues'])} issues")
        
        return result
    
    def _check_job_sources(self) -> Dict:
        """Check health of job sources."""
        result = {'status': 'ok', 'issues': [], 'sources': {}}
        
        if os.path.exists(self.source_health_path):
            try:
                with open(self.source_health_path, 'r') as f:
                    sources = json.load(f)
                
                for source, health in sources.items():
                    success = health.get('success_count', 0)
                    failure = health.get('failure_count', 0)
                    consecutive_failures = health.get('consecutive_failures', 0)
                    total = success + failure
                    
                    if total > 0:
                        success_rate = (success / total) * 100
                        result['sources'][source] = f"{success_rate:.0f}% success"
                        
                        if consecutive_failures >= 3:
                            result['issues'].append({
                                'type': 'source_failing',
                                'description': f"Job source failing: {source} ({consecutive_failures} consecutive failures)",
                                'severity': 'warning',
                                'recommendation': f"Check if {source} API/website has changed"
                            })
                        elif success_rate < 50:
                            result['issues'].append({
                                'type': 'source_unreliable',
                                'description': f"Low success rate for {source}: {success_rate:.0f}%",
                                'severity': 'info'
                            })
                    else:
                        result['sources'][source] = 'no data'
                
            except Exception as e:
                logging.warning(f"Could not read source health: {e}")
        
        if not result['issues']:
            logging.info("   📡 Job sources: OK")
        else:
            logging.info(f"   📡 Job sources: {len(result['issues'])} issues")
        
        return result
    
    def _check_email_system(self) -> Dict:
        """Check email sending health."""
        result = {'status': 'ok', 'issues': []}
        
        sent_log_path = os.path.join(self.data_path, 'sent_emails_log.csv')
        bounce_log_path = os.path.join(self.data_path, 'bounced_emails.csv')
        
        sent_count = 0
        bounce_count = 0
        recent_sent = 0
        
        if os.path.exists(sent_log_path):
            try:
                sent_df = pd.read_csv(sent_log_path)
                sent_count = len(sent_df)
                
                # Check recent sends
                if 'sent_at' in sent_df.columns:
                    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
                    recent = sent_df[sent_df['sent_at'] > cutoff]
                    recent_sent = len(recent)
            except:
                pass
        
        if os.path.exists(bounce_log_path):
            try:
                bounce_df = pd.read_csv(bounce_log_path)
                bounce_count = len(bounce_df)
            except:
                pass
        
        result['sent_total'] = sent_count
        result['bounces'] = bounce_count
        result['recent_sent'] = recent_sent
        
        if sent_count > 0:
            bounce_rate = (bounce_count / sent_count) * 100
            result['bounce_rate'] = f"{bounce_rate:.1f}%"
            
            if bounce_rate > 20:
                result['issues'].append({
                    'type': 'high_bounce_rate',
                    'description': f"High bounce rate: {bounce_rate:.1f}%",
                    'severity': 'warning',
                    'recommendation': "Review email verification process"
                })
        
        # Check if emails are being sent
        if recent_sent == 0 and sent_count > 0:
            result['issues'].append({
                'type': 'no_recent_emails',
                'description': "No emails sent in the last 7 days",
                'severity': 'warning',
                'recommendation': "Check if pipeline is running"
            })
        
        if not result['issues']:
            logging.info(f"   📧 Email system: OK ({recent_sent} sent this week)")
        else:
            logging.info(f"   📧 Email system: {len(result['issues'])} issues")
        
        return result
    
    def _check_success_rate(self) -> Dict:
        """Check application success rate."""
        result = {'status': 'ok', 'issues': []}
        
        applied_path = os.path.join(self.data_path, 'applied_log.csv')
        replies_path = os.path.join(self.data_path, 'hr_replies.csv')
        
        applied_count = 0
        reply_count = 0
        
        if os.path.exists(applied_path):
            try:
                applied_df = pd.read_csv(applied_path)
                applied_count = len(applied_df)
            except:
                pass
        
        if os.path.exists(replies_path):
            try:
                replies_df = pd.read_csv(replies_path)
                reply_count = len(replies_df)
            except:
                pass
        
        result['applications'] = applied_count
        result['replies'] = reply_count
        
        if applied_count > 0:
            response_rate = (reply_count / applied_count) * 100
            result['response_rate'] = f"{response_rate:.1f}%"
            
            logging.info(f"   📊 Success rate: {response_rate:.1f}% ({reply_count}/{applied_count})")
        else:
            logging.info("   📊 Success rate: No applications yet")
        
        return result
    
    def _detect_gaps(self) -> Dict:
        """Detect gaps in the pipeline."""
        result = {'status': 'ok', 'issues': [], 'gaps': []}
        
        # Check for unapplied jobs
        jobs_path = os.path.join(self.data_path, 'all_jobs_database.csv')
        applied_path = os.path.join(self.data_path, 'applied_log.csv')
        queue_path = os.path.join(self.data_path, 'application_queue.csv')
        
        unapplied_count = 0
        
        if os.path.exists(jobs_path):
            try:
                jobs_df = pd.read_csv(jobs_path)
                total_jobs = len(jobs_df)
                
                applied_companies = set()
                if os.path.exists(applied_path):
                    applied_df = pd.read_csv(applied_path)
                    applied_companies = set(applied_df['company'].str.lower().dropna())
                
                queued_companies = set()
                if os.path.exists(queue_path):
                    queue_df = pd.read_csv(queue_path)
                    queued_companies = set(queue_df['company'].str.lower().dropna())
                
                for _, job in jobs_df.iterrows():
                    company = str(job.get('company', '')).lower()
                    if company and company not in applied_companies and company not in queued_companies:
                        unapplied_count += 1
                
                result['unapplied_jobs'] = unapplied_count
                
                if unapplied_count > 10:
                    result['issues'].append({
                        'type': 'unapplied_jobs',
                        'description': f"{unapplied_count} jobs discovered but not applied to",
                        'severity': 'info',
                        'recommendation': "Run enrichment to find HR emails"
                    })
                
            except Exception as e:
                logging.warning(f"Gap detection error: {e}")
        
        if unapplied_count > 0:
            logging.info(f"   🔍 Gap detection: {unapplied_count} unapplied jobs")
        else:
            logging.info("   🔍 Gap detection: No gaps found")
        
        return result
    
    # =========================================================================
    # RECOVERY ACTIONS
    # =========================================================================
    
    def auto_recover(self, health_report: Dict) -> List[str]:
        """
        Automatically attempt to recover from issues.
        """
        logging.info("")
        logging.info("="*60)
        logging.info("🔧 AUTO-RECOVERY ACTIONS")
        logging.info("="*60)
        
        actions_taken = []
        
        for issue in health_report.get('issues', []):
            issue_type = issue.get('type', '')
            
            if issue_type == 'missing_file':
                # Trigger job discovery
                action = self._recover_missing_data()
                if action:
                    actions_taken.append(action)
            
            elif issue_type == 'stale_file':
                # Trigger refresh
                action = self._recover_stale_data()
                if action:
                    actions_taken.append(action)
            
            elif issue_type == 'source_failing':
                # Try alternative sources
                action = self._recover_failing_source(issue.get('description', ''))
                if action:
                    actions_taken.append(action)
            
            elif issue_type == 'unapplied_jobs':
                # Trigger enrichment
                action = self._recover_unapplied_jobs()
                if action:
                    actions_taken.append(action)
        
        if actions_taken:
            logging.info(f"✅ Took {len(actions_taken)} recovery actions")
            for action in actions_taken:
                logging.info(f"   - {action}")
        else:
            logging.info("No recovery actions needed")
        
        # Save recovery log
        self.health_data['recovery_actions'].extend([
            {'timestamp': datetime.now().isoformat(), 'action': a}
            for a in actions_taken
        ])
        self._save_health_data()
        
        return actions_taken
    
    def _recover_missing_data(self) -> Optional[str]:
        """Recover from missing data files."""
        try:
            from bulletproof_job_engine import BulletproofJobEngine
            engine = BulletproofJobEngine()
            total, new = engine.run_full_scrape()
            return f"Ran job discovery, found {new} new jobs"
        except Exception as e:
            logging.error(f"Recovery failed: {e}")
            return None
    
    def _recover_stale_data(self) -> Optional[str]:
        """Recover from stale data."""
        try:
            from bulletproof_job_engine import BulletproofJobEngine
            engine = BulletproofJobEngine()
            total, new = engine.run_full_scrape()
            return f"Refreshed job data, found {new} new jobs"
        except Exception as e:
            logging.error(f"Recovery failed: {e}")
            return None
    
    def _recover_failing_source(self, description: str) -> Optional[str]:
        """Handle failing job source."""
        # Just log - the bulletproof engine handles failover
        return f"Noted failing source, engine will use alternatives"
    
    def _recover_unapplied_jobs(self) -> Optional[str]:
        """Recover unapplied jobs by enriching with emails."""
        try:
            from auto_application_pipeline import AutoApplicationPipeline
            pipeline = AutoApplicationPipeline()
            enriched = pipeline.phase_enrich()
            return f"Enriched {enriched} jobs with HR emails"
        except Exception as e:
            logging.error(f"Recovery failed: {e}")
            return None
    
    # =========================================================================
    # METRICS & ANALYTICS
    # =========================================================================
    
    def log_daily_metrics(self):
        """Log daily metrics for analytics."""
        metrics = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'jobs_in_db': 0,
            'applications_sent': 0,
            'responses': 0,
            'bounce_rate': 0,
            'queue_size': 0
        }
        
        # Count jobs
        jobs_path = os.path.join(self.data_path, 'all_jobs_database.csv')
        if os.path.exists(jobs_path):
            try:
                df = pd.read_csv(jobs_path)
                metrics['jobs_in_db'] = len(df)
            except:
                pass
        
        # Count applications
        applied_path = os.path.join(self.data_path, 'applied_log.csv')
        if os.path.exists(applied_path):
            try:
                df = pd.read_csv(applied_path)
                metrics['applications_sent'] = len(df)
            except:
                pass
        
        # Count responses
        replies_path = os.path.join(self.data_path, 'hr_replies.csv')
        if os.path.exists(replies_path):
            try:
                df = pd.read_csv(replies_path)
                metrics['responses'] = len(df)
            except:
                pass
        
        # Save metrics
        if os.path.exists(self.metrics_path):
            metrics_df = pd.read_csv(self.metrics_path)
            # Update today's entry or append
            if metrics['date'] in metrics_df['date'].values:
                metrics_df.loc[metrics_df['date'] == metrics['date']] = pd.Series(metrics)
            else:
                metrics_df = pd.concat([metrics_df, pd.DataFrame([metrics])], ignore_index=True)
        else:
            metrics_df = pd.DataFrame([metrics])
        
        metrics_df.to_csv(self.metrics_path, index=False)
        logging.info(f"📊 Daily metrics logged: {metrics}")
    
    def get_performance_summary(self) -> str:
        """Get performance summary for the last 7 days."""
        summary = "\n📊 PERFORMANCE SUMMARY (Last 7 Days)\n"
        summary += "="*50 + "\n"
        
        if os.path.exists(self.metrics_path):
            try:
                df = pd.read_csv(self.metrics_path)
                cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                recent = df[df['date'] >= cutoff]
                
                if not recent.empty:
                    summary += f"   Jobs Discovered: {recent['jobs_in_db'].iloc[-1] - recent['jobs_in_db'].iloc[0]}\n"
                    summary += f"   Applications Sent: {recent['applications_sent'].sum()}\n"
                    summary += f"   Responses: {recent['responses'].sum()}\n"
                else:
                    summary += "   No data for last 7 days\n"
            except:
                summary += "   Could not load metrics\n"
        else:
            summary += "   No metrics data yet\n"
        
        return summary


def main():
    """Run the self-healing monitor."""
    monitor = SelfHealingMonitor()
    
    # Run health check
    health_report = monitor.check_pipeline_health()
    
    # Auto-recover if needed
    if health_report['overall_status'] != 'healthy':
        monitor.auto_recover(health_report)
    
    # Log metrics
    monitor.log_daily_metrics()
    
    # Print performance summary
    print(monitor.get_performance_summary())


if __name__ == '__main__':
    main()
