"""
Layer 1 Standalone Example

Demonstrates running Layer 1 (Rule Engine) independently
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer1_engine.rule_engine import RuleEngine


def main():
    print("🎯 ATS Forge - Layer 1 Standalone Demo\n")
    
    # Initialize Layer 1
    engine = RuleEngine()
    
    # Sample job description
    jd_text = """
    Senior Software Engineer - Backend

    We are seeking an experienced Senior Software Engineer to join our growing team.
    
    Required Skills:
    - 5+ years of software development experience
    - Strong proficiency in Python and Java
    - Experience with AWS cloud services (EC2, S3, Lambda)
    - Docker and Kubernetes for containerization
    - REST API development
    - PostgreSQL or MySQL database experience
    
    Preferred Skills:
    - Experience with microservices architecture
    - CI/CD pipeline setup (Jenkins, GitHub Actions)
    - Agile/Scrum methodology
    - Team leadership experience
    
    Soft Skills:
    - Strong communication and collaboration skills
    - Problem-solving mindset
    - Ability to mentor junior developers
    """
    
    # Path to resume (you'll need to provide a real PDF)
    resume_path = "tests/sample_data/resumes/sample_resume.pdf"
    
    # Check if sample resume exists
    if not os.path.exists(resume_path):
        print(f"⚠️  Sample resume not found at: {resume_path}")
        print("   Please place a resume PDF at that location to test.\n")
        print("   For now, creating a placeholder path...")
        resume_path = "path/to/your/resume.pdf"  # Update this
    
    print(f"📄 Job Description:")
    print("-" * 60)
    print(jd_text[:200] + "...\n")
    
    print("=" * 60)
    
    try:
        # Run Layer 1 analysis
        results = engine.analyze(resume_path, jd_text)
        
        # Save results to JSON
        output_file = "layer1_analysis_report.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Full report saved to: {output_file}")
        print(f"   File size: {os.path.getsize(output_file)} bytes\n")
        
        # Display key metrics
        print("📈 Key Metrics:")
        print(f"   • Keyword Match: {results['keyword_analysis']['match_results']['match_percentage']}%")
        print(f"   • Exact Matches: {results['keyword_analysis']['match_results']['exact_matches']}")
        print(f"   • Fuzzy Matches: {results['keyword_analysis']['match_results']['fuzzy_matches']}")
        print(f"   • Missing Keywords: {results['keyword_analysis']['match_results']['total_missing']}")
        print(f"   • Formatting Score: {results['formatting_analysis']['score']}/100")
        print(f"   • ATS Score: {results['ats_analysis']['total_score']}/100")
        
        print(f"\n🎯 Final Score: {results['score']['total_score']}/100 ({results['score']['grade']})\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please update the resume_path variable with a valid PDF path.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
