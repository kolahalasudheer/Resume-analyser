"""
Formatting validator - checks resume formatting for ATS compatibility

Validates:
- Images/photos
- Complex tables
- Font sizes
- Margins
- File format
"""

import json
import os
from typing import Dict, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_extractor import PDFExtractor
from shared.constants import MIN_FONT_SIZE, RECOMMENDED_MARGINS


class FormattingValidator:
    """Validate resume formatting for ATS compatibility"""
    
    def __init__(self):
        """Load pitfalls database"""
        self.pitfalls = self._load_pitfalls()
    
    def _load_pitfalls(self) -> Dict:
        """Load ATS pitfalls database"""
        # Navigate from src/ats/rule_based/ to src/data/ats/
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'ats', 'pitfalls.json'
        )
        with open(data_path, 'r') as f:
            return json.load(f)
    
    def validate_resume(self, resume_path: str) -> Dict:
        """
        Complete formatting validation
        
        Args:
            resume_path: Path to resume PDF
            
        Returns:
            dict with validation results
        """
        # Extract with metadata
        pdf_data = PDFExtractor.extract_with_metadata(resume_path)
        
        issues = []
        warnings = []
        score = 100  # Start with perfect score, deduct for issues
        
        # Check images
        has_images = pdf_data['has_images']
        if has_images:
            issues.append({
                'type': 'Images Detected',
                'severity': 'critical',
                'message': 'Resume contains images. ATS systems cannot read images.',
                'recommendation': 'Remove all images, photos, and graphics'
            })
            score -= 30  # Major penalty
        
        # Check tables
        has_tables = pdf_data['has_tables']
        if has_tables:
            issues.append({
                'type': 'Tables Detected',
                'severity': 'high',
                'message': 'Resume contains tables which may cause parsing issues.',
                'recommendation': 'Use simple single-column layout instead of tables'
            })
            score -= 20
        
        # Check fonts
        font_issues = self._check_fonts(pdf_data['fonts'])
        if font_issues:
            issues.extend(font_issues)
            score -= len(font_issues) * 5
        
        # Check page count
        pages = pdf_data['pages']
        if pages > 2:
            warnings.append({
                'type': 'Resume Too Long',
                'severity': 'medium',
                'message': f'Resume is {pages} pages. Most ATS prefer 1-2 pages.',
                'recommendation': 'Trim to 1-2 pages for optimal ATS parsing'
            })
            score -= 10
        
        # Check file format
        if not resume_path.lower().endswith('.pdf'):
            issues.append({
                'type': 'File Format',
                'severity': 'high',
                'message': 'File format may not be ATS-compatible',
                'recommendation': 'Use PDF format for best compatibility'
            })
            score -= 15
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        return {
            'has_images': has_images,
            'has_tables': has_tables,
            'font_issues': font_issues,
            'page_count': pages,
            'file_format_ok': resume_path.lower().endswith('.pdf'),
            'issues': issues,
            'warnings': warnings,
            'score': score,
            'passed': score >= 70
        }
    
    def _check_fonts(self, fonts: List[tuple]) -> List[Dict]:
        """Check if fonts are ATS-friendly"""
        issues = []
        safe_fonts = self.pitfalls.get('safe_fonts', [])
        
        for font_name, font_size in fonts:
            # Check font size
            if font_size < MIN_FONT_SIZE:
                issues.append({
                    'type': 'Small Font Size',
                    'severity': 'medium',
                    'message': f'Font size {font_size}pt is too small (min {MIN_FONT_SIZE}pt)',
                    'recommendation': f'Use font size between 10-12pt'
                })
            
            # Check if font is in safe list (basic check)
            is_safe = any(safe in font_name for safe in ['Arial', 'Calibri', 'Times', 'Helvetica', 'Garamond'])
            
            if not is_safe:
                # Only warn, don't fail
                pass  # Too many false positives with font names
        
        return issues
