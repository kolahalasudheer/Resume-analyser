"""
PDF text extraction using pdfplumber for layout-aware parsing
"""

import pdfplumber
from typing import Dict, List, Optional
import os


class PDFExtractor:
    """Extract text and metadata from PDF resumes with advanced layout awareness"""
    
    @staticmethod
    def extract_text(pdf_path: str, strategy: str = 'auto') -> str:
        """
        Extract text from PDF with smart strategy selection
        
        Args:
            pdf_path: Path to PDF file
            strategy: Extraction strategy ('auto', 'layout_aware', 'simple')
            
        Returns:
            Extracted text as string
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if strategy == 'auto':
                    # Auto-detect best strategy
                    first_page = pdf.pages[0]
                    num_columns = PDFExtractor._detect_columns(first_page)
                    strategy = 'layout_aware' if num_columns > 1 else 'simple'
                
                if strategy == 'layout_aware':
                    return PDFExtractor._extract_layout_aware(pdf)
                else:
                    return PDFExtractor._extract_simple(pdf)
                    
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def _extract_simple(pdf) -> str:
        """Simple text extraction (legacy method)"""
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return PDFExtractor._clean_text(text.strip())
    
    @staticmethod
    def _extract_layout_aware(pdf) -> str:
        """
        Layout-aware extraction that handles multi-column layouts
        by sorting text by coordinates
        """
        text = ""
        for page in pdf.pages:
            # Extract text with layout preserved
            page_text = page.extract_text(layout=True)
            if page_text:
                text += page_text + "\n"
        return PDFExtractor._clean_text(text.strip())
    
    @staticmethod
    def _detect_columns(page) -> int:
        """
        Detect number of columns in a page based on text positioning
        Returns estimated number of columns (1, 2, or 3)
        """
        try:
            chars = page.chars
            if not chars:
                return 1
            
            # Get x-coordinates of all characters
            x_coords = [char['x0'] for char in chars if 'x0' in char]
            if not x_coords:
                return 1
            
            # Simple heuristic: check for distinct clusters of x-positions
            # Group characters by x-position (with some tolerance)
            page_width = page.width
            left_third = page_width / 3
            middle_third = 2 * page_width / 3
            
            left_chars = sum(1 for x in x_coords if x < left_third)
            middle_chars = sum(1 for x in x_coords if left_third <= x < middle_third)
            right_chars = sum(1 for x in x_coords if x >= middle_third)
            
            total = len(x_coords)
            # If significant text in multiple regions, likely multi-column
            if left_chars > total * 0.3 and right_chars > total * 0.3:
                if middle_chars > total * 0.2:
                    return 3
                return 2
            
            return 1
        except:
            return 1
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted text from common PDF artifacts
        """
        import re
        
        # Fix common ligatures
        ligatures = {
            'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
            'ﬅ': 'ft', 'ﬆ': 'st'
        }
        for lig, replacement in ligatures.items():
            text = text.replace(lig, replacement)
        
        # Fix hyphenation at line breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2\n', text)
        
        # Normalize whitespace but preserve structure
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove excessive blank lines (more than 2)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Fix common Unicode issues
        text = text.replace('\u2022', '•')  # Bullet
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        text = text.replace('\u2019', "'")  # Right single quote
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        
        return text.strip()
    
    @staticmethod
    def extract_tables(pdf_path: str) -> List[Dict]:
        """
        Extract all tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of tables, each as dict with page, data, and bbox
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        all_tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        all_tables.append({
                            'page': page_num,
                            'table_index': table_idx,
                            'data': table,
                            'rows': len(table),
                            'cols': len(table[0]) if table else 0
                        })
        except Exception as e:
            raise Exception(f"Error extracting tables: {str(e)}")
        
        return all_tables
    
    @staticmethod
    def extract_with_metadata(pdf_path: str) -> Dict:
        """
        Extract text along with metadata (fonts, images, tables)
        Now includes enhanced text and table extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict with text, metadata, fonts, images, tables
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        result = {
            'text': '',
            'pages': 0,
            'has_images': False,
            'has_tables': False,
            'tables': [],
            'fonts': [],
            'metadata': {},
            'num_columns': 1
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result['pages'] = len(pdf.pages)
                result['metadata'] = pdf.metadata or {}
                
                all_fonts = set()
                
                # Detect layout on first page
                if pdf.pages:
                    result['num_columns'] = PDFExtractor._detect_columns(pdf.pages[0])
                
                # Extract text with appropriate strategy
                result['text'] = PDFExtractor.extract_text(pdf_path, strategy='auto')
                
                # Extract tables
                result['tables'] = PDFExtractor.extract_tables(pdf_path)
                result['has_tables'] = len(result['tables']) > 0
                
                # Check for images and fonts
                for page in pdf.pages:
                    if page.images:
                        result['has_images'] = True
                    
                    # Extract font information
                    if hasattr(page, 'chars'):
                        for char in page.chars:
                            if 'fontname' in char and 'size' in char:
                                all_fonts.add((char['fontname'], round(char['size'], 1)))
                
                result['fonts'] = list(all_fonts)
                
        except Exception as e:
            raise Exception(f"Error extracting metadata from PDF: {str(e)}")
        
        return result
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """
        Get number of pages in PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def check_images(pdf_path: str) -> bool:
        """
        Check if PDF contains images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if images found, False otherwise
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    if page.images:
                        return True
            return False
        except Exception as e:
            raise Exception(f"Error checking for images: {str(e)}")
    
    @staticmethod
    def check_tables(pdf_path: str) -> int:
        """
        Count tables in PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of tables found
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        table_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        table_count += len(tables)
            return table_count
        except Exception as e:
            raise Exception(f"Error checking for tables: {str(e)}")
