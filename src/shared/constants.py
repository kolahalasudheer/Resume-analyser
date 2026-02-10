"""
Shared constants used across the application
"""

# Scoring weights
SCORING_WEIGHTS = {
    'keyword_match': 0.5,
    'formatting': 0.25,
    'ats_compliance': 0.25
}

# Fuzzy match threshold
FUZZY_MATCH_THRESHOLD = 0.85

# Resume length (pages)
OPTIMAL_RESUME_LENGTH = {
    'min': 1,
    'max': 2
}

# Font size (points)
MIN_FONT_SIZE = 10

# Margins (inches)
RECOMMENDED_MARGINS = {
    'min': 0.5,
    'max': 1.0
}

# Grade thresholds
GRADE_THRESHOLDS = {
    'A+': 95,
    'A': 90,
    'B+': 85,
    'B': 80,
    'C': 70,
    'D': 60,
    'F': 0
}
