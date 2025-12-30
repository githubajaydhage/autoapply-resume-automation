#!/usr/bin/env python3
"""
📊 SKILLS GAP ANALYZER
Identify missing skills and recommend courses/certifications.

Features:
- Analyzes job requirements vs your skills
- Identifies skill gaps
- Recommends FREE courses (Coursera, Udemy, YouTube)
- Prioritizes skills by job market demand
- Tracks skill development progress
- Estimates time to become qualified
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import FreeAIManager
except ImportError:
    FreeAIManager = None


class SkillsGapAnalyzer:
    """Analyze skill gaps and recommend learning paths"""
    
    # Common skill categories
    SKILL_CATEGORIES = {
        'programming_languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'sql', 'bash', 'perl'
        ],
        'frameworks': [
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
            'node.js', 'express', 'nextjs', 'rails', 'laravel', '.net', 'tensorflow',
            'pytorch', 'keras', 'pandas', 'numpy', 'scikit-learn'
        ],
        'cloud_platforms': [
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
            'cloudflare', 'vercel', 'netlify'
        ],
        'databases': [
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'dynamodb', 'sqlite', 'oracle', 'sql server', 'neo4j', 'firebase'
        ],
        'devops': [
            'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions',
            'terraform', 'ansible', 'puppet', 'chef', 'circleci', 'travis'
        ],
        'data_tools': [
            'tableau', 'power bi', 'looker', 'metabase', 'excel', 'spark',
            'hadoop', 'airflow', 'dbt', 'snowflake', 'databricks', 'bigquery'
        ],
        'soft_skills': [
            'communication', 'leadership', 'teamwork', 'problem solving',
            'critical thinking', 'time management', 'project management', 'agile'
        ]
    }
    
    # Free course providers
    FREE_COURSES = {
        'python': [
            {'title': 'Python for Everybody', 'provider': 'Coursera', 'url': 'https://www.coursera.org/specializations/python', 'hours': 60},
            {'title': 'Learn Python', 'provider': 'Codecademy', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'hours': 25},
            {'title': 'Python Tutorial', 'provider': 'YouTube (freeCodeCamp)', 'url': 'https://www.youtube.com/watch?v=rfscVS0vtbw', 'hours': 4},
        ],
        'sql': [
            {'title': 'SQL for Data Science', 'provider': 'Coursera', 'url': 'https://www.coursera.org/learn/sql-for-data-science', 'hours': 15},
            {'title': 'SQL Tutorial', 'provider': 'W3Schools', 'url': 'https://www.w3schools.com/sql/', 'hours': 10},
            {'title': 'Learn SQL', 'provider': 'Codecademy', 'url': 'https://www.codecademy.com/learn/learn-sql', 'hours': 8},
        ],
        'aws': [
            {'title': 'AWS Cloud Practitioner', 'provider': 'AWS Training', 'url': 'https://aws.amazon.com/training/', 'hours': 20},
            {'title': 'AWS Fundamentals', 'provider': 'Coursera', 'url': 'https://www.coursera.org/specializations/aws-fundamentals', 'hours': 16},
        ],
        'docker': [
            {'title': 'Docker Tutorial', 'provider': 'Docker Docs', 'url': 'https://docs.docker.com/get-started/', 'hours': 5},
            {'title': 'Docker for Beginners', 'provider': 'YouTube (TechWorld)', 'url': 'https://www.youtube.com/watch?v=fqMOX6JJhGo', 'hours': 3},
        ],
        'kubernetes': [
            {'title': 'Kubernetes Basics', 'provider': 'Kubernetes.io', 'url': 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'hours': 10},
            {'title': 'Kubernetes Course', 'provider': 'YouTube (TechWorld)', 'url': 'https://www.youtube.com/watch?v=X48VuDVv0do', 'hours': 4},
        ],
        'react': [
            {'title': 'React Tutorial', 'provider': 'React Docs', 'url': 'https://react.dev/learn', 'hours': 15},
            {'title': 'React Course', 'provider': 'YouTube (freeCodeCamp)', 'url': 'https://www.youtube.com/watch?v=bMknfKXIFA8', 'hours': 12},
        ],
        'tableau': [
            {'title': 'Tableau Training', 'provider': 'Tableau Public', 'url': 'https://public.tableau.com/app/learn/how-to-videos', 'hours': 10},
            {'title': 'Data Visualization', 'provider': 'Coursera', 'url': 'https://www.coursera.org/learn/analytics-tableau', 'hours': 15},
        ],
        'power bi': [
            {'title': 'Power BI Learning', 'provider': 'Microsoft Learn', 'url': 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi', 'hours': 20},
        ],
        'machine learning': [
            {'title': 'Machine Learning', 'provider': 'Coursera (Stanford)', 'url': 'https://www.coursera.org/learn/machine-learning', 'hours': 60},
            {'title': 'ML Crash Course', 'provider': 'Google', 'url': 'https://developers.google.com/machine-learning/crash-course', 'hours': 15},
        ],
        'data analysis': [
            {'title': 'Google Data Analytics', 'provider': 'Coursera', 'url': 'https://www.coursera.org/professional-certificates/google-data-analytics', 'hours': 180},
            {'title': 'Data Analysis with Python', 'provider': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/learn/data-analysis-with-python/', 'hours': 300},
        ],
    }
    
    def __init__(self):
        self.my_skills = self._load_my_skills()
        self.skill_gaps_file = Path("data/skill_gaps.json")
        self.learning_progress_file = Path("data/learning_progress.json")
        self.ai = FreeAIManager() if FreeAIManager else None
        
    def _load_my_skills(self) -> Set[str]:
        """Load user's current skills"""
        skills_str = os.getenv('APPLICANT_SKILLS', '')
        skills = set()
        
        for skill in skills_str.lower().replace(';', ',').split(','):
            skill = skill.strip()
            if skill:
                skills.add(skill)
        
        return skills
    
    def extract_skills_from_job(self, job_description: str) -> Dict[str, List[str]]:
        """Extract required skills from job description"""
        
        job_lower = job_description.lower()
        found_skills = defaultdict(list)
        
        # Check each category
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                # Use word boundary matching
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, job_lower):
                    found_skills[category].append(skill)
        
        # Use AI for deeper analysis if available
        if self.ai:
            prompt = f"""
            Extract all technical skills, tools, and technologies from this job description.
            Also identify soft skills and years of experience requirements.
            
            Job Description:
            {job_description[:2000]}
            
            Return as JSON:
            {{
                "technical_skills": ["skill1", "skill2"],
                "tools": ["tool1", "tool2"],
                "soft_skills": ["skill1"],
                "years_experience": 0,
                "education": "degree required"
            }}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=400)
                if response:
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        ai_skills = json.loads(json_match.group())
                        for skill in ai_skills.get('technical_skills', []):
                            found_skills['ai_extracted'].append(skill.lower())
            except:
                pass
        
        return dict(found_skills)
    
    def analyze_gap(self, job_description: str, job_title: str = "") -> Dict:
        """Analyze skill gap for a specific job"""
        
        required_skills = self.extract_skills_from_job(job_description)
        
        # Flatten all required skills
        all_required = set()
        for category, skills in required_skills.items():
            all_required.update(skill.lower() for skill in skills)
        
        # Find gaps
        matching_skills = self.my_skills.intersection(all_required)
        missing_skills = all_required - self.my_skills
        
        # Calculate match percentage
        if all_required:
            match_percentage = len(matching_skills) / len(all_required) * 100
        else:
            match_percentage = 0
        
        # Prioritize missing skills
        prioritized_gaps = self._prioritize_skills(list(missing_skills))
        
        # Get course recommendations
        recommendations = []
        for skill, priority in prioritized_gaps[:5]:  # Top 5 gaps
            courses = self._get_courses_for_skill(skill)
            if courses:
                recommendations.append({
                    'skill': skill,
                    'priority': priority,
                    'courses': courses
                })
        
        # Estimate time to close gap
        total_hours = sum(
            min(course['hours'] for course in rec['courses']) 
            for rec in recommendations if rec['courses']
        )
        
        analysis = {
            'job_title': job_title,
            'analyzed_at': datetime.now().isoformat(),
            'required_skills': list(all_required),
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'match_percentage': round(match_percentage, 1),
            'skill_gaps': prioritized_gaps,
            'recommendations': recommendations,
            'estimated_hours_to_qualify': total_hours,
            'estimated_weeks': round(total_hours / 10, 1),  # Assuming 10 hrs/week
            'qualification_status': self._get_qualification_status(match_percentage)
        }
        
        return analysis
    
    def _prioritize_skills(self, skills: List[str]) -> List[Tuple[str, str]]:
        """Prioritize skills by market demand"""
        
        # High-demand skills get higher priority
        high_demand = {'python', 'sql', 'aws', 'kubernetes', 'react', 'machine learning', 
                       'docker', 'typescript', 'go', 'rust', 'terraform'}
        medium_demand = {'java', 'javascript', 'azure', 'gcp', 'mongodb', 'postgresql',
                        'tableau', 'power bi', 'spark', 'airflow'}
        
        prioritized = []
        
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in high_demand:
                prioritized.append((skill, 'HIGH'))
            elif skill_lower in medium_demand:
                prioritized.append((skill, 'MEDIUM'))
            else:
                prioritized.append((skill, 'LOW'))
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        prioritized.sort(key=lambda x: priority_order.get(x[1], 2))
        
        return prioritized
    
    def _get_courses_for_skill(self, skill: str) -> List[Dict]:
        """Get course recommendations for a skill"""
        
        skill_lower = skill.lower()
        
        # Direct match
        if skill_lower in self.FREE_COURSES:
            return self.FREE_COURSES[skill_lower]
        
        # Partial match
        for course_skill, courses in self.FREE_COURSES.items():
            if course_skill in skill_lower or skill_lower in course_skill:
                return courses
        
        # Use AI to find courses
        if self.ai:
            prompt = f"""
            Recommend 2-3 FREE online courses to learn "{skill}".
            Include courses from: Coursera (audit), YouTube, freeCodeCamp, official docs.
            
            Return as JSON array:
            [
                {{"title": "Course Name", "provider": "Platform", "url": "https://...", "hours": 10}}
            ]
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=300)
                if response:
                    json_match = re.search(r'\[[^\[\]]*\]', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
            except:
                pass
        
        return []
    
    def _get_qualification_status(self, match_percentage: float) -> str:
        """Get qualification status based on match percentage"""
        
        if match_percentage >= 80:
            return "HIGHLY QUALIFIED ✅"
        elif match_percentage >= 60:
            return "QUALIFIED - Apply Now! 👍"
        elif match_percentage >= 40:
            return "PARTIALLY QUALIFIED - Apply & Upskill 📚"
        elif match_percentage >= 20:
            return "SKILL GAP - Upskill First ⚠️"
        else:
            return "SIGNIFICANT GAP - Major Upskilling Needed ❌"
    
    def analyze_multiple_jobs(self, jobs: List[Dict]) -> Dict:
        """Analyze skill gaps across multiple job listings"""
        
        all_required = Counter()
        all_missing = Counter()
        
        for job in jobs:
            description = job.get('description', '')
            if not description:
                continue
            
            analysis = self.analyze_gap(description, job.get('title', ''))
            
            for skill in analysis['required_skills']:
                all_required[skill] += 1
            
            for skill in analysis['missing_skills']:
                all_missing[skill] += 1
        
        # Most commonly required skills
        top_required = all_required.most_common(20)
        
        # Most common gaps
        top_gaps = all_missing.most_common(10)
        
        # Generate learning plan
        learning_plan = []
        for skill, count in top_gaps[:5]:
            courses = self._get_courses_for_skill(skill)
            learning_plan.append({
                'skill': skill,
                'jobs_requiring': count,
                'percentage_of_jobs': round(count / len(jobs) * 100, 1),
                'recommended_courses': courses[:2]
            })
        
        return {
            'jobs_analyzed': len(jobs),
            'most_required_skills': top_required,
            'your_top_gaps': top_gaps,
            'learning_plan': learning_plan,
            'estimated_total_hours': sum(
                min(c['hours'] for c in item['recommended_courses']) 
                for item in learning_plan if item['recommended_courses']
            )
        }
    
    def track_learning_progress(self, skill: str, hours_completed: float, course_name: str = ""):
        """Track learning progress for a skill"""
        
        progress = self._load_learning_progress()
        
        if skill not in progress:
            progress[skill] = {
                'started_at': datetime.now().isoformat(),
                'total_hours': 0,
                'sessions': []
            }
        
        progress[skill]['total_hours'] += hours_completed
        progress[skill]['sessions'].append({
            'date': datetime.now().isoformat(),
            'hours': hours_completed,
            'course': course_name
        })
        progress[skill]['last_updated'] = datetime.now().isoformat()
        
        self._save_learning_progress(progress)
        
        return progress[skill]
    
    def _load_learning_progress(self) -> Dict:
        """Load learning progress"""
        if self.learning_progress_file.exists():
            try:
                with open(self.learning_progress_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_learning_progress(self, progress: Dict):
        """Save learning progress"""
        self.learning_progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.learning_progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_learning_dashboard(self) -> Dict:
        """Get learning progress dashboard"""
        
        progress = self._load_learning_progress()
        
        total_hours = sum(skill['total_hours'] for skill in progress.values())
        skills_in_progress = len(progress)
        
        # Recent activity
        recent_sessions = []
        for skill, data in progress.items():
            for session in data.get('sessions', [])[-5:]:
                session['skill'] = skill
                recent_sessions.append(session)
        
        recent_sessions.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'total_learning_hours': total_hours,
            'skills_in_progress': skills_in_progress,
            'skills': list(progress.keys()),
            'recent_activity': recent_sessions[:10],
            'streak_days': self._calculate_streak(progress)
        }
    
    def _calculate_streak(self, progress: Dict) -> int:
        """Calculate learning streak in days"""
        
        all_dates = set()
        for skill_data in progress.values():
            for session in skill_data.get('sessions', []):
                date = session['date'][:10]
                all_dates.add(date)
        
        if not all_dates:
            return 0
        
        # Count consecutive days ending today
        streak = 0
        check_date = datetime.now().date()
        
        while check_date.isoformat() in all_dates:
            streak += 1
            check_date -= timedelta(days=1)
        
        return streak
    
    def print_gap_report(self, analysis: Dict):
        """Print formatted skill gap report"""
        
        print(f"\n{'='*60}")
        print(f"📊 SKILL GAP ANALYSIS: {analysis.get('job_title', 'Job')}")
        print(f"{'='*60}")
        
        print(f"\n📈 Match Score: {analysis['match_percentage']}%")
        print(f"📋 Status: {analysis['qualification_status']}")
        
        print(f"\n✅ MATCHING SKILLS ({len(analysis['matching_skills'])}):")
        if analysis['matching_skills']:
            print(f"   {', '.join(analysis['matching_skills'][:10])}")
        else:
            print("   None")
        
        print(f"\n❌ MISSING SKILLS ({len(analysis['missing_skills'])}):")
        for skill, priority in analysis['skill_gaps'][:10]:
            print(f"   • {skill} [{priority}]")
        
        print(f"\n📚 RECOMMENDED LEARNING PATH:")
        for rec in analysis['recommendations'][:5]:
            print(f"\n   🎯 {rec['skill'].upper()} [{rec['priority']}]:")
            for course in rec['courses'][:2]:
                print(f"      • {course['title']} ({course['provider']}) - {course['hours']}hrs")
                print(f"        {course['url']}")
        
        print(f"\n⏱️ ESTIMATED TIME TO QUALIFY:")
        print(f"   {analysis['estimated_hours_to_qualify']} hours")
        print(f"   (~{analysis['estimated_weeks']} weeks at 10 hrs/week)")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    analyzer = SkillsGapAnalyzer()
    
    print(f"\n📊 SKILLS GAP ANALYZER")
    print(f"{'='*50}")
    print(f"Your Skills: {', '.join(list(analyzer.my_skills)[:10])}")
    
    # Example job description
    sample_job = """
    We're looking for a Senior Data Analyst with:
    - 3+ years of experience with Python and SQL
    - Experience with Tableau or Power BI
    - Strong Excel skills
    - Knowledge of AWS or GCP
    - Machine Learning experience is a plus
    - Experience with Spark or Hadoop
    - Strong communication skills
    """
    
    analysis = analyzer.analyze_gap(sample_job, "Senior Data Analyst")
    analyzer.print_gap_report(analysis)
    
    # Show learning dashboard
    dashboard = analyzer.get_learning_dashboard()
    print(f"📚 LEARNING PROGRESS:")
    print(f"   Total Hours: {dashboard['total_learning_hours']}")
    print(f"   Skills in Progress: {dashboard['skills_in_progress']}")
    print(f"   Current Streak: {dashboard['streak_days']} days")


if __name__ == "__main__":
    main()
