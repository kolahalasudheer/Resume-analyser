"""
Rule Engine - Main orchestrator for Layer 1

This is the entry point for Layer 1 analysis. It coordinates all validators,
matchers, and parsers to produce a comprehensive analysis.
"""

from datetime import datetime
from typing import Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_extractor import PDFExtractor
from ats.rule_based.keyword_matcher import KeywordMatcher
from ats.rule_based.section_parser import SectionParser
from ats.rule_based.formatting_validator import FormattingValidator
from ats.rule_based.ats_validator import ATSValidator
from ats.rule_based.scorer import Layer1Scorer


class RuleEngine:
    """
    Main orchestrator for Layer 1 (Rule-Based Engine)
    
    Coordinates all validation and analysis modules to produce
    a comprehensive resume analysis without using any LLM/API calls.
    """
    
    def __init__(self):
        """Initialize all validators and matchers"""
        print("🔧 Initializing Layer 1 (Rule Engine)...")
        
        self.keyword_matcher = KeywordMatcher()
        self.section_parser = SectionParser()
        self.formatting_validator = FormattingValidator()
        self.ats_validator = ATSValidator()
        self.scorer = Layer1Scorer()
        
        print("✅ Layer 1 Ready!")
    
    def analyze(self, resume_path: str, jd_text: str) -> Dict:
        """
        Complete Layer 1 analysis
        
        Args:
            resume_path: Path to resume PDF file
            jd_text: Job description text
            
        Returns:
            Comprehensive JSON report with all analysis results
        """
        print(f"\n📄 Analyzing resume: {os.path.basename(resume_path)}")
        print("=" * 60)
        
        # Step 1: Extract text from PDF
        print("1️⃣  Extracting text from PDF...")
        try:
            resume_text = PDFExtractor.extract_text(resume_path)
            pdf_metadata = PDFExtractor.extract_with_metadata(resume_path)
            page_count = pdf_metadata['pages']
            print(f"   ✓ Extracted {len(resume_text)} characters ({page_count} pages)")
        except Exception as e:
            print(f"   ✗ Error extracting PDF: {str(e)}")
            raise
        
        # Step 2: Parse resume sections
        print("2️⃣  Parsing resume sections...")
        tables = pdf_metadata.get('tables', [])
        sections = self.section_parser.parse_resume(resume_text, tables=tables)
        sections_found = list(sections.get('raw_sections', {}).keys())
        print(f"   ✓ Found sections: {', '.join(sections_found)}")
        if 'skills_detailed' in sections:
            tech_count = len(sections['skills_detailed'].get('tech_skills', []))
            soft_count = len(sections['skills_detailed'].get('soft_skills', []))
            print(f"   ✓ Extracted {tech_count} tech skills, {soft_count} soft skills")
        
        # Step 3: Keyword matching
        print("3️⃣  Matching keywords...")
        keyword_analysis = self.keyword_matcher.analyze(resume_text, jd_text)
        match_pct = keyword_analysis['match_results']['match_percentage']
        print(f"   ✓ Keyword Match: {match_pct}%")
        
        # Step 4: Formatting validation
        print("4️⃣  Validating formatting...")
        formatting_results = self.formatting_validator.validate_resume(resume_path)
        formatting_score = formatting_results['score']
        print(f"   ✓ Formatting Score: {formatting_score}/100")
        
        # Step 5: ATS compliance validation
        print("5️⃣  Checking ATS compliance...")
        ats_results = self.ats_validator.validate(resume_text, sections, page_count)
        ats_score = ats_results['total_score']
        print(f"   ✓ ATS Score: {ats_score}/100")
        
        # Step 6: Calculate comprehensive score
        print("6️⃣  Calculating final score...")
        score_results = self.scorer.calculate_score(
            keyword_analysis['match_results'],
            formatting_results,
            ats_results
        )
        total_score = score_results['total_score']
        grade = score_results['grade']
        print(f"   ✓ Total Score: {total_score}/100 (Grade: {grade})")
        
        # Step 7: Generate recommendations
        # Step 7: Generate recommendations
        print("7️⃣  Generating recommendations...")
        recommendations = self.scorer.generate_recommendations(
            keyword_analysis['match_results'],
            formatting_results,
            ats_results
        )
        print(f"   ✓ Generated {len(recommendations)} recommendations")
        
        print("=" * 60)
        print(f"✅ Layer 1 Analysis Complete!")
        print(f"   Final Score: {total_score}/100 ({grade})")
        print(f"   Keyword Match: {match_pct}%")
        print(f"   Formatting: {formatting_score}/100")
        print(f"   ATS Compliance: {ats_score}/100\n")
        
        # Compile final report
        return {
            'metadata': {
                'resume_file': os.path.basename(resume_path),
                'pages': page_count,
                'format': 'PDF' if resume_path.endswith('.pdf') else 'Unknown',
                'analyzed_at': datetime.now().isoformat(),
                'layer': 'Layer 1 (Rule Engine)'
            },
            'keyword_analysis': {
                'jd_keywords': keyword_analysis['jd_keywords'],
                'resume_keywords': keyword_analysis['resume_keywords'],
                'match_results': keyword_analysis['match_results']
            },
            'formatting_analysis': formatting_results,
            'ats_analysis': ats_results,
            'sections': sections,
            'score': score_results,
            'recommendations': self._format_recommendations(recommendations)
        }
    
    def _format_recommendations(self, recommendations: list) -> list:
        """Format recommendations for output"""
        formatted = []
        for rec in recommendations:
            formatted.append(f"[{rec['priority'].upper()}] {rec['category']}: {rec['message']}")
        return formatted
    
    def quick_score(self, resume_path: str, jd_text: str) -> float:
        """
        Quick score without full analysis (for batch processing)
        
        Args:
            resume_path: Path to resume PDF
            jd_text: Job description text
            
        Returns:
            Total score (0-100)
        """
        results = self.analyze(resume_path, jd_text)
        return results['score']['total_score']
