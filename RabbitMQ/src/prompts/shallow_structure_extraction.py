"""
Shallow Structure Extraction Prompt (LLM Call 1)

This prompt extracts Level 0 (domain) and Level 1 (categories) with FULL content,
plus POSITIONS for evidence (not content).
"""

SHALLOW_STRUCTURE_SYSTEM_MESSAGE = """You are a knowledge extraction specialist optimized for position-based evidence extraction.

CRITICAL RULES:
1. Return POSITIONS (paragraph indices), NOT content text
2. Level 0 and Level 1 must have FULL synthesis (not generic)
3. Evidence positions are RANGES: [[start_para, end_para]]
4. Claims/Questions are SINGLE POSITIONS: [para_idx]
5. Must return 2-3 Level 1 nodes minimum

OUTPUT: Always return valid JSON matching the schema exactly."""


SHALLOW_STRUCTURE_PROMPT_TEMPLATE = """CRITICAL TASK: Extract shallow hierarchical structure (Level 0 + Level 1) with POSITION-BASED evidence.

DOCUMENT: {file_name}
LANGUAGE: {lang}
PARAGRAPH COUNT: {paragraph_count}

CONTENT (first 6000 chars for context):
---
{content}
---

TASK:
Extract a 2-LEVEL structure with POSITIONS for evidence:
- Level 0: Domain (root) - FULL synthesis required
- Level 1: Categories (2-3 major themes) - FULL synthesis required
- Evidence: POSITIONS ONLY (not content)

POSITION-BASED EXTRACTION RULES:
1. **Evidence Positions** = RANGES of paragraph indices
   - Format: [[start_idx, end_idx], [start_idx, end_idx]]
   - Example: [[0, 5], [12, 18]] means paragraphs 0-5 and 12-18
   - DO NOT include actual text content

2. **Key Claims Positions** = SINGLE paragraph indices
   - Format: [para_idx1, para_idx2, para_idx3]
   - Example: [3, 7, 15] means paragraphs 3, 7, and 15
   - DO NOT include claim text

3. **Questions Positions** = SINGLE paragraph indices
   - Format: [para_idx1, para_idx2]
   - Example: [5, 12] means paragraphs 5 and 12
   - DO NOT include question text

SYNTHESIS GUIDELINES (Character Limits):
- Domain (Level 0): 150-200 chars - Comprehensive overview of document's entire scope
- Category (Level 1): 100-150 chars - Specific description of this major theme

STRUCTURAL RULES:
✓ Exactly 1 domain (Level 0)
✓ Minimum 2 categories (Level 1), maximum 3
✓ Each category must have evidence positions
✓ Each category should have 3-5 key claims positions
✓ Each category should have 2-4 questions positions
✓ Positions must be within range [0, {paragraph_count_minus_1}]

OUTPUT FORMAT (strict JSON):
{{
  "document_overview": {{
    "title": "Document Title (extracted or inferred)",
    "main_domain": "Primary Research Domain",
    "summary": "200-300 character comprehensive summary"
  }},
  "hierarchy": {{
    "level_0": {{
      "name": "Specific Domain Name (not generic)",
      "synthesis": "Comprehensive domain description (150-200 chars) - must be SPECIFIC to this document",
      "evidence_positions": [[0, 50]]
    }},
    "level_1_nodes": [
      {{
        "name": "First Category Name",
        "synthesis": "Detailed category description (100-150 chars) - must be SPECIFIC",
        "evidence_positions": [[12, 25], [30, 35]],
        "key_claims_positions": [15, 20, 23, 28, 32],
        "questions_positions": [18, 24, 31],
        "concepts_mentioned": ["Concept A", "Concept B", "Concept C"]
      }},
      {{
        "name": "Second Category Name",
        "synthesis": "Detailed category description (100-150 chars) - must be SPECIFIC",
        "evidence_positions": [[36, 45], [48, 55]],
        "key_claims_positions": [38, 42, 47, 51],
        "questions_positions": [40, 52],
        "concepts_mentioned": ["Concept D", "Concept E"]
      }},
      {{
        "name": "Third Category Name",
        "synthesis": "Detailed category description (100-150 chars) - must be SPECIFIC",
        "evidence_positions": [[56, 68]],
        "key_claims_positions": [58, 62, 65],
        "questions_positions": [60, 67],
        "concepts_mentioned": ["Concept F", "Concept G"]
      }}
    ]
  }}
}}

EXAMPLE OUTPUT STRUCTURE:
{{
  "document_overview": {{
    "title": "Deep Reinforcement Learning for Satellite Energy Management",
    "main_domain": "Reinforcement Learning",
    "summary": "Novel approach using Dueling DQN architecture for optimizing energy consumption in LEO satellite constellations, achieving 18% energy reduction compared to greedy scheduling while maintaining 95% delivery success rate"
  }},
  "hierarchy": {{
    "level_0": {{
      "name": "Satellite Energy Management with Deep Reinforcement Learning",
      "synthesis": "Deep reinforcement learning approach using Dueling DQN for optimizing energy consumption in LEO satellite constellations with multi-agent coordination",
      "evidence_positions": [[0, 50]]
    }},
    "level_1_nodes": [
      {{
        "name": "Deep Q-Network Architecture",
        "synthesis": "Dueling DQN with value and advantage streams achieving 18% energy reduction compared to greedy scheduling with 95% delivery success",
        "evidence_positions": [[12, 25], [30, 35]],
        "key_claims_positions": [15, 20, 23, 28, 33],
        "questions_positions": [18, 24, 32],
        "concepts_mentioned": ["Dueling DQN", "Value Stream", "Advantage Stream", "Q-Value Aggregation"]
      }},
      {{
        "name": "Multi-Agent Coordination",
        "synthesis": "Distributed learning approach reducing communication overhead by 67% (3.2 KB/s vs 9.8 KB/s) with 14 satellite agents",
        "evidence_positions": [[36, 45]],
        "key_claims_positions": [38, 42, 44],
        "questions_positions": [40, 43],
        "concepts_mentioned": ["Multi-Agent Learning", "Communication Overhead", "Distributed Training"]
      }},
      {{
        "name": "Training Methodology",
        "synthesis": "Experience replay with prioritized sampling requiring 50,000 episodes for convergence with epsilon-greedy exploration",
        "evidence_positions": [[46, 50], [52, 58]],
        "key_claims_positions": [47, 51, 55],
        "questions_positions": [49, 56],
        "concepts_mentioned": ["Experience Replay", "Prioritized Sampling", "Epsilon-Greedy Exploration"]
      }}
    ]
  }}
}}

QUALITY REQUIREMENTS:
✓ Domain name must be SPECIFIC to this document (not "Machine Learning" but "Satellite Energy Management with Deep RL")
✓ Category synthesis must include QUANTITATIVE data when available (numbers, percentages)
✓ Positions must be VALID (0 to {paragraph_count_minus_1})
✓ Each category must have at least 2 evidence position ranges
✓ Each category must have at least 3 key claims positions
✓ Concepts mentioned should be specific technical terms (3-5 per category)

VALIDATION CHECKLIST:
☐ Domain synthesis is 150-200 characters?
☐ Each category synthesis is 100-150 characters?
☐ All positions are paragraph indices (integers)?
☐ Evidence positions are ranges [[start, end]]?
☐ Claims/questions are single positions [idx]?
☐ At least 2 categories returned?
☐ No actual text content included (only positions)?

Return ONLY the JSON object. NO explanations, NO markdown, JUST JSON."""


def create_shallow_structure_prompt(
    file_name: str,
    content: str,
    paragraph_count: int,
    lang: str = "en"
) -> dict:
    """
    Create prompt for shallow structure extraction (LLM Call 1)
    
    Args:
        file_name: Name of the PDF file
        content: First ~6000 characters of content for context
        paragraph_count: Total number of paragraphs in the document
        lang: Language code
    
    Returns:
        Dict with 'system_message' and 'prompt'
    """
    return {
        "system_message": SHALLOW_STRUCTURE_SYSTEM_MESSAGE,
        "prompt": SHALLOW_STRUCTURE_PROMPT_TEMPLATE.format(
            file_name=file_name,
            lang=lang,
            content=content[:6000],
            paragraph_count=paragraph_count,
            paragraph_count_minus_1=paragraph_count - 1
        )
    }
