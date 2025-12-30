"""
Cover Letter Generator
Generates personalized cover letters based on job descriptions and resume.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from string import Template
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CoverLetterGenerator:
    """Generate personalized cover letters for job applications."""
    
    # Cover letter templates for different scenarios
    TEMPLATES = {
        'standard': """Dear ${hiring_manager},

I am writing to express my strong interest in the ${job_title} position at ${company}. With my background in ${primary_skill} and experience in ${secondary_skills}, I am confident I would be a valuable addition to your team.

${experience_paragraph}

${skills_paragraph}

${company_paragraph}

I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to ${company}'s continued success. Thank you for considering my application.

Sincerely,
${name}
${phone}
${email}""",

        'career_change': """Dear ${hiring_manager},

I am excited to apply for the ${job_title} position at ${company}. While my background may be unconventional for this role, my transferable skills in ${primary_skill} combined with my genuine passion for ${industry} make me a strong candidate.

${experience_paragraph}

${skills_paragraph}

${company_paragraph}

I am eager to bring my unique perspective and dedicated work ethic to ${company}. I look forward to the opportunity to discuss how my diverse experience can benefit your team.

Best regards,
${name}
${phone}
${email}""",

        'entry_level': """Dear ${hiring_manager},

I am thrilled to apply for the ${job_title} opportunity at ${company}. As a motivated professional with foundational skills in ${primary_skill} and ${secondary_skills}, I am eager to contribute to your team and grow with your organization.

${experience_paragraph}

${skills_paragraph}

${company_paragraph}

I am ready to bring my enthusiasm, fresh perspective, and commitment to excellence to ${company}. Thank you for considering my application.

Warmly,
${name}
${phone}
${email}""",

        'senior': """Dear ${hiring_manager},

I am writing to express my interest in the ${job_title} position at ${company}. With ${years_experience} years of experience in ${primary_skill} and a proven track record of ${key_achievement}, I am well-positioned to make an immediate impact on your team.

${experience_paragraph}

${skills_paragraph}

${company_paragraph}

I would appreciate the opportunity to discuss how my expertise and leadership can help ${company} achieve its objectives. Thank you for your time and consideration.

Best regards,
${name}
${phone}
${email}"""
    }
    
    # Experience paragraphs based on skills
    EXPERIENCE_PARAGRAPHS = {
        'python': "In my previous roles, I have developed robust Python applications, automated workflows, and built data pipelines that improved operational efficiency. My experience includes working with Django, Flask, pandas, and various cloud technologies.",
        
        'data': "I bring extensive experience in data analysis, visualization, and machine learning. I have worked with large datasets, built predictive models, and created dashboards that drove data-informed decision making.",
        
        'frontend': "My frontend development experience includes building responsive, user-friendly interfaces using modern frameworks. I am proficient in React, Vue.js, and have a strong foundation in HTML, CSS, and JavaScript.",
        
        'backend': "I have designed and implemented scalable backend systems, RESTful APIs, and microservices architectures. My experience spans database design, server optimization, and cloud deployment.",
        
        'fullstack': "As a full-stack developer, I have end-to-end experience building web applications from database design to user interface. I am comfortable working across the entire technology stack.",
        
        'devops': "My DevOps experience includes implementing CI/CD pipelines, containerization with Docker and Kubernetes, and managing cloud infrastructure on AWS, Azure, or GCP.",
        
        'qa': "I have comprehensive experience in quality assurance, including test automation, performance testing, and implementing testing frameworks that ensure product reliability.",
        
        # Interior Design & Architecture Experience Paragraphs
        'interior_design': "In my previous roles, I have successfully designed and executed residential and commercial interior projects. My experience includes space planning, material selection, 3D visualization, and client presentations using AutoCAD, SketchUp, and 3ds Max.",
        
        'architecture': "I bring comprehensive experience in architectural design, from concept development to construction documentation. My portfolio includes residential, commercial, and mixed-use projects designed with attention to sustainability and building codes.",
        
        'estimation': "My experience includes preparing detailed quantity surveys, cost estimations, and billing analysis for construction projects. I excel at BOQ preparation, rate analysis, and ensuring projects stay within budget.",
        
        'autocad': "I am proficient in AutoCAD, creating precise 2D drawings and technical documentation. My experience includes floor plans, elevation drawings, section details, and construction documents.",
        
        'furniture': "I have extensive experience in furniture design and modular solutions. My work includes custom furniture conceptualization, production drawings, and vendor coordination for residential and commercial projects.",
        
        'project_management': "I have managed multiple interior and construction projects from inception to completion. My experience includes vendor management, site supervision, timeline coordination, and quality control.",
        
        'default': "Throughout my career, I have demonstrated strong problem-solving abilities, attention to detail, and a commitment to delivering high-quality work. I adapt quickly to new technologies and thrive in collaborative environments."
    }
    
    # Skills paragraphs
    SKILLS_PARAGRAPHS = {
        'technical': "My technical skills include ${skills_list}. I am committed to continuous learning and staying current with industry best practices and emerging technologies.",
        
        'soft': "Beyond technical abilities, I excel in communication, teamwork, and project management. I have successfully collaborated with cross-functional teams and stakeholders to deliver projects on time.",
        
        'leadership': "I have experience leading teams, mentoring junior developers, and driving technical decisions. I believe in fostering a collaborative environment where everyone can contribute their best work."
    }
    
    def __init__(self):
        """Initialize the cover letter generator."""
        self.applicant_name = os.getenv('APPLICANT_NAME', 'Your Name')
        self.applicant_email = os.getenv('SENDER_EMAIL', '')
        self.applicant_phone = os.getenv('APPLICANT_PHONE', '')
        self.applicant_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        self.years_experience = os.getenv('YEARS_EXPERIENCE', '3+')
        
        # Path for saving cover letters
        self.output_dir = 'cover_letters'
        os.makedirs(self.output_dir, exist_ok=True)
        
        logging.info(f"📝 Cover Letter Generator initialized for {self.applicant_name}")
    
    def detect_job_category(self, job_title: str, description: str = '') -> str:
        """Detect the job category based on title and description."""
        text = f"{job_title} {description}".lower()
        
        categories = {
            # Interior Design & Architecture categories (check first for priority)
            'interior_design': ['interior design', 'interior designer', 'space planning', 'home decor', 
                               'residential design', 'commercial interior', '3ds max', 'sketchup', 
                               'vray', 'modular kitchen', 'furniture design'],
            'architecture': ['architect', 'architectural', 'building design', 'revit', 'bim', 
                            'construction drawing', 'elevation'],
            'estimation': ['estimator', 'quantity surveyor', 'boq', 'billing engineer', 'cost estimation',
                          'rate analysis', 'material estimation', 'civil estimation'],
            'autocad': ['autocad', 'drafting', 'cad', 'draughtsman', 'draftsman', 'technical drawing'],
            'furniture': ['furniture', 'modular', 'woodwork', 'joinery', 'cabinetry'],
            'project_management': ['project manager', 'site engineer', 'construction manager', 
                                   'site supervisor', 'execution'],
            
            # IT/Tech categories
            'python': ['python', 'django', 'flask', 'pandas'],
            'data': ['data science', 'data analyst', 'machine learning', 'ml engineer', 'analytics'],
            'frontend': ['frontend', 'front-end', 'react', 'vue', 'angular', 'ui developer'],
            'backend': ['backend', 'back-end', 'api', 'microservices', 'server'],
            'fullstack': ['full stack', 'fullstack', 'full-stack'],
            'devops': ['devops', 'sre', 'platform engineer', 'infrastructure', 'cloud engineer'],
            'qa': ['qa', 'quality', 'test engineer', 'sdet', 'automation engineer']
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return 'default'
    
    def select_template(self, years_experience: str = None) -> str:
        """Select appropriate template based on experience level."""
        years = years_experience or self.years_experience
        
        try:
            years_num = int(years.replace('+', ''))
        except:
            years_num = 3
        
        if years_num <= 2:
            return 'entry_level'
        elif years_num >= 8:
            return 'senior'
        else:
            return 'standard'
    
    def extract_skills_from_job(self, job_title: str, description: str = '') -> Dict[str, str]:
        """Extract key skills from job posting."""
        text = f"{job_title} {description}".lower()
        
        # Detect job industry first
        job_keywords = os.getenv('JOB_KEYWORDS', '').lower()
        is_interior_design = any(kw in job_keywords for kw in ['interior', 'design', 'architect', 'autocad'])
        
        # Interior Design & Architecture skills
        design_skills = [
            'autocad', 'sketchup', '3ds max', 'vray', 'revit', 'photoshop', 'illustrator',
            'space planning', 'interior design', 'furniture design', 'color theory',
            'material selection', 'lighting design', 'project management', 'client presentation',
            'boq', 'estimation', 'site supervision', 'vendor management', 'costing',
            'modular design', 'kitchen design', 'residential design', 'commercial design',
            'elevation', 'working drawings', 'technical drawings', 'bim'
        ]
        
        # Common tech skills
        tech_skills = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'sql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'ci/cd',
            'machine learning', 'data analysis', 'agile', 'scrum', 'rest api'
        ]
        
        # Choose skills based on job type
        all_skills = design_skills if is_interior_design else tech_skills
        
        found_skills = [skill for skill in all_skills if skill in text]
        
        if not found_skills:
            # Default based on job type
            if is_interior_design:
                found_skills = ['AutoCAD', 'SketchUp', 'interior design', 'project management']
            elif 'python' in text:
                found_skills = ['python', 'sql', 'git']
            elif 'frontend' in text or 'react' in text:
                found_skills = ['react', 'javascript', 'css']
            else:
                found_skills = ['programming', 'problem-solving', 'teamwork']
        
        return {
            'primary': found_skills[0] if found_skills else 'interior design' if is_interior_design else 'software development',
            'secondary': ', '.join(found_skills[1:4]) if len(found_skills) > 1 else 'related skills',
            'all': ', '.join(found_skills[:6])
        }
    
    def generate_cover_letter(self, 
                               job_title: str, 
                               company: str,
                               description: str = '',
                               hiring_manager: str = 'Hiring Manager') -> str:
        """Generate a personalized cover letter."""
        
        # Detect job category and skills
        category = self.detect_job_category(job_title, description)
        skills = self.extract_skills_from_job(job_title, description)
        
        # Select template
        template_key = self.select_template()
        template = Template(self.TEMPLATES[template_key])
        
        # Get experience paragraph
        exp_paragraph = self.EXPERIENCE_PARAGRAPHS.get(category, self.EXPERIENCE_PARAGRAPHS['default'])
        
        # Generate skills paragraph
        skills_template = Template(self.SKILLS_PARAGRAPHS['technical'])
        skills_paragraph = skills_template.substitute(skills_list=skills['all'])
        
        # Company paragraph
        company_paragraph = f"I am particularly drawn to {company} because of its reputation for innovation and commitment to excellence. I am excited about the opportunity to contribute to your team's success."
        
        # Key achievement based on experience
        key_achievement = "delivering high-quality solutions and improving team productivity"
        
        # Generate the letter
        letter = template.substitute(
            hiring_manager=hiring_manager,
            job_title=job_title,
            company=company,
            primary_skill=skills['primary'],
            secondary_skills=skills['secondary'],
            experience_paragraph=exp_paragraph,
            skills_paragraph=skills_paragraph,
            company_paragraph=company_paragraph,
            name=self.applicant_name,
            phone=self.applicant_phone,
            email=self.applicant_email,
            years_experience=self.years_experience,
            key_achievement=key_achievement,
            industry=category
        )
        
        return letter
    
    def save_cover_letter(self, letter: str, job_title: str, company: str) -> str:
        """Save cover letter to file."""
        # Clean filename
        safe_company = "".join(c for c in company if c.isalnum() or c in ' -_').strip()[:30]
        safe_title = "".join(c for c in job_title if c.isalnum() or c in ' -_').strip()[:30]
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"cover_letter_{safe_company}_{safe_title}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(letter)
        
        logging.info(f"💾 Saved: {filepath}")
        return filepath
    
    def generate_from_jobs_csv(self, jobs_csv: str = 'data/jobs_today.csv', 
                                max_letters: int = 10) -> List[Dict]:
        """Generate cover letters for jobs from CSV."""
        
        if not os.path.exists(jobs_csv):
            logging.error(f"❌ Jobs file not found: {jobs_csv}")
            return []
        
        df = pd.read_csv(jobs_csv)
        logging.info(f"📊 Loaded {len(df)} jobs from {jobs_csv}")
        
        results = []
        
        for idx, row in df.head(max_letters).iterrows():
            job_title = row.get('title', row.get('job_title', 'Position'))
            company = row.get('company', 'Company')
            description = row.get('description', row.get('summary', ''))
            
            try:
                letter = self.generate_cover_letter(
                    job_title=job_title,
                    company=company,
                    description=description
                )
                
                filepath = self.save_cover_letter(letter, job_title, company)
                
                results.append({
                    'job_title': job_title,
                    'company': company,
                    'cover_letter_path': filepath,
                    'status': 'generated'
                })
                
                logging.info(f"✅ Generated cover letter for {job_title} at {company}")
                
            except Exception as e:
                logging.error(f"❌ Failed for {job_title} at {company}: {e}")
                results.append({
                    'job_title': job_title,
                    'company': company,
                    'cover_letter_path': None,
                    'status': f'failed: {e}'
                })
        
        # Save results log
        results_df = pd.DataFrame(results)
        results_path = os.path.join(self.output_dir, 'cover_letters_log.csv')
        results_df.to_csv(results_path, index=False)
        logging.info(f"📊 Log saved to {results_path}")
        
        return results


def main():
    """Main function to generate cover letters."""
    logging.info("="*60)
    logging.info("📝 COVER LETTER GENERATOR")
    logging.info("="*60)
    
    generator = CoverLetterGenerator()
    
    # Check for jobs file
    jobs_file = 'data/jobs_today.csv'
    if os.path.exists(jobs_file):
        logging.info(f"📂 Processing jobs from {jobs_file}")
        results = generator.generate_from_jobs_csv(jobs_file, max_letters=5)
        
        success = sum(1 for r in results if r['status'] == 'generated')
        logging.info(f"\n📊 Summary: {success}/{len(results)} cover letters generated")
    else:
        # Demo with sample job
        logging.info("📝 Demo mode - generating sample cover letter")
        
        letter = generator.generate_cover_letter(
            job_title="Python Developer",
            company="Tech Solutions Inc",
            description="Looking for Python developer with Django experience"
        )
        
        print("\n" + "="*60)
        print("SAMPLE COVER LETTER")
        print("="*60)
        print(letter)
    
    logging.info("="*60)
    logging.info("✅ Cover letter generation complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
