#!/usr/bin/env python3
"""
🔗 NETWORK MAPPER - REFERRAL FINDER
Find 1st, 2nd, and 3rd degree LinkedIn connections at target companies.
Get warm introductions instead of cold applications.

Features:
- Maps your LinkedIn network
- Finds connections at target companies
- Identifies mutual connections for introductions
- Suggests referral request messages
- Tracks referral requests and outcomes
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import FreeAIManager
except ImportError:
    FreeAIManager = None


class NetworkMapper:
    """Map your professional network for referrals"""
    
    def __init__(self):
        self.connections_file = Path("data/linkedin_connections.json")
        self.referrals_file = Path("data/referral_requests.json")
        self.connections = self._load_connections()
        self.referral_requests = self._load_referrals()
        self.ai = FreeAIManager() if FreeAIManager else None
        
        # Applicant info
        self.my_name = os.getenv('APPLICANT_NAME', '')
        self.my_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        self.target_roles = os.getenv('APPLICANT_TARGET_ROLE', '').split(',')
        
    def _load_connections(self) -> Dict:
        """Load LinkedIn connections data"""
        if self.connections_file.exists():
            try:
                with open(self.connections_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'first_degree': [],
            'companies': defaultdict(list),
            'last_updated': None
        }
    
    def _save_connections(self):
        """Save connections data"""
        self.connections_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.connections_file, 'w') as f:
            json.dump(self.connections, f, indent=2, default=str)
    
    def _load_referrals(self) -> Dict:
        """Load referral request history"""
        if self.referrals_file.exists():
            try:
                with open(self.referrals_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'requests': [], 'stats': {'sent': 0, 'accepted': 0, 'hired': 0}}
    
    def _save_referrals(self):
        """Save referral requests"""
        self.referrals_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.referrals_file, 'w') as f:
            json.dump(self.referral_requests, f, indent=2)
    
    def import_linkedin_connections(self, csv_path: str):
        """
        Import connections from LinkedIn export CSV.
        Go to LinkedIn > Settings > Data Privacy > Get a copy of your data
        """
        import csv
        
        connections = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    connection = {
                        'first_name': row.get('First Name', ''),
                        'last_name': row.get('Last Name', ''),
                        'email': row.get('Email Address', ''),
                        'company': row.get('Company', ''),
                        'position': row.get('Position', ''),
                        'connected_on': row.get('Connected On', ''),
                        'degree': 1
                    }
                    connections.append(connection)
                    
                    # Index by company
                    company = connection['company'].strip()
                    if company:
                        self.connections['companies'][company.lower()].append(connection)
            
            self.connections['first_degree'] = connections
            self.connections['last_updated'] = datetime.now().isoformat()
            self._save_connections()
            
            print(f"✅ Imported {len(connections)} connections")
            print(f"📊 Connections at {len(self.connections['companies'])} companies")
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
    
    def find_connections_at_company(self, company: str) -> List[Dict]:
        """Find all connections at a specific company"""
        
        company_lower = company.lower()
        matches = []
        
        # Direct matches
        for comp_name, people in self.connections.get('companies', {}).items():
            if company_lower in comp_name or comp_name in company_lower:
                matches.extend(people)
        
        # Also search through all connections for partial matches
        for conn in self.connections.get('first_degree', []):
            conn_company = conn.get('company', '').lower()
            if company_lower in conn_company and conn not in matches:
                matches.append(conn)
        
        return matches
    
    def find_best_referrer(self, company: str, job_title: str = "") -> Optional[Dict]:
        """Find the best person to ask for a referral"""
        
        connections = self.find_connections_at_company(company)
        
        if not connections:
            return None
        
        # Score each connection
        scored = []
        job_keywords = set(job_title.lower().split())
        
        for conn in connections:
            score = 50  # Base score
            position = conn.get('position', '').lower()
            
            # Hiring manager / leadership bonus
            if any(kw in position for kw in ['manager', 'director', 'head', 'lead', 'vp', 'chief']):
                score += 30
            
            # Same department bonus
            if any(kw in position for kw in job_keywords):
                score += 25
            
            # Recruiter / HR bonus
            if any(kw in position for kw in ['recruiter', 'hr', 'talent', 'hiring']):
                score += 20
            
            # Recent connection bonus (connected in last year)
            try:
                connected = datetime.strptime(conn.get('connected_on', ''), '%d %b %Y')
                if (datetime.now() - connected).days < 365:
                    score += 10
            except:
                pass
            
            scored.append((conn, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if scored:
            return scored[0][0]
        
        return None
    
    def generate_referral_message(self, connection: Dict, job_title: str, company: str) -> str:
        """Generate personalized referral request message"""
        
        first_name = connection.get('first_name', 'there')
        position = connection.get('position', '')
        
        # Use AI if available
        if self.ai:
            prompt = f"""
            Write a brief, professional LinkedIn message requesting a job referral.
            
            Context:
            - Sender: {self.my_name}
            - Recipient: {first_name} {connection.get('last_name', '')}
            - Recipient's Position: {position}
            - Company: {company}
            - Target Job: {job_title}
            - Connection type: 1st degree LinkedIn connection
            
            Requirements:
            - Keep it under 150 words
            - Be genuine and not pushy
            - Mention specific interest in the role
            - Ask if they'd be willing to refer or share insights
            - Professional but friendly tone
            
            Write only the message, no subject line.
            """
            
            try:
                message = self.ai.generate(prompt, max_tokens=300)
                if message:
                    return message.strip()
            except:
                pass
        
        # Fallback template
        return f"""Hi {first_name},

I hope you're doing well! I noticed you're at {company} and I'm really interested in a {job_title} position there.

Given your experience as {position}, I'd love to hear your perspective on the team and culture. If you're open to it, would you be willing to refer me or share any insights about the role?

I've attached my resume for reference. No pressure at all - I completely understand if you're not able to.

Thanks so much for considering!

Best,
{self.my_name}"""
    
    def generate_introduction_request(self, mutual_connection: Dict, target_person: Dict, company: str) -> str:
        """Generate message asking mutual connection for an introduction"""
        
        mutual_name = mutual_connection.get('first_name', 'there')
        target_name = f"{target_person.get('first_name', '')} {target_person.get('last_name', '')}"
        target_position = target_person.get('position', '')
        
        return f"""Hi {mutual_name},

I hope you're doing well! I'm reaching out because I noticed you're connected with {target_name} at {company}.

I'm very interested in opportunities at {company}, and I believe {target_name}'s role as {target_position} aligns with my background.

Would you be open to making a brief introduction? I'd really appreciate any help you could provide.

Thank you so much!

Best regards,
{self.my_name}"""
    
    def track_referral_request(self, connection: Dict, company: str, job_title: str, message: str):
        """Track a referral request"""
        
        request = {
            'id': len(self.referral_requests['requests']) + 1,
            'connection': {
                'name': f"{connection.get('first_name', '')} {connection.get('last_name', '')}",
                'position': connection.get('position', ''),
                'email': connection.get('email', '')
            },
            'company': company,
            'job_title': job_title,
            'message': message,
            'status': 'sent',
            'sent_at': datetime.now().isoformat(),
            'response': None,
            'outcome': None
        }
        
        self.referral_requests['requests'].append(request)
        self.referral_requests['stats']['sent'] += 1
        self._save_referrals()
        
        return request
    
    def update_referral_status(self, request_id: int, status: str, notes: str = ""):
        """Update referral request status"""
        
        for request in self.referral_requests['requests']:
            if request['id'] == request_id:
                request['status'] = status
                request['updated_at'] = datetime.now().isoformat()
                request['notes'] = notes
                
                if status == 'accepted':
                    self.referral_requests['stats']['accepted'] += 1
                elif status == 'hired':
                    self.referral_requests['stats']['hired'] += 1
                
                self._save_referrals()
                return True
        
        return False
    
    def get_referral_stats(self) -> Dict:
        """Get referral success statistics"""
        
        stats = self.referral_requests['stats'].copy()
        
        if stats['sent'] > 0:
            stats['acceptance_rate'] = round(stats['accepted'] / stats['sent'] * 100, 1)
            stats['hire_rate'] = round(stats['hired'] / stats['sent'] * 100, 1)
        else:
            stats['acceptance_rate'] = 0
            stats['hire_rate'] = 0
        
        # Recent activity
        recent = [r for r in self.referral_requests['requests'] 
                  if r.get('sent_at', '').startswith(datetime.now().strftime('%Y-%m'))]
        stats['this_month'] = len(recent)
        
        return stats
    
    def analyze_network_strength(self) -> Dict:
        """Analyze overall network strength for job search"""
        
        connections = self.connections.get('first_degree', [])
        companies = self.connections.get('companies', {})
        
        analysis = {
            'total_connections': len(connections),
            'unique_companies': len(companies),
            'top_companies': [],
            'industry_distribution': defaultdict(int),
            'seniority_distribution': defaultdict(int),
            'network_score': 0
        }
        
        # Top companies by connection count
        company_counts = [(company, len(people)) for company, people in companies.items()]
        company_counts.sort(key=lambda x: x[1], reverse=True)
        analysis['top_companies'] = company_counts[:20]
        
        # Analyze positions
        senior_keywords = ['director', 'vp', 'chief', 'head', 'president', 'founder', 'ceo', 'cto', 'cfo']
        mid_keywords = ['manager', 'lead', 'senior', 'principal']
        
        for conn in connections:
            position = conn.get('position', '').lower()
            
            if any(kw in position for kw in senior_keywords):
                analysis['seniority_distribution']['senior'] += 1
            elif any(kw in position for kw in mid_keywords):
                analysis['seniority_distribution']['mid-level'] += 1
            else:
                analysis['seniority_distribution']['entry-level'] += 1
        
        # Calculate network score (0-100)
        score = 0
        score += min(30, len(connections) / 10)  # Up to 30 points for 300+ connections
        score += min(20, len(companies) / 5)  # Up to 20 points for 100+ companies
        score += min(25, analysis['seniority_distribution'].get('senior', 0) / 2)  # Senior connections
        score += min(25, analysis['seniority_distribution'].get('mid-level', 0) / 3)  # Mid-level
        
        analysis['network_score'] = int(min(100, score))
        
        return analysis
    
    def suggest_networking_actions(self, target_companies: List[str]) -> List[Dict]:
        """Suggest actions to improve network for target companies"""
        
        suggestions = []
        
        for company in target_companies:
            connections = self.find_connections_at_company(company)
            
            if len(connections) >= 3:
                suggestions.append({
                    'company': company,
                    'action': 'READY_FOR_REFERRAL',
                    'message': f"You have {len(connections)} connections at {company}. Request a referral!",
                    'connections': connections[:3]
                })
            elif len(connections) > 0:
                suggestions.append({
                    'company': company,
                    'action': 'STRENGTHEN_CONNECTION',
                    'message': f"You have {len(connections)} connection(s). Engage with them before requesting.",
                    'connections': connections
                })
            else:
                suggestions.append({
                    'company': company,
                    'action': 'BUILD_CONNECTIONS',
                    'message': f"No connections at {company}. Search for alumni or mutual connections.",
                    'tips': [
                        "Search LinkedIn for company employees",
                        "Look for alumni from your school",
                        "Join company-related LinkedIn groups",
                        "Engage with company's LinkedIn posts"
                    ]
                })
        
        return suggestions


def main():
    """Main entry point"""
    mapper = NetworkMapper()
    
    print(f"\n🔗 NETWORK MAPPER")
    print(f"{'='*50}")
    
    # Example: Find connections at a company
    test_companies = ['Google', 'Microsoft', 'Amazon', 'Meta']
    
    print(f"\n📊 Searching for connections at target companies...")
    
    suggestions = mapper.suggest_networking_actions(test_companies)
    
    for suggestion in suggestions:
        print(f"\n🏢 {suggestion['company']}:")
        print(f"   Action: {suggestion['action']}")
        print(f"   {suggestion['message']}")
        
        if 'connections' in suggestion:
            for conn in suggestion['connections'][:3]:
                name = f"{conn.get('first_name', '')} {conn.get('last_name', '')}"
                position = conn.get('position', 'Unknown')
                print(f"   • {name} - {position}")
    
    # Referral stats
    stats = mapper.get_referral_stats()
    print(f"\n📈 REFERRAL STATS:")
    print(f"   Sent: {stats['sent']}")
    print(f"   Accepted: {stats['accepted']} ({stats['acceptance_rate']}%)")
    print(f"   Hired: {stats['hired']} ({stats['hire_rate']}%)")


if __name__ == "__main__":
    main()
