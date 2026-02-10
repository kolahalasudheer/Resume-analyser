"""
Hybrid Skill Matcher
Combines rule-based keyword matching with AI semantic understanding for accurate skill extraction.
"""

import logging
from typing import Dict, List, Set
from collections import Counter

logger = logging.getLogger(__name__)

class HybridSkillMatcher:
    """
    Combines rule-based and AI-based skill extraction for maximum accuracy
    """
    
    def __init__(self):
        """Initialize the hybrid matcher"""
        pass
    
    def extract_skills_hybrid(
        self, 
        jd_text: str,
        rule_based_skills: Dict,
        ai_skills: Dict
    ) -> Dict:
        """
        Merge rule-based and AI skill extraction results
        
        Args:
            jd_text: Job description text
            rule_based_skills: Skills from rule-based parser
            ai_skills: Skills from AI analyzer
            
        Returns:
            dict: Merged and deduplicated skills with confidence scores
        """
        
        # Extract skills from both sources
        rb_required_tech = set(rule_based_skills.get('required_skills', {}).get('technical', []))
        rb_required_soft = set(rule_based_skills.get('required_skills', {}).get('soft', []))
        rb_preferred_tech = set(rule_based_skills.get('preferred_skills', {}).get('technical', []))
        rb_preferred_soft = set(rule_based_skills.get('preferred_skills', {}).get('soft', []))
        
        ai_required_tech = set(ai_skills.get('required_skills', {}).get('technical', []))
        ai_required_soft = set(ai_skills.get('required_skills', {}).get('soft', []))
        ai_preferred_tech = set(ai_skills.get('preferred_skills', {}).get('technical', []))
        ai_preferred_soft = set(ai_skills.get('preferred_skills', {}).get('soft', []))
        
        # Merge with confidence scoring
        merged_required_tech = self._merge_skills(rb_required_tech, ai_required_tech, jd_text)
        merged_required_soft = self._merge_skills(rb_required_soft, ai_required_soft, jd_text)
        merged_preferred_tech = self._merge_skills(rb_preferred_tech, ai_preferred_tech, jd_text)
        merged_preferred_soft = self._merge_skills(rb_preferred_soft, ai_preferred_soft, jd_text)
        
        return {
            'required_skills': {
                'technical': sorted(merged_required_tech, key=lambda x: x['confidence'], reverse=True),
                'soft': sorted(merged_required_soft, key=lambda x: x['confidence'], reverse=True)
            },
            'preferred_skills': {
                'technical': sorted(merged_preferred_tech, key=lambda x: x['confidence'], reverse=True),
                'soft': sorted(merged_preferred_soft, key=lambda x: x['confidence'], reverse=True)
            },
            'metadata': {
                'rule_based_count': len(rb_required_tech) + len(rb_required_soft) + len(rb_preferred_tech) + len(rb_preferred_soft),
                'ai_count': len(ai_required_tech) + len(ai_required_soft) + len(ai_preferred_tech) + len(ai_preferred_soft),
                'merged_count': len(merged_required_tech) + len(merged_required_soft) + len(merged_preferred_tech) + len(merged_preferred_soft)
            }
        }
    
    def _merge_skills(self, rb_skills: Set[str], ai_skills: Set[str], jd_text: str) -> List[Dict]:
        """
        Merge skills from both sources with confidence scoring
        
        Confidence logic:
        - Both found: 100% (high confidence)
        - Only rule-based: 85% (exact match)
        - Only AI: 70% (semantic understanding)
        """
        merged = []
        jd_lower = jd_text.lower()
        
        # Skills found by both (highest confidence)
        both = rb_skills & ai_skills
        for skill in both:
            merged.append({
                'skill': skill,
                'confidence': 100,
                'source': 'both'
            })
        
        # Skills only from rule-based
        only_rb = rb_skills - ai_skills
        for skill in only_rb:
            # Verify it actually appears in JD
            if skill.lower() in jd_lower:
                merged.append({
                    'skill': skill,
                    'confidence': 85,
                    'source': 'rule_based'
                })
        
        # Skills only from AI
        only_ai = ai_skills - rb_skills
        for skill in only_ai:
            # AI might have found synonyms or implied skills
            merged.append({
                'skill': skill,
                'confidence': 70,
                'source': 'ai'
            })
        
        return merged
    
    def match_resume_skills(
        self,
        resume_skills: List[str],
        jd_required_skills: List[Dict],
        jd_preferred_skills: List[Dict]
    ) -> Dict:
        """
        Match resume skills against JD requirements
        
        Args:
            resume_skills: List of skills found in resume
            jd_required_skills: Required skills from JD (with confidence)
            jd_preferred_skills: Preferred skills from JD (with confidence)
            
        Returns:
            dict: Match analysis with scores
        """
        
        resume_skills_lower = {skill.lower() for skill in resume_skills}
        
        # Match required skills
        required_matched = []
        required_missing = []
        
        for skill_info in jd_required_skills:
            skill = skill_info['skill']
            if skill.lower() in resume_skills_lower:
                required_matched.append({
                    **skill_info,
                    'matched': True
                })
            else:
                required_missing.append({
                    **skill_info,
                    'matched': False
                })
        
        # Match preferred skills
        preferred_matched = []
        preferred_missing = []
        
        for skill_info in jd_preferred_skills:
            skill = skill_info['skill']
            if skill.lower() in resume_skills_lower:
                preferred_matched.append({
                    **skill_info,
                    'matched': True
                })
            else:
                preferred_missing.append({
                    **skill_info,
                    'matched': False
                })
        
        # Calculate match score
        total_required = len(jd_required_skills)
        matched_required = len(required_matched)
        
        required_match_pct = (matched_required / total_required * 100) if total_required > 0 else 100
        
        total_preferred = len(jd_preferred_skills)
        matched_preferred = len(preferred_matched)
        
        preferred_match_pct = (matched_preferred / total_preferred * 100) if total_preferred > 0 else 100
        
        # Overall score (weighted: 80% required, 20% preferred)
        overall_score = (required_match_pct * 0.8) + (preferred_match_pct * 0.2)
        
        return {
            'required': {
                'matched': required_matched,
                'missing': required_missing,
                'match_percentage': round(required_match_pct, 2)
            },
            'preferred': {
                'matched': preferred_matched,
                'missing': preferred_missing,
                'match_percentage': round(preferred_match_pct, 2)
            },
            'overall_match_score': round(overall_score, 2),
            'summary': {
                'total_required': total_required,
                'matched_required': matched_required,
                'total_preferred': total_preferred,
                'matched_preferred': matched_preferred
            }
        }
