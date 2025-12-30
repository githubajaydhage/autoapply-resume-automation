#!/usr/bin/env python3
"""
👥 RECRUITER CRM
Track recruiter relationships, conversations, and follow-up history.

Features:
- Store recruiter contacts with notes
- Track conversation history
- Schedule follow-ups
- Relationship scoring
- Agency vs direct recruiter tracking
- Interaction analytics
- Auto-remind for follow-ups
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RecruiterCRM:
    """Manage recruiter relationships"""
    
    def __init__(self):
        self.contacts_file = Path("data/recruiter_contacts.json")
        self.interactions_file = Path("data/recruiter_interactions.json")
        self.contacts = self._load_contacts()
        self.interactions = self._load_interactions()
        
    def _load_contacts(self) -> Dict:
        """Load recruiter contacts"""
        if self.contacts_file.exists():
            try:
                with open(self.contacts_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'recruiters': {}}
    
    def _save_contacts(self):
        """Save contacts"""
        self.contacts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.contacts_file, 'w') as f:
            json.dump(self.contacts, f, indent=2)
    
    def _load_interactions(self) -> Dict:
        """Load interaction history"""
        if self.interactions_file.exists():
            try:
                with open(self.interactions_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'interactions': []}
    
    def _save_interactions(self):
        """Save interactions"""
        self.interactions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.interactions_file, 'w') as f:
            json.dump(self.interactions, f, indent=2)
    
    def add_recruiter(self, email: str, name: str, company: str = "", 
                      recruiter_type: str = "direct", notes: str = "") -> Dict:
        """Add a new recruiter contact"""
        
        recruiter_id = email.lower()
        
        recruiter = {
            'id': recruiter_id,
            'email': email,
            'name': name,
            'company': company,
            'type': recruiter_type,  # 'direct', 'agency', 'internal_hr'
            'phone': '',
            'linkedin': '',
            'notes': notes,
            'specializations': [],
            'companies_hiring_for': [],
            'relationship_score': 50,
            'created_at': datetime.now().isoformat(),
            'last_interaction': None,
            'next_followup': None,
            'tags': [],
            'status': 'active'  # 'active', 'cold', 'unresponsive', 'do_not_contact'
        }
        
        self.contacts['recruiters'][recruiter_id] = recruiter
        self._save_contacts()
        
        print(f"✅ Added recruiter: {name} ({email})")
        return recruiter
    
    def update_recruiter(self, email: str, updates: Dict) -> Optional[Dict]:
        """Update recruiter information"""
        
        recruiter_id = email.lower()
        
        if recruiter_id not in self.contacts['recruiters']:
            print(f"❌ Recruiter not found: {email}")
            return None
        
        self.contacts['recruiters'][recruiter_id].update(updates)
        self.contacts['recruiters'][recruiter_id]['updated_at'] = datetime.now().isoformat()
        self._save_contacts()
        
        return self.contacts['recruiters'][recruiter_id]
    
    def log_interaction(self, email: str, interaction_type: str, 
                        subject: str = "", notes: str = "", 
                        outcome: str = "") -> Dict:
        """
        Log an interaction with a recruiter.
        
        interaction_type: 'email_sent', 'email_received', 'call', 'linkedin_message', 'meeting', 'interview'
        outcome: 'positive', 'neutral', 'negative', 'pending'
        """
        
        recruiter_id = email.lower()
        
        interaction = {
            'id': len(self.interactions['interactions']) + 1,
            'recruiter_id': recruiter_id,
            'type': interaction_type,
            'subject': subject,
            'notes': notes,
            'outcome': outcome or 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        self.interactions['interactions'].append(interaction)
        self._save_interactions()
        
        # Update recruiter's last interaction
        if recruiter_id in self.contacts['recruiters']:
            self.contacts['recruiters'][recruiter_id]['last_interaction'] = datetime.now().isoformat()
            
            # Update relationship score based on outcome
            if outcome == 'positive':
                self._adjust_relationship_score(recruiter_id, 10)
            elif outcome == 'negative':
                self._adjust_relationship_score(recruiter_id, -5)
            
            self._save_contacts()
        
        return interaction
    
    def _adjust_relationship_score(self, recruiter_id: str, adjustment: int):
        """Adjust relationship score"""
        
        if recruiter_id in self.contacts['recruiters']:
            current = self.contacts['recruiters'][recruiter_id].get('relationship_score', 50)
            new_score = max(0, min(100, current + adjustment))
            self.contacts['recruiters'][recruiter_id]['relationship_score'] = new_score
    
    def schedule_followup(self, email: str, days_from_now: int = 7, 
                          reason: str = "") -> Optional[Dict]:
        """Schedule a follow-up with recruiter"""
        
        recruiter_id = email.lower()
        
        if recruiter_id not in self.contacts['recruiters']:
            print(f"❌ Recruiter not found: {email}")
            return None
        
        followup_date = (datetime.now() + timedelta(days=days_from_now)).isoformat()
        
        self.contacts['recruiters'][recruiter_id]['next_followup'] = {
            'date': followup_date,
            'reason': reason
        }
        self._save_contacts()
        
        print(f"📅 Follow-up scheduled with {email} in {days_from_now} days")
        return self.contacts['recruiters'][recruiter_id]
    
    def get_due_followups(self) -> List[Dict]:
        """Get recruiters due for follow-up"""
        
        due = []
        now = datetime.now()
        
        for recruiter_id, recruiter in self.contacts['recruiters'].items():
            followup = recruiter.get('next_followup')
            if not followup:
                continue
            
            try:
                followup_date = datetime.fromisoformat(followup['date'])
                if followup_date <= now:
                    due.append({
                        'recruiter': recruiter,
                        'followup': followup,
                        'days_overdue': (now - followup_date).days
                    })
            except:
                pass
        
        due.sort(key=lambda x: x['days_overdue'], reverse=True)
        return due
    
    def get_recruiter_history(self, email: str) -> Dict:
        """Get complete history with a recruiter"""
        
        recruiter_id = email.lower()
        
        if recruiter_id not in self.contacts['recruiters']:
            return None
        
        recruiter = self.contacts['recruiters'][recruiter_id]
        
        # Get all interactions
        interactions = [
            i for i in self.interactions['interactions']
            if i['recruiter_id'] == recruiter_id
        ]
        interactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'recruiter': recruiter,
            'interactions': interactions,
            'interaction_count': len(interactions),
            'positive_outcomes': len([i for i in interactions if i['outcome'] == 'positive']),
            'last_contact': interactions[0]['timestamp'] if interactions else None
        }
    
    def find_recruiters(self, query: str = None, recruiter_type: str = None,
                        company: str = None, min_score: int = None) -> List[Dict]:
        """Search and filter recruiters"""
        
        results = []
        
        for recruiter_id, recruiter in self.contacts['recruiters'].items():
            # Filter by query
            if query:
                query_lower = query.lower()
                if not (query_lower in recruiter['name'].lower() or
                        query_lower in recruiter['email'].lower() or
                        query_lower in recruiter.get('company', '').lower() or
                        query_lower in ' '.join(recruiter.get('tags', [])).lower()):
                    continue
            
            # Filter by type
            if recruiter_type and recruiter['type'] != recruiter_type:
                continue
            
            # Filter by company
            if company and company.lower() not in recruiter.get('company', '').lower():
                continue
            
            # Filter by score
            if min_score and recruiter.get('relationship_score', 0) < min_score:
                continue
            
            results.append(recruiter)
        
        # Sort by relationship score
        results.sort(key=lambda x: x.get('relationship_score', 0), reverse=True)
        
        return results
    
    def get_top_recruiters(self, limit: int = 10) -> List[Dict]:
        """Get top recruiters by relationship score"""
        
        recruiters = list(self.contacts['recruiters'].values())
        recruiters.sort(key=lambda x: x.get('relationship_score', 0), reverse=True)
        
        return recruiters[:limit]
    
    def get_inactive_recruiters(self, days: int = 30) -> List[Dict]:
        """Get recruiters with no recent interaction"""
        
        cutoff = datetime.now() - timedelta(days=days)
        inactive = []
        
        for recruiter in self.contacts['recruiters'].values():
            last = recruiter.get('last_interaction')
            if not last:
                inactive.append(recruiter)
            else:
                try:
                    last_date = datetime.fromisoformat(last)
                    if last_date < cutoff:
                        inactive.append(recruiter)
                except:
                    pass
        
        return inactive
    
    def get_analytics(self) -> Dict:
        """Get CRM analytics"""
        
        total_recruiters = len(self.contacts['recruiters'])
        total_interactions = len(self.interactions['interactions'])
        
        # Count by type
        by_type = defaultdict(int)
        for recruiter in self.contacts['recruiters'].values():
            by_type[recruiter.get('type', 'unknown')] += 1
        
        # Count by status
        by_status = defaultdict(int)
        for recruiter in self.contacts['recruiters'].values():
            by_status[recruiter.get('status', 'active')] += 1
        
        # Interaction outcomes
        outcomes = defaultdict(int)
        for interaction in self.interactions['interactions']:
            outcomes[interaction.get('outcome', 'pending')] += 1
        
        # Average relationship score
        scores = [r.get('relationship_score', 50) for r in self.contacts['recruiters'].values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Recent activity (last 30 days)
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        recent = [i for i in self.interactions['interactions'] if i['timestamp'] >= cutoff]
        
        return {
            'total_recruiters': total_recruiters,
            'total_interactions': total_interactions,
            'by_type': dict(by_type),
            'by_status': dict(by_status),
            'interaction_outcomes': dict(outcomes),
            'average_relationship_score': round(avg_score, 1),
            'interactions_last_30_days': len(recent),
            'due_followups': len(self.get_due_followups())
        }
    
    def generate_followup_email(self, email: str, context: str = "") -> str:
        """Generate follow-up email for a recruiter"""
        
        history = self.get_recruiter_history(email)
        if not history:
            return ""
        
        recruiter = history['recruiter']
        name = recruiter['name'].split()[0]  # First name
        last_interaction = history['interactions'][0] if history['interactions'] else None
        
        # Basic template
        template = f"""Hi {name},

I hope you're doing well! I wanted to follow up on our previous conversation.

{context if context else "I'm still very interested in opportunities you might be working on."}

Please let me know if there are any updates or if you need any additional information from me.

Thank you!

Best regards,
{os.getenv('APPLICANT_NAME', '')}"""
        
        return template
    
    def import_from_email(self, emails: List[Dict]):
        """Import recruiters from email data"""
        
        imported = 0
        
        for email_data in emails:
            sender = email_data.get('from', '')
            sender_name = email_data.get('from_name', '')
            
            # Check if it looks like a recruiter
            recruiter_indicators = ['recruit', 'talent', 'hr', 'hiring', 'staffing']
            if not any(ind in sender.lower() or ind in sender_name.lower() for ind in recruiter_indicators):
                continue
            
            # Add if not exists
            if sender.lower() not in self.contacts['recruiters']:
                self.add_recruiter(
                    email=sender,
                    name=sender_name or sender.split('@')[0],
                    recruiter_type='agency' if any(x in sender.lower() for x in ['staffing', 'consulting', 'solution']) else 'direct'
                )
                imported += 1
        
        print(f"✅ Imported {imported} recruiters from emails")
        return imported
    
    def print_dashboard(self):
        """Print CRM dashboard"""
        
        analytics = self.get_analytics()
        due = self.get_due_followups()
        top = self.get_top_recruiters(5)
        
        print(f"\n{'='*60}")
        print(f"👥 RECRUITER CRM DASHBOARD")
        print(f"{'='*60}")
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Recruiters: {analytics['total_recruiters']}")
        print(f"   Total Interactions: {analytics['total_interactions']}")
        print(f"   Avg Relationship Score: {analytics['average_relationship_score']}/100")
        print(f"   Last 30 Days Activity: {analytics['interactions_last_30_days']} interactions")
        
        print(f"\n📋 BY TYPE:")
        for type_name, count in analytics['by_type'].items():
            print(f"   • {type_name}: {count}")
        
        print(f"\n⚠️ DUE FOLLOW-UPS ({len(due)}):")
        for item in due[:5]:
            r = item['recruiter']
            print(f"   • {r['name']} ({r['email']}) - {item['days_overdue']} days overdue")
        
        print(f"\n🌟 TOP RECRUITERS:")
        for r in top:
            print(f"   • {r['name']} - Score: {r['relationship_score']}/100")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    crm = RecruiterCRM()
    
    # Print dashboard
    crm.print_dashboard()
    
    # Show analytics
    analytics = crm.get_analytics()
    print(f"📈 Total in CRM: {analytics['total_recruiters']} recruiters")


if __name__ == "__main__":
    main()
