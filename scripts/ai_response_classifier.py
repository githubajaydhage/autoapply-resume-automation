"""
🤖 AI RESPONSE CLASSIFIER - Smart Email Reply Analysis

Uses AI to automatically classify HR responses:
1. INTERVIEW - Positive response requesting interview
2. REJECTION - Polite decline
3. MORE_INFO - Requesting more information
4. FOLLOW_UP - Generic response, follow-up needed
5. AUTO_REPLY - Automated response
6. SPAM - Irrelevant response

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ResponseType(Enum):
    """Email response types."""
    INTERVIEW = "interview"          # Interview request - HIGH PRIORITY
    OFFER = "offer"                  # Job offer - HIGHEST PRIORITY
    ASSESSMENT = "assessment"        # Technical test/assessment
    MORE_INFO = "more_info"          # Request for more info
    FOLLOW_UP_NEEDED = "follow_up"   # Needs follow-up
    REJECTION = "rejection"          # Polite decline
    AUTO_REPLY = "auto_reply"        # Automated response
    SPAM = "spam"                    # Irrelevant
    UNKNOWN = "unknown"              # Could not classify


class AIResponseClassifier:
    """
    🤖 AI-Powered Email Response Classifier
    
    Analyzes HR responses and classifies them for appropriate action.
    """
    
    # Keywords for classification
    INTERVIEW_KEYWORDS = [
        'interview', 'schedule', 'available', 'meet', 'discuss',
        'call', 'zoom', 'teams', 'google meet', 'availability',
        'convenient time', 'slot', 'round', 'technical interview',
        'hr round', 'panel', 'shortlisted', 'selected for'
    ]
    
    OFFER_KEYWORDS = [
        'offer letter', 'job offer', 'pleased to offer', 'congratulations',
        'offer of employment', 'start date', 'joining date', 'compensation',
        'salary package', 'welcome aboard', 'accepted', 'you are hired'
    ]
    
    ASSESSMENT_KEYWORDS = [
        'assessment', 'test', 'coding challenge', 'assignment',
        'hackerrank', 'codility', 'leetcode', 'take-home',
        'technical exercise', 'case study', 'project', 'submission'
    ]
    
    REJECTION_KEYWORDS = [
        'unfortunately', 'regret', 'not able to proceed', 'other candidates',
        'not shortlisted', 'position filled', 'decided to move forward',
        'not selected', 'do not match', 'wish you best', 'all the best',
        'keep your resume', 'future opportunities', 'not successful'
    ]
    
    MORE_INFO_KEYWORDS = [
        'could you provide', 'please send', 'need more information',
        'could you share', 'attach', 'resume format', 'portfolio',
        'references', 'salary expectations', 'notice period', 'ctc'
    ]
    
    AUTO_REPLY_KEYWORDS = [
        'automatic response', 'auto-reply', 'out of office',
        'currently unavailable', 'will respond', 'thank you for your email',
        'received your application', 'acknowledgment', 'do not reply'
    ]
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_path, 'data')
        
        # AI Configuration
        self.ai_backend = self._detect_ai_backend()
        
        # Classification history
        self.history_path = os.path.join(self.data_path, 'response_classifications.json')
        self.history = self._load_history()
        
        logging.info(f"🤖 AI Response Classifier initialized (backend: {self.ai_backend})")
    
    def _detect_ai_backend(self) -> str:
        """Detect available AI backend."""
        if os.getenv('OPENAI_API_KEY'):
            return 'openai'
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            return 'gemini'
        return 'keyword_analysis'
    
    def _load_history(self) -> List[Dict]:
        """Load classification history."""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_history(self):
        """Save classification history."""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(self.history[-1000:], f, indent=2)  # Keep last 1000
        except:
            pass
    
    def classify(
        self,
        email_subject: str,
        email_body: str,
        sender_email: str = ''
    ) -> Dict:
        """
        Classify an email response.
        
        Returns:
        {
            'type': ResponseType,
            'confidence': float,
            'action': str,
            'priority': int,  # 1-5, 1 is highest
            'key_phrases': List[str],
            'suggested_reply': str
        }
        """
        # Combine subject and body
        full_text = f"{email_subject} {email_body}".lower()
        
        # Try AI classification first
        if self.ai_backend != 'keyword_analysis':
            try:
                result = self._ai_classify(email_subject, email_body)
                if result and result.get('confidence', 0) > 0.7:
                    self._log_classification(email_subject, sender_email, result)
                    return result
            except Exception as e:
                logging.warning(f"AI classification failed: {e}")
        
        # Fallback to keyword analysis
        return self._keyword_classify(full_text, email_subject, sender_email)
    
    def _ai_classify(self, subject: str, body: str) -> Optional[Dict]:
        """Use AI to classify email."""
        prompt = f"""Classify this email response from an HR/recruiter.

SUBJECT: {subject}

BODY:
{body[:2000]}

Classify as ONE of:
- INTERVIEW: They want to schedule an interview
- OFFER: Job offer extended
- ASSESSMENT: Sending a test/assignment
- MORE_INFO: Requesting more information
- REJECTION: Declining the application
- AUTO_REPLY: Automated response
- FOLLOW_UP: Generic, needs follow-up
- UNKNOWN: Cannot determine

Return JSON:
{{
    "type": "INTERVIEW|OFFER|ASSESSMENT|MORE_INFO|REJECTION|AUTO_REPLY|FOLLOW_UP|UNKNOWN",
    "confidence": 0.0-1.0,
    "action": "What the applicant should do next",
    "priority": 1-5 (1=urgent, 5=low),
    "key_phrases": ["phrases that led to this classification"]
}}"""

        try:
            if self.ai_backend == 'openai':
                import openai
                client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                response = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300
                )
                result = response.choices[0].message.content
            elif self.ai_backend == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                result = response.text
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                data['type'] = ResponseType[data['type'].upper()]
                data['suggested_reply'] = self._generate_reply_suggestion(data['type'])
                return data
        except Exception as e:
            logging.warning(f"AI classification error: {e}")
        
        return None
    
    def _keyword_classify(
        self,
        full_text: str,
        subject: str,
        sender_email: str
    ) -> Dict:
        """Classify using keyword matching."""
        
        # Count matches for each category
        scores = {
            ResponseType.OFFER: self._count_matches(full_text, self.OFFER_KEYWORDS),
            ResponseType.INTERVIEW: self._count_matches(full_text, self.INTERVIEW_KEYWORDS),
            ResponseType.ASSESSMENT: self._count_matches(full_text, self.ASSESSMENT_KEYWORDS),
            ResponseType.MORE_INFO: self._count_matches(full_text, self.MORE_INFO_KEYWORDS),
            ResponseType.REJECTION: self._count_matches(full_text, self.REJECTION_KEYWORDS),
            ResponseType.AUTO_REPLY: self._count_matches(full_text, self.AUTO_REPLY_KEYWORDS),
        }
        
        # Get highest scoring type
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # If no significant matches, mark as follow-up needed
        if max_score < 2:
            max_type = ResponseType.FOLLOW_UP_NEEDED
            confidence = 0.5
        else:
            confidence = min(0.9, 0.5 + (max_score * 0.1))
        
        # Get key phrases that matched
        key_phrases = self._extract_key_phrases(full_text, max_type)
        
        result = {
            'type': max_type,
            'confidence': confidence,
            'action': self._get_action(max_type),
            'priority': self._get_priority(max_type),
            'key_phrases': key_phrases,
            'suggested_reply': self._generate_reply_suggestion(max_type)
        }
        
        self._log_classification(subject, sender_email, result)
        return result
    
    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """Count keyword matches."""
        count = 0
        for keyword in keywords:
            if keyword.lower() in text:
                count += 1
        return count
    
    def _extract_key_phrases(self, text: str, response_type: ResponseType) -> List[str]:
        """Extract key phrases that matched."""
        keywords_map = {
            ResponseType.INTERVIEW: self.INTERVIEW_KEYWORDS,
            ResponseType.OFFER: self.OFFER_KEYWORDS,
            ResponseType.ASSESSMENT: self.ASSESSMENT_KEYWORDS,
            ResponseType.REJECTION: self.REJECTION_KEYWORDS,
            ResponseType.MORE_INFO: self.MORE_INFO_KEYWORDS,
            ResponseType.AUTO_REPLY: self.AUTO_REPLY_KEYWORDS,
        }
        
        keywords = keywords_map.get(response_type, [])
        matched = [kw for kw in keywords if kw.lower() in text]
        return matched[:5]
    
    def _get_action(self, response_type: ResponseType) -> str:
        """Get recommended action."""
        actions = {
            ResponseType.OFFER: "🎉 Review offer and respond within 24-48 hours",
            ResponseType.INTERVIEW: "📅 Respond immediately with availability",
            ResponseType.ASSESSMENT: "💻 Complete assessment within deadline",
            ResponseType.MORE_INFO: "📝 Send requested information promptly",
            ResponseType.FOLLOW_UP_NEEDED: "📧 Send follow-up in 3-5 days",
            ResponseType.REJECTION: "🙏 Send thank you, request feedback",
            ResponseType.AUTO_REPLY: "⏳ Wait for human response",
            ResponseType.UNKNOWN: "🔍 Review manually",
        }
        return actions.get(response_type, "Review and respond appropriately")
    
    def _get_priority(self, response_type: ResponseType) -> int:
        """Get priority level (1=highest, 5=lowest)."""
        priorities = {
            ResponseType.OFFER: 1,
            ResponseType.INTERVIEW: 1,
            ResponseType.ASSESSMENT: 2,
            ResponseType.MORE_INFO: 2,
            ResponseType.FOLLOW_UP_NEEDED: 3,
            ResponseType.REJECTION: 4,
            ResponseType.AUTO_REPLY: 5,
            ResponseType.UNKNOWN: 3,
        }
        return priorities.get(response_type, 3)
    
    def _generate_reply_suggestion(self, response_type: ResponseType) -> str:
        """Generate suggested reply template."""
        templates = {
            ResponseType.INTERVIEW: """Thank you for considering my application. I am excited about this opportunity!

I am available at the following times:
- [Date 1]: [Time slots]
- [Date 2]: [Time slots]
- [Date 3]: [Time slots]

Please let me know what works best for you.

Best regards""",

            ResponseType.OFFER: """Thank you so much for extending this offer. I am thrilled about the opportunity to join [Company].

I would like to discuss a few details regarding the compensation package. Could we schedule a brief call to discuss?

I appreciate your time and look forward to speaking with you.

Best regards""",

            ResponseType.ASSESSMENT: """Thank you for sharing the assessment details.

I will complete and submit the assignment by [Deadline].

Please let me know if you need any clarification from my end.

Best regards""",

            ResponseType.MORE_INFO: """Thank you for your response.

Please find the requested information below:
[Provide the requested details]

Please let me know if you need anything else.

Best regards""",

            ResponseType.REJECTION: """Thank you for informing me of your decision.

While I am disappointed, I appreciate the opportunity to have been considered. I would be grateful for any feedback that could help me in future applications.

I remain interested in [Company] and would welcome the opportunity to be considered for future openings.

Best regards""",
        }
        return templates.get(response_type, "Thank you for your response. I will review and get back to you shortly.")
    
    def _log_classification(self, subject: str, sender: str, result: Dict):
        """Log classification for analytics."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject[:100],
            'sender': sender,
            'type': result['type'].value if isinstance(result['type'], ResponseType) else result['type'],
            'confidence': result.get('confidence', 0),
            'priority': result.get('priority', 3)
        }
        self.history.append(log_entry)
        self._save_history()
    
    def get_analytics(self) -> Dict:
        """Get classification analytics."""
        if not self.history:
            return {'message': 'No classifications yet'}
        
        type_counts = {}
        for entry in self.history:
            t = entry.get('type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total_classified': len(self.history),
            'by_type': type_counts,
            'interview_rate': type_counts.get('interview', 0) / len(self.history) * 100,
            'rejection_rate': type_counts.get('rejection', 0) / len(self.history) * 100
        }
    
    def classify_batch(self, emails: List[Dict]) -> List[Dict]:
        """
        Classify multiple emails.
        
        Input: [{'subject': str, 'body': str, 'sender': str}, ...]
        Returns: List of classification results
        """
        results = []
        
        for email in emails:
            classification = self.classify(
                email.get('subject', ''),
                email.get('body', ''),
                email.get('sender', '')
            )
            classification['email'] = email
            results.append(classification)
        
        # Sort by priority
        results.sort(key=lambda x: x.get('priority', 5))
        
        return results
    
    def generate_daily_digest(self, emails: List[Dict]) -> str:
        """
        Generate a daily digest of email responses.
        """
        classifications = self.classify_batch(emails)
        
        digest = "\n📬 DAILY EMAIL RESPONSE DIGEST\n"
        digest += "="*50 + "\n"
        digest += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n"
        digest += f"📧 Total responses: {len(emails)}\n\n"
        
        # Group by priority
        priority_groups = {1: [], 2: [], 3: [], 4: [], 5: []}
        for c in classifications:
            priority = c.get('priority', 5)
            priority_groups[priority].append(c)
        
        # High priority
        if priority_groups[1] or priority_groups[2]:
            digest += "🔴 HIGH PRIORITY:\n"
            for c in priority_groups[1] + priority_groups[2]:
                email = c.get('email', {})
                digest += f"  • [{c['type'].value.upper()}] {email.get('subject', 'No subject')[:50]}\n"
                digest += f"    Action: {c.get('action', '')}\n"
        
        # Medium priority
        if priority_groups[3]:
            digest += "\n🟡 NEEDS ATTENTION:\n"
            for c in priority_groups[3]:
                email = c.get('email', {})
                digest += f"  • [{c['type'].value.upper()}] {email.get('subject', 'No subject')[:50]}\n"
        
        # Low priority
        if priority_groups[4] or priority_groups[5]:
            digest += f"\n🟢 LOW PRIORITY: {len(priority_groups[4]) + len(priority_groups[5])} emails\n"
        
        return digest


def main():
    """Test response classifier."""
    classifier = AIResponseClassifier()
    
    # Test emails
    test_emails = [
        {
            'subject': 'Interview Invitation - Data Analyst Position',
            'body': 'Dear Candidate, We were impressed by your profile. We would like to schedule an interview. Please share your availability for next week.',
            'sender': 'hr@techcorp.com'
        },
        {
            'subject': 'RE: Application for Designer Role',
            'body': 'Thank you for your application. Unfortunately, we have decided to move forward with other candidates. We wish you all the best.',
            'sender': 'careers@designco.com'
        },
        {
            'subject': 'Technical Assessment - Next Steps',
            'body': 'Congratulations on clearing the initial screening! Please complete the attached coding challenge within 5 days.',
            'sender': 'talent@startup.io'
        }
    ]
    
    print("\n🤖 CLASSIFYING EMAIL RESPONSES...\n")
    
    for email in test_emails:
        result = classifier.classify(
            email['subject'],
            email['body'],
            email['sender']
        )
        
        print(f"📧 Subject: {email['subject']}")
        print(f"   Type: {result['type'].value.upper()}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Priority: {result['priority']}/5")
        print(f"   Action: {result['action']}")
        print()
    
    # Generate digest
    print(classifier.generate_daily_digest(test_emails))


if __name__ == '__main__':
    main()
