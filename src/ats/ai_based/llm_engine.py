"""
LLM Engine for Hybrid ATS Resume Analyzer
Uses Google Gemini API for intelligent analysis.
"""

import os
import json
import logging
import random
from typing import Dict, List
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_llm_engine(resume_text: str, job_description: str) -> Dict:
    """
    Evaluate resume against JD using Google Gemini API.
    Falls back to mock logic if API key is missing or call fails.
    
    Args:
        resume_text: Cleaned resume text
        job_description: Job description text
        
    Returns:
        dict: {
            "score": int,
            "summary": str,
            "strengths": list,
            "weaknesses": list
        }
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Using mock fallback.")
        return _mock_analysis(resume_text, job_description)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) reviewer. 
        Evaluate the following resume against the provided job description.
        
        Job Description:
        {job_description[:2000]}... (truncated for efficiency)
        
        Resume Text:
        {resume_text[:4000]}... (truncated for efficiency)
        
        Provide the output strictly in the following JSON format ONLY:
        {{
            "score": <int 0-100>,
            "summary": "<concise summary of fit logic>",
            "strengths": ["<strength 1>", "<strength 2>", ...],
            "weaknesses": ["<weakness 1>", "<weakness 2>", ...]
        }}
        """

        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Use regex to find JSON block
        import re
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if match:
             json_str = match.group(0)
             result = json.loads(json_str)
             
             # Track API usage
             try:
                 from utils.api_usage_tracker import APIUsageTracker
                 tracker = APIUsageTracker()
                 tracker.increment_usage(tokens_estimate=1500)  # Resume analysis uses ~1500 tokens
             except:
                 pass  # Don't fail if tracker unavailable
             
             return result
        else:
             # Try parsing the whole text if no braces found (unlikely but possible)
             return json.loads(text_response)

    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        return _mock_analysis(resume_text, job_description)

def _mock_analysis(resume_text, job_description):
    """Fallback mock logic"""
    base_score = 60
    if len(resume_text) > 500: base_score += 10
    if len(job_description) > 500: base_score += 10
    
    return {
        "score": min(100, max(0, base_score + random.randint(-5, 15))),
        "summary": "AI Analysis (Mock): API unavailable. Resume length suggests moderate fit.",
        "strengths": ["Structure detected (Mock)", "Content present (Mock)"],
        "weaknesses": ["Cannot verify keywords (Mock)", "API Key missing"]
    }
