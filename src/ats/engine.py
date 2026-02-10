"""
Unified ATS Engine Orchestrator
Coordinates Rule-Based and AI-Based analysis with enhanced JD understanding and project optimization.
"""

from ats.rule_based.rule_engine import RuleEngine
from ats.ai_based.llm_engine import run_llm_engine
from ats.ai_based.jd_analyzer import analyze_jd_with_ai
from ats.ai_based.project_analyzer import ProjectAnalyzer
from ats.hybrid.skill_matcher import HybridSkillMatcher
from utils.jd_parser import JDParser

# Singleton instance of RuleEngine to avoid reloading data
_RULE_ENGINE = None

def get_rule_engine():
    global _RULE_ENGINE
    if _RULE_ENGINE is None:
        _RULE_ENGINE = RuleEngine()
    return _RULE_ENGINE

def run_ats(resume_text=None, job_description=None, resume_path=None, mode="hybrid"):
    """
    Main entry point for ATS analysis with enhanced JD understanding.
    
    Args:
        resume_text: Text content of resume (optional if path provided)
        job_description: Job description text
        resume_path: Path to resume PDF (required for RuleEngine full analysis)
        mode: 'hybrid', 'rule', or 'ai'
        
    Returns:
        Dict containing scores, analysis, and enhanced JD insights.
    """
    
    # Validation
    if not job_description:
        raise ValueError("Job description is required")
    
    # Step 1: Analyze JD with AI for deep understanding
    print("🔍 Analyzing Job Description with AI...")
    ai_jd_analysis = analyze_jd_with_ai(job_description)
    
    # Step 2: Also run rule-based JD parsing for comparison
    print("📋 Running rule-based JD parsing...")
    jd_parser = JDParser()
    rule_jd_analysis = jd_parser.parse_jd(job_description)
    
    # Step 3: Hybrid skill extraction from JD
    print("🔗 Merging AI and rule-based skill extraction...")
    hybrid_matcher = HybridSkillMatcher()
    
    # Extract skills from rule-based analysis
    rule_skills_data = rule_jd_analysis.get('skills_analysis', {})
    rule_skills_formatted = {
        'required_skills': {
            'technical': [s['skill'] for s in rule_skills_data.get('required_skills', [])],
            'soft': []
        },
        'preferred_skills': {
            'technical': [s['skill'] for s in rule_skills_data.get('preferred_skills', [])],
            'soft': []
        }
    }
    
    # Merge with AI skills
    merged_jd_skills = hybrid_matcher.extract_skills_hybrid(
        job_description,
        rule_skills_formatted,
        ai_jd_analysis
    )
    
    # Prepare enriched JD context
    enriched_jd = {
        **ai_jd_analysis,
        'hybrid_skills': merged_jd_skills,
        'rule_based_insights': rule_jd_analysis
    }
        
    rule_result = None
    ai_result = None
    
    # Extract resume text if needed
    text_for_ai = resume_text
    if mode in ["ai", "hybrid"] and not text_for_ai and resume_path:
        from utils.pdf_extractor import PDFExtractor
        text_for_ai = PDFExtractor.extract_text(resume_path)

    # Step 4: Run Rule-Based Engine
    if mode in ["rule", "hybrid"]:
        if not resume_path:
            raise ValueError("Resume path required for Rule-Based analysis")
              
        engine = get_rule_engine()
        rule_result = engine.analyze(resume_path, job_description)

    # Step 5: Run AI-Based Engine
    if mode in ["ai", "hybrid"]:
        if not text_for_ai:
            raise ValueError("Resume text required for AI analysis")
            
        ai_result = run_llm_engine(text_for_ai, job_description)
    
    # Step 6: Analyze Projects (if resume text available)
    project_analysis = None
    if text_for_ai:
        print("📂 Analyzing resume projects...")
        project_analyzer = ProjectAnalyzer()
        project_analysis = project_analyzer.analyze_projects(text_for_ai, enriched_jd)

    # Step 7: Combine Results
    if mode == "rule":
        return {
            "final_score": rule_result['score']['total_score'],
            "rule_based": rule_result,
            "ai_based": None,
            "jd_analysis": enriched_jd,
            "project_analysis": project_analysis
        }

    if mode == "ai":
        return {
            "final_score": ai_result['score'],
            "rule_based": None,
            "ai_based": ai_result,
            "jd_analysis": enriched_jd,
            "project_analysis": project_analysis
        }

    # Hybrid Calculation
    # Weighted Average: 60% Rule (Proven), 40% AI (Experimental)
    
    rule_score = rule_result['score']['total_score']
    ai_score = ai_result['score']
    
    final_score = int(0.6 * rule_score + 0.4 * ai_score)
    
    return {
        "final_score": final_score,
        "rule_based": rule_result,
        "ai_based": ai_result,
        "jd_analysis": enriched_jd,
        "project_analysis": project_analysis,
        "summary": ai_result.get("summary", ""),
        "hybrid_breakdown": {
            "rule_score": rule_score,
            "ai_score": ai_score,
            "weights": "60% Rule / 40% AI"
        }
    }
