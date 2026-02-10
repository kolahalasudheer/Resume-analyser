"""
Resume section parser - identifies and extracts resume sections

Handles:
- Contact information extraction
- Section identification (Experience, Education, Skills, etc.)
- Bullet point extraction
- Date parsing
"""

import json
import os
import re
from typing import Dict, List, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_normalizer import TextNormalizer
from utils.skills_extractor import SkillsExtractor


class SectionParser:
    """Parse and identify resume sections"""
    
    def __init__(self):
        """Load section headers database"""
        self.section_headers = self._load_section_headers()
        self.skills_extractor = SkillsExtractor()
    
    def _load_section_headers(self) -> Dict:
        """Load ATS-friendly section headers"""
        # Navigate from src/ats/rule_based/ to src/data/ats/
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'ats', 'section_headers.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def parse_resume(self, resume_text: str, tables: List[Dict] = None) -> Dict:
        """
        Identify and extract resume sections
        
        Args:
            resume_text: Full resume text
            tables: Optional list of tables extracted from PDF
            
        Returns:
            dict with parsed sections
        """
        lines = resume_text.split('\n')
        
        # Extract contact info first
        contact = self.extract_contact_info(resume_text)
        
        # Identify section boundaries
        sections = self._identify_section_boundaries(lines)
        
        # Extract content for each section
        parsed_sections = {
            'contact': contact,
            'summary': sections.get('summary', ''),
            'experience': self._parse_experience_section(sections.get('experience', '')),
            'education': self._parse_education_section(sections.get('education', '')),
            'skills': self._parse_skills_section(sections.get('skills', '')),
            'projects': self._parse_projects_section(sections.get('projects', '')),
            'certifications': self._parse_certifications_section(sections.get('certifications', '')),
            'raw_sections': sections
        }
        
        # Enhanced skills extraction using SkillsExtractor
        extracted_skills = self.skills_extractor.extract_all_skills(
            resume_text,
            parsed_data=parsed_sections,
            tables=tables
        )
        
        # Update skills with comprehensive extraction
        parsed_sections['skills_detailed'] = extracted_skills
        # Keep simple list for backward compatibility
        parsed_sections['skills'] = extracted_skills.get('all_skills', parsed_sections['skills'])
        
        return parsed_sections
    
    def _identify_section_boundaries(self, lines: List[str]) -> Dict[str, str]:
        """Identify where sections start and end"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line is a section header
            section_type = self._is_section_header(line_stripped)
            
            if section_type:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_type
                current_content = []
            elif current_section:
                # Add to current section
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _is_section_header(self, line: str) -> Optional[str]:
        """Check if line is a section header, return section type"""
        line_lower = line.lower().strip()
        
        # Check experience synonyms
        for header in self.section_headers.get('experience_synonyms', []):
            if line_lower == header.lower():
                return 'experience'
        
        # Check education synonyms
        for header in self.section_headers.get('education_synonyms', []):
            if line_lower == header.lower():
                return 'education'
        
        # Check skills synonyms
        for header in self.section_headers.get('skills_synonyms', []):
            if line_lower == header.lower():
                return 'skills'
        
        # Check projects synonyms
        for header in self.section_headers.get('projects_synonyms', []):
            if line_lower == header.lower():
                return 'projects'
        
        # Check other standard headers
        if 'certif' in line_lower and len(line_lower) < 30:
            return 'certifications'
        if ('summary' in line_lower or 'profile' in line_lower or 'objective' in line_lower) and len(line_lower) < 30:
            return 'summary'
        
        return None
    
    def extract_contact_info(self, text: str) -> Dict:
        """
        Extract contact information from resume
        
        Args:
            text: Resume text
            
        Returns:
            dict with email, phone, linkedin, github, etc.
        """
        # Get first ~500 characters (contact usually at top)
        top_section = text[:500]
        
        contact = {
            'email': TextNormalizer.extract_email(top_section),
            'phone': TextNormalizer.extract_phone(top_section),
            'urls': TextNormalizer.extract_urls(top_section),
            'linkedin': '',
            'github': ''
        }
        
        # Extract LinkedIn and GitHub from URLs
        for url in contact['urls']:
            if 'linkedin.com' in url.lower():
                contact['linkedin'] = url
            elif 'github.com' in url.lower():
                contact['github'] = url
        
        return contact
    
    def _parse_experience_section(self, content: str) -> List[Dict]:
        """Parse experience section into structured data"""
        if not content:
            return []
        
        experiences = []
        lines = content.split('\n')
        
        current_exp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line looks like a job title or company
            if self._looks_like_job_title(line):
                # Save previous experience
                if current_exp:
                    experiences.append(current_exp)
                
                # Start new experience
                current_exp = {
                    'title': line,
                    'company': '',
                    'dates': '',
                    'bullets': []
                }
            elif current_exp:
                # Check if it's a date range
                if self._looks_like_date(line):
                    current_exp['dates'] = line
                # Check if it's a bullet point
                elif self._is_bullet_point(line):
                    bullet_text = self._extract_bullet_text(line)
                    current_exp['bullets'].append(bullet_text)
                # Otherwise might be company name
                elif not current_exp['company'] and len(line) < 100:
                    current_exp['company'] = line
                else:
                    # Add to last bullet or create new one
                    if current_exp['bullets']:
                        current_exp['bullets'][-1] += ' ' + line
                    else:
                        current_exp['bullets'].append(line)
        
        # Save last experience
        if current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def _parse_education_section(self, content: str) -> List[Dict]:
        """Parse education section"""
        if not content:
            return []
        
        education = []
        lines = content.split('\n')
        
        current_edu = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # New education entry (degree or university name)
            if self._looks_like_degree(line) or (current_edu is None and len(line) > 10):
                if current_edu:
                    education.append(current_edu)
                
                current_edu = {
                    'degree': line,
                    'institution': '',
                    'dates': '',
                    'details': []
                }
            elif current_edu:
                if self._looks_like_date(line):
                    current_edu['dates'] = line
                elif not current_edu['institution']:
                    current_edu['institution'] = line
                else:
                    current_edu['details'].append(line)
        
        if current_edu:
            education.append(current_edu)
        
        return education
    
    def _parse_skills_section(self, content: str) -> List[str]:
        """Parse skills section into list"""
        if not content:
            return []
        
        # Split by common separators
        skills = []
        
        # Try comma-separated
        if ',' in content:
            skills = [s.strip() for s in content.split(',')]
        # Try bullet points
        elif '•' in content or '-' in content:
            bullets = TextNormalizer.extract_bullet_points(content)
            skills = bullets
        # Try line-separated
        else:
            skills = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Clean up
        skills = [s for s in skills if s and len(s) > 1 and len(s) < 50]
        
        return skills
    
    def _parse_projects_section(self, content: str) -> List[Dict]:
        """Parse projects section - similar to experience"""
        if not content:
            return []
        
        projects = []
        lines = content.split('\n')
        
        current_proj = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Project title (usually bold or first line)
            if self._looks_like_project_title(line):
                if current_proj:
                    projects.append(current_proj)
                
                current_proj = {
                    'title': line,
                    'description': '',
                    'bullets': []
                }
            elif current_proj:
                if self._is_bullet_point(line):
                    bullet_text = self._extract_bullet_text(line)
                    current_proj['bullets'].append(bullet_text)
                elif not current_proj['description']:
                    current_proj['description'] = line
                else:
                    if current_proj['bullets']:
                        current_proj['bullets'][-1] += ' ' + line
        
        if current_proj:
            projects.append(current_proj)
        
        return projects
    
    def _parse_certifications_section(self, content: str) -> List[str]:
        """Parse certifications"""
        if not content:
            return []
        
        # Similar to skills
        certs = []
        
        if '•' in content or '-' in content:
            certs = TextNormalizer.extract_bullet_points(content)
        else:
            certs = [line.strip() for line in content.split('\n') if line.strip()]
        
        return certs
    
    def _looks_like_job_title(self, line: str) -> bool:
        """Check if line looks like a job title"""
        # Heuristics: usually short, contains job-related keywords
        if len(line) < 10 or len(line) > 100:
            return False
        
        job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'director',
                       'lead', 'senior', 'junior', 'intern', 'consultant',
                       'architect', 'specialist', 'coordinator']
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in job_keywords)
    
    def _looks_like_date(self, line: str) -> bool:
        """Check if line contains date range"""
        # Look for patterns like "Jan 2020 - Present" or "2020-2023"
        date_patterns = [
            r'\d{4}\s*-\s*\d{4}',
            r'\d{4}\s*-\s*present',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
            r'\d{1,2}/\d{4}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line.lower()):
                return True
        
        return False
    
    def _looks_like_degree(self, line: str) -> bool:
        """Check if line looks like a degree"""
        degree_keywords = ['bachelor', 'master', 'phd', 'bsc', 'msc', 'ba', 'ma',
                          'b.s.', 'm.s.', 'b.a.', 'm.a.', 'associate', 'diploma']
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in degree_keywords)
    
    def _looks_like_project_title(self, line: str) -> bool:
        """Check if line looks like a project title"""
        # Projects usually have certain patterns
        if len(line) < 5 or len(line) > 100:
            return False
        
        # Often Contains tech keywords or "project"
        project_indicators = ['project', 'application', 'system', 'platform', 'tool']
        line_lower = line.lower()
        
        # Also check if it's the first non-empty line
        return any(ind in line_lower for ind in project_indicators) or line.isupper()
    
    def _is_bullet_point(self, line: str) -> bool:
        """Check if line is a bullet point"""
        bullet_chars = ['•', '●', '○', '■', '□', '▪', '▫', '–', '—', '*', '-']
        
        line_stripped = line.lstrip()
        if not line_stripped:
            return False
        
        # Check if starts with bullet character
        if line_stripped[0] in bullet_chars:
            return True
        
        # Check for numbered lists
        if re.match(r'^\d+\.', line_stripped):
            return True
        
        return False
    
    def _extract_bullet_text(self, line: str) -> str:
        """Extract text from bullet point, removing bullet character"""
        # Remove bullet indicators
        bullet_pattern = r'^[•●○■□▪▫–—\*\-]\s*'
        line = re.sub(bullet_pattern, '', line.strip())
        
        # Remove numbered list indicators
        line = re.sub(r'^\d+\.\s*', '', line)
        
        return line.strip()
