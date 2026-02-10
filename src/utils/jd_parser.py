"""
Advanced Job Description Parser

Extracts comprehensive information from job descriptions:
- Job title and seniority level
- Required vs Preferred skills (with importance weights)
- Key responsibilities
- Domain/Industry context
- Skill importance scoring based on context
"""

import re
import json
import os
from typing import Dict, List, Set, Tuple
from collections import Counter


class JDParser:
    """Parse and analyze job descriptions with advanced context understanding"""
    
    def __init__(self):
        """Initialize with skill databases"""
        self.tech_skills = self._load_tech_skills()
        self.soft_skills = self._load_soft_skills()
        
        # Keywords that indicate requirement levels
        self.required_indicators = [
            'required', 'must have', 'must-have', 'essential', 'mandatory',
            'necessary', 'need', 'required:', 'requirements:', 'must:'
        ]
        
        self.preferred_indicators = [
            'preferred', 'nice to have', 'nice-to-have', 'bonus', 'plus',
            'desired', 'ideal', 'advantage', 'a plus', 'preferred:'
        ]
        
        # Seniority level indicators
        self.seniority_levels = {
            'intern': ['intern', 'internship', 'trainee'],
            'junior': ['junior', 'entry level', 'entry-level', 'associate', '0-2 years'],
            'mid': ['mid level', 'mid-level', 'intermediate', '2-5 years', '3-5 years'],
            'senior': ['senior', 'sr.', 'experienced', '5+ years', '7+ years', 'lead'],
            'lead': ['lead', 'principal', 'staff', 'architect', 'head of'],
            'manager': ['manager', 'engineering manager', 'team lead']
        }
    
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
    
    def parse_jd(self, jd_text: str) -> Dict:
        """
        Comprehensive JD parsing
        
        Returns:
            dict with job_info, skills_categorized, responsibilities, etc.
        """
        # Extract job information
        job_info = self._extract_job_info(jd_text)
        
        # Parse skills with context
        skills_analysis = self._analyze_skills_with_context(jd_text)
        
        # Extract responsibilities
        responsibilities = self._extract_responsibilities(jd_text)
        
        # Detect domain/industry
        domain_info = self._detect_domain(jd_text, skills_analysis)
        
        return {
            'job_info': job_info,
            'skills_analysis': skills_analysis,
            'responsibilities': responsibilities,
            'domain_info': domain_info,
            'raw_text_length': len(jd_text)
        }
    
    def _extract_job_info(self, jd_text: str) -> Dict:
        """Extract job title, seniority, experience requirements"""
        lines = jd_text.split('\n')
        
        # Job title is usually in first few lines
        job_title = lines[0].strip() if lines else "Unknown"
        
        # Clean up title (remove company name if present)
        if ' at ' in job_title.lower():
            job_title = job_title.split(' at ')[0].strip()
        if ' - ' in job_title:
            parts = job_title.split(' - ')
            # Take the part that looks more like a job title
            job_title = max(parts, key=len).strip()
        
        # Detect seniority level
        seniority = self._detect_seniority(jd_text, job_title)
        
        # Extract experience requirements
        experience_years = self._extract_experience_years(jd_text)
        
        return {
            'job_title': job_title,
            'seniority_level': seniority,
            'experience_required': experience_years
        }
    
    def _detect_seniority(self, jd_text: str, job_title: str) -> str:
        """Detect seniority level from JD text and title"""
        text_lower = (jd_text + ' ' + job_title).lower()
        
        # Check each seniority level
        matches = {}
        for level, keywords in self.seniority_levels.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                matches[level] = count
        
        if not matches:
            return 'mid'  # Default
        
        # Return the level with most matches
        return max(matches, key=matches.get)
    
    def _extract_experience_years(self, jd_text: str) -> str:
        """Extract years of experience from JD"""
        # Patterns like "5+ years", "3-5 years", "minimum 7 years"
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)-(\d+)\s*years?',
            r'minimum\s+(\d+)\s*years?',
            r'at least\s+(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Not specified"
    
    def _analyze_skills_with_context(self, jd_text: str) -> Dict:
        """
        Analyze skills with importance weighting based on context
        
        Returns skills categorized by:
        - Required vs Preferred
        - Importance score (0-100)
        """
        # Split into sections if possible
        sections = self._split_into_sections(jd_text)
        
        # Find all skills with their context
        skills_with_context = self._find_skills_with_context(jd_text, sections)
        
        # Calculate importance scores
        skills_scored = self._calculate_skill_importance(skills_with_context, jd_text)
        
        # Categorize as required vs preferred
        required_skills = []
        preferred_skills = []
        
        for skill_info in skills_scored:
            if skill_info['importance'] >= 80:
                required_skills.append(skill_info)
            else:
                preferred_skills.append(skill_info)
        
        return {
            'required_skills': sorted(required_skills, key=lambda x: -x['importance']),
            'preferred_skills': sorted(preferred_skills, key=lambda x: -x['importance']),
            'all_skills': sorted(skills_scored, key=lambda x: -x['importance'])
        }
    
    def _split_into_sections(self, jd_text: str) -> Dict[str, str]:
        """Split JD into common sections"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'requirements': r'(requirements?|qualifications?|what (?:we\'re looking for|you\'ll need)|what you bring)',
            'responsibilities': r'(responsibilities|duties|what you\'ll do|role description|day[ -]to[ -]day)',
            'preferred': r'(preferred|nice to have|bonus|plus)',
            'experience': r'(experience|background)',
            'skills': r'(skills?|technical skills?|core competencies)'
        }
        
        text_lower = jd_text.lower()
        lines = jd_text.split('\n')
        
        current_section = 'general'
        sections[current_section] = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            matched_section = None
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line_lower):
                    matched_section = section_name
                    break
            
            if matched_section:
                current_section = matched_section
                sections[current_section] = []
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)
        
        # Join lines back
        for section in sections:
            sections[section] = '\n'.join(sections[section])
        
        return sections
    
    def _find_skills_with_context(self, jd_text: str, sections: Dict[str, str]) -> List[Dict]:
        """Find skills and track their context"""
        skills_found = []
        full_text_lower = jd_text.lower()
        
        # Gather all known skills
        all_known_skills = self._get_all_known_skills()
        
        for skill in all_known_skills:
            skill_lower = skill.lower()
            
            # Find skill with word boundaries
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            matches = list(re.finditer(pattern, full_text_lower))
            
            if matches:
                # Determine context for each occurrence
                contexts = []
                for match in matches:
                    # Get surrounding text
                    start = max(0, match.start() - 100)
                    end = min(len(full_text_lower), match.end() + 100)
                    context = full_text_lower[start:end]
                    
                    # Check for requirement indicators
                    is_required = any(indicator in context for indicator in self.required_indicators)
                    is_preferred = any(indicator in context for indicator in self.preferred_indicators)
                    
                    # Determine which section
                    section_name = self._find_section_for_position(match.start(), jd_text, sections)
                    
                    contexts.append({
                        'is_required': is_required,
                        'is_preferred': is_preferred,
                        'section': section_name
                    })
                
                skills_found.append({
                    'skill': skill,
                    'frequency': len(matches),
                    'contexts': contexts
                })
        
        return skills_found
    
    def _get_all_known_skills(self) -> List[str]:
        """Get all skills from database"""
        skills = []
        
        # Tech skills
        for category, data in self.tech_skills.items():
            if isinstance(data, dict):
                for subcat, skill_list in data.items():
                    if subcat != 'aliases' and isinstance(skill_list, list):
                        skills.extend(skill_list)
        
        # Soft skills
        for skill_type, data in self.soft_skills.items():
            if 'primary' in data:
                skills.extend(data['primary'])
        
        return skills
    
    def _find_section_for_position(self, position: int, full_text: str, sections: Dict[str, str]) -> str:
        """Find which section a text position belongs to"""
        # Simple heuristic - check which section's content contains this position
        char_count = 0
        for section_name, section_text in sections.items():
            char_count += len(section_text)
            if position < char_count:
                return section_name
        return 'general'
    
    def _calculate_skill_importance(self, skills_with_context: List[Dict], jd_text: str) -> List[Dict]:
        """
        Calculate importance score (0-100) for each skill based on:
        - Frequency
        - Context (required vs preferred indicators)
        - Section placement
        """
        scored_skills = []
        
        for skill_data in skills_with_context:
            score = 50  # Base score
            
            # Frequency bonus (up to +20)
            frequency_bonus = min(20, skill_data['frequency'] * 10)
            score += frequency_bonus
            
            # Context bonuses
            has_required_context = any(ctx['is_required'] for ctx in skill_data['contexts'])
            has_preferred_context = any(ctx['is_preferred'] for ctx in skill_data['contexts'])
            
            if has_required_context:
                score += 30  # Strong indicator
            elif has_preferred_context:
                score -= 10  # Less critical
            
            # Section bonus
            in_requirements = any(ctx['section'] in ['requirements', 'skills'] for ctx in skill_data['contexts'])
            if in_requirements:
                score += 20
            
            # Cap at 100
            score = min(100, score)
            
            scored_skills.append({
                'skill': skill_data['skill'],
                'importance': score,
                'frequency': skill_data['frequency'],
                'is_required': has_required_context,
                'is_preferred': has_preferred_context
            })
        
        return scored_skills
    
    def _extract_responsibilities(self, jd_text: str) -> List[str]:
        """Extract key responsibilities from JD"""
        responsibilities = []
        
        # Look for responsibility section
        lines = jd_text.split('\n')
        in_responsibility_section = False
        
        resp_patterns = r'(responsibilities|duties|what you\'ll do|role description|you will)'
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Check if entering responsibility section
            if re.search(resp_patterns, line_lower):
                in_responsibility_section = True
                continue
            
            # Check if leaving section (new header)
            if in_responsibility_section and line_lower and not line_lower[0].isalnum() == False:
                if re.search(r'^(requirements?|qualifications?|skills?|experience):', line_lower):
                    in_responsibility_section = False
            
            # Extract bullet points
            if in_responsibility_section:
                # Remove bullet characters
                clean_line = re.sub(r'^[•●○■□▪▫–—\*\-]\s*', '', line_stripped)
                if clean_line and len(clean_line) > 20:  # Substantial content
                    responsibilities.append(clean_line)
        
        return responsibilities[:10]  # Top 10 responsibilities
    
    def _detect_domain(self, jd_text: str, skills_analysis: Dict) -> Dict:
        """Detect job domain/industry based on skills and keywords"""
        text_lower = jd_text.lower()
        
        # Domain indicators
        domains = {
            'web_development': ['web', 'frontend', 'backend', 'full stack', 'react', 'angular', 'vue', 'html', 'css'],
            'data_science': ['data science', 'machine learning', 'deep learning', 'ai', 'tensorflow', 'pytorch', 'pandas'],
            'mobile_development': ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin'],
            'devops': ['devops', 'ci/cd', 'kubernetes', 'docker', 'jenkins', 'terraform', 'aws', 'cloud'],
            'backend': ['backend', 'api', 'microservices', 'database', 'sql', 'nosql', 'rest', 'graphql'],
            'security': ['security', 'cybersecurity', 'penetration', 'vulnerability', 'encryption'],
            'qa': ['qa', 'testing', 'automation', 'selenium', 'test', 'quality assurance']
        }
        
        domain_scores = {}
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            primary_domain = max(domain_scores, key=domain_scores.get)
            return {
                'primary_domain': primary_domain.replace('_', ' ').title(),
                'confidence': min(100, domain_scores[primary_domain] * 10)
            }
        
        return {
            'primary_domain': 'General Software Engineering',
            'confidence': 50
        }
