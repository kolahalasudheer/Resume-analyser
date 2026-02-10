"""
Scoring engine for Layer 1 - calculates comprehensive scores

Combines:
- Keyword matching score
- Formatting score
- ATS compliance score
Into weighted final score with grade
"""

from typing import Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.constants import SCORING_WEIGHTS, GRADE_THRESHOLDS


class Layer1Scorer:
    """Calculate comprehensive Layer 1 scores"""
    
    def __init__(self):
        """Initialize with scoring weights"""
        self.weights = SCORING_WEIGHTS
        self.grade_thresholds = GRADE_THRESHOLDS
    
    def calculate_score(self,
                       keyword_match: Dict,
                       formatting: Dict,
                       ats_validation: Dict) -> Dict:
        """
        Calculate weighted final score
        
        Args:
            keyword_match: Results from KeywordMatcher
            formatting: Results from FormattingValidator
            ats_validation: Results from ATSValidator
            
        Returns:
            dict with scores, grade, and breakdown
        """
        # Extract individual scores
        keyword_score = keyword_match['match_percentage']
        formatting_score = formatting['score']
        ats_score = ats_validation['total_score']
        
        # Calculate weighted total
        total_score = (
            keyword_score * self.weights['keyword_match'] +
            formatting_score * self.weights['formatting'] +
            ats_score * self.weights['ats_compliance']
        )
        
        # Calculate grade
        grade = self._calculate_grade(total_score)
        
        # Identify strengths and weaknesses
        breakdown = self._analyze_breakdown(keyword_score, formatting_score, ats_score)
        
        return {
            'keyword_score': round(keyword_score, 2),
            'formatting_score': round(formatting_score, 2),
            'ats_score': round(ats_score, 2),
            'total_score': round(total_score, 2),
            'grade': grade,
            'breakdown': breakdown,
            'weights_used': self.weights
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        for grade, threshold in sorted(self.grade_thresholds.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True):
            if score >= threshold:
                return grade
        return 'F'
    
    def _analyze_breakdown(self, keyword_score: float, 
                          formatting_score: float, 
                          ats_score: float) -> Dict:
        """Identify strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        # Keyword matching
        if keyword_score >= 80:
            strengths.append(f"Excellent keyword match ({keyword_score}%)")
        elif keyword_score >= 60:
            strengths.append(f"Good keyword match ({keyword_score}%)")
        elif keyword_score >= 40:
            weaknesses.append(f"Moderate keyword match ({keyword_score}%) - add more relevant skills")
        else:
            weaknesses.append(f"Poor keyword match ({keyword_score}%) - missing critical skills")
        
        # Formatting
        if formatting_score >= 90:
            strengths.append("Perfect formatting - ATS-friendly")
        elif formatting_score >= 70:
            strengths.append("Good formatting")
        else:
            weaknesses.append(f"Formatting issues detected - may cause ATS parsing problems")
        
        # ATS compliance
        if ats_score >= 90:
            strengths.append("Excellent ATS compliance")
        elif ats_score >= 70:
            strengths.append("Good ATS compliance")
        else:
            weaknesses.append("ATS compliance issues - follow best practices")
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def generate_recommendations(self, 
                                keyword_match: Dict,
                                formatting: Dict,
                                ats_validation: Dict) -> list:
        """
        Generate actionable recommendations
        
        Args:
            keyword_match: Keyword matching results
            formatting: Formatting validation results
            ats_validation: ATS validation results
            
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # Keyword recommendations (highest priority)
        missing_keywords = keyword_match.get('missing_keywords', {})
        
        missing_tech = missing_keywords.get('tech_skills', [])
        missing_soft = missing_keywords.get('soft_skills', [])
        
        if missing_tech:
            top_missing = missing_tech[:5]  # Top 5
            recommendations.append({
                'priority': 'high',
                'category': 'Keywords',
                'message': f"Add missing technical skills: {', '.join(top_missing)}",
                'action': 'Include these skills in your experience bullets or skills section'
            })
        
        if missing_soft:
            top_missing_soft = missing_soft[:3]
            recommendations.append({
                'priority': 'medium',
                'category': 'Keywords',
                'message': f"Highlight soft skills: {', '.join(top_missing_soft)}",
                'action': 'Demonstrate these through your achievements and bullet points'
            })
        
        # Formatting recommendations
        if formatting.get('issues'):
            for issue in formatting['issues'][:3]:  # Top 3
                recommendations.append({
                    'priority': issue.get('severity', 'medium'),
                    'category': 'Formatting',
                    'message': issue['message'],
                    'action': issue['recommendation']
                })
        
        # ATS compliance recommendations
        ats_recs = ats_validation.get('recommendations', [])
        for rec in ats_recs[:3]:  # Top 3
            recommendations.append({
                'priority': 'medium',
                'category': 'ATS Compliance',
                'message': rec,
                'action': 'Update resume to follow ATS best practices'
            })
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations
