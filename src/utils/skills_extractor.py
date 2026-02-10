"""
Advanced skills extraction from resumes with multi-format support

This module handles:
- Skills extraction from dedicated Skills sections
- Skills from tables (common in modern resumes)
- Skills embedded in experience/project descriptions
- Multiple skill formats (comma-separated, bullets, tables, categorized)
- Database matching with fuzzy logic
- Context-aware extraction
"""

import json
import os
import re
from typing import Dict, List, Set, Tuple
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_normalizer import TextNormalizer


class SkillsExtractor:
    """Extract and validate skills from resume text with advanced format support"""
    
    def __init__(self):
        """Load skill databases"""
        self.tech_skills = self._load_tech_skills()
        self.soft_skills = self._load_soft_skills()
        self.all_known_skills = self._build_skill_set()
    
    def _load_tech_skills(self) -> Dict:
        """Load technical skills database"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'skills', 'tech_skills.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def _load_soft_skills(self) -> Dict:
        """Load soft skills database"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'skills', 'soft_skills.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def _build_skill_set(self) -> Set[str]:
        """Build a comprehensive set of all known skills for validation"""
        skills = set()
        
        # Add tech skills
        for category, data in self.tech_skills.items():
            if isinstance(data, dict):
                for subcat, skill_list in data.items():
                    if subcat != 'aliases' and isinstance(skill_list, list):
                        skills.update([s.lower() for s in skill_list])
                # Add aliases
                if 'aliases' in data:
                    for primary, aliases in data['aliases'].items():
                        skills.add(primary.lower())
                        skills.update([a.lower() for a in aliases])
            elif isinstance(data, list):
                skills.update([s.lower() for s in data])
        
        # Add soft skills
        for skill_type, data in self.soft_skills.items():
            if 'primary' in data:
                skills.update([s.lower() for s in data['primary']])
            if 'related_phrases' in data and isinstance(data['related_phrases'], list):
                skills.update([p.lower() for p in data['related_phrases']])
        
        return skills
    
    def extract_all_skills(self, resume_text: str, parsed_data: Dict = None, 
                          tables: List[Dict] = None) -> Dict[str, List[str]]:
        """
        Extract skills from all sources in resume
        
        Args:
            resume_text: Full resume text
            parsed_data: Parsed resume sections (optional)
            tables: Extracted tables from PDF (optional)
            
        Returns:
            dict with tech_skills, soft_skills, and source attribution
        """
        all_skills = set()
        skill_sources = {}  # Track where each skill was found
        
        # 1. Extract from dedicated Skills section
        if parsed_data and 'skills' in parsed_data and parsed_data['skills']:
            section_skills = self._extract_from_skills_section(
                parsed_data.get('raw_sections', {}).get('skills', '')
            )
            for skill in section_skills:
                all_skills.add(skill)
                skill_sources[skill] = 'skills_section'
        
        # 2. Extract from tables (if available)
        if tables:
            table_skills = self._extract_from_tables(tables)
            for skill in table_skills:
                all_skills.add(skill)
                skill_sources[skill] = 'table'
        
        # 3. Extract from experience descriptions
        if parsed_data and 'experience' in parsed_data:
            exp_skills = self._extract_from_experience(parsed_data['experience'])
            for skill in exp_skills:
                if skill not in all_skills:
                    all_skills.add(skill)
                    skill_sources[skill] = 'experience'
        
        # 4. Extract from projects
        if parsed_data and 'projects' in parsed_data:
            proj_skills = self._extract_from_projects(parsed_data['projects'])
            for skill in proj_skills:
                if skill not in all_skills:
                    all_skills.add(skill)
                    skill_sources[skill] = 'projects'
        
        # 5. Validate and categorize skills
        validated_skills = self._validate_skills(list(all_skills))
        
        # Categorize into tech vs soft
        tech_skills = []
        soft_skills = []
        
        for skill in validated_skills:
            if self._is_tech_skill(skill):
                tech_skills.append(skill)
            elif self._is_soft_skill(skill):
                soft_skills.append(skill)
            else:
                # If unknown but looks valid, add to tech by default
                tech_skills.append(skill)
        
        return {
            'tech_skills': sorted(tech_skills),
            'soft_skills': sorted(soft_skills),
            'all_skills': sorted(validated_skills),
            'sources': skill_sources
        }
    
    def _extract_from_skills_section(self, section_text: str) -> List[str]:
        """
        Extract skills from dedicated skills section
        Handles multiple formats: comma-separated, bullets, categories
        """
        if not section_text:
            return []
        
        skills = []
        
        # Check for categorized format like "Languages: Python, Java"
        category_pattern = r'([A-Za-z\s]+):\s*([^\n]+)'
        category_matches = re.findall(category_pattern, section_text)
        
        if category_matches:
            # Categorized format
            for category, skill_text in category_matches:
                # Extract skills from each category
                category_skills = self._parse_skill_list(skill_text)
                skills.extend(category_skills)
        else:
            # Non-categorized format
            skills = self._parse_skill_list(section_text)
        
        return skills
    
    def _parse_skill_list(self, text: str) -> List[str]:
        """
        Parse a skill list that may be comma-separated, bullet-pointed, or newline-separated
        """
        skills = []
        
        # Try comma-separated first
        if ',' in text:
            potential_skills = [s.strip() for s in text.split(',')]
            skills.extend(potential_skills)
        # Try semicolon-separated
        elif ';' in text:
            potential_skills = [s.strip() for s in text.split(';')]
            skills.extend(potential_skills)
        # Try pipe-separated
        elif '|' in text:
            potential_skills = [s.strip() for s in text.split('|')]
            skills.extend(potential_skills)
        # Try bullet points
        elif '•' in text or '·' in text:
            bullets = TextNormalizer.extract_bullet_points(text)
            skills.extend(bullets)
        # Try newline-separated
        else:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Remove common bullet characters
                line = re.sub(r'^[•●○■□▪▫–—\*\-]\s*', '', line)
                if line and len(line) > 1 and len(line) < 50:
                    skills.append(line)
        
        # Clean up skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            # Remove bullet characters
            skill = re.sub(r'^[•●○■□▪▫–—\*\-]\s*', '', skill)
            skill = re.sub(r'\s+', ' ', skill)  # Normalize whitespace
            
            # Filter out invalid entries
            if skill and len(skill) > 1 and len(skill) < 50:
                # Avoid full sentences
                if not self._looks_like_sentence(skill):
                    cleaned_skills.append(skill)
        
        return cleaned_skills
    
    def _extract_from_tables(self, tables: List[Dict]) -> List[str]:
        """Extract skills from table data"""
        skills = []
        
        for table_info in tables:
            table_data = table_info.get('data', [])
            
            # For each row in table
            for row in table_data:
                if not row:
                    continue
                
                # Check if this row contains skills
                for cell in row:
                    if cell and isinstance(cell, str):
                        # Parse the cell content as potential skills
                        cell_skills = self._parse_skill_list(cell)
                        skills.extend(cell_skills)
        
        return skills
    
    def _extract_from_experience(self, experiences: List[Dict]) -> List[str]:
        """Extract skills mentioned in experience descriptions"""
        skills = set()
        
        for exp in experiences:
            # Check job title
            if 'title' in exp and exp['title']:
                title_skills = self._extract_skills_from_text(exp['title'])
                skills.update(title_skills)
            
            # Check bullet points
            if 'bullets' in exp:
                for bullet in exp['bullets']:
                    bullet_skills = self._extract_skills_from_text(bullet)
                    skills.update(bullet_skills)
        
        return list(skills)
    
    def _extract_from_projects(self, projects: List[Dict]) -> List[str]:
        """Extract skills from project descriptions"""
        skills = set()
        
        for proj in projects:
            # Check description
            if 'description' in proj and proj['description']:
                desc_skills = self._extract_skills_from_text(proj['description'])
                skills.update(desc_skills)
            
            # Check bullets
            if 'bullets' in proj:
                for bullet in proj['bullets']:
                    bullet_skills = self._extract_skills_from_text(bullet)
                    skills.update(bullet_skills)
        
        return list(skills)
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract known skills from free-form text
        Uses word boundary matching to find skill mentions
        """
        if not text:
            return []
        
        found_skills = set()
        text_lower = text.lower()
        
        # Check all known skills
        for skill in self.all_known_skills:
            # Use word boundary for exact matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                # Add the original casing from database
                found_skills.add(self._get_proper_skill_name(skill))
        
        return list(found_skills)
    
    def _get_proper_skill_name(self, skill_lower: str) -> str:
        """Get the proper casing/name for a skill from database"""
        # Search tech skills
        for category, data in self.tech_skills.items():
            if isinstance(data, dict):
                for subcat, skill_list in data.items():
                    if subcat != 'aliases' and isinstance(skill_list, list):
                        for s in skill_list:
                            if s.lower() == skill_lower:
                                return s
                # Check aliases
                if 'aliases' in data:
                    for primary, aliases in data['aliases'].items():
                        for alias in aliases:
                            if alias.lower() == skill_lower:
                                return primary
                        if primary.lower() == skill_lower:
                            return primary
        
        # Search soft skills
        for skill_type, data in self.soft_skills.items():
            if 'primary' in data:
                for s in data['primary']:
                    if s.lower() == skill_lower:
                        return s
        
        # Return title-cased if not found
        return skill_lower.title()
    
    def _validate_skills(self, skills: List[str]) -> List[str]:
        """
        Validate extracted skills against database
        Remove duplicates, resolve aliases
        """
        validated = set()
        
        for skill in skills:
            skill_clean = skill.strip()
            if not skill_clean:
                continue
            
            skill_lower = skill_clean.lower()
            
            # Check if it's a known skill (including aliases)
            if skill_lower in self.all_known_skills:
                # Get the primary name
                proper_name = self._get_proper_skill_name(skill_lower)
                validated.add(proper_name)
            else:
                # Check for partial matches or keep if looks valid
                if self._looks_like_valid_skill(skill_clean):
                    validated.add(skill_clean)
        
        return list(validated)
    
    def _looks_like_valid_skill(self, text: str) -> bool:
        """Check if text looks like a valid skill"""
        # Length checks
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Not a sentence
        if self._looks_like_sentence(text):
            return False
        
        # Contains mostly alphanumeric characters
        if not re.search(r'[a-zA-Z]', text):
            return False
        
        # Not too many non-alphanumeric chars
        non_alnum = len(re.findall(r'[^a-zA-Z0-9\s\-\.\+#]', text))
        if non_alnum > len(text) * 0.3:
            return False
        
        return True
    
    def _looks_like_sentence(self, text: str) -> bool:
        """Check if text looks like a full sentence rather than a skill name"""
        # Has multiple words and ends with punctuation
        words = text.split()
        if len(words) > 5:
            return True
        
        # Contains sentence-ending punctuation
        if text.rstrip().endswith(('.', '!', '?')):
            return True
        
        # Contains verb indicators (simple heuristic)
        verb_indicators = ['developed', 'created', 'managed', 'led', 'designed',
                          'implemented', 'built', 'responsible for']
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in verb_indicators):
            return True
        
        return False
    
    def _is_tech_skill(self, skill: str) -> bool:
        """Check if skill is a technical skill"""
        skill_lower = skill.lower()
        
        for category, data in self.tech_skills.items():
            if isinstance(data, dict):
                for subcat, skill_list in data.items():
                    if subcat != 'aliases' and isinstance(skill_list, list):
                        if any(s.lower() == skill_lower for s in skill_list):
                            return True
                if 'aliases' in data:
                    for primary, aliases in data['aliases'].items():
                        if primary.lower() == skill_lower:
                            return True
                        if any(a.lower() == skill_lower for a in aliases):
                            return True
        
        return False
    
    def _is_soft_skill(self, skill: str) -> bool:
        """Check if skill is a soft skill"""
        skill_lower = skill.lower()
        
        for skill_type, data in self.soft_skills.items():
            if 'primary' in data:
                if any(s.lower() == skill_lower for s in data['primary']):
                    return True
            if 'related_phrases' in data and isinstance(data['related_phrases'], list):
                if any(p.lower() == skill_lower for p in data['related_phrases']):
                    return True
        
        return False
