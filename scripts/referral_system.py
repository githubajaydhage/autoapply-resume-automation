"""
Referral Request System
Generate and send referral request emails to employees at target companies.
"""

import os
import re
import time
import random
import logging
import smtplib
import ssl
import pandas as pd
from datetime import datetime
from string import Template
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ReferralRequestSystem:
    """Generate and send referral request emails."""
    
    # Common company email patterns
    EMAIL_PATTERNS = {
        'google': '{first}.{last}@google.com',
        'microsoft': '{first}.{last}@microsoft.com',
        'amazon': '{first}{last}@amazon.com',
        'meta': '{first}.{last}@fb.com',
        'apple': '{first}_{last}@apple.com',
        'netflix': '{first}.{last}@netflix.com',
        'salesforce': '{first}.{last}@salesforce.com',
        'adobe': '{first}{last}@adobe.com',
        'linkedin': '{first}{last}@linkedin.com',
        'uber': '{first}.{last}@uber.com',
        'twitter': '{first}{last}@twitter.com',
        'stripe': '{first}@stripe.com',
        'airbnb': '{first}.{last}@airbnb.com',
        'spotify': '{first}.{last}@spotify.com',
        'nvidia': '{first}{last}@nvidia.com',
        'intel': '{first}.{last}@intel.com',
        'ibm': '{first}.{last}@ibm.com',
        'oracle': '{first}.{last}@oracle.com',
        'cisco': '{first}{last}@cisco.com',
        'vmware': '{first}.{last}@vmware.com',
        # Indian companies
        'infosys': '{first}.{last}@infosys.com',
        'tcs': '{first}.{last}@tcs.com',
        'wipro': '{first}.{last}@wipro.com',
        'hcl': '{first}.{last}@hcl.com',
        'techm': '{first}.{last}@techmahindra.com',
        'flipkart': '{first}.{last}@flipkart.com',
        'paytm': '{first}.{last}@paytm.com',
        'zomato': '{first}.{last}@zomato.com',
        'swiggy': '{first}@swiggy.in',
        'razorpay': '{first}.{last}@razorpay.com',
        'zerodha': '{first}@zerodha.com',
        'phonepe': '{first}.{last}@phonepe.com',
        'cred': '{first}@cred.club',
        'myntra': '{first}.{last}@myntra.com',
        'ola': '{first}.{last}@olacabs.com',
        'byju': '{first}.{last}@byjus.com',
        'freshworks': '{first}.{last}@freshworks.com',
        'zoho': '{first}@zohocorp.com',
        'default': '{first}.{last}@{company}.com'
    }
    
    # Referral request templates
    TEMPLATES = {
        'connection': """Hi ${employee_name},

I hope this message finds you well! I came across your profile while researching ${company} and noticed your impressive work as a ${employee_role}.

I'm ${my_name}, a ${my_role} with ${my_experience} of experience. I recently applied for the ${job_title} position at ${company} and was wondering if you might be open to a brief chat about your experience there.

I'm particularly interested in:
• The team culture and work environment
• Growth opportunities for someone in this role
• Any advice for standing out as a candidate

I completely understand if you're busy, but even a 15-minute call would be incredibly helpful. I'm also happy to share my resume if you'd be willing to refer me for the position.

Thank you for considering this, and I look forward to connecting!

Best regards,
${my_name}
${my_phone}
${my_linkedin}""",

        'direct_referral': """Hi ${employee_name},

I hope you're doing well! I'm reaching out because I'm very interested in the ${job_title} position at ${company}.

My name is ${my_name}, and I'm a ${my_role} with ${my_experience} of experience in ${my_skills}. I believe my background would be a great fit for this role.

I noticed you work at ${company} and wanted to ask if you might be willing to refer me for this position. I know referral bonuses are often offered, so this could potentially be a win-win!

Here's a quick summary of why I'd be a strong candidate:
${qualifications}

I've attached my resume for your reference. If you're open to it, I'd be happy to schedule a quick call to discuss my qualifications.

Thank you for your time and consideration. Even if you're unable to help, I appreciate you reading this.

Best regards,
${my_name}
${my_phone}
${my_linkedin}""",

        'alumni': """Hi ${employee_name},

I hope this message finds you well! I'm reaching out as a fellow ${alumni_connection}.

I'm ${my_name}, and I'm currently exploring opportunities in ${my_field}. I noticed you've built an impressive career at ${company}, and I'd love to learn from your experience.

I recently came across the ${job_title} position and I believe it would be a great fit for my background. I have ${my_experience} of experience in ${my_skills}.

Would you be open to a brief chat? I'd really appreciate any insights you could share about the company culture, interview process, or the team.

If you're comfortable, I would also be grateful if you could consider referring me for the position.

Thank you for your time!

Best,
${my_name}
${my_phone}
${my_linkedin}""",

        'short': """Hi ${employee_name},

I'm ${my_name}, applying for the ${job_title} role at ${company}. 

Quick ask: Would you consider referring me? I have ${my_experience} in ${my_skills} and I'm confident I'd be a great fit.

Happy to share my resume or chat briefly if helpful.

Thanks!
${my_name}
${my_phone}"""
    }
    
    def __init__(self):
        """Initialize the referral request system."""
        self.my_name = os.getenv('APPLICANT_NAME', 'Your Name')
        self.my_email = os.getenv('SENDER_EMAIL', '')
        self.my_phone = os.getenv('APPLICANT_PHONE', '')
        self.my_linkedin = os.getenv('APPLICANT_LINKEDIN', '')
        self.my_role = os.getenv('APPLICANT_ROLE', 'Software Engineer')
        self.my_experience = os.getenv('YEARS_EXPERIENCE', '3+') + ' years'
        self.my_skills = os.getenv('APPLICANT_SKILLS', 'software development')
        
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Output directory
        self.output_dir = 'data'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Log file
        self.log_file = os.path.join(self.output_dir, 'referral_requests_log.csv')
        
        logging.info(f"🤝 Referral Request System initialized for {self.my_name}")
    
    def guess_email(self, first_name: str, last_name: str, company: str) -> List[str]:
        """Generate possible email addresses for an employee."""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
        
        # Get company-specific pattern
        pattern = self.EMAIL_PATTERNS.get(company_clean)
        
        emails = []
        
        if pattern:
            email = pattern.format(first=first, last=last, company=company_clean)
            emails.append(email)
        
        # Generate common variations
        variations = [
            f"{first}.{last}@{company_clean}.com",
            f"{first}{last}@{company_clean}.com",
            f"{first}_{last}@{company_clean}.com",
            f"{first[0]}{last}@{company_clean}.com",
            f"{first}@{company_clean}.com",
            f"{first}.{last[0]}@{company_clean}.com",
        ]
        
        for v in variations:
            if v not in emails:
                emails.append(v)
        
        return emails[:3]  # Return top 3 guesses
    
    def generate_qualifications_list(self) -> str:
        """Generate qualifications bullet list."""
        qualifications = [
            f"• {self.my_experience} of hands-on experience",
            f"• Strong skills in {self.my_skills}",
            "• Track record of delivering quality work on time",
            "• Excellent communication and teamwork abilities"
        ]
        return '\n'.join(qualifications)
    
    def generate_referral_request(self,
                                   employee_name: str,
                                   employee_role: str,
                                   company: str,
                                   job_title: str,
                                   template_type: str = 'connection',
                                   alumni_connection: str = None) -> str:
        """Generate a personalized referral request email."""
        
        template = Template(self.TEMPLATES.get(template_type, self.TEMPLATES['connection']))
        
        return template.substitute(
            employee_name=employee_name.split()[0],  # First name only
            employee_role=employee_role,
            company=company,
            job_title=job_title,
            my_name=self.my_name,
            my_role=self.my_role,
            my_experience=self.my_experience,
            my_skills=self.my_skills,
            my_phone=self.my_phone,
            my_linkedin=f"LinkedIn: {self.my_linkedin}" if self.my_linkedin else "",
            qualifications=self.generate_qualifications_list(),
            alumni_connection=alumni_connection or "our network",
            my_field=self.my_skills
        )
    
    def generate_subject(self, job_title: str, company: str, template_type: str) -> str:
        """Generate email subject line."""
        subjects = {
            'connection': [
                f"Quick question about {company}",
                f"Coffee chat request - {company}",
                f"Seeking advice about {job_title} at {company}",
            ],
            'direct_referral': [
                f"Referral request for {job_title} position",
                f"Would you consider referring me? - {job_title}",
                f"Seeking referral: {job_title} at {company}",
            ],
            'alumni': [
                f"Fellow alumni reaching out - {company}",
                f"Connection request from a fellow graduate",
                f"Alumni networking - {job_title} opportunity",
            ],
            'short': [
                f"Quick referral request - {job_title}",
                f"Referral for {job_title}?",
            ]
        }
        
        options = subjects.get(template_type, subjects['connection'])
        return random.choice(options)
    
    def send_referral_request(self,
                               recipient_email: str,
                               employee_name: str,
                               employee_role: str,
                               company: str,
                               job_title: str,
                               template_type: str = 'connection') -> bool:
        """Send a referral request email."""
        
        if not self.sender_password:
            logging.error("❌ SENDER_PASSWORD not set")
            return False
        
        try:
            subject = self.generate_subject(job_title, company, template_type)
            body = self.generate_referral_request(
                employee_name=employee_name,
                employee_role=employee_role,
                company=company,
                job_title=job_title,
                template_type=template_type
            )
            
            message = MIMEMultipart()
            message['From'] = f"{self.my_name} <{self.my_email}>"
            message['To'] = recipient_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.my_email, self.sender_password)
                server.sendmail(self.my_email, recipient_email, message.as_string())
            
            logging.info(f"✅ Referral request sent to {employee_name} at {company}")
            self._log_request(recipient_email, employee_name, company, job_title, 'sent')
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send to {recipient_email}: {e}")
            self._log_request(recipient_email, employee_name, company, job_title, f'failed: {e}')
            return False
    
    def _log_request(self, email: str, name: str, company: str, job_title: str, status: str):
        """Log referral request to CSV."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'recipient_email': email,
            'employee_name': name,
            'company': company,
            'job_title': job_title,
            'status': status
        }
        
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])
        
        df.to_csv(self.log_file, index=False)
    
    def find_employees_to_contact(self, company: str, job_title: str = None) -> List[Dict]:
        """
        Find potential employees to contact at a company.
        In a real implementation, this would use LinkedIn API or web scraping.
        For now, returns placeholder data that user should fill in.
        """
        logging.info(f"🔍 Finding employees at {company}...")
        
        # Placeholder - in production, use LinkedIn Sales Navigator or similar
        # Return format for manual entry
        template = {
            'company': company,
            'job_title': job_title,
            'employees': [
                {
                    'name': 'Employee Name',
                    'role': 'Software Engineer / HR',
                    'email': 'to be determined',
                    'linkedin': 'linkedin.com/in/profile'
                }
            ],
            'email_pattern': self.EMAIL_PATTERNS.get(
                re.sub(r'[^a-z0-9]', '', company.lower()),
                self.EMAIL_PATTERNS['default']
            )
        }
        
        return template
    
    def process_employee_list(self, employee_file: str) -> Dict:
        """Process a CSV file with employee contacts and send referral requests."""
        
        if not os.path.exists(employee_file):
            logging.error(f"❌ File not found: {employee_file}")
            return {'sent': 0, 'failed': 0}
        
        df = pd.read_csv(employee_file)
        required_cols = ['name', 'email', 'company', 'job_title']
        
        if not all(col in df.columns for col in required_cols):
            logging.error(f"❌ Missing columns. Required: {required_cols}")
            return {'sent': 0, 'failed': 0}
        
        stats = {'sent': 0, 'failed': 0}
        
        for idx, row in df.iterrows():
            success = self.send_referral_request(
                recipient_email=row['email'],
                employee_name=row['name'],
                employee_role=row.get('role', 'Employee'),
                company=row['company'],
                job_title=row['job_title'],
                template_type=row.get('template', 'connection')
            )
            
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            
            # Delay between emails
            if idx < len(df) - 1:
                delay = random.uniform(120, 180)  # 2-3 minutes
                logging.info(f"⏳ Waiting {delay:.0f}s...")
                time.sleep(delay)
        
        return stats


def create_employee_template(output_file: str = 'data/referral_contacts.csv'):
    """Create a template CSV for entering employee contacts."""
    template_data = [
        {
            'name': 'John Smith',
            'email': 'john.smith@company.com',
            'role': 'Senior Software Engineer',
            'company': 'TechCorp',
            'job_title': 'Python Developer',
            'template': 'connection',
            'notes': 'Found on LinkedIn - same college'
        }
    ]
    
    df = pd.DataFrame(template_data)
    df.to_csv(output_file, index=False)
    
    logging.info(f"📝 Template created: {output_file}")
    logging.info("Fill in employee details and run the system to send referral requests.")
    
    return output_file


def main():
    """Main function for referral request system."""
    logging.info("="*60)
    logging.info("🤝 REFERRAL REQUEST SYSTEM")
    logging.info("="*60)
    
    system = ReferralRequestSystem()
    
    # Check for employee contacts file
    contacts_file = 'data/referral_contacts.csv'
    
    if os.path.exists(contacts_file):
        logging.info(f"📂 Found contacts file: {contacts_file}")
        stats = system.process_employee_list(contacts_file)
        
        logging.info(f"\n📊 Summary:")
        logging.info(f"   ✅ Sent: {stats['sent']}")
        logging.info(f"   ❌ Failed: {stats['failed']}")
    else:
        logging.info("📝 No contacts file found. Creating template...")
        create_employee_template(contacts_file)
        
        # Demo - generate sample referral request
        logging.info("\n📧 Sample Referral Request:")
        logging.info("="*40)
        
        sample = system.generate_referral_request(
            employee_name="John Smith",
            employee_role="Senior Software Engineer",
            company="Google",
            job_title="Python Developer",
            template_type="connection"
        )
        print(sample)
        
        logging.info("\n💡 How to use:")
        logging.info("1. Edit data/referral_contacts.csv with employee details")
        logging.info("2. Find employees on LinkedIn who work at your target companies")
        logging.info("3. Use email pattern to guess their work email")
        logging.info("4. Run this script again to send referral requests")
    
    logging.info("="*60)
    logging.info("✅ Referral system complete!")
    logging.info("="*60)


if __name__ == "__main__":
    main()
