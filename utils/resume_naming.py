"""
Resume naming and job title standardization utilities.
Handles the mapping between scraped job titles and standardized naming conventions.
"""

import re
import os
from typing import Dict, Optional


class JobTitleStandardizer:
    """Standardizes job titles to consistent naming conventions for resume matching."""
    
    # Default mapping of keywords to standardized titles
    # This can be extended at runtime via environment variable
    DEFAULT_TITLE_MAPPINGS = {
        # Data roles
        'data analyst': 'Data Analyst',
        'senior data analyst': 'Data Analyst',  # Standardize to base title
        'data scientist': 'Data Scientist',
        'senior data scientist': 'Data Scientist',
        'data engineer': 'Data Engineer',
        'senior data engineer': 'Data Engineer',
        
        # Business roles  
        'business analyst': 'Business Analyst',
        'senior business analyst': 'Business Analyst',
        'business intelligence analyst': 'Business Analyst',
        'bi analyst': 'Business Analyst',
        
        # Specialized roles
        'power bi specialist': 'Business Analyst',
        'tableau analyst': 'Data Analyst',
        'sql developer': 'Data Analyst',
        'analytics consultant': 'Data Analyst',
        
        # DevOps/SRE roles
        'devops engineer': 'DevOps Engineer',
        'senior devops engineer': 'DevOps Engineer',
        'site reliability engineer': 'SRE Engineer',
        'sre': 'SRE Engineer',
        'platform engineer': 'Platform Engineer',
        'cloud engineer': 'Cloud Engineer',
        'infrastructure engineer': 'DevOps Engineer',
        'kubernetes engineer': 'DevOps Engineer',
        'devsecops engineer': 'DevOps Engineer',
        
        # Interior Design/Architecture roles
        'interior designer': 'Interior Designer',
        'autocad designer': 'AutoCAD Designer',
        'junior interior designer': 'Interior Designer',
        'senior interior designer': 'Interior Designer',
        'estimation engineer': 'Estimation Engineer',
        'quantity surveyor': 'Quantity Surveyor',
        'revit specialist': 'Interior Designer',
        '3d visualizer': 'Interior Designer',
    }
    
    # Class-level cache for custom mappings
    _title_mappings = None
    
    @classmethod
    def _get_title_mappings(cls) -> dict:
        """Get title mappings, including any from environment variable."""
        if cls._title_mappings is None:
            cls._title_mappings = cls.DEFAULT_TITLE_MAPPINGS.copy()
            
            # Check for custom mappings from environment
            # Format: "keyword1:Standard Title 1,keyword2:Standard Title 2"
            custom_mappings = os.getenv('JOB_TITLE_MAPPINGS', '')
            if custom_mappings:
                for mapping in custom_mappings.split(','):
                    if ':' in mapping:
                        keyword, standardized = mapping.split(':', 1)
                        cls._title_mappings[keyword.strip().lower()] = standardized.strip()
                        
            # Also use APPLICANT_TARGET_ROLE as default fallback
            target_role = os.getenv('APPLICANT_TARGET_ROLE', '')
            if target_role:
                cls._default_role = target_role.split(',')[0].strip()
            else:
                cls._default_role = 'Data Analyst'
                
        return cls._title_mappings
    
    # Keep backward compatibility
    TITLE_MAPPINGS = property(lambda self: self._get_title_mappings())
    
    @classmethod
    def _get_default_role(cls) -> str:
        """Get default role from environment or fallback."""
        target_role = os.getenv('APPLICANT_TARGET_ROLE', '')
        if target_role:
            return target_role.split(',')[0].strip()
        return 'Data Analyst'
    
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
            return cls._get_default_role()  # Dynamic default fallback
            
        # Clean the title - remove company suffixes and special chars
        cleaned_title = cls._clean_title(original_title)
        
        # Get title mappings (includes custom ones from env)
        title_mappings = cls._get_title_mappings()
        
        # Check for exact matches first
        title_lower = cleaned_title.lower()
        if title_lower in title_mappings:
            return title_mappings[title_lower]
        
        # Check for partial matches
        for keyword, standardized in title_mappings.items():
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
        
        # Priority order for role detection
        if 'scientist' in title_lower:
            return 'Data Scientist'
        elif 'devops' in title_lower or 'sre' in title_lower or 'reliability' in title_lower:
            return 'DevOps Engineer'
        elif 'cloud' in title_lower:
            return 'Cloud Engineer'
        elif 'interior' in title_lower or 'autocad' in title_lower or 'revit' in title_lower:
            return 'Interior Designer'
        elif 'engineer' in title_lower:
            return 'Data Engineer'
        elif 'business' in title_lower and 'analyst' in title_lower:
            return 'Business Analyst'
        elif 'data' in title_lower and 'analyst' in title_lower:
            return 'Data Analyst'
        elif 'analyst' in title_lower:
            return 'Data Analyst'
        else:
            return cls._get_default_role()  # Dynamic default fallback


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