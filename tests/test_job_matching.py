import unittest
import os
import tempfile
import warnings
from email.mime.multipart import MIMEMultipart

import pandas as pd

from scripts.email_sender import _job_matches_workflow_criteria
from scripts.email_sender import PersonalizedEmailSender
from scripts.smart_job_matcher import SmartJobMatcher


class RequiredResumeTests(unittest.TestCase):
    def test_message_includes_resume_attachment(self):
        sender = PersonalizedEmailSender.__new__(PersonalizedEmailSender)
        sender.sender_name = "Applicant"
        sender.sender_email = "applicant@example.org"

        with tempfile.NamedTemporaryFile() as resume:
            resume.write(b"resume content")
            resume.flush()
            sender.resume_path = resume.name

            message = sender.create_email_message("hr@example.org", "Application", "Hello")

        self.assertIsInstance(message, MIMEMultipart)
        attachments = [
            part for part in message.walk()
            if part.get_content_disposition() == "attachment"
        ]
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_payload(decode=True), b"resume content")

    def test_missing_resume_prevents_sending(self):
        sender = PersonalizedEmailSender.__new__(PersonalizedEmailSender)
        sender.resume_path = os.path.join(tempfile.gettempdir(), "missing-required-resume.pdf")

        self.assertFalse(sender.send_email("hr@example.org", "Acme", "Support Engineer"))


class ProblematicDomainTests(unittest.TestCase):
    def test_domain_stats_avoid_pandas_groupby_apply_warning(self):
        sender = PersonalizedEmailSender.__new__(PersonalizedEmailSender)

        with tempfile.TemporaryDirectory() as directory:
            sender.sent_log_path = os.path.join(directory, "sent_emails.csv")
            pd.DataFrame(
                [
                    {"recipient_email": "hr1@acme.org", "status": "bounced"},
                    {"recipient_email": "hr2@acme.org", "status": "rejected"},
                ]
            ).to_csv(sender.sent_log_path, index=False)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                problematic_domains = sender._analyze_problematic_domains()

        self.assertIn("acme.org", problematic_domains)
        self.assertFalse(
            any(issubclass(item.category, FutureWarning) for item in caught)
        )


class SmartJobMatcherTests(unittest.TestCase):
    def test_missing_hr_email_is_skipped(self):
        matcher = SmartJobMatcher()
        jobs = pd.DataFrame(
            [{"company": "Acme", "title": "Support Engineer", "match_score": 80}]
        )
        hr_emails = pd.DataFrame(
            [
                {"hr_email": float("nan"), "company": "Acme"},
                {"hr_email": "hr@acme.com", "company": "Acme"},
            ]
        )

        matches = matcher.match_jobs_to_hr(jobs, hr_emails)

        self.assertEqual(matches["hr_email"].tolist(), ["hr@acme.com"])


class WorkflowCriteriaTests(unittest.TestCase):
    def test_comma_separated_target_roles_are_alternatives(self):
        row = pd.Series({"job_title": "Software Support Engineer"})

        matches = _job_matches_workflow_criteria(
            row,
            ["product support engineer", "software support engineer"],
            ["product support engineer", "software support engineer"],
            [],
        )

        self.assertTrue(matches)

    def test_nonmatching_role_is_rejected(self):
        row = pd.Series({"job_title": "Data Analyst"})

        matches = _job_matches_workflow_criteria(
            row,
            ["product support engineer", "software support engineer"],
            ["product support engineer", "software support engineer"],
            [],
        )

        self.assertFalse(matches)


if __name__ == "__main__":
    unittest.main()
