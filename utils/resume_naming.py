"""
Resume naming and job title standardization utilities.
Handles the mapping between scraped job titles and standardized naming conventions.
"""

import re
import os
from typing import Dict, Optional


class JobTitleStandardizer:
    """Standardizes job titles to consistent naming conventions for resume matching."""
    
    # Mapping of keywords to standardized titles - Ajay Dhage (DevOps/SRE)
    TITLE_MAPPINGS = {
        # DevOps roles
        'devops engineer': 'DevOps Engineer',
        'senior devops engineer': 'DevOps Engineer',
        'lead devops engineer': 'DevOps Engineer',
        'devops lead': 'DevOps Engineer',
        'devops architect': 'DevOps Engineer',
        
        # SRE roles
        'site reliability engineer': 'SRE',
        'sre': 'SRE',
        'senior sre': 'SRE',
        'reliability engineer': 'SRE',
        
        # Platform/Cloud roles
        'platform engineer': 'Platform Engineer',
        'cloud engineer': 'Cloud Engineer',
        'cloud architect': 'Cloud Engineer',
        'aws engineer': 'Cloud Engineer',
        'azure engineer': 'Cloud Engineer',
        'gcp engineer': 'Cloud Engineer',
        
        # Infrastructure roles
        'infrastructure engineer': 'Infrastructure Engineer',
        'kubernetes engineer': 'Infrastructure Engineer',
        'k8s engineer': 'Infrastructure Engineer',
        
        # Automation roles
        'automation engineer': 'DevOps Engineer',
        'devsecops engineer': 'DevOps Engineer',
        'build engineer': 'DevOps Engineer',
        'release engineer': 'DevOps Engineer',
    }
    
    @classmethod
    def standardize_title(cls, original_title: str) -> str:
        """
        Standardize a job title to a consistent format.
        
        Args:
            original_title: The original scraped job title
            
        Returns:
            Standardized job title
        """
        if not original_title:
            return "DevOps Engineer"  # Default fallback for Ajay
            
        # Clean the title - remove company suffixes and special chars
        cleaned_title = cls._clean_title(original_title)
        
        # Check for exact matches first
        title_lower = cleaned_title.lower()
        if title_lower in cls.TITLE_MAPPINGS:
            return cls.TITLE_MAPPINGS[title_lower]
        
        # Check for partial matches
        for keyword, standardized in cls.TITLE_MAPPINGS.items():
            if keyword in title_lower:
                return standardized
        
        # If no match found, try to extract main role
        return cls._extract_main_role(cleaned_title)
    
    @classmethod
    def _clean_title(cls, title: str) -> str:
        """Clean job title by removing company suffixes and specializations."""
        # Remove company name suffixes (e.g., "Data Engineer - Amazon" -> "Data Engineer")
        title = re.sub(r'\s*-\s*[A-Z][a-zA-Z\s]+$', '', title)
        
        # Remove parenthetical content
        title = re.sub(r'\([^)]*\)', '', title)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        return title.strip()
    
    @classmethod
    def _extract_main_role(cls, title: str) -> str:
        """Extract main role from title when no direct mapping exists."""
        title_lower = title.lower()
        
        # Priority order for role detection - DevOps/SRE focus
        if 'devops' in title_lower:
            return 'DevOps Engineer'
        elif 'sre' in title_lower or 'reliability' in title_lower:
            return 'SRE'
        elif 'platform' in title_lower:
            return 'Platform Engineer'
        elif 'cloud' in title_lower or 'aws' in title_lower or 'azure' in title_lower:
            return 'Cloud Engineer'
        elif 'kubernetes' in title_lower or 'k8s' in title_lower:
            return 'Infrastructure Engineer'
        elif 'infrastructure' in title_lower:
            return 'Infrastructure Engineer'
        elif 'automation' in title_lower:
            return 'DevOps Engineer'
        else:
            return 'DevOps Engineer'  # Default fallback for Ajay


class ResumeNamingManager:
    """Manages consistent resume naming across tailoring and application processes."""
    
    def __init__(self, tailored_resumes_dir: str):
        self.tailored_resumes_dir = tailored_resumes_dir
        self.title_standardizer = JobTitleStandardizer()
    
    def get_tailored_resume_filename(self, job: Dict[str, str], use_standardized_title: bool = True) -> str:
        """
        Generate the filename for a tailored resume.
        
        Args:
            job: Job dictionary with 'title' and 'company' keys
            use_standardized_title: Whether to use standardized title or original
            
        Returns:
            Resume filename without path
        """
        safe_company = self._sanitize_filename(job["company"])
        
        if use_standardized_title:
            title = self.title_standardizer.standardize_title(job["title"])
        else:
            title = job["title"]
            
        safe_title = self._sanitize_filename(title)
        
        return f"{safe_company}_{safe_title}.pdf"
    
    def get_tailored_resume_path(self, job: Dict[str, str], use_standardized_title: bool = True) -> str:
        """
        Generate the full path for a tailored resume.
        
        Args:
            job: Job dictionary with 'title' and 'company' keys
            use_standardized_title: Whether to use standardized title or original
            
        Returns:
            Full path to resume file
        """
        filename = self.get_tailored_resume_filename(job, use_standardized_title)
        return os.path.join(self.tailored_resumes_dir, filename)
    
    def find_matching_resume(self, job: Dict[str, str]) -> Optional[str]:
        """
        Find existing tailored resume for a job, trying multiple naming patterns.
        
        Args:
            job: Job dictionary with 'title' and 'company' keys
            
        Returns:
            Path to matching resume file if found, None otherwise
        """
        possible_filenames = [
            # Try standardized title first
            self.get_tailored_resume_filename(job, use_standardized_title=True),
            # Try original title
            self.get_tailored_resume_filename(job, use_standardized_title=False),
        ]
        
        for filename in possible_filenames:
            filepath = os.path.join(self.tailored_resumes_dir, filename)
            if os.path.exists(filepath):
                return filepath
        
        return None
    
    def _sanitize_filename(self, text: str) -> str:
        """Remove characters that are invalid in filenames."""
        return re.sub(r'[\\/*?:"<>|]', "", text)
    
    def get_title_mapping_report(self) -> Dict[str, str]:
        """Get a report of all title mappings for debugging."""
        return self.title_standardizer.TITLE_MAPPINGS.copy()


# Global instance for easy access
def get_resume_naming_manager(tailored_resumes_dir: str) -> ResumeNamingManager:
    """Get a ResumeNamingManager instance."""
    return ResumeNamingManager(tailored_resumes_dir)