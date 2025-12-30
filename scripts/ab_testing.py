#!/usr/bin/env python3
"""
🧪 APPLICATION A/B TESTING
Test different resume versions, cover letters, and email subjects.
Track which versions get the best response rates.

Features:
- Create A/B test experiments
- Randomly assign versions to applications
- Track response rates by version
- Statistical significance testing
- Auto-select winning variants
- Continuous optimization
"""

import os
import sys
import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ABTestManager:
    """Manage A/B tests for job applications"""
    
    def __init__(self):
        self.experiments_file = Path("data/ab_experiments.json")
        self.results_file = Path("data/ab_results.json")
        self.experiments = self._load_experiments()
        self.results = self._load_results()
        
    def _load_experiments(self) -> Dict:
        """Load experiments"""
        if self.experiments_file.exists():
            try:
                with open(self.experiments_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'experiments': {}}
    
    def _save_experiments(self):
        """Save experiments"""
        self.experiments_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.experiments_file, 'w') as f:
            json.dump(self.experiments, f, indent=2)
    
    def _load_results(self) -> Dict:
        """Load results"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'applications': []}
    
    def _save_results(self):
        """Save results"""
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def create_experiment(self, name: str, experiment_type: str, variants: List[Dict]) -> Dict:
        """
        Create a new A/B test experiment.
        
        experiment_type: 'resume', 'cover_letter', 'email_subject', 'email_body'
        variants: List of variant configurations
        """
        
        experiment_id = hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        experiment = {
            'id': experiment_id,
            'name': name,
            'type': experiment_type,
            'variants': [],
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'total_assignments': 0,
            'winner': None
        }
        
        # Add variants with equal traffic split
        traffic_per_variant = 100 / len(variants)
        for i, variant in enumerate(variants):
            experiment['variants'].append({
                'id': f"v{i+1}",
                'name': variant.get('name', f"Variant {i+1}"),
                'content': variant.get('content', ''),
                'file_path': variant.get('file_path', ''),
                'traffic_percentage': traffic_per_variant,
                'assignments': 0,
                'responses': 0,
                'interviews': 0,
                'offers': 0
            })
        
        self.experiments['experiments'][experiment_id] = experiment
        self._save_experiments()
        
        print(f"✅ Created experiment: {name} ({experiment_id})")
        return experiment
    
    def get_variant(self, experiment_id: str, application_id: str = None) -> Dict:
        """
        Get a variant for an application.
        Uses deterministic assignment if application_id provided.
        """
        
        experiment = self.experiments['experiments'].get(experiment_id)
        if not experiment or experiment['status'] != 'active':
            return None
        
        # If there's a winner, always return it
        if experiment.get('winner'):
            for variant in experiment['variants']:
                if variant['id'] == experiment['winner']:
                    return variant
        
        # Deterministic assignment based on application_id
        if application_id:
            hash_val = int(hashlib.md5(f"{experiment_id}{application_id}".encode()).hexdigest(), 16)
            rand_val = (hash_val % 100) + 1
        else:
            rand_val = random.randint(1, 100)
        
        # Select variant based on traffic percentage
        cumulative = 0
        for variant in experiment['variants']:
            cumulative += variant['traffic_percentage']
            if rand_val <= cumulative:
                variant['assignments'] += 1
                experiment['total_assignments'] += 1
                self._save_experiments()
                return variant
        
        # Fallback to first variant
        return experiment['variants'][0]
    
    def record_outcome(self, experiment_id: str, variant_id: str, outcome: str, 
                       application_details: Dict = None):
        """
        Record outcome for an application.
        outcome: 'sent', 'opened', 'response', 'interview', 'offer', 'rejection'
        """
        
        experiment = self.experiments['experiments'].get(experiment_id)
        if not experiment:
            return False
        
        # Find variant
        for variant in experiment['variants']:
            if variant['id'] == variant_id:
                if outcome == 'response':
                    variant['responses'] += 1
                elif outcome == 'interview':
                    variant['interviews'] += 1
                elif outcome == 'offer':
                    variant['offers'] += 1
                break
        
        # Record in results
        self.results['applications'].append({
            'experiment_id': experiment_id,
            'variant_id': variant_id,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat(),
            'details': application_details or {}
        })
        
        self._save_experiments()
        self._save_results()
        
        # Check for statistical significance
        self._check_significance(experiment_id)
        
        return True
    
    def _check_significance(self, experiment_id: str, confidence: float = 0.95):
        """Check if there's a statistically significant winner"""
        
        experiment = self.experiments['experiments'].get(experiment_id)
        if not experiment or len(experiment['variants']) < 2:
            return
        
        # Need minimum sample size
        min_samples = 30
        if experiment['total_assignments'] < min_samples * len(experiment['variants']):
            return
        
        # Calculate response rates
        rates = []
        for variant in experiment['variants']:
            if variant['assignments'] > 0:
                rate = variant['responses'] / variant['assignments']
                rates.append((variant['id'], rate, variant['assignments']))
        
        if len(rates) < 2:
            return
        
        # Sort by rate
        rates.sort(key=lambda x: x[1], reverse=True)
        best = rates[0]
        second = rates[1]
        
        # Simple statistical test (Z-test for proportions)
        p1, n1 = best[1], best[2]
        p2, n2 = second[1], second[2]
        
        if n1 == 0 or n2 == 0:
            return
        
        # Pooled proportion
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        
        if p_pool == 0 or p_pool == 1:
            return
        
        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        if se == 0:
            return
        
        # Z-score
        z = (p1 - p2) / se
        
        # For 95% confidence, z > 1.96
        z_critical = 1.96 if confidence == 0.95 else 2.576
        
        if z > z_critical:
            experiment['winner'] = best[0]
            experiment['status'] = 'completed'
            experiment['completed_at'] = datetime.now().isoformat()
            experiment['winning_rate'] = round(p1 * 100, 1)
            experiment['confidence'] = confidence
            
            self._save_experiments()
            
            print(f"🏆 WINNER FOUND: {best[0]} with {round(p1*100, 1)}% response rate!")
    
    def get_experiment_stats(self, experiment_id: str) -> Dict:
        """Get statistics for an experiment"""
        
        experiment = self.experiments['experiments'].get(experiment_id)
        if not experiment:
            return None
        
        stats = {
            'name': experiment['name'],
            'type': experiment['type'],
            'status': experiment['status'],
            'total_assignments': experiment['total_assignments'],
            'created_at': experiment['created_at'],
            'winner': experiment.get('winner'),
            'variants': []
        }
        
        for variant in experiment['variants']:
            assignments = variant['assignments']
            response_rate = (variant['responses'] / assignments * 100) if assignments > 0 else 0
            interview_rate = (variant['interviews'] / assignments * 100) if assignments > 0 else 0
            
            stats['variants'].append({
                'id': variant['id'],
                'name': variant['name'],
                'assignments': assignments,
                'responses': variant['responses'],
                'interviews': variant['interviews'],
                'offers': variant['offers'],
                'response_rate': round(response_rate, 1),
                'interview_rate': round(interview_rate, 1),
                'is_winner': variant['id'] == experiment.get('winner')
            })
        
        return stats
    
    def print_experiment_report(self, experiment_id: str):
        """Print formatted experiment report"""
        
        stats = self.get_experiment_stats(experiment_id)
        if not stats:
            print(f"Experiment not found: {experiment_id}")
            return
        
        print(f"\n{'='*60}")
        print(f"🧪 A/B TEST REPORT: {stats['name']}")
        print(f"{'='*60}")
        
        print(f"\n📊 Status: {stats['status'].upper()}")
        print(f"📅 Created: {stats['created_at'][:10]}")
        print(f"📧 Total Applications: {stats['total_assignments']}")
        
        if stats['winner']:
            print(f"🏆 Winner: {stats['winner']}")
        
        print(f"\n{'─'*60}")
        print(f"{'Variant':<15} {'Sent':<8} {'Responses':<10} {'Rate':<8} {'Interviews':<10}")
        print(f"{'─'*60}")
        
        for variant in stats['variants']:
            winner_mark = " 🏆" if variant['is_winner'] else ""
            print(f"{variant['name']:<15} {variant['assignments']:<8} {variant['responses']:<10} "
                  f"{variant['response_rate']:<8}% {variant['interviews']:<10}{winner_mark}")
        
        print(f"{'─'*60}\n")
    
    def create_resume_test(self, resume_paths: List[str], test_name: str = "Resume Test") -> str:
        """Quick helper to create a resume A/B test"""
        
        variants = []
        for i, path in enumerate(resume_paths):
            variants.append({
                'name': f"Resume V{i+1}",
                'file_path': path,
                'content': f"Resume version {i+1}"
            })
        
        experiment = self.create_experiment(test_name, 'resume', variants)
        return experiment['id']
    
    def create_subject_test(self, subjects: List[str], test_name: str = "Subject Line Test") -> str:
        """Quick helper to create email subject A/B test"""
        
        variants = []
        for i, subject in enumerate(subjects):
            variants.append({
                'name': f"Subject V{i+1}",
                'content': subject
            })
        
        experiment = self.create_experiment(test_name, 'email_subject', variants)
        return experiment['id']
    
    def get_best_performing(self, experiment_type: str = None) -> List[Dict]:
        """Get best performing variants across experiments"""
        
        best = []
        
        for exp_id, experiment in self.experiments['experiments'].items():
            if experiment_type and experiment['type'] != experiment_type:
                continue
            
            for variant in experiment['variants']:
                if variant['assignments'] >= 10:  # Minimum sample size
                    rate = variant['responses'] / variant['assignments'] * 100
                    best.append({
                        'experiment': experiment['name'],
                        'variant': variant['name'],
                        'content': variant.get('content', '')[:100],
                        'response_rate': round(rate, 1),
                        'sample_size': variant['assignments']
                    })
        
        best.sort(key=lambda x: x['response_rate'], reverse=True)
        return best[:10]
    
    def list_active_experiments(self) -> List[Dict]:
        """List all active experiments"""
        
        active = []
        for exp_id, experiment in self.experiments['experiments'].items():
            if experiment['status'] == 'active':
                active.append({
                    'id': exp_id,
                    'name': experiment['name'],
                    'type': experiment['type'],
                    'total_assignments': experiment['total_assignments'],
                    'variants_count': len(experiment['variants'])
                })
        
        return active


# Pre-configured test templates
class TestTemplates:
    """Pre-built A/B test templates"""
    
    @staticmethod
    def get_subject_line_variants() -> List[str]:
        """Get pre-written subject line variants to test"""
        return [
            "Application for {job_title} - {name}",
            "{name} - Experienced {role} interested in {job_title}",
            "Passionate {role} seeking {job_title} opportunity at {company}",
            "{years} years exp {role} - {job_title} application",
            "Referred candidate for {job_title} - {name}",
            "[Application] {job_title} - {name} | {years}+ years experience",
        ]
    
    @staticmethod
    def get_email_opening_variants() -> List[str]:
        """Get email opening variants to test"""
        return [
            "I hope this email finds you well.",
            "I came across the {job_title} position and was immediately excited.",
            "I'm reaching out regarding the {job_title} opening at {company}.",
            "Your {job_title} position caught my attention on LinkedIn.",
            "I was referred by a colleague who spoke highly of {company}.",
        ]
    
    @staticmethod
    def get_cta_variants() -> List[str]:
        """Get call-to-action variants to test"""
        return [
            "I would love the opportunity to discuss how my skills can benefit your team.",
            "Would you be available for a brief call this week?",
            "I'm available for an interview at your earliest convenience.",
            "Please let me know if you'd like to schedule a conversation.",
            "I'd welcome the chance to learn more about this role and share my experience.",
        ]


def main():
    """Main entry point"""
    manager = ABTestManager()
    
    print(f"\n🧪 A/B TEST MANAGER")
    print(f"{'='*50}")
    
    # List active experiments
    active = manager.list_active_experiments()
    print(f"\n📊 Active Experiments: {len(active)}")
    
    for exp in active:
        print(f"   • {exp['name']} ({exp['type']}) - {exp['total_assignments']} assignments")
    
    # Show templates
    print(f"\n📝 Available Subject Line Variants:")
    for i, subject in enumerate(TestTemplates.get_subject_line_variants(), 1):
        print(f"   {i}. {subject}")
    
    # Best performing
    best = manager.get_best_performing()
    if best:
        print(f"\n🏆 Top Performing Variants:")
        for item in best[:5]:
            print(f"   • {item['variant']} ({item['response_rate']}% response rate)")


if __name__ == "__main__":
    main()
