"""
AI-Powered Job Description Analyzer
Uses Gemini to deeply understand job requirements, qualifications, and expectations.
"""

import os
import json
import logging
import re
from typing import Dict, List
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_jd_with_ai(job_description: str) -> Dict:
    """
    Deeply analyze job description using AI to extract:
    - Job summary and company expectations
    - Job type and seniority
    - Key responsibilities
    - Required vs preferred qualifications
    - Required vs preferred skills (technical and soft)
    
    Args:
        job_description: Raw JD text
        
    Returns:
        dict: Comprehensive JD analysis
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Using rule-based fallback.")
        return _fallback_analysis(job_description)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        You are an expert HR analyst and job description parser. Analyze the following job description deeply and extract comprehensive information.
        
        Job Description:
        {job_description[:6000]}
        
        Provide the output strictly in the following JSON format ONLY:
        {{
            "job_summary": "A 2-3 sentence summary explaining what the company wants from the candidate and what they'll do post-hire",
            "job_type": "Full-time/Part-time/Contract/Remote/Hybrid/On-site",
            "seniority_level": "Intern/Junior/Mid/Senior/Lead/Manager",
            "company_expectations": "What the company expects the candidate to achieve in this role",
            "key_responsibilities": [
                "Responsibility 1",
                "Responsibility 2",
                "..."
            ],
            "required_qualifications": [
                "Qualification 1",
                "Qualification 2",
                "..."
            ],
            "preferred_qualifications": [
                "Qualification 1",
                "..."
            ],
            "required_skills": {{
                "technical": ["skill1", "skill2", "..."],
                "soft": ["skill1", "skill2", "..."]
            }},
            "preferred_skills": {{
                "technical": ["skill1", "..."],
                "soft": ["skill1", "..."]
            }},
            "experience_required": "X years or Not specified",
            "education_required": "Degree requirement or Not specified"
        }}
        
        IMPORTANT:
        - Be thorough and extract ALL skills mentioned
        - Distinguish clearly between required and preferred
        - Make the job_summary user-friendly and insightful
        - Include both explicit and implicit requirements
        """

        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Extract JSON using regex
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            result = json.loads(json_str)
            logger.info("AI JD analysis successful")
            
            # Track API usage
            try:
                from utils.api_usage_tracker import APIUsageTracker
                tracker = APIUsageTracker()
                tracker.increment_usage(tokens_estimate=2000)  # JD analysis uses ~2000 tokens
            except:
                pass  # Don't fail if tracker unavailable
            
            return result
        else:
            logger.warning("Failed to parse AI response, using fallback")
            return _fallback_analysis(job_description)

    except Exception as e:
        logger.error(f"Gemini API Error in JD analysis: {str(e)}")
        return _fallback_analysis(job_description)

def _fallback_analysis(job_description: str) -> Dict:
    """
    Fallback rule-based analysis when AI is unavailable
    """
    logger.info("Using rule-based JD analysis fallback")
    
    # Import existing parser
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from utils.jd_parser import JDParser
    
    parser = JDParser()
    parsed = parser.parse_jd(job_description)
    
    # Convert to AI format
    job_info = parsed.get('job_info', {})
    skills_analysis = parsed.get('skills_analysis', {})
    responsibilities = parsed.get('responsibilities', [])
    
    # Extract skills from parsed data
    required_tech = []
    required_soft = []
    preferred_tech = []
    preferred_soft = []
    
    for skill_info in skills_analysis.get('required_skills', []):
        skill = skill_info['skill']
        # Simple heuristic: check if it's in tech or soft skills
        if any(char.isupper() for char in skill) or any(tech_word in skill.lower() for tech_word in ['python', 'java', 'sql', 'aws', 'react']):
            required_tech.append(skill)
        else:
            required_soft.append(skill)
    
    for skill_info in skills_analysis.get('preferred_skills', []):
        skill = skill_info['skill']
        if any(char.isupper() for char in skill) or any(tech_word in skill.lower() for tech_word in ['python', 'java', 'sql', 'aws', 'react']):
            preferred_tech.append(skill)
        else:
            preferred_soft.append(skill)
    
    return {
        "job_summary": f"This is a {job_info.get('seniority_level', 'mid-level')} position requiring {job_info.get('experience_required', 'relevant')} experience. (AI analysis unavailable - using rule-based parsing)",
        "job_type": "Not specified",
        "seniority_level": job_info.get('seniority_level', 'Mid').title(),
        "company_expectations": "The company expects the candidate to fulfill the listed responsibilities and contribute to team goals.",
        "key_responsibilities": responsibilities,
        "required_qualifications": ["See job description for details"],
        "preferred_qualifications": [],
        "required_skills": {
            "technical": required_tech[:10],
            "soft": required_soft[:5]
        },
        "preferred_skills": {
            "technical": preferred_tech[:5],
            "soft": preferred_soft[:3]
        },
        "experience_required": job_info.get('experience_required', 'Not specified'),
        "education_required": "Not specified"
    }
