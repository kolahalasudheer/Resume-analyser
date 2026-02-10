"""
Keyword matching engine for exact keyword detection between JD and Resume

This module handles:
- Loading skill databases
- Extracting keywords from JD and Resume
- Exact matching with alias support
- Fuzzy matching for typos
- Match percentage calculation
"""

import json
import os
from typing import Dict, List, Set, Tuple
from fuzzywuzzy import fuzz
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_normalizer import TextNormalizer
from utils.jd_parser import JDParser
from ats.rule_based.context_aware_matcher import ContextAwareMatcher
from shared.constants import FUZZY_MATCH_THRESHOLD


class KeywordMatcher:
    """Exact keyword matching between JD and Resume"""
    
    def __init__(self):
        """Load skill databases and initialize JD parser"""
        self.tech_skills = self._load_tech_skills()
        self.soft_skills = self._load_soft_skills()
        
        # Build reverse lookup for aliases
        self.alias_to_primary = self._build_alias_map()
        
        # Initialize advanced JD parser
        self.jd_parser = JDParser()
        
        # Initialize context matcher
        self.context_matcher = ContextAwareMatcher()
    
    def _load_tech_skills(self) -> Dict:
        """Load technical skills database"""
        # Navigate from src/ats/rule_based/ to src/data/skills/
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'skills', 'tech_skills.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def _load_soft_skills(self) -> Dict:
        """Load soft skills database"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'skills', 'soft_skills.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def _build_alias_map(self) -> Dict[str, str]:
        """Build reverse lookup from alias to primary term"""
        alias_map = {}
        
        # Tech skills aliases
        for category, data in self.tech_skills.items():
            if 'aliases' in data:
                for primary, aliases in data['aliases'].items():
                    for alias in aliases:
                        alias_map[alias.lower()] = primary
        
        return alias_map
    
    def extract_jd_keywords(self, jd_text: str) -> Dict[str, List[str]]:
        """
        Extract required keywords from job description
        
        Args:
            jd_text: Job description text
            
        Returns:
            dict with tech_skills, soft_skills, domains
        """
        clean_text = TextNormalizer.clean_for_keyword_matching(jd_text)
        tokens = set(TextNormalizer.tokenize(jd_text))
        
        # Also check bigrams and trigrams for multi-word skills
        bigrams = TextNormalizer.extract_ngrams(jd_text, 2)
        trigrams = TextNormalizer.extract_ngrams(jd_text, 3)
        phrases = set([b.lower() for b in bigrams] + [t.lower() for t in trigrams])
        
        tech_skills_found = set()
        soft_skills_found = set()
        
        # Find tech skills
        tech_skills_found = self._find_tech_skills(tokens, phrases, jd_text)
        
        # Find soft skills
        soft_skills_found = self._find_soft_skills(tokens, phrases, jd_text)
        
        return {
            'tech_skills': sorted(list(tech_skills_found)),
            'soft_skills': sorted(list(soft_skills_found)),
            'all_keywords': sorted(list(tech_skills_found | soft_skills_found))
        }
    
    def _find_tech_skills(self, tokens: Set[str], phrases: Set[str], full_text: str) -> Set[str]:
        """Find technical skills in text"""
        import re
        found = set()
        full_text_lower = full_text.lower()
        
        # Check each category of tech skills
        for category, data in self.tech_skills.items():
            if category == 'aliases':
                continue
            
            # Get all skills for this category
            if isinstance(data, dict):
                all_skills = []
                for subcat, skills in data.items():
                    if subcat != 'aliases' and isinstance(skills, list):
                        all_skills.extend(skills)
            elif isinstance(data, list):
                all_skills = data
            else:
                continue
            
            # Check each skill
            for skill in all_skills:
                skill_lower = skill.lower()
                
                # Skip very short skills (1-2 chars) unless exact token match
                if len(skill_lower) <= 2:
                    if skill_lower in tokens:
                        found.add(skill)
                    continue
                
                # For multi-word skills, check exact phrase match
                if ' ' in skill_lower:
                    # Use word boundary regex for exact match
                    pattern = r'\b' + re.escape(skill_lower) + r'\b'
                    if re.search(pattern, full_text_lower):
                        found.add(skill)
                    continue
                
                # For single-word skills, check whole word match
                # Use word boundary to avoid substring matches
                pattern = r'\b' + re.escape(skill_lower) + r'\b'
                if re.search(pattern, full_text_lower):
                    found.add(skill)
        
        return found
    
    def _find_soft_skills(self, tokens: Set[str], phrases: Set[str], full_text: str) -> Set[str]:
        """Find soft skills in text"""
        import re
        found = set()
        full_text_lower = full_text.lower()
        
        for skill_type, data in self.soft_skills.items():
            # Check primary terms
            if 'primary' in data:
                for skill in data['primary']:
                    skill_lower = skill.lower()
                    
                    # Use word boundary for whole-word match
                    pattern = r'\b' + re.escape(skill_lower) + r'\b'
                    if re.search(pattern, full_text_lower):
                        found.add(skill)
                        continue
            
            # Check related phrases
            if 'related_phrases' in data:
                for phrase in data['related_phrases']:
                    phrase_lower = phrase.lower()
                    # Use word boundary for exact phrase match
                    pattern = r'\b' + re.escape(phrase_lower) + r'\b'
                    if re.search(pattern, full_text_lower):
                        # Add the main skill category
                        if 'primary' in data and data['primary']:
                            found.add(data['primary'][0])
                            break
        
        return found
    
    def extract_resume_keywords(self, resume_text: str) -> Dict[str, List[str]]:
        """
        Extract keywords from resume
        
        Args:
            resume_text: Resume text
            
        Returns:
            dict with tech_skills, soft_skills
        """
        # Initial extraction (same as JD)
        raw_keywords = self.extract_jd_keywords(resume_text)
        
        # Apply context filtering
        filtered_keywords = {
            'tech_skills': [],
            'soft_skills': [],
            'all_keywords': []
        }
        
        # Filter tech skills based on context
        for skill in raw_keywords['tech_skills']:
            context = self.context_matcher.check_context(resume_text, skill)
            if context['confidence'] >= 0.5:  # Filter out negative/learning contexts
                filtered_keywords['tech_skills'].append(skill)
                
        # Filter soft skills based on context
        for skill in raw_keywords['soft_skills']:
            context = self.context_matcher.check_context(resume_text, skill)
            if context['confidence'] >= 0.5:
                filtered_keywords['soft_skills'].append(skill)
                
        # Rebuild all_keywords map
        filtered_keywords['all_keywords'] = sorted(list(set(
            filtered_keywords['tech_skills'] + filtered_keywords['soft_skills']
        )))
        
        return filtered_keywords
    
    def match_keywords(self, jd_keywords: Dict, resume_keywords: Dict) -> Dict:
        """
        Compare and match keywords between JD and Resume
        Now includes importance scoring for each resume skill:
        - 100% if skill is in JD (must keep)
        - Lower % if skill not in JD (optional, depends on relevance)
        
        Args:
            jd_keywords: Keywords from JD
            resume_keywords: Keywords from Resume
            
        Returns:
            dict with found, missing, resume_skills_with_importance, match_percentage
        """
        jd_all = set(jd_keywords['all_keywords'])
        resume_all = set(resume_keywords['all_keywords'])
        
        # Exact matches (Required skills)
        found_exact = jd_all & resume_all
        missing_potential = jd_all - resume_all
        
        # Try fuzzy matching for missing keywords
        found_fuzzy = set()
        still_missing = set()
        
        for jd_keyword in missing_potential:
            matched = False
            for resume_keyword in resume_all:
                if self.fuzzy_match(jd_keyword, resume_keyword):
                    found_fuzzy.add(jd_keyword)
                    matched = True
                    break
            
            if not matched:
                # Check aliases
                jd_keyword_lower = jd_keyword.lower()
                if jd_keyword_lower in self.alias_to_primary:
                    primary = self.alias_to_primary[jd_keyword_lower]
                    if primary in resume_all or primary.lower() in [r.lower() for r in resume_all]:
                        found_fuzzy.add(jd_keyword)
                        matched = True
            
            if not matched:
                still_missing.add(jd_keyword)
        
        all_found = found_exact | found_fuzzy
        
        # NEW: Calculate importance score for each resume skill
        resume_skills_with_importance = []
        
        for skill in resume_all:
            skill_lower = skill.lower()
            
            # Check if skill matches JD (exact or fuzzy)
            if skill in all_found:
                importance = 100  # Must keep - matches JD
                status = "Must Keep"
            elif any(self.fuzzy_match(skill, jd_skill) for jd_skill in jd_all):
                importance = 100  # Close match to JD
                status = "Must Keep"
            else:
                # Skill not in JD - calculate relevance
                # Check if it's a known skill from database
                is_known = (skill_lower in self.alias_to_primary or 
                           any(skill_lower in [s.lower() for s in self.tech_skills.get(cat, {}).get(subcat, [])]
                               for cat in self.tech_skills
                               for subcat in self.tech_skills.get(cat, {}) 
                               if isinstance(self.tech_skills.get(cat, {}), dict) and subcat != 'aliases'))
                
                if is_known:
                    importance = 40  # Valid skill, not required by this JD
                    status = "Optional"
                else:
                    importance = 30  # Unknown skill, might be domain-specific
                    status = "Optional"
            
            resume_skills_with_importance.append({
                'skill': skill,
                'importance': importance,
                'status': status,
                'in_jd': skill in all_found
            })
        
        # Sort by importance (highest first)
        resume_skills_with_importance.sort(key=lambda x: (-x['importance'], x['skill']))
        
        # Calculate match percentage (based on JD requirements)
        if len(jd_all) > 0:
            match_percentage = (len(all_found) / len(jd_all)) * 100
        else:
            match_percentage = 0.0
        
        # Categorize found and missing
        found_tech = [k for k in all_found if k in jd_keywords['tech_skills']]
        found_soft = [k for k in all_found if k in jd_keywords['soft_skills']]
        missing_tech = [k for k in still_missing if k in jd_keywords['tech_skills']]
        missing_soft = [k for k in still_missing if k in jd_keywords['soft_skills']]
        
        return {
            'found_keywords': {
                'tech_skills': sorted(found_tech),
                'soft_skills': sorted(found_soft),
                'all': sorted(list(all_found))
            },
            'missing_keywords': {
                'tech_skills': sorted(missing_tech),
                'soft_skills': sorted(missing_soft),
                'all': sorted(list(still_missing))
            },
            'resume_skills_with_importance': resume_skills_with_importance,
            'match_percentage': round(match_percentage, 2),
            'exact_matches': len(found_exact),
            'fuzzy_matches': len(found_fuzzy),
            'total_jd_keywords': len(jd_all),
            'total_found': len(all_found),
            'total_missing': len(still_missing),
            'total_resume_skills': len(resume_all)
        }
    
    def fuzzy_match(self, keyword1: str, keyword2: str, 
                    threshold: float = FUZZY_MATCH_THRESHOLD) -> bool:
        """
        Fuzzy matching for handling typos
        
        Args:
            keyword1: First keyword
            keyword2: Second keyword
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            True if keywords match above threshold
        """
        # Normalize for comparison
        k1 = keyword1.lower().strip()
        k2 = keyword2.lower().strip()
        
        # Exact match
        if k1 == k2:
            return True
        
        # Fuzzy ratio
        ratio = fuzz.ratio(k1, k2) / 100.0
        if ratio >= threshold:
            return True
        
        # Partial ratio (for substring matching)
        partial_ratio = fuzz.partial_ratio(k1, k2) / 100.0
        if partial_ratio >= threshold:
            return True
        
        return False
    
    def analyze(self, resume_text: str, jd_text: str) -> Dict:
        """
        Complete keyword analysis with advanced JD understanding
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            
        Returns:
            Complete analysis results with JD insights
        """
        # Traditional keyword extraction (for backward compatibility)
        jd_keywords = self.extract_jd_keywords(jd_text)
        resume_keywords = self.extract_resume_keywords(resume_text)
        match_results = self.match_keywords(jd_keywords, resume_keywords)
        
        # NEW: Advanced JD analysis
        jd_analysis = self.jd_parser.parse_jd(jd_text)
        
        return {
            'jd_keywords': jd_keywords,
            'resume_keywords': resume_keywords,
            'match_results': match_results,
            'jd_analysis': jd_analysis  # New comprehensive JD insights
        }
