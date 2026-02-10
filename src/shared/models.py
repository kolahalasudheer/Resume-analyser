"""
Shared data models used by both Layer 1 and Layer 2

These models ensure consistent data exchange between layers.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class KeywordMatch:
    """Represents a matched keyword with metadata"""
    keyword: str
    found: bool
    source: str  # "exact"
    confidence: float  # 1.0 for exact
    context: Optional[str] = None  # Where it was found in resume
