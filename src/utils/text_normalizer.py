"""
Text preprocessing and normalization utilities
"""

import re
from typing import List, Set
import string


class TextNormalizer:
    """Text cleaning and normalization utilities"""
    
    # Common stopwords to remove (basic list)
    STOPWORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with'
    }
    
    @staticmethod
    def normalize(text: str, lowercase: bool = True, remove_punctuation: bool = False) -> str:
        """
        Normalize text by cleaning and standardizing
        
        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_punctuation: Remove punctuation marks
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep useful ones
        text = re.sub(r'[^\w\s\-\.\,\;\:\(\)\[\]\/\+\#]', '', text)
        
        if lowercase:
            text = text.lower()
        
        if remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Normalize whitespace again
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def remove_stopwords(text: str) -> str:
        """
        Remove common stopwords from text
        
        Args:
            text: Input text
            
        Returns:
            Text without stopwords
        """
        words = text.lower().split()
        filtered_words = [w for w in words if w not in TextNormalizer.STOPWORDS]
        return ' '.join(filtered_words)
    
    @staticmethod
    def extract_ngrams(text: str, n: int = 2) -> List[str]:
        """
        Extract n-grams for phrase matching
        
        Args:
            text: Input text
            n: Size of n-grams (2 for bigrams, 3 for trigrams)
            
        Returns:
            List of n-grams
        """
        words = text.split()
        ngrams = []
        
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    @staticmethod
    def extract_email(text: str) -> str:
        """
        Extract email address from text
        
        Args:
            text: Input text
            
        Returns:
            Email address if found, empty string otherwise
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else ""
    
    @staticmethod
    def extract_phone(text: str) -> str:
        """
        Extract phone number from text
        
        Args:
            text: Input text
            
        Returns:
            Phone number if found, empty string otherwise
        """
        # Match various phone formats
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-234-567-8900
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (234) 567-8900
            r'\d{10}'  # 2345678900
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return ""
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        Extract URLs from text (LinkedIn, GitHub, portfolio)
        
        Args:
            text: Input text
            
        Returns:
            List of URLs found
        """
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    @staticmethod
    def clean_for_keyword_matching(text: str) -> str:
        """
        Clean text specifically for keyword matching
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text ready for keyword matching
        """
        # Lowercase
        text = text.lower()
        
        # Replace common separators with spaces
        text = re.sub(r'[/\-_]', ' ', text)
        
        # Remove extra punctuation but keep periods for abbreviations
        text = re.sub(r'[^\w\s\.]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Simple tokenization into words
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    @staticmethod
    def extract_bullet_points(text: str) -> List[str]:
        """
        Extract bullet points from text
        
        Args:
            text: Input text
            
        Returns:
            List of bullet points
        """
        # Match common bullet point patterns
        bullet_patterns = [
            r'[•●○■□▪▫–—]\s*(.+)',  # Unicode bullets
            r'[\*\-]\s+(.+)',         # * or - bullets
            r'^\d+\.\s+(.+)',         # Numbered lists
        ]
        
        bullets = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    bullets.append(match.group(1).strip())
                    break
        
        return bullets
