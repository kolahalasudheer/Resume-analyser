"""
Test Layer 1 with your real resume and job description
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from layer1_engine.rule_engine import RuleEngine


def main():
    print("=" * 70)
    print("🎯 ATS Forge - Layer 1 Analysis")
    print("=" * 70)
    
    # =================================================================
    # STEP 1: UPDATE THIS PATH TO YOUR RESUME PDF
    # =================================================================
    resume_path = r"C:\Users\sudhe\Desktop\path\to\your\resume.pdf"
    
    # Check if file exists
    if not os.path.exists(resume_path):
        print(f"\n❌ ERROR: Resume not found at: {resume_path}")
        print("\n📝 Please update line 21 in this file with your actual resume path.")
        print("   Example: resume_path = r'C:\\Users\\sudhe\\Desktop\\MyResume.pdf'")
        return
    
    # =================================================================
    # STEP 2: PASTE YOUR JOB DESCRIPTION HERE
    # =================================================================
    jd_text = """
Senior Software Engineer

We are seeking a Senior Software Engineer with 5+ years of experience.

Required Skills:
- Python programming
- AWS cloud services (EC2, S3, Lambda)
- Docker and Kubernetes
- PostgreSQL or MySQL
- REST API development
- Git version control

Preferred Skills:
- FastAPI or Django framework
- CI/CD pipeline experience
- Microservices architecture
- Team leadership

Responsibilities:
- Design and develop backend services
- Lead technical discussions
- Mentor junior engineers
- Collaborate with product team

Soft Skills:
- Strong communication skills
- Problem-solving mindset
- Team player
- Ownership and accountability
"""
    
    print(f"\n📄 Resume: {os.path.basename(resume_path)}")
    print(f"📋 Job Description: {len(jd_text)} characters")
    print("\n" + "=" * 70)
    
    # Initialize and run analysis
    engine = RuleEngine()
    
    try:
        # Run analysis
        results = engine.analyze(resume_path, jd_text)
        
        # Save to JSON
        output_file = "analysis_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full report saved to: {output_file}")
        
        # Display summary
        print("\n" + "=" * 70)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 70)
        
        score = results['score']
        kw_match = results['keyword_analysis']['match_results']
        
        print(f"\n🎯 FINAL SCORE: {score['total_score']}/100 (Grade: {score['grade']})")
        print(f"\n📈 Score Breakdown:")
        print(f"   • Keyword Match:   {score['keyword_score']}/100")
        print(f"   • Formatting:      {score['formatting_score']}/100")
        print(f"   • ATS Compliance:  {score['ats_score']}/100")
        
        print(f"\n🔍 Keyword Analysis:")
        print(f"   • Match Percentage: {kw_match['match_percentage']}%")
        print(f"   • Found: {kw_match['total_found']} keywords")
        print(f"   • Missing: {kw_match['total_missing']} keywords")
        print(f"   • Exact matches: {kw_match['exact_matches']}")
        print(f"   • Fuzzy matches: {kw_match['fuzzy_matches']}")
        
        # Show found keywords
        found_tech = kw_match['found_keywords']['tech_skills']
        found_soft = kw_match['found_keywords']['soft_skills']
        
        if found_tech:
            print(f"\n✅ Found Technical Skills ({len(found_tech)}):")
            for skill in found_tech[:10]:  # Show first 10
                print(f"   • {skill}")
            if len(found_tech) > 10:
                print(f"   ... and {len(found_tech) - 10} more")
        
        if found_soft:
            print(f"\n✅ Found Soft Skills ({len(found_soft)}):")
            for skill in found_soft[:5]:
                print(f"   • {skill}")
        
        # Show missing keywords
        missing_tech = kw_match['missing_keywords']['tech_skills']
        missing_soft = kw_match['missing_keywords']['soft_skills']
        
        if missing_tech:
            print(f"\n❌ Missing Technical Skills ({len(missing_tech)}):")
            for skill in missing_tech[:10]:  # Show first 10
                print(f"   • {skill}")
            if len(missing_tech) > 10:
                print(f"   ... and {len(missing_tech) - 10} more")
        
        if missing_soft:
            print(f"\n❌ Missing Soft Skills ({len(missing_soft)}):")
            for skill in missing_soft[:5]:
                print(f"   • {skill}")
        
        # Show recommendations
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(results['recommendations'][:8], 1):
            print(f"   {i}. {rec}")
        
        # Strengths and weaknesses
        breakdown = score['breakdown']
        if breakdown['strengths']:
            print(f"\n💪 Strengths:")
            for strength in breakdown['strengths']:
                print(f"   • {strength}")
        
        if breakdown['weaknesses']:
            print(f"\n⚠️  Areas to Improve:")
            for weakness in breakdown['weaknesses']:
                print(f"   • {weakness}")
        
        print("\n" + "=" * 70)
        print(f"✅ Analysis complete! Check '{output_file}' for full details.")
        print("=" * 70 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Resume file not found")
        print(f"   Please check the path: {resume_path}")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
