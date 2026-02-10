
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from ats.engine import run_ats
from utils.pdf_extractor import PDFExtractor

class TestHybridIntegration(unittest.TestCase):
    def setUp(self):
        self.jd_text = "Looking for a Python Developer with experience in Flask and APIs."
        self.resume_text = "I am a Python Developer. I know Flask and REST APIs."
        # Create a dummy PDF for RuleEngine validation
        self.dummy_pdf_path = "test_resume.pdf"
        with open(self.dummy_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy content")
            
        # Mock PDFExtractor to avoid actual file reading issues during simple logic tests
        # We perform a side_effect to return text for extract_text
        self.original_extract_text = PDFExtractor.extract_text
        self.original_extract_metadata = PDFExtractor.extract_with_metadata
        
        PDFExtractor.extract_text = MagicMock(return_value=self.resume_text)
        PDFExtractor.extract_with_metadata = MagicMock(return_value={
            'pages': 1, 
            'tables': [],
            'has_images': False,
            'has_tables': False,
            'fonts': [('Arial', 11)]
        })

    def tearDown(self):
        # Restore mocks
        PDFExtractor.extract_text = self.original_extract_text
        PDFExtractor.extract_with_metadata = self.original_extract_metadata
        
        if os.path.exists(self.dummy_pdf_path):
            os.remove(self.dummy_pdf_path)

    def test_rule_only_mode(self):
        print("\nTesting Rule-Only Mode...")
        result = run_ats(resume_path=self.dummy_pdf_path, job_description=self.jd_text, mode="rule")
        self.assertIsNotNone(result['rule_based'])
        self.assertIsNone(result['ai_based'])
        self.assertIn('final_score', result)
        print(f"✓ Rule-Only Score: {result['final_score']}")

    def test_ai_only_mode(self):
        print("\nTesting AI-Only Mode...")
        result = run_ats(resume_text=self.resume_text, job_description=self.jd_text, mode="ai")
        self.assertIsNone(result['rule_based'])
        self.assertIsNotNone(result['ai_based'])
        self.assertIn('final_score', result)
        print(f"✓ AI-Only Score: {result['final_score']}")

    def test_hybrid_mode(self):
        print("\nTesting Hybrid Mode...")
        result = run_ats(resume_path=self.dummy_pdf_path, job_description=self.jd_text, mode="hybrid")
        self.assertIsNotNone(result['rule_based'])
        self.assertIsNotNone(result['ai_based'])
        self.assertIn('final_score', result)
        
        # Verify weighting (60% Rule, 40% AI)
        rule_s = result['rule_based']['score']['total_score']
        ai_s = result['ai_based']['score']
        expected_final = int(0.6 * rule_s + 0.4 * ai_s)
        self.assertEqual(result['final_score'], expected_final)
        print(f"✓ Hybrid Score: {result['final_score']} (Rule: {rule_s}, AI: {ai_s})")

if __name__ == '__main__':
    unittest.main()
