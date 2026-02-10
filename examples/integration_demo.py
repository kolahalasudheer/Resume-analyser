"""
Integration Demo: Shows how Layer 1 and Layer 2 work together

This is a reference implementation for your friend to understand
how to integrate their LLM Engine with your Rule Engine.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator.ats_forge import ATSForgeOrchestrator


def main():
    print("🚀 ATS Forge - Complete Analysis Demo (Layer 1 + Layer 2)\n")
    
    # Initialize orchestrator (will use Layer 2 if available)
    orchestrator = ATSForgeOrchestrator(use_layer2=True)
    
    # Sample job description
    jd_text = """
    Senior Python Developer

    We are seeking a Senior Python Developer with 5+ years experience
    to join our fast-growing startup.
    
    Must have:
    - Expert-level Python programming
    - AWS cloud services (EC2, S3, Lambda)
    - Docker and container orchestration
    - REST API development
    - PostgreSQL database experience
    
    Nice to have:
    - Machine Learning experience
    - FastAPI or Django framework
    - CI/CD pipeline experience
    
    You will:
    - Lead development of our core platform
    - Mentor junior developers
    - Architect scalable solutions
    - Work closely with product team
    
    We value:
    - Strong communication skills
    - Ownership and accountability
    - Innovation and creative problem-solving
    """
    
    # Path to resume
    resume_path = "tests/sample_data/resumes/sample_resume.pdf"
    
    if not os.path.exists(resume_path):
        print(f"⚠️  Sample resume not found.")
        print("   Please provide a resume PDF path to test.\n")
        return
    
    print(f"📄 Analyzing resume against job description...")
    print("=" * 60)
    
    try:
        # Run complete analysis (Layer 1 + Layer 2)
        results = orchestrator.analyze(resume_path, jd_text)
        
        # Save results
        output_file = "complete_analysis_report.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Full report saved to: {output_file}\n")
        
        # Show what data Layer 2 would receive
        print("=" * 60)
        print("📦 Data Passed to Layer 2:")
        print("=" * 60)
        
        preprocessed = results['layer1_results']['preprocessed_data']
        print(f"\n✓ Resume text (cleaned): {len(preprocessed['resume_text_clean'])} characters")
        print(f"✓ JD text (cleaned): {len(preprocessed['jd_text_clean'])} characters")
        print(f"✓ Found keywords: {len(preprocessed['found_keywords'].get('all', []))}")
        print(f"✓ Missing keywords: {len(preprocessed['missing_keywords'].get('all', []))}")
        print(f"✓ Bullets for STAR check: {len(preprocessed['bullets_for_star_check'])}")
        
        triggers = results['layer1_results']['layer2_triggers']
        print(f"\n📋 Layer 2 Tasks:")
        print(f"   • Semantic Matching: {'✓' if triggers['need_semantic_match'] else '✗'}")
        print(f"   • Mission Extraction: {'✓' if triggers['need_mission_extraction'] else '✗'}")
        print(f"   • STAR Validation: {'✓' if triggers['need_star_validation'] else '✗'}")
        print(f"   • Rephrasing Suggestions: {'✓' if triggers['need_rephrasing_suggestions'] else '✗'}")
        
        print("\n" + "=" * 60)
        print("✅ Demo complete! Check the JSON files for full details.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
