#!/usr/bin/env python3
"""
📅 INTERVIEW SCHEDULER BOT
Automatically detect interview invitations and propose meeting times.

Features:
- Parses interview invitation emails
- Extracts proposed times
- Checks calendar availability
- Suggests optimal meeting times
- Generates professional responses
- Handles timezone conversions
- Integrates with Google Calendar
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.free_ai_providers import FreeAIManager
except ImportError:
    FreeAIManager = None


class InterviewScheduler:
    """Detect and respond to interview invitations"""
    
    # Common interview invitation patterns
    INTERVIEW_PATTERNS = [
        r'schedule.*interview',
        r'interview.*schedule',
        r'would you be available',
        r'can we set up a call',
        r'like to invite you',
        r'next.*round.*interview',
        r'phone screen',
        r'technical interview',
        r'onsite interview',
        r'video call',
        r'zoom meeting',
        r'teams call',
        r'please.*confirm.*availability',
        r'book.*slot',
        r'calendly',
    ]
    
    # Time extraction patterns
    TIME_PATTERNS = [
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        r'(\d{1,2}:\d{2})',
        r'(morning|afternoon|evening)',
        r'(\d{1,2}(?:st|nd|rd|th)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)',
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
        r'(next\s+week)',
        r'(tomorrow)',
    ]
    
    def __init__(self):
        self.calendar_file = Path("data/my_calendar.json")
        self.interviews_file = Path("data/scheduled_interviews.json")
        self.calendar = self._load_calendar()
        self.interviews = self._load_interviews()
        self.ai = FreeAIManager() if FreeAIManager else None
        
        # User preferences
        self.timezone = os.getenv('TIMEZONE', 'Asia/Kolkata')
        self.preferred_times = os.getenv('PREFERRED_INTERVIEW_TIMES', '10:00-12:00,14:00-17:00')
        self.notice_period = int(os.getenv('MIN_INTERVIEW_NOTICE_HOURS', '24'))
        
    def _load_calendar(self) -> Dict:
        """Load calendar (blocked times)"""
        if self.calendar_file.exists():
            try:
                with open(self.calendar_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'blocked_times': [], 'working_hours': {'start': '09:00', 'end': '18:00'}}
    
    def _save_calendar(self):
        """Save calendar"""
        self.calendar_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.calendar_file, 'w') as f:
            json.dump(self.calendar, f, indent=2)
    
    def _load_interviews(self) -> Dict:
        """Load scheduled interviews"""
        if self.interviews_file.exists():
            try:
                with open(self.interviews_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'interviews': []}
    
    def _save_interviews(self):
        """Save scheduled interviews"""
        self.interviews_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.interviews_file, 'w') as f:
            json.dump(self.interviews, f, indent=2)
    
    def is_interview_invitation(self, email_content: str) -> bool:
        """Check if email is an interview invitation"""
        
        email_lower = email_content.lower()
        
        # Check patterns
        for pattern in self.INTERVIEW_PATTERNS:
            if re.search(pattern, email_lower):
                return True
        
        # Use AI for better detection
        if self.ai:
            prompt = f"""
            Is this email an interview invitation or scheduling request?
            Answer only "YES" or "NO".
            
            Email:
            {email_content[:1000]}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=10)
                if response and 'yes' in response.lower():
                    return True
            except:
                pass
        
        return False
    
    def extract_interview_details(self, email_content: str, subject: str = "") -> Dict:
        """Extract interview details from email"""
        
        details = {
            'type': 'unknown',
            'company': '',
            'role': '',
            'proposed_times': [],
            'duration': 60,
            'format': 'video',
            'interviewer': '',
            'meeting_link': ''
        }
        
        # Extract meeting links
        zoom_match = re.search(r'(https://[^\s]*zoom\.us/[^\s]+)', email_content)
        teams_match = re.search(r'(https://teams\.microsoft\.com/[^\s]+)', email_content)
        meet_match = re.search(r'(https://meet\.google\.com/[^\s]+)', email_content)
        calendly_match = re.search(r'(https://calendly\.com/[^\s]+)', email_content)
        
        if zoom_match:
            details['meeting_link'] = zoom_match.group(1)
            details['format'] = 'Zoom'
        elif teams_match:
            details['meeting_link'] = teams_match.group(1)
            details['format'] = 'Microsoft Teams'
        elif meet_match:
            details['meeting_link'] = meet_match.group(1)
            details['format'] = 'Google Meet'
        elif calendly_match:
            details['meeting_link'] = calendly_match.group(1)
            details['format'] = 'Calendly'
        
        # Extract times mentioned
        for pattern in self.TIME_PATTERNS:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            details['proposed_times'].extend(matches)
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(?:min|minute|hour)', email_content.lower())
        if duration_match:
            duration = int(duration_match.group(1))
            if 'hour' in email_content.lower():
                duration *= 60
            details['duration'] = duration
        
        # Use AI for deeper extraction
        if self.ai:
            prompt = f"""
            Extract interview details from this email:
            
            Subject: {subject}
            Content: {email_content[:1500]}
            
            Return JSON:
            {{
                "interview_type": "phone screen / technical / behavioral / onsite",
                "company": "company name",
                "role": "job title",
                "interviewer_name": "name if mentioned",
                "proposed_dates": ["date1", "date2"],
                "proposed_times": ["time1", "time2"],
                "duration_minutes": 60,
                "preparation_notes": "any tips mentioned"
            }}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=400)
                if response:
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        ai_details = json.loads(json_match.group())
                        details.update({
                            'type': ai_details.get('interview_type', details['type']),
                            'company': ai_details.get('company', details['company']),
                            'role': ai_details.get('role', details['role']),
                            'interviewer': ai_details.get('interviewer_name', details['interviewer']),
                            'duration': ai_details.get('duration_minutes', details['duration']),
                            'prep_notes': ai_details.get('preparation_notes', '')
                        })
                        
                        # Add AI-extracted times
                        details['proposed_times'].extend(ai_details.get('proposed_dates', []))
                        details['proposed_times'].extend(ai_details.get('proposed_times', []))
            except:
                pass
        
        # Clean up proposed times
        details['proposed_times'] = list(set(details['proposed_times']))
        
        return details
    
    def get_available_slots(self, days_ahead: int = 7, slots_per_day: int = 3) -> List[Dict]:
        """Get available interview slots"""
        
        available = []
        now = datetime.now()
        
        # Parse preferred times
        preferred_ranges = []
        for time_range in self.preferred_times.split(','):
            if '-' in time_range:
                start, end = time_range.strip().split('-')
                preferred_ranges.append((start.strip(), end.strip()))
        
        # Generate slots for next N days
        for day_offset in range(1, days_ahead + 1):
            date = now + timedelta(days=day_offset)
            
            # Skip weekends
            if date.weekday() >= 5:
                continue
            
            date_str = date.strftime('%Y-%m-%d')
            
            # Generate slots within preferred times
            for start_time, end_time in preferred_ranges:
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                
                current_hour = start_hour
                while current_hour < end_hour:
                    slot_start = f"{current_hour:02d}:00"
                    slot_end = f"{current_hour + 1:02d}:00"
                    
                    # Check if slot is blocked
                    slot_datetime = f"{date_str}T{slot_start}"
                    if not self._is_time_blocked(slot_datetime):
                        available.append({
                            'date': date_str,
                            'day': date.strftime('%A'),
                            'start': slot_start,
                            'end': slot_end,
                            'datetime': slot_datetime
                        })
                    
                    current_hour += 1
            
            # Limit slots per day
            day_slots = [s for s in available if s['date'] == date_str]
            if len(day_slots) > slots_per_day:
                # Keep evenly distributed slots
                available = [s for s in available if s['date'] != date_str]
                step = len(day_slots) // slots_per_day
                available.extend(day_slots[::step][:slots_per_day])
        
        return available[:15]  # Max 15 slots
    
    def _is_time_blocked(self, datetime_str: str) -> bool:
        """Check if a time slot is blocked"""
        
        for blocked in self.calendar.get('blocked_times', []):
            if blocked.get('datetime') == datetime_str:
                return True
            # Could add more sophisticated overlap checking
        
        return False
    
    def block_time(self, datetime_str: str, duration: int = 60, reason: str = ""):
        """Block a time slot in calendar"""
        
        self.calendar['blocked_times'].append({
            'datetime': datetime_str,
            'duration': duration,
            'reason': reason,
            'created_at': datetime.now().isoformat()
        })
        self._save_calendar()
    
    def generate_availability_response(self, details: Dict, custom_message: str = "") -> str:
        """Generate response with availability"""
        
        slots = self.get_available_slots()
        
        name = os.getenv('APPLICANT_NAME', '')
        
        if self.ai:
            slots_text = "\n".join([f"- {s['day']}, {s['date']} at {s['start']}" for s in slots[:6]])
            
            prompt = f"""
            Write a professional email response to an interview invitation.
            
            Context:
            - My name: {name}
            - Interview type: {details.get('type', 'interview')}
            - Company: {details.get('company', 'the company')}
            - Role: {details.get('role', 'the position')}
            - Custom note: {custom_message}
            
            My available times:
            {slots_text}
            
            Requirements:
            - Express enthusiasm
            - Confirm availability (list 3-4 time options)
            - Ask to confirm timezone if international
            - Professional but warm tone
            - Keep under 150 words
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=300)
                if response:
                    return response.strip()
            except:
                pass
        
        # Fallback template
        slots_text = "\n".join([f"  • {s['day']}, {s['date']} at {s['start']}" for s in slots[:4]])
        
        return f"""Dear Hiring Team,

Thank you for considering me for the {details.get('role', 'position')} at {details.get('company', 'your company')}. I'm excited about the opportunity and would be happy to schedule an interview.

I'm available at the following times ({self.timezone}):
{slots_text}

Please let me know which time works best for you, or feel free to suggest an alternative.

Looking forward to speaking with you!

Best regards,
{name}"""
    
    def schedule_interview(self, company: str, role: str, datetime_str: str, 
                          interview_type: str = "Interview", details: Dict = None) -> Dict:
        """Schedule an interview"""
        
        interview = {
            'id': len(self.interviews['interviews']) + 1,
            'company': company,
            'role': role,
            'datetime': datetime_str,
            'type': interview_type,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.interviews['interviews'].append(interview)
        self._save_interviews()
        
        # Block calendar
        self.block_time(datetime_str, 60, f"{interview_type} - {company}")
        
        print(f"✅ Interview scheduled: {company} on {datetime_str}")
        
        return interview
    
    def get_upcoming_interviews(self, days: int = 7) -> List[Dict]:
        """Get upcoming interviews"""
        
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = []
        for interview in self.interviews['interviews']:
            try:
                interview_dt = datetime.fromisoformat(interview['datetime'])
                if now <= interview_dt <= cutoff and interview['status'] == 'scheduled':
                    interview['days_until'] = (interview_dt - now).days
                    upcoming.append(interview)
            except:
                pass
        
        upcoming.sort(key=lambda x: x['datetime'])
        return upcoming
    
    def generate_preparation_plan(self, interview: Dict) -> Dict:
        """Generate interview preparation plan"""
        
        company = interview.get('company', '')
        role = interview.get('role', '')
        interview_type = interview.get('type', 'Interview')
        
        prep = {
            'interview': interview,
            'company_research': [],
            'technical_prep': [],
            'behavioral_prep': [],
            'questions_to_ask': [],
            'logistics': []
        }
        
        if self.ai:
            prompt = f"""
            Create an interview preparation plan for:
            - Company: {company}
            - Role: {role}
            - Interview Type: {interview_type}
            
            Return JSON:
            {{
                "company_research": ["point1", "point2", "point3"],
                "technical_topics": ["topic1", "topic2"],
                "behavioral_questions": ["question1", "question2"],
                "questions_to_ask": ["question1", "question2"],
                "day_before_checklist": ["item1", "item2"],
                "common_mistakes": ["mistake1", "mistake2"]
            }}
            """
            
            try:
                response = self.ai.generate(prompt, max_tokens=500)
                if response:
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        ai_prep = json.loads(json_match.group())
                        prep.update(ai_prep)
            except:
                pass
        
        # Add logistics checklist
        prep['logistics'] = [
            "Test video/audio setup",
            "Prepare quiet environment",
            "Have resume ready",
            "Research interviewer on LinkedIn",
            "Prepare 2-minute introduction",
            "Have water nearby",
            "Join 5 minutes early"
        ]
        
        return prep
    
    def print_upcoming_schedule(self):
        """Print upcoming interview schedule"""
        
        upcoming = self.get_upcoming_interviews()
        
        print(f"\n{'='*60}")
        print(f"📅 UPCOMING INTERVIEWS")
        print(f"{'='*60}")
        
        if not upcoming:
            print("\n   No interviews scheduled")
            return
        
        for interview in upcoming:
            days = interview.get('days_until', 0)
            urgency = "🔴" if days == 0 else "🟡" if days <= 2 else "🟢"
            
            print(f"\n{urgency} {interview['company']} - {interview['role']}")
            print(f"   📅 {interview['datetime']}")
            print(f"   📋 Type: {interview['type']}")
            print(f"   ⏰ In {days} days")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    scheduler = InterviewScheduler()
    
    print(f"\n📅 INTERVIEW SCHEDULER BOT")
    print(f"{'='*50}")
    
    # Show available slots
    slots = scheduler.get_available_slots()
    print(f"\n📆 Available Interview Slots:")
    for slot in slots[:6]:
        print(f"   • {slot['day']}, {slot['date']} at {slot['start']}")
    
    # Show upcoming interviews
    scheduler.print_upcoming_schedule()
    
    # Test email detection
    test_email = """
    Hi,
    
    Thank you for your interest in the Software Engineer position.
    We would like to schedule a technical interview with you.
    
    Would you be available next Tuesday or Wednesday afternoon?
    The interview will be approximately 45 minutes via Zoom.
    
    Please let me know your availability.
    
    Best,
    HR Team
    """
    
    if scheduler.is_interview_invitation(test_email):
        print(f"\n✅ Detected as interview invitation!")
        details = scheduler.extract_interview_details(test_email)
        print(f"   Type: {details.get('type')}")
        print(f"   Duration: {details.get('duration')} minutes")
        print(f"   Proposed times: {details.get('proposed_times')}")
        
        response = scheduler.generate_availability_response(details)
        print(f"\n📧 Generated Response:\n{response}")


if __name__ == "__main__":
    main()
