"""
Quick test to demonstrate improved PDF and skills extraction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.pdf_extractor import PDFExtractor
from utils.skills_extractor import SkillsExtractor
from layer1_engine.section_parser import SectionParser


def test_pdf_extraction(pdf_path: str):
    """Test enhanced PDF extraction"""
    print("\n" + "=" * 70)
    print("🧪 TESTING ENHANCED PDF EXTRACTION")
    print("=" * 70)
    
    if not os.path.exists(pdf_path):
        print(f"\n❌ PDF not found: {pdf_path}")
        print("\n📝 Please provide a valid resume PDF path.")
        return
    
    # Test 1: Extract with metadata
    print("\n1️⃣  Extracting PDF with metadata...")
    metadata = PDFExtractor.extract_with_metadata(pdf_path)
    
    print(f"   ✓ Pages: {metadata['pages']}")
    print(f"   ✓ Columns detected: {metadata['num_columns']}")
    print(f"   ✓ Tables found: {len(metadata['tables'])}")
    print(f"   ✓ Has images: {metadata['has_images']}")
    print(f"   ✓ Text length: {len(metadata['text'])} characters")
    
    # Show table details if any
    if metadata['tables']:
        print(f"\n   📊 Table Details:")
        for i, table in enumerate(metadata['tables'], 1):
            print(f"      • Table {i}: {table['rows']} rows × {table['cols']} cols (page {table['page']})")
    
    # Test 2: Skills extraction
    print("\n2️⃣  Parsing resume sections...")
    parser = SectionParser()
    sections = parser.parse_resume(metadata['text'], tables=metadata['tables'])
    
    print(f"   ✓ Sections found: {len(sections.get('raw_sections', {}))}")
    
    # Test 3: Show skills extraction
    if 'skills_detailed' in sections:
        skills = sections['skills_detailed']
        print("\n3️⃣  Skills Extraction Results:")
        
        tech_skills = skills.get('tech_skills', [])
        soft_skills = skills.get('soft_skills', [])
        sources = skills.get('sources', {})
        
        print(f"\n   ✅ Technical Skills ({len(tech_skills)}):")
        for skill in tech_skills[:15]:
            source = sources.get(skill, 'unknown')
            print(f"      • {skill:30} [from: {source}]")
        if len(tech_skills) > 15:
            print(f"      ... and {len(tech_skills) - 15} more")
        
        print(f"\n   ✅ Soft Skills ({len(soft_skills)}):")
        for skill in soft_skills[:10]:
            source = sources.get(skill, 'unknown')
            print(f"      • {skill:30} [from: {source}]")
        if len(soft_skills) > 10:
            print(f"      ... and {len(soft_skills) - 10} more")
        
        # Show source breakdown
        print("\n   📍 Skills by Source:")
        source_counts = {}
        for source in sources.values():
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {source:20} {count} skills")
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path - user should update this
        pdf_path = input("\n📄 Enter path to your resume PDF: ").strip().strip('"')
    
    test_pdf_extraction(pdf_path)
