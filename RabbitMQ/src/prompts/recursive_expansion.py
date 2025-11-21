"""
Recursive Expansion Prompt (LLM Call N)

This prompt expands a parent node into 2-3 children with POSITIONS relative to parent content.
"""

RECURSIVE_EXPANSION_SYSTEM_MESSAGE = """You are a knowledge expansion specialist for recursive hierarchical extraction.

CRITICAL RULES:
1. Positions are RELATIVE to parent content (not absolute document positions)
2. Must return 2-3 children minimum (if content sufficient)
3. Synthesis must be specific (not generic)
4. Stop if parent content < 500 characters
5. Return POSITIONS ONLY (not content text)

OUTPUT: Always return valid JSON matching the schema exactly."""


RECURSIVE_EXPANSION_PROMPT_TEMPLATE = """CRITICAL TASK: Expand parent node into 2-3 children with RELATIVE POSITION-BASED evidence.

PARENT NODE: {parent_name}
PARENT SYNTHESIS: {parent_synthesis}
CURRENT LEVEL: {current_level}
TARGET LEVEL: {target_level}
PARENT PARAGRAPH COUNT: {parent_paragraph_count}

PARENT CONTENT (normalized, first 4000 chars):
---
{parent_content}
---

TASK:
Expand this parent node into {children_count} child nodes (Level {target_level}).
Extract POSITIONS RELATIVE TO PARENT CONTENT.

RELATIVE POSITION RULES:
1. **All positions are RELATIVE to parent content**
   - Parent has {parent_paragraph_count} paragraphs (indices 0 to {parent_paragraph_count_minus_1})
   - Position [2, 8] means paragraphs 2-8 WITHIN parent content
   - NOT absolute positions in the original document

2. **Evidence Positions** = RANGES relative to parent
   - Format: [[start_idx, end_idx]]
   - Example: [[2, 8], [10, 15]]
   - Must be within [0, {parent_paragraph_count_minus_1}]

3. **Key Claims/Questions** = SINGLE positions relative to parent
   - Format: [para_idx1, para_idx2]
   - Example: [4, 6, 12]
   - Must be within [0, {parent_paragraph_count_minus_1}]

SYNTHESIS GUIDELINES (Character Limits by Level):
- Level 2 (Concept): 80-120 chars - Specific idea, method, or approach
- Level 3 (Subconcept): 60-100 chars - Detailed aspect, component, or technique
- Level 4 (Detail): 40-80 chars - Implementation detail, example, or specific instance

STRUCTURAL RULES:
✓ Minimum {children_count} children (maximum {children_count})
✓ Each child must have evidence positions
✓ Each child should have 2-4 key claims positions
✓ Each child should have 1-3 questions positions
✓ Synthesis must be SPECIFIC (include numbers/details when available)
✓ Stop if parent content < 500 characters

OUTPUT FORMAT (strict JSON):
{{
  "parent_node": "{parent_name}",
  "parent_level": {current_level},
  "children_level": {target_level},
  "stop_expansion": false,
  "stop_reason": "",
  "children": [
    {{
      "name": "First Child Name",
      "synthesis": "Detailed description (length depends on level) - must be SPECIFIC",
      "evidence_positions": [[2, 8], [12, 18]],
      "key_claims_positions": [4, 6, 14],
      "questions_positions": [7, 16],
      "relative_to_parent": true
    }},
    {{
      "name": "Second Child Name",
      "synthesis": "Detailed description (length depends on level) - must be SPECIFIC",
      "evidence_positions": [[20, 28]],
      "key_claims_positions": [22, 25],
      "questions_positions": [24],
      "relative_to_parent": true
    }},
    {{
      "name": "Third Child Name",
      "synthesis": "Detailed description (length depends on level) - must be SPECIFIC",
      "evidence_positions": [[30, 40]],
      "key_claims_positions": [32, 36, 38],
      "questions_positions": [34, 39],
      "relative_to_parent": true
    }}
  ]
}}

EXAMPLE OUTPUT (Level 1 → Level 2):
{{
  "parent_node": "Deep Q-Network Architecture",
  "parent_level": 1,
  "children_level": 2,
  "stop_expansion": false,
  "stop_reason": "",
  "children": [
    {{
      "name": "Value Stream Design",
      "synthesis": "Neural network stream estimating state value function V(s) with 3 fully connected layers (256-128-64 neurons)",
      "evidence_positions": [[2, 8]],
      "key_claims_positions": [4, 6],
      "questions_positions": [7],
      "relative_to_parent": true
    }},
    {{
      "name": "Advantage Stream Design",
      "synthesis": "Parallel stream computing advantage function A(s,a) for each action with identical architecture to value stream",
      "evidence_positions": [[9, 15]],
      "key_claims_positions": [11, 13],
      "questions_positions": [12],
      "relative_to_parent": true
    }},
    {{
      "name": "Q-Value Aggregation",
      "synthesis": "Combines value and advantage streams: Q(s,a) = V(s) + A(s,a) - mean(A) ensuring identifiability constraint",
      "evidence_positions": [[16, 22]],
      "key_claims_positions": [18, 20],
      "questions_positions": [19],
      "relative_to_parent": true
    }}
  ]
}}

EXAMPLE OUTPUT (Insufficient Content - Stop):
{{
  "parent_node": "Some Node",
  "parent_level": 3,
  "children_level": 4,
  "stop_expansion": true,
  "stop_reason": "Parent content too short (342 characters < 500 minimum)",
  "children": []
}}

QUALITY REQUIREMENTS:
✓ Child synthesis must include SPECIFICS (not "This discusses X" but "X achieves Y% improvement using Z method")
✓ Positions must be VALID (0 to {parent_paragraph_count_minus_1})
✓ Each child must have at least 1 evidence position range
✓ Each child must have at least 2 key claims positions
✓ Names should be concise (2-5 words)
✓ Avoid parent name repetition in child names

VALIDATION CHECKLIST:
☐ {children_count} children returned (or stop_expansion=true)?
☐ All positions are relative to parent [0, {parent_paragraph_count_minus_1}]?
☐ Evidence positions are ranges [[start, end]]?
☐ Claims/questions are single positions [idx]?
☐ Synthesis lengths appropriate for level {target_level}?
☐ No actual text content included (only positions)?
☐ Each child has unique, specific name?

Return ONLY the JSON object. NO explanations, NO markdown, JUST JSON."""


def create_recursive_expansion_prompt(
    parent_name: str,
    parent_synthesis: str,
    parent_content: str,
    current_level: int,
    target_level: int,
    children_count: int = 3
) -> dict:
    """
    Create prompt for recursive node expansion (LLM Call N)
    
    Args:
        parent_name: Name of the parent node
        parent_synthesis: Synthesis of the parent node
        parent_content: Normalized content from parent's evidence
        current_level: Current level (0, 1, 2, ...)
        target_level: Target level for children (current_level + 1)
        children_count: Number of children to create (default 3)
    
    Returns:
        Dict with 'system_message' and 'prompt'
    """
    from ..pipeline.position_extraction import split_text_to_paragraphs
    
    # Split parent content into paragraphs to count them
    parent_paragraphs = split_text_to_paragraphs(parent_content)
    parent_paragraph_count = len(parent_paragraphs)
    
    return {
        "system_message": RECURSIVE_EXPANSION_SYSTEM_MESSAGE,
        "prompt": RECURSIVE_EXPANSION_PROMPT_TEMPLATE.format(
            parent_name=parent_name,
            parent_synthesis=parent_synthesis[:200],
            parent_content=parent_content[:4000],
            current_level=current_level,
            target_level=target_level,
            children_count=children_count,
            parent_paragraph_count=parent_paragraph_count,
            parent_paragraph_count_minus_1=parent_paragraph_count - 1
        )
    }
