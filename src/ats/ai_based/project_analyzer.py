"""
AI-Powered Project Analyzer
Parses resume projects, analyzes relevance to JD, and suggests ATS-optimized rewrites.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    """
    Analyzes resume projects for ATS optimization
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    def analyze_projects(self, resume_text: str, jd_analysis: Dict) -> Dict:
        """
        Main entry point: Parse and analyze all projects
        
        Args:
            resume_text: Full resume text
            jd_analysis: Analyzed job description with required skills
            
        Returns:
            dict: Complete project analysis with suggestions
        """
        
        # Step 1: Extract project section
        project_section = self._extract_project_section(resume_text)
        
        if not project_section:
            return {
                "projects": [],
                "overall_score": 0,
                "message": "No project section found in resume"
            }
        
        # Step 2: Parse individual projects
        projects = self._parse_projects(project_section)
        
        if not projects:
            return {
                "projects": [],
                "overall_score": 0,
                "message": "No projects could be parsed"
            }
        
        # Step 3: Analyze each project against JD
        analyzed_projects = []
        for project in projects:
            analysis = self._analyze_single_project(project, jd_analysis)
            analyzed_projects.append(analysis)
        
        # Step 4: Calculate overall project score
        overall_score = self._calculate_overall_score(analyzed_projects)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_recommendations(analyzed_projects, jd_analysis)
        
        return {
            "projects": analyzed_projects,
            "overall_score": overall_score,
            "recommendations": recommendations,
            "total_projects": len(analyzed_projects)
        }
    
    def _extract_project_section(self, resume_text: str) -> Optional[str]:
        """
        Extract the projects section from resume
        """
        # Common project section headers
        patterns = [
            r'(?i)(ACADEMIC\s+)?PROJECTS?\s*\n(.*?)(?=\n[A-Z\s]{3,}:|\n\n[A-Z]|$)',
            r'(?i)TECHNICAL\s+PROJECTS?\s*\n(.*?)(?=\n[A-Z\s]{3,}:|\n\n[A-Z]|$)',
            r'(?i)KEY\s+PROJECTS?\s*\n(.*?)(?=\n[A-Z\s]{3,}:|\n\n[A-Z]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resume_text, re.DOTALL)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _parse_projects(self, project_section: str) -> List[Dict]:
        """
        Parse individual projects from the section
        """
        projects = []
        
        # Split by project (usually separated by blank lines or new titles)
        # Look for patterns like "Project Name | Technology" or just "Project Name"
        lines = project_section.split('\n')
        
        current_project = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a project title (usually has | or is followed by date)
            if '|' in line or re.search(r'\d{4}', line):
                # Save previous project
                if current_project and current_project.get('bullets'):
                    projects.append(current_project)
                
                # Start new project
                parts = line.split('|')
                title = parts[0].strip()
                tech_or_course = parts[1].strip() if len(parts) > 1 else ""
                
                current_project = {
                    'title': title,
                    'tech_or_course': tech_or_course,
                    'duration': '',
                    'bullets': []
                }
            
            # Check if this is a date line
            elif current_project and re.search(r'[A-Za-z]+\s+\d{4}', line):
                current_project['duration'] = line
            
            # Check if this is a bullet point
            elif current_project and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                bullet = re.sub(r'^[-•*]\s*', '', line)
                current_project['bullets'].append(bullet)
        
        # Add last project
        if current_project and current_project.get('bullets'):
            projects.append(current_project)
        
        return projects
    
    def _analyze_single_project(self, project: Dict, jd_analysis: Dict) -> Dict:
        """
        Analyze a single project against JD requirements
        """
        # Extract JD keywords
        jd_keywords = self._extract_jd_keywords(jd_analysis)
        
        # Combine all project text
        project_text = f"{project['title']} {project.get('tech_or_course', '')} {' '.join(project['bullets'])}"
        project_text_lower = project_text.lower()
        
        # Calculate keyword match
        matched_keywords = [kw for kw in jd_keywords if kw.lower() in project_text_lower]
        keyword_match_pct = (len(matched_keywords) / len(jd_keywords) * 100) if jd_keywords else 0
        
        # Identify missing keywords
        missing_keywords = [kw for kw in jd_keywords if kw.lower() not in project_text_lower]
        
        # Score relevance
        relevance_score = self._calculate_relevance_score(keyword_match_pct, project['bullets'])
        
        # Get AI suggestions for improvement
        suggestions = self._get_ai_suggestions(project, jd_analysis, missing_keywords[:5])
        
        return {
            **project,
            'relevance_score': round(relevance_score, 1),
            'keyword_match_pct': round(keyword_match_pct, 1),
            'matched_keywords': matched_keywords[:10],
            'missing_keywords': missing_keywords[:10],
            'suggestions': suggestions
        }
    
    def _extract_jd_keywords(self, jd_analysis: Dict) -> List[str]:
        """
        Extract all important keywords from JD analysis
        """
        keywords = []
        
        # Get required technical skills
        req_tech = jd_analysis.get('required_skills', {}).get('technical', [])
        keywords.extend(req_tech[:15])
        
        # Get preferred technical skills
        pref_tech = jd_analysis.get('preferred_skills', {}).get('technical', [])
        keywords.extend(pref_tech[:10])
        
        return keywords
    
    def _calculate_relevance_score(self, keyword_match_pct: float, bullets: List[str]) -> float:
        """
        Calculate overall relevance score for a project
        """
        # Base score from keyword match
        score = keyword_match_pct * 0.6
        
        # Bonus for number of bullets (2-3 is ideal)
        bullet_count = len(bullets)
        if bullet_count >= 2:
            score += 20
        
        # Bonus for strong action verbs
        strong_verbs = ['developed', 'implemented', 'designed', 'created', 'built', 'analyzed', 'optimized']
        bullets_text = ' '.join(bullets).lower()
        verb_count = sum(1 for verb in strong_verbs if verb in bullets_text)
        score += min(20, verb_count * 5)
        
        return min(100, score)
    
    def _get_ai_suggestions(self, project: Dict, jd_analysis: Dict, missing_keywords: List[str]) -> List[Dict]:
        """
        Use AI to suggest improved bullet points with 3-tier intelligent analysis
        
        Tier 1 (>70% match): Minor improvements, keyword optimization, spell check
        Tier 2 (30-70% match): Suggest small feature additions with tech stack
        Tier 3 (<30% match): Recommend project replacement or removal
        """
        if not self.api_key:
            return self._fallback_suggestions(project, missing_keywords)
        
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Calculate relevance tier
            keyword_match_pct = self._calculate_keyword_match_pct(project, jd_analysis)
            
            # Get JD context
            jd_summary = jd_analysis.get('job_summary', '')
            required_skills = jd_analysis.get('required_skills', {})
            required_tech = required_skills.get('technical', [])[:15]
            
            # Determine analysis tier
            if keyword_match_pct >= 70:
                tier = "HIGHLY_RELEVANT"
                instruction = """
This project is HIGHLY RELEVANT to the JD (>70% keyword match).

TIER 1 INSTRUCTIONS:
1. Make MINOR improvements only
2. Fix spelling/grammar mistakes
3. Add missing JD keywords ONLY where they naturally fit
4. Use strong action verbs (Developed, Implemented, Designed, etc.)
5. Add metrics/numbers where realistic
6. DO NOT suggest adding technologies that weren't used (e.g., if project used MySQL, DON'T suggest MongoDB even if JD mentions it)
7. Keep improvements truthful and realistic

Focus on polishing what's already there, not major changes.
"""
            elif keyword_match_pct >= 30:
                tier = "MODERATELY_RELEVANT"
                instruction = f"""
This project is MODERATELY RELEVANT to the JD (30-70% keyword match).

TIER 2 INSTRUCTIONS:
1. Suggest SMALL FEATURE ADDITIONS that align with JD requirements
2. Recommend specific tech stack additions from JD: {', '.join(required_tech[:5])}
3. Suggest minor enhancements user can implement quickly
4. For each suggestion, explain: "Add [feature] using [tech] to align with JD requirement for [skill]"
5. Keep suggestions realistic - features that can be added in 1-2 days
6. DO NOT fake technologies - only suggest additions user can actually implement
7. Clearly mark suggestions as "PROPOSED ADDITION" so user knows to implement before using

Example: "PROPOSED: Add user authentication using JWT tokens to demonstrate security skills mentioned in JD"
"""
            else:
                tier = "NOT_RELEVANT"
                instruction = """
This project is NOT RELEVANT to the JD (<30% keyword match).

TIER 3 INSTRUCTIONS:
1. Recommend REMOVING this project from resume OR replacing it
2. Suggest 2-3 alternative project ideas that match the JD
3. For each alternative, provide:
   - Project title
   - Brief description (2-3 lines)
   - Key technologies from JD to use
   - Expected impact on ATS score
4. Make it clear this is a RECOMMENDATION, not a requirement
5. Keep alternative projects realistic and achievable

Be honest: "This project doesn't align with the JD. Consider replacing with..."
"""

            prompt = f"""
You are an ATS optimization expert analyzing a resume project against job requirements.

ANALYSIS TIER: {tier}
Keyword Match: {keyword_match_pct:.1f}%

Job Requirements Summary:
{jd_summary[:500]}

Required Technical Skills from JD:
{', '.join(required_tech)}

Project Title: {project['title']}
Project Tech/Course: {project.get('tech_or_course', 'N/A')}
Current Bullet Points:
{chr(10).join(f"{i+1}. {bullet}" for i, bullet in enumerate(project['bullets']))}

Missing JD Keywords: {', '.join(missing_keywords[:10])}

{instruction}

Provide output in JSON format:
{{
    "tier": "{tier}",
    "recommendation": "keep_and_optimize" | "enhance_with_features" | "consider_replacing",
    "overall_advice": "brief advice for this project",
    "suggestions": [
        {{
            "original": "original bullet text",
            "improved": "improved bullet text",
            "added_keywords": ["keyword1", "keyword2"],
            "improvement_reason": "brief reason",
            "is_proposed_addition": false
        }}
    ],
    "feature_additions": [
        {{
            "feature": "feature name",
            "tech_stack": "technologies to use",
            "reason": "why this helps",
            "estimated_effort": "1-2 days"
        }}
    ],
    "alternative_projects": [
        {{
            "title": "project title",
            "description": "brief description",
            "key_technologies": ["tech1", "tech2"],
            "expected_impact": "high/medium/low"
        }}
    ]
}}

CRITICAL: Be honest and helpful. Don't suggest faking skills or technologies.
"""
            
            response = model.generate_content(prompt)
            text_response = response.text.strip()
            
            # Extract JSON
            match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if match:
                result = json.loads(match.group(0))
                
                # Track API usage
                try:
                    from utils.api_usage_tracker import APIUsageTracker
                    tracker = APIUsageTracker()
                    tracker.increment_usage(tokens_estimate=2500)  # Project analysis uses ~2500 tokens
                except:
                    pass  # Don't fail if tracker unavailable
                
                return result
            
            return self._fallback_suggestions(project, missing_keywords)
            
        except Exception as e:
            logger.error(f"AI suggestion error: {str(e)}")
            return self._fallback_suggestions(project, missing_keywords)
    
    def _calculate_keyword_match_pct(self, project: Dict, jd_analysis: Dict) -> float:
        """Helper to calculate keyword match percentage"""
        jd_keywords = self._extract_jd_keywords(jd_analysis)
        project_text = f"{project['title']} {project.get('tech_or_course', '')} {' '.join(project['bullets'])}"
        project_text_lower = project_text.lower()
        
        matched_keywords = [kw for kw in jd_keywords if kw.lower() in project_text_lower]
        return (len(matched_keywords) / len(jd_keywords) * 100) if jd_keywords else 0

    
    def _fallback_suggestions(self, project: Dict, missing_keywords: List[str]) -> List[Dict]:
        """
        Fallback suggestions when AI is unavailable
        """
        suggestions = []
        
        for bullet in project['bullets'][:3]:
            # Simple improvement: add action verb if missing
            improved = bullet
            if not any(bullet.lower().startswith(verb) for verb in ['developed', 'implemented', 'created', 'designed', 'built']):
                improved = f"Developed {bullet.lower()}"
            
            suggestions.append({
                'original': bullet,
                'improved': improved,
                'added_keywords': [],
                'improvement_reason': 'Added strong action verb (AI unavailable for detailed suggestions)'
            })
        
        return suggestions
    
    def _calculate_overall_score(self, analyzed_projects: List[Dict]) -> float:
        """
        Calculate overall project section score
        """
        if not analyzed_projects:
            return 0
        
        avg_relevance = sum(p['relevance_score'] for p in analyzed_projects) / len(analyzed_projects)
        avg_keyword_match = sum(p['keyword_match_pct'] for p in analyzed_projects) / len(analyzed_projects)
        
        # Weighted average
        overall = (avg_relevance * 0.6) + (avg_keyword_match * 0.4)
        
        return round(overall, 1)
    
    def _generate_recommendations(self, analyzed_projects: List[Dict], jd_analysis: Dict) -> List[str]:
        """
        Generate actionable recommendations
        """
        recommendations = []
        
        # Check for low-scoring projects
        low_score_projects = [p for p in analyzed_projects if p['relevance_score'] < 50]
        if low_score_projects:
            recommendations.append(f"⚠️ {len(low_score_projects)} project(s) have low relevance scores - consider adding more JD keywords")
        
        # Check for missing dates
        no_date_projects = [p for p in analyzed_projects if not p.get('duration')]
        if no_date_projects:
            recommendations.append(f"📅 Add duration (Month/Year format) to {len(no_date_projects)} project(s)")
        
        # Check for weak bullets
        weak_bullet_projects = [p for p in analyzed_projects if len(p['bullets']) < 2]
        if weak_bullet_projects:
            recommendations.append(f"📝 Add more bullet points (2-3 minimum) to {len(weak_bullet_projects)} project(s)")
        
        # Overall keyword coverage
        avg_keyword_match = sum(p['keyword_match_pct'] for p in analyzed_projects) / len(analyzed_projects)
        if avg_keyword_match < 50:
            recommendations.append("🎯 Overall keyword match is low - review AI suggestions to improve")
        
        return recommendations
