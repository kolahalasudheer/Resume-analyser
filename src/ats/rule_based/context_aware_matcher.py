"""
Context-aware matcher matching for Layer 1
Handles context detection to reduce false positives (e.g. "willing to learn Python" vs "Expert in Python")
"""

import re
from typing import Dict, List, Tuple

class ContextAwareMatcher:
    """
    Wraps keyword matching with context awareness.
    Detects:
    - Negative context ("not familiar with", "no experience in")
    - Future/Learning context ("willing to learn", "interested in")
    - Experience context ("expert in", "proficient with", "2 years of")
    """
    
    def __init__(self):
        self.negative_patterns = [
            r'not\s+familiar\s+with',
            r'no\s+experience\s+in',
            r'never\s+used',
            r'learning\s+curve',
            r'without\s+using'
        ]
        
        self.learning_patterns = [
            r'willing\s+to\s+learn',
            r'interested\s+in\s+learning',
            r'learning',
            r'studying',
            r'identifying\s+as\s+a\s+beginner',
            r'novice\s+in'
        ]
        
        self.expert_patterns = [
            r'expert\s+in',
            r'proficient\s+with',
            r'advanced',
            r'years?\s+of\s+experience',
            r'architected',
            r'designed'
        ]

    def check_context(self, text: str, keyword: str, window_size: int = 50) -> Dict:
        """
        Check the context surrounding a keyword usage.
        
        Args:
            text: Full text containing the keyword
            keyword: The specific keyword to check
            window_size: Number of characters to check around match
            
        Returns:
            Dict with context status and confidence modifier
        """
        modifier = 1.0
        status = "neutral"
        
        # Find all occurrences
        keyword_safe = re.escape(keyword)
        for match in re.finditer(r'\b' + keyword_safe + r'\b', text, re.IGNORECASE):
            start, end = match.span()
            # Get window around keyword
            context_start = max(0, start - window_size)
            context_end = min(len(text), end + window_size)
            context_snippet = text[context_start:context_end].lower()
            
            # Check negative patterns
            for pattern in self.negative_patterns:
                if re.search(pattern, context_snippet):
                    return {'status': 'negative', 'confidence': 0.0}
            
            # Check learning patterns
            for pattern in self.learning_patterns:
                if re.search(pattern, context_snippet):
                    # Reduce confidence significantly but don't eliminate
                    modifier = 0.3
                    status = "learning"
                    
            # Check expert patterns
            for pattern in self.expert_patterns:
                if re.search(pattern, context_snippet):
                    modifier = 1.2
                    status = "expert"
                    
        return {'status': status, 'confidence': modifier}

    def refine_matches(self, found_keywords: List[str], full_text: str) -> List[Dict]:
        """
        Process a list of found keywords and refine based on context.
        """
        refined = []
        for keyword in found_keywords:
            context = self.check_context(full_text, keyword)
            if context['confidence'] > 0.0:
                refined.append({
                    'keyword': keyword,
                    'context': context['status'],
                    'confidence': context['confidence']
                })
        return refined
