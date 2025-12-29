#!/usr/bin/env python3
"""
Multi-Channel Job Search Analytics Dashboard
Tracks and analyzes job search performance across all channels:
- Email outreach
- LinkedIn connections
- Job portal applications
- Referrals
Provides actionable insights to optimize the job search strategy.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import csv
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ChannelMetrics:
    """Metrics for a single outreach channel."""
    channel_name: str
    total_outreach: int = 0
    responses: int = 0
    positive_responses: int = 0
    interviews: int = 0
    offers: int = 0
    avg_response_time_days: float = 0.0
    
    @property
    def response_rate(self) -> float:
        return (self.responses / self.total_outreach * 100) if self.total_outreach > 0 else 0
    
    @property
    def positive_rate(self) -> float:
        return (self.positive_responses / self.total_outreach * 100) if self.total_outreach > 0 else 0
    
    @property
    def interview_rate(self) -> float:
        return (self.interviews / self.total_outreach * 100) if self.total_outreach > 0 else 0
    
    @property
    def conversion_rate(self) -> float:
        return (self.interviews / self.responses * 100) if self.responses > 0 else 0


@dataclass
class WeeklySnapshot:
    """Weekly performance snapshot."""
    week_start: str
    week_end: str
    emails_sent: int = 0
    linkedin_connections: int = 0
    portal_applications: int = 0
    referrals_requested: int = 0
    responses_received: int = 0
    interviews_scheduled: int = 0


class MultiChannelTracker:
    """Track job search activities across multiple channels."""
    
    CHANNELS = ['email', 'linkedin', 'naukri', 'wellfound', 'instahyre', 'referral', 'direct', 'other']
    
    def __init__(self, data_dir: str = 'data'):
        """Initialize tracker with data directory."""
        self.data_dir = data_dir
        self.tracker_path = os.path.join(data_dir, 'multi_channel_tracker.csv')
        self.analytics_path = os.path.join(data_dir, 'channel_analytics.json')
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create tracker file if it doesn't exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.tracker_path):
            with open(self.tracker_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'channel', 'action', 'company', 'job_title',
                    'contact_name', 'contact_email', 'status', 'response_date',
                    'response_type', 'notes'
                ])
    
    def log_activity(
        self,
        channel: str,
        action: str,
        company: str,
        job_title: str,
        contact_name: str = "",
        contact_email: str = "",
        status: str = "sent",
        notes: str = ""
    ):
        """
        Log an outreach activity.
        
        Args:
            channel: Channel used (email, linkedin, naukri, etc.)
            action: Action taken (application, connection, message, referral_request)
            company: Company name
            job_title: Job title
            contact_name: Contact person's name
            contact_email: Contact email
            status: Current status
            notes: Additional notes
        """
        with open(self.tracker_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                channel,
                action,
                company,
                job_title,
                contact_name,
                contact_email,
                status,
                '',  # response_date (to be updated)
                '',  # response_type (to be updated)
                notes
            ])
    
    def update_response(
        self,
        company: str,
        job_title: str,
        response_type: str,
        response_date: str = None
    ):
        """
        Update an activity with response information.
        
        Args:
            company: Company name
            job_title: Job title
            response_type: Type of response (positive, negative, interview, offer)
            response_date: When response was received
        """
        if not response_date:
            response_date = datetime.now().strftime('%Y-%m-%d')
        
        # Read all records
        records = []
        updated = False
        
        if os.path.exists(self.tracker_path):
            with open(self.tracker_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                records.append(header)
                
                for row in reader:
                    # Find matching record to update
                    if (not updated and 
                        row[3].lower() == company.lower() and 
                        row[4].lower() == job_title.lower() and
                        not row[8]):  # No response date yet
                        row[8] = response_date
                        row[9] = response_type
                        row[7] = 'responded'
                        updated = True
                    records.append(row)
        
        # Write back
        with open(self.tracker_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(records)
    
    def get_all_activities(self, days: int = None) -> List[Dict]:
        """
        Get all activities, optionally filtered by days.
        
        Args:
            days: Number of days to look back (None for all)
            
        Returns:
            List of activity dictionaries
        """
        activities = []
        cutoff = None
        if days:
            cutoff = datetime.now() - timedelta(days=days)
        
        if os.path.exists(self.tracker_path):
            with open(self.tracker_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if cutoff:
                        try:
                            activity_date = datetime.strptime(
                                row['timestamp'][:10], '%Y-%m-%d'
                            )
                            if activity_date < cutoff:
                                continue
                        except:
                            pass
                    activities.append(row)
        
        return activities


class ChannelAnalyzer:
    """Analyze performance across channels."""
    
    def __init__(self, tracker: MultiChannelTracker):
        """Initialize with tracker instance."""
        self.tracker = tracker
    
    def calculate_channel_metrics(self, days: int = 30) -> Dict[str, ChannelMetrics]:
        """
        Calculate metrics for each channel.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary of channel metrics
        """
        activities = self.tracker.get_all_activities(days)
        
        channel_data = defaultdict(lambda: {
            'total': 0,
            'responses': 0,
            'positive': 0,
            'interviews': 0,
            'offers': 0,
            'response_times': []
        })
        
        for activity in activities:
            channel = activity.get('channel', 'other').lower()
            channel_data[channel]['total'] += 1
            
            response_type = activity.get('response_type', '').lower()
            response_date = activity.get('response_date', '')
            
            if response_date:
                channel_data[channel]['responses'] += 1
                
                # Calculate response time
                try:
                    sent_date = datetime.strptime(
                        activity['timestamp'][:10], '%Y-%m-%d'
                    )
                    resp_date = datetime.strptime(response_date, '%Y-%m-%d')
                    response_time = (resp_date - sent_date).days
                    channel_data[channel]['response_times'].append(response_time)
                except:
                    pass
                
                if response_type in ['positive', 'interested', 'interview', 'offer']:
                    channel_data[channel]['positive'] += 1
                
                if response_type == 'interview':
                    channel_data[channel]['interviews'] += 1
                
                if response_type == 'offer':
                    channel_data[channel]['offers'] += 1
        
        # Convert to ChannelMetrics objects
        metrics = {}
        for channel, data in channel_data.items():
            avg_response_time = 0
            if data['response_times']:
                avg_response_time = sum(data['response_times']) / len(data['response_times'])
            
            metrics[channel] = ChannelMetrics(
                channel_name=channel,
                total_outreach=data['total'],
                responses=data['responses'],
                positive_responses=data['positive'],
                interviews=data['interviews'],
                offers=data['offers'],
                avg_response_time_days=avg_response_time
            )
        
        return metrics
    
    def get_weekly_trends(self, weeks: int = 4) -> List[WeeklySnapshot]:
        """
        Get weekly performance trends.
        
        Args:
            weeks: Number of weeks to analyze
            
        Returns:
            List of weekly snapshots
        """
        activities = self.tracker.get_all_activities(days=weeks * 7)
        
        # Group by week
        weekly_data = defaultdict(lambda: {
            'emails': 0,
            'linkedin': 0,
            'portals': 0,
            'referrals': 0,
            'responses': 0,
            'interviews': 0
        })
        
        for activity in activities:
            try:
                activity_date = datetime.strptime(
                    activity['timestamp'][:10], '%Y-%m-%d'
                )
                # Get week start (Monday)
                week_start = activity_date - timedelta(days=activity_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                channel = activity.get('channel', '').lower()
                
                if channel == 'email':
                    weekly_data[week_key]['emails'] += 1
                elif channel == 'linkedin':
                    weekly_data[week_key]['linkedin'] += 1
                elif channel in ['naukri', 'wellfound', 'instahyre']:
                    weekly_data[week_key]['portals'] += 1
                elif channel == 'referral':
                    weekly_data[week_key]['referrals'] += 1
                
                if activity.get('response_date'):
                    weekly_data[week_key]['responses'] += 1
                
                if activity.get('response_type', '').lower() == 'interview':
                    weekly_data[week_key]['interviews'] += 1
                    
            except:
                continue
        
        # Convert to snapshots
        snapshots = []
        for week_start_str, data in sorted(weekly_data.items()):
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d')
            week_end = week_start + timedelta(days=6)
            
            snapshots.append(WeeklySnapshot(
                week_start=week_start_str,
                week_end=week_end.strftime('%Y-%m-%d'),
                emails_sent=data['emails'],
                linkedin_connections=data['linkedin'],
                portal_applications=data['portals'],
                referrals_requested=data['referrals'],
                responses_received=data['responses'],
                interviews_scheduled=data['interviews']
            ))
        
        return snapshots
    
    def get_best_performing_channel(self) -> Tuple[str, float]:
        """
        Get the best performing channel by response rate.
        
        Returns:
            Tuple of (channel_name, response_rate)
        """
        metrics = self.calculate_channel_metrics()
        
        if not metrics:
            return ('none', 0.0)
        
        best_channel = max(
            metrics.items(),
            key=lambda x: x[1].response_rate if x[1].total_outreach >= 5 else 0
        )
        
        return (best_channel[0], best_channel[1].response_rate)
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        Generate recommendations to improve job search.
        
        Returns:
            List of actionable recommendations
        """
        metrics = self.calculate_channel_metrics()
        weekly = self.get_weekly_trends(4)
        recommendations = []
        
        # Check response rates
        for channel, m in metrics.items():
            if m.total_outreach >= 10:
                if m.response_rate < 5:
                    recommendations.append(
                        f"📉 {channel.title()} has very low response rate ({m.response_rate:.1f}%). "
                        "Consider improving message personalization or targeting."
                    )
                elif m.response_rate > 20:
                    recommendations.append(
                        f"📈 {channel.title()} is performing well ({m.response_rate:.1f}% response rate). "
                        "Consider increasing volume on this channel."
                    )
        
        # Check total volume
        total_activities = sum(m.total_outreach for m in metrics.values())
        if total_activities < 50:
            recommendations.append(
                f"⚠️ Low outreach volume ({total_activities} total). "
                "Aim for at least 10-20 applications per day for best results."
            )
        
        # Check channel diversity
        active_channels = [c for c, m in metrics.items() if m.total_outreach >= 5]
        if len(active_channels) < 3:
            recommendations.append(
                "🔀 Limited channel diversity. Try adding more channels "
                "(LinkedIn, referrals, direct applications) for better coverage."
            )
        
        # Check follow-up rate
        email_metrics = metrics.get('email', ChannelMetrics('email'))
        if email_metrics.total_outreach > 20 and email_metrics.response_rate < 10:
            recommendations.append(
                "📧 Low email response rate. Ensure you're sending follow-up emails "
                "3-5 days after initial outreach."
            )
        
        # Check LinkedIn usage
        linkedin_metrics = metrics.get('linkedin', ChannelMetrics('linkedin'))
        if linkedin_metrics.total_outreach < 10:
            recommendations.append(
                "🔗 LinkedIn underutilized. Warm up leads on LinkedIn before email "
                "for 3x higher response rates."
            )
        
        # Check referral usage
        referral_metrics = metrics.get('referral', ChannelMetrics('referral'))
        if referral_metrics.total_outreach < 5:
            recommendations.append(
                "👥 Referrals underutilized. Referral applications have 5-10x higher "
                "success rate. Tap into your network!"
            )
        
        if not recommendations:
            recommendations.append(
                "✅ Your job search strategy looks balanced! Keep up the momentum."
            )
        
        return recommendations


class AnalyticsDashboard:
    """Generate analytics dashboard reports."""
    
    def __init__(self, data_dir: str = 'data'):
        """Initialize dashboard with data directory."""
        self.tracker = MultiChannelTracker(data_dir)
        self.analyzer = ChannelAnalyzer(self.tracker)
    
    def generate_dashboard_report(
        self,
        output_path: str = 'data/analytics_dashboard.txt'
    ) -> str:
        """
        Generate comprehensive analytics dashboard.
        
        Args:
            output_path: Where to save the report
            
        Returns:
            Path to saved report
        """
        metrics = self.analyzer.calculate_channel_metrics()
        weekly = self.analyzer.get_weekly_trends(4)
        recommendations = self.analyzer.get_optimization_recommendations()
        
        lines = [
            "=" * 70,
            "📊 JOB SEARCH ANALYTICS DASHBOARD",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "=" * 70,
            "CHANNEL PERFORMANCE (Last 30 Days)",
            "=" * 70,
            "",
            f"{'Channel':<15} {'Sent':<8} {'Resp':<8} {'Rate':<10} {'Interviews':<12} {'Avg Days':<10}",
            "-" * 70,
        ]
        
        total_sent = 0
        total_responses = 0
        total_interviews = 0
        
        for channel, m in sorted(metrics.items(), key=lambda x: x[1].response_rate, reverse=True):
            lines.append(
                f"{channel.title():<15} {m.total_outreach:<8} {m.responses:<8} "
                f"{m.response_rate:.1f}%{'':<6} {m.interviews:<12} "
                f"{m.avg_response_time_days:.1f}"
            )
            total_sent += m.total_outreach
            total_responses += m.responses
            total_interviews += m.interviews
        
        lines.extend([
            "-" * 70,
            f"{'TOTAL':<15} {total_sent:<8} {total_responses:<8} "
            f"{(total_responses/total_sent*100 if total_sent > 0 else 0):.1f}%{'':<6} {total_interviews:<12}",
            "",
        ])
        
        # Weekly trends
        lines.extend([
            "=" * 70,
            "WEEKLY ACTIVITY TRENDS",
            "=" * 70,
            "",
            f"{'Week':<25} {'Emails':<10} {'LinkedIn':<12} {'Portals':<10} {'Responses':<12}",
            "-" * 70,
        ])
        
        for week in weekly[-4:]:  # Last 4 weeks
            lines.append(
                f"{week.week_start} to {week.week_end[-5:]:<10} "
                f"{week.emails_sent:<10} {week.linkedin_connections:<12} "
                f"{week.portal_applications:<10} {week.responses_received:<12}"
            )
        
        # Best channel
        best_channel, best_rate = self.analyzer.get_best_performing_channel()
        
        lines.extend([
            "",
            "=" * 70,
            "KEY INSIGHTS",
            "=" * 70,
            "",
            f"🏆 Best Performing Channel: {best_channel.title()} ({best_rate:.1f}% response rate)",
            f"📈 Total Outreach: {total_sent} contacts",
            f"💬 Total Responses: {total_responses}",
            f"🎯 Interviews Scheduled: {total_interviews}",
            f"📊 Overall Response Rate: {(total_responses/total_sent*100 if total_sent > 0 else 0):.1f}%",
            "",
        ])
        
        # Recommendations
        lines.extend([
            "=" * 70,
            "OPTIMIZATION RECOMMENDATIONS",
            "=" * 70,
            "",
        ])
        
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "=" * 70,
            "NEXT ACTIONS",
            "=" * 70,
            "",
            "1. Review and implement the recommendations above",
            "2. Focus more time on high-performing channels",
            "3. Experiment with new approaches on low-performing channels",
            "4. Set daily targets: 5 emails, 10 LinkedIn connections, 5 applications",
            "5. Review this dashboard weekly to track progress",
            "",
        ])
        
        # Save report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"Analytics dashboard saved to: {output_path}")
        return output_path
    
    def generate_json_summary(self) -> Dict:
        """
        Generate JSON summary for programmatic access.
        
        Returns:
            Dictionary with analytics data
        """
        metrics = self.analyzer.calculate_channel_metrics()
        best_channel, best_rate = self.analyzer.get_best_performing_channel()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'channels': {
                channel: {
                    'total_outreach': m.total_outreach,
                    'responses': m.responses,
                    'response_rate': m.response_rate,
                    'interviews': m.interviews,
                    'avg_response_time_days': m.avg_response_time_days
                }
                for channel, m in metrics.items()
            },
            'best_channel': best_channel,
            'best_rate': best_rate,
            'recommendations': self.analyzer.get_optimization_recommendations()
        }


def integrate_existing_logs():
    """
    Integrate data from existing log files into multi-channel tracker.
    """
    tracker = MultiChannelTracker()
    
    # Import from applied_log.csv
    applied_log = 'data/applied_log.csv'
    if os.path.exists(applied_log):
        print(f"Importing from {applied_log}...")
        with open(applied_log, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracker.log_activity(
                    channel='email',
                    action='application',
                    company=row.get('company', ''),
                    job_title=row.get('job_title', row.get('title', '')),
                    contact_email=row.get('hr_email', row.get('email', '')),
                    status='sent',
                    notes='Imported from applied_log'
                )
    
    # Import from linkedin_outreach.csv
    linkedin_log = 'data/linkedin_outreach.csv'
    if os.path.exists(linkedin_log):
        print(f"Importing from {linkedin_log}...")
        with open(linkedin_log, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracker.log_activity(
                    channel='linkedin',
                    action=row.get('action', 'connection'),
                    company=row.get('company', ''),
                    job_title=row.get('job_applied', ''),
                    contact_name=row.get('name', ''),
                    status=row.get('status', 'sent'),
                    notes='Imported from linkedin_outreach'
                )
    
    print("Import complete!")


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("MULTI-CHANNEL ANALYTICS DEMO")
    print("=" * 60)
    
    # Create sample data
    tracker = MultiChannelTracker()
    
    # Log some sample activities
    sample_activities = [
        ('email', 'application', 'Razorpay', 'Data Engineer'),
        ('email', 'application', 'PhonePe', 'Senior Data Engineer'),
        ('linkedin', 'connection', 'Swiggy', 'ML Engineer'),
        ('linkedin', 'message', 'Zomato', 'Backend Developer'),
        ('naukri', 'application', 'Flipkart', 'Software Engineer'),
        ('referral', 'request', 'Google', 'Software Engineer'),
    ]
    
    for channel, action, company, title in sample_activities:
        tracker.log_activity(channel, action, company, title)
    
    # Generate dashboard
    dashboard = AnalyticsDashboard()
    dashboard.generate_dashboard_report()
    
    # Get recommendations
    print("\n📊 Optimization Recommendations:")
    for rec in dashboard.analyzer.get_optimization_recommendations():
        print(f"  {rec}")
