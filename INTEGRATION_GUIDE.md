# 🔗 Integration Guide: Layer 1 (Rule Engine) ↔ Layer 2 (LLM Engine)

**For: Your Friend (Layer 2 Developer)**  
**From: Layer 1 Developer**

This document explains how to integrate your LLM Engine (Layer 2) with the Rule-Based Engine (Layer 1).

---

## 🎯 High-Level Overview

### Division of Responsibilities

| **Layer 1 (Rule Engine)** | **Layer 2 (LLM Engine)** |
|---------------------------|--------------------------|
| ✅ Exact keyword matching | ✅ Semantic matching ("Leadership" = "Managed team") |
| ✅ Formatting validation | ✅ STAR method validation |
| ✅ ATS compliance checks | ✅ Mission extraction from JD |
| ✅ Section parsing | ✅ Company DNA analysis |
| ✅ Rule-based scoring | ✅ Semantic scoring & rephrasing suggestions |
| **Fast, offline, zero API cost** | **Deep intelligence, context-aware** |

### Flow

```
User Input (Resume + JD)
    ↓
Master Orchestrator
    ↓
Layer 1 (Fast Analysis) → Layer 1 Results + Preprocessed Data
    ↓
Decision: Need Layer 2?
    ↓ (Yes)
Layer 2 (Deep Analysis) → Layer 2 Results
    ↓
Merge Results → Final Report
```

---

## 📦 What You'll Receive from Layer 1

### Input Format for Layer 2

When Layer 1 finishes, it will pass you a **standardized JSON object**:

```python
{
    "context": {
        "layer1_score": 65.0,  # How well Layer 1 matched
        "found_keywords": ["Python", "Git", "Leadership"],
        "missing_keywords": ["AWS", "Docker", "Communication"]
    },
    "tasks": {
        "semantic_matching": {
            "jd_text": "Cleaned job description text...",
            "resume_text": "Cleaned resume text...",
            "exact_matches_done": ["Python", "Git"]  # Don't re-check these
        },
        "mission_extraction": {
            "jd_text": "Cleaned job description text..."
        },
        "star_validation": {
            "bullets": [
                "Developed REST API using Python",
                "Led team of 5 developers",
                ...
            ]
        },
        "rephrasing": {
            "missing_skills": ["AWS", "Docker"],
            "current_bullets": [...]
        }
    },
    "preprocessed_data": {
        "resume_text_clean": "...",
        "jd_text_clean": "...",
        "resume_sections": {
            "experience": [...],
            "education": [...],
            "skills": [...]
        },
        "bullets_for_star_check": [...]
    }
}
```

---

## 📤 What Layer 1 Expects from You

### Output Format from Layer 2

Return a JSON object with these fields:

```python
{
    "mission": "The company is scaling their cloud infrastructure and needs...",
    
    "semantic_matches": [
        {
            "keyword": "AWS",
            "found": false,
            "source": "semantic",
            "confidence": 0.0
        },
        {
            "keyword": "Leadership",
            "found": true,  # Found "Led team of 5"
            "source": "semantic",
            "confidence": 0.92,
            "context": "Led team of 5 developers in building REST API"
        }
    ],
    
    "star_validation": {
        "strong_bullets": [
            "Led team of 5 developers to build REST API, reducing latency by 40%"
        ],
        "weak_bullets": [
            "Developed REST API using Python"  # Missing impact/result
        ],
        "star_score": 70.0  # 0-100
    },
    
    "rephrasing_suggestions": [
        "Add AWS experience: 'Deployed Python applications on AWS EC2 using Docker'",
        "Strengthen bullet: 'Developed REST API using Python' → 'Architected scalable REST API using Python and FastAPI, serving 10K+ requests/day'"
    ],
    
    "company_dna": "Startup culture, values innovation and ownership",
    
    "implicit_needs": [
        "Ability to work independently",
        "Startup experience",
        "Scale systems"
    ],
    
    "semantic_score": 75.0  # Your overall score (0-100)
}
```

---

## 🏗️ How to Integrate

### Step 1: Implement Your LLM Engine

Create `src/layer2_engine/llm_engine.py`:

```python
from typing import Dict
import google.generativeai as genai

class LLMEngine:
    """
    Layer 2: LLM-powered semantic analysis
    
    This is YOUR implementation. Use Gemini 1.5 Pro or your chosen LLM.
    """
    
    def __init__(self):
        """Initialize Gemini API"""
        # Load your API key
        genai.configure(api_key="YOUR_API_KEY")
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def analyze(self, layer1_output: Dict) -> Dict:
        """
        Main entry point - receives Layer 1 output, returns Layer 2 output
        
        Args:
            layer1_output: Standardized input from Layer 1
        
        Returns:
            dict with semantic_matches, mission, star_validation, etc.
        """
        tasks = layer1_output['tasks']
        context = layer1_output['context']
        
        # Run your LLM analysis
        mission = self._extract_mission(tasks['mission_extraction']['jd_text'])
        semantic_matches = self._semantic_matching(
            tasks['semantic_matching']['jd_text'],
            tasks['semantic_matching']['resume_text'],
            context['missing_keywords']
        )
        star_validation = self._validate_star(tasks['star_validation']['bullets'])
        suggestions = self._generate_suggestions(
            tasks['rephrasing']['missing_skills'],
            tasks['rephrasing']['current_bullets']
        )
        
        return {
            "mission": mission,
            "semantic_matches": semantic_matches,
            "star_validation": star_validation,
            "rephrasing_suggestions": suggestions,
            "company_dna": "...",  # Your extraction
            "implicit_needs": [...],
            "semantic_score": self._calculate_score(semantic_matches, star_validation)
        }
    
    def _extract_mission(self, jd_text: str) -> str:
        """Use LLM to extract company mission from JD"""
        prompt = f"""
        Analyze this job description and extract the company's mission:
        Why are they hiring? What problem are they solving?
        
        JD: {jd_text}
        
        Return a 1-2 sentence mission statement.
        """
        response = self.model.generate_content(prompt)
        return response.text
    
    def _semantic_matching(self, jd_text: str, resume_text: str, missing_keywords: list) -> list:
        """Find semantic matches that Layer 1 missed"""
        # Your LLM prompt for semantic matching
        pass
    
    def _validate_star(self, bullets: list) -> dict:
        """Check if bullets follow STAR method"""
        # Your LLM prompt for STAR validation
        pass
    
    def _generate_suggestions(self, missing_skills: list, current_bullets: list) -> list:
        """Generate rephrasing suggestions"""
        # Your LLM prompt for suggestions
        pass
    
    def _calculate_score(self, matches: list, star: dict) -> float:
        """Calculate Layer 2 semantic score"""
        # Your scoring logic
        pass
```

---

### Step 2: Test Standalone

You can test Layer 2 independently:

```python
# examples/layer2_standalone.py

from src.layer2_engine.llm_engine import LLMEngine
import json

# Mock Layer 1 output for testing
mock_layer1_output = {
    "context": {...},
    "tasks": {...},
    "preprocessed_data": {...}
}

llm_engine = LLMEngine()
results = llm_engine.analyze(mock_layer1_output)

print(json.dumps(results, indent=2))
```

---

### Step 3: Integration Testing

Once both layers are ready, test together:

```python
# examples/integration_test.py

from src.orchestrator.ats_forge import ATSForgeOrchestrator

orchestrator = ATSForgeOrchestrator(use_layer2=True)
results = orchestrator.analyze("resume.pdf", "job description text")

print(f"Layer 1 Score: {results['layer1_results']['score']['total_score']}")
print(f"Layer 2 Score: {results['layer2_results']['semantic_score']}")
print(f"Final Score: {results['combined_score']}")
```

---

## 🔑 Key Integration Points

### 1. Shared Models

Use the common data models in `src/shared/models.py`:

```python
from shared.models import KeywordMatch, Layer2Output

# Create your semantic matches
match = KeywordMatch(
    keyword="Leadership",
    found=True,
    source="semantic",
    confidence=0.92,
    context="Led team of 5 developers"
)
```

### 2. Orchestrator Handles Everything

You **don't** need to worry about:
- ❌ When to run (orchestrator decides)
- ❌ Merging results (orchestrator does it)
- ❌ Final scoring (orchestrator calculates)

You **only** focus on:
- ✅ Receiving standardized input
- ✅ Running LLM analysis
- ✅ Returning standardized output

### 3. Graceful Degradation

If Layer 2 is not available, the system works with Layer 1 only:

```python
# Layer 2 not installed? No problem!
orchestrator = ATSForgeOrchestrator(use_layer2=False)
results = orchestrator.analyze(resume, jd)  # Still works!
```

---

## 📊 Final Score Calculation

The orchestrator merges scores like this:

```python
# If Layer 2 is used:
final_score = (layer1_score × 0.4) + (layer2_semantic_score × 0.6)

# Layer 2 has MORE weight because semantic matching is more valuable
```

---

## 🛠️ Recommended Prompts for Layer 2

### Mission Extraction

```python
prompt = """
You are an expert HR analyst. Analyze this job description and extract:
1. The company's MISSION for this hire (why are they hiring?)
2. The COMPANY DNA (culture, values, work style)
3. IMPLICIT NEEDS (skills not explicitly stated but implied)

Output strictly in JSON format:
{
  "mission": "...",
  "company_dna": "...",
  "implicit_needs": [...]
}

JD: {jd_text}
"""
```

### Semantic Matching

```python
prompt = """
Check if the resume contains SEMANTIC equivalents of these missing skills:
Missing: {missing_keywords}

Resume: {resume_text}

For each missing skill, determine if there's a semantic match.
Example: "AWS" might match "deployed on cloud infrastructure"

Output JSON:
[
  {{"keyword": "AWS", "found": true, "confidence": 0.85, "context": "..."}}
]
"""
```

### STAR Validation

```python
prompt = """
Analyze these resume bullets for STAR method (Situation-Task-Action-Result):
{bullets}

Rate each bullet:
- STRONG: Has clear action AND measurable result
- WEAK: Only describes task without impact

Output JSON:
{
  "strong_bullets": [...],
  "weak_bullets": [...],
  "star_score": 0-100
}
"""
```

---

## 🤝 Communication Protocol

### Option 1: In-Memory (Recommended)

```python
layer1_output = layer1.analyze(resume, jd)
layer2_output = layer2.analyze(layer1_output)
```

### Option 2: File-Based (For Debugging)

```python
# Layer 1 saves output
with open("temp/layer1_output.json", "w") as f:
    json.dump(layer1_output, f)

# Layer 2 reads input
with open("temp/layer1_output.json", "r") as f:
    layer1_data = json.load(f)

layer2_output = layer2.analyze(layer1_data)
```

---

## ✅ Testing Checklist

Before integration:

- [ ] Your `LLMEngine` class exists in `src/layer2_engine/llm_engine.py`
- [ ] It has an `__init__()` method
- [ ] It has an `analyze(layer1_output: dict) -> dict` method
- [ ] It returns all required fields (mission, semantic_matches, etc.)
- [ ] You can run it standalone with mock data
- [ ] Orchestrator can import it without errors

---

## 🚀 Next Steps

1. **Review the implementation plan** (see `implementation_plan.md`)
2. **Check the shared models** in `src/shared/models.py` (will be created)
3. **Run the integration demo** to see expected flow
4. **Build your LLM Engine** following the interface contract
5. **Test together** using the orchestrator

---

## 💬 Questions?

If anything is unclear about the integration:
1. Check `examples/integration_demo.py` for a working example
2. Review the orchestrator code in `src/orchestrator/ats_forge.py`
3. Look at the shared models in `src/shared/models.py`

**The key principle**: Layer 1 does the heavy lifting (parsing, formatting, exact matches), 
and Layer 2 adds intelligence (semantic matching, mission extraction, STAR validation).

Together, we build the smartest ATS tool! 🎯
