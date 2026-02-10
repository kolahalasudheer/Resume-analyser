"""
Quick test to verify JD parser is working
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.jd_parser import JDParser

# Sample JD
jd_text = """
Senior Software Engineer

We are seeking a Senior Software Engineer with 5+ years of experience.

Required Skills:
- Python programming (must have)
- AWS cloud services
- Docker and Kubernetes

Preferred Skills:
- FastAPI or Django
- CI/CD experience

Responsibilities:
- Design and develop backend services
- Lead technical discussions
- Mentor junior engineers
"""

parser = JDParser()
result = parser.parse_jd(jd_text)

print("=" * 60)
print("JD PARSER TEST")
print("=" * 60)
print(f"\nJob Title: {result['job_info']['job_title']}")
print(f"Seniority: {result['job_info']['seniority_level']}")
print(f"Experience: {result['job_info']['experience_required']}")
print(f"Domain: {result['domain_info']['primary_domain']}")
print(f"\nRequired Skills: {len(result['skills_analysis']['required_skills'])}")
print(f"Preferred Skills: {len(result['skills_analysis']['preferred_skills'])}")
print(f"Responsibilities: {len(result['responsibilities'])}")

print("\nTop Required Skills:")
for skill in result['skills_analysis']['required_skills'][:5]:
    print(f"  - {skill['skill']}: {skill['importance']}%")

print("\n✅ JD Parser is working!")
