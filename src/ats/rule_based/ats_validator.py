"""
ATS best practices validator

Validates:
- Section headers (standard vs creative)
- Contact information format
- Special characters
- Bullet points usage
- Resume length
"""

import json
import os
import re
from typing import Dict, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.constants import OPTIMAL_RESUME_LENGTH


class ATSValidator:
    """Validate ATS best practices compliance"""
    
    def __init__(self):
        """Load best practices and headers databases"""
        self.best_practices = self._load_best_practices()
        self.section_headers = self._load_section_headers()
    
    def _load_best_practices(self) -> Dict:
        """Load ATS best practices"""
        # Navigate from src/ats/rule_based/ to src/data/ats/
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'ats', 'best_practices.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def _load_section_headers(self) -> Dict:
        """Load section headers"""
        # Navigate from src/ats/rule_based/ to src/data/ats/
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'ats', 'section_headers.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def validate(self, resume_text: str, parsed_sections: Dict, page_count: int = 1) -> Dict:
        """
        Complete ATS validation
        
        Args:
            resume_text: Full resume text
            parsed_sections: Parsed sections from SectionParser
            page_count: Number of pages
            
        Returns:
            dict with validation scores and recommendations
        """
        results = {}
        total_score = 0
        max_points = 5  # 5 categories
        
        # 1. Check section headers
        header_score, header_issues = self.check_section_headers(parsed_sections)
        results['section_headers'] = {
            'score': header_score,
            'issues': header_issues
        }
        total_score += header_score
        
        # 2. Check contact info
        contact_score, contact_issues = self.check_contact_info(parsed_sections.get('contact', {}))
        results['contact_info'] = {
            'score': contact_score,
            'issues': contact_issues
        }
        total_score += contact_score
        
        # 3. Check special characters
        special_char_score, special_char_issues = self.check_special_characters(resume_text)
        results['special_characters'] = {
            'score': special_char_score,
            'issues': special_char_issues
        }
        total_score += special_char_score
        
        # 4. Check bullet points
        bullet_score, bullet_issues = self.check_bullet_points(parsed_sections)
        results['bullet_points'] = {
            'score': bullet_score,
            'issues': bullet_issues
        }
        total_score += bullet_score
        
        # 5. Check resume length
        length_score, length_issues = self.check_length(page_count)
        results['resume_length'] = {
            'score': length_score,
            'issues': length_issues
        }
        total_score += length_score
        
        # Calculate overall score (0-100)
        overall_score = (total_score / max_points) * 100
        
        # Compile all recommendations
        all_recommendations = []
        for category in results.values():
            all_recommendations.extend(category['issues'])
        
        return {
            'section_headers_score': header_score * 20,
            'contact_info_score': contact_score * 20,
            'special_chars_score': special_char_score * 20,
            'bullet_points_score': bullet_score * 20,
            'length_score': length_score * 20,
            'total_score': round(overall_score, 2),
            'details': results,
            'recommendations': all_recommendations,
            'passed': overall_score >= 70
        }
    
    def check_section_headers(self, parsed_sections: Dict) -> tuple:
        """Validate section headers are ATS-friendly"""
        score = 0
        issues = []
        
        standard_headers = self.section_headers.get('standard_headers', [])
        required_sections = ['experience', 'education', 'skills']
        
        # Check if required sections exist
        sections_found = list(parsed_sections.get('raw_sections', {}).keys())
        
        for required in required_sections:
            if required in sections_found or any(required in s for s in sections_found):
                score += 0.33
            else:
                issues.append(f"Missing standard section: '{required.title()}'")
        
        # Bonus for having all standard sections
        if len(sections_found) >= 3:
            score = min(1.0, score + 0.1)
        
        # Cap score at 1.0
        score = min(1.0, score)
        
        return score, issues
    
    def check_contact_info(self, contact: Dict) -> tuple:
        """Validate contact information"""
        score = 0
        issues = []
        
        # Check email (required)
        if contact.get('email'):
            score += 0.5
        else:
            issues.append("Missing email address")
        
        # Check phone (required)
        if contact.get('phone'):
            score += 0.5
        else:
            issues.append("Missing phone number")
        
        # Bonus for LinkedIn
        if contact.get('linkedin'):
            score = min(1.0, score + 0.1)
        
        return score, issues
    
    def check_special_characters(self, text: str) -> tuple:
        """Check for problematic special characters"""
        score = 1.0  # Start perfect
        issues = []
        
        problematic_chars = ['%', '&', '#', '@', '£', '€', '©', '®', '™']
        
        # Don't count these in email addresses
        text_no_email = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        found_chars = set()
        for char in problematic_chars:
            if char in text_no_email:
                found_chars.add(char)
        
        if found_chars:
            penalty = min(0.3, len(found_chars) * 0.1)
            score -= penalty
            issues.append(f"Problematic characters found: {', '.join(found_chars)}")
        
        score = max(0, score)
        return score, issues
    
    def check_bullet_points(self, parsed_sections: Dict) -> tuple:
        """Check bullet point usage and quality"""
        score = 0
        issues = []
        
        # Get bullets from experience
        experiences = parsed_sections.get('experience', [])
        
        if not experiences:
            issues.append("No work experience bullets found")
            return 0.3, issues  # Partial credit
        
        total_bullets = 0
        weak_bullets = 0
        
        weak_starters = ['responsible for', 'worked on', 'helped with', 'assisted']
        strong_verbs = ['led', 'developed', 'implemented', 'created', 'designed', 
                       'managed', 'built', 'achieved', 'improved', 'optimized']
        
        for exp in experiences:
            bullets = exp.get('bullets', [])
            total_bullets += len(bullets)
            
            for bullet in bullets:
                bullet_lower = bullet.lower()
                
                # Check for weak starters
                if any(weak in bullet_lower for weak in weak_starters):
                    weak_bullets += 1
                
                # Check for strong action verbs
                starts_strong = any(bullet_lower.startswith(verb) for verb in strong_verbs)
                if starts_strong:
                    score += 0.1
        
        # Calculate score
        if total_bullets > 0:
            # Base score on bullet quality
            quality_ratio = 1 - (weak_bullets / total_bullets)
            score = quality_ratio * 0.7  # 70% based on quality
            
            # Bonus for having bullets at all
            score += 0.3
        else:
            score = 0
        
        if weak_bullets > 0:
            issues.append(f"{weak_bullets} weak bullet points found (use stronger action verbs)")
        
        score = min(1.0, score)
        return score, issues
    
    def check_length(self, page_count: int) -> tuple:
        """Check if resume length is optimal"""
        score = 1.0
        issues = []
        
        min_pages = OPTIMAL_RESUME_LENGTH['min']
        max_pages = OPTIMAL_RESUME_LENGTH['max']
        
        if page_count < min_pages:
            score = 0.7
            issues.append(f"Resume is too short ({page_count} page)")
        elif page_count > max_pages:
            excess_pages = page_count - max_pages
            penalty = min(0.5, excess_pages * 0.2)
            score -= penalty
            issues.append(f"Resume is too long ({page_count} pages). Consider trimming to {max_pages} pages.")
        
        score = max(0, score)
        return score, issues
