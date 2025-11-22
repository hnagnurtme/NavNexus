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

SYNTHESIS GUIDELINES (STRICT Character Limits by Level):
- Level 1 (Category): 100-150 chars - Major theme or area with context
- Level 2 (Concept): 80-120 chars - Specific idea, method, or approach with details
- Level 3 (Subconcept): 60-100 chars - Detailed aspect, component, or technique
- Level 4 (Detail): 40-80 chars - Implementation detail, example, or specific instance

⚠️ CRITICAL: Synthesis MUST include:
  - Numbers, percentages, or quantitative data when available
  - Specific technical terms (not generic descriptions)
  - Clear relationship to parent concept
  - Actual content summary (not meta-descriptions like "discusses X")

STRUCTURAL RULES:
✓ MANDATORY: Minimum {children_count} children (maximum {children_count})
✓ MANDATORY: Each child must have evidence positions
✓ MANDATORY: Each child must have 3-5 key claims (actual text, not just positions)
✓ MANDATORY: Each child must have 2-3 questions raised (actual text, not just positions)
✓ MANDATORY: Synthesis must be SPECIFIC and meet minimum length
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
      "name": "First Child Name (3-7 words, specific)",
      "synthesis": "DETAILED synthesis meeting minimum char requirement with specific facts, numbers, and technical terms - NOT generic",
      "evidence_positions": [[2, 8], [12, 18]],
      "key_claims": [
        "Specific claim with data: System achieves 95% accuracy using X method",
        "Another claim: Component Y reduces latency by 40% compared to baseline",
        "Third claim: Approach Z enables real-time processing with <10ms delay"
      ],
      "key_claims_positions": [4, 6, 14],
      "questions_raised": [
        "How does this approach scale to datasets larger than 1M samples?",
        "What are the trade-offs between accuracy and computational cost?",
        "Can this method adapt to non-stationary environments?"
      ],
      "questions_positions": [7, 16],
      "relative_to_parent": true
    }},
    {{
      "name": "Second Child Name",
      "synthesis": "Another DETAILED synthesis with specifics and minimum required length",
      "evidence_positions": [[20, 28]],
      "key_claims": [
        "Claim 1 with specific details",
        "Claim 2 with numbers or facts",
        "Claim 3 with technical insight"
      ],
      "key_claims_positions": [22, 25, 27],
      "questions_raised": [
        "Analytical question about limitations or implications?",
        "Question about scalability or trade-offs?"
      ],
      "questions_positions": [24, 26],
      "relative_to_parent": true
    }},
    {{
      "name": "Third Child Name",
      "synthesis": "Third DETAILED synthesis meeting all requirements with substance",
      "evidence_positions": [[30, 40]],
      "key_claims": [
        "Specific claim with evidence",
        "Another claim with details",
        "Third claim with context"
      ],
      "key_claims_positions": [32, 36, 38],
      "questions_raised": [
        "Deep question about the approach?",
        "Question exploring extensions or alternatives?"
      ],
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
      "synthesis": "Neural network stream estimating state value function V(s) with 3 fully connected layers (256-128-64 neurons) using ReLU activation",
      "evidence_positions": [[2, 8]],
      "key_claims": [
        "Value stream uses dense layers with 256, 128, and 64 neurons respectively for hierarchical feature extraction",
        "ReLU activation functions enable non-linear value function approximation with faster convergence",
        "Batch normalization between layers reduces training time by 40% compared to standard DQN"
      ],
      "key_claims_positions": [4, 6, 7],
      "questions_raised": [
        "How does the value stream handle high-dimensional state spaces with >1000 features?",
        "What is the optimal layer size ratio for different problem complexities?"
      ],
      "questions_positions": [5, 8],
      "relative_to_parent": true
    }},
    {{
      "name": "Advantage Stream Design",
      "synthesis": "Parallel stream computing advantage function A(s,a) for each action with identical 3-layer architecture enabling direct action comparison",
      "evidence_positions": [[9, 15]],
      "key_claims": [
        "Advantage stream outputs one value per action, enabling direct comparison of action quality",
        "Shared feature extraction with value stream reduces parameters by 30% while maintaining performance",
        "Mean advantage subtraction ensures zero-mean advantages for stable learning"
      ],
      "key_claims_positions": [11, 13, 14],
      "questions_raised": [
        "Can advantage stream architecture be asymmetric to value stream for better action differentiation?",
        "How does this design scale to continuous action spaces?"
      ],
      "questions_positions": [12, 15],
      "relative_to_parent": true
    }},
    {{
      "name": "Q-Value Aggregation Layer",
      "synthesis": "Combines value and advantage streams using Q(s,a) = V(s) + A(s,a) - mean(A) formula ensuring unique decomposition and stable gradients",
      "evidence_positions": [[16, 22]],
      "key_claims": [
        "Aggregation formula ensures identifiability: subtracting mean(A) makes V and A uniquely determined",
        "This architecture improves learning stability by 25% compared to standard Q-networks in benchmark tests",
        "Gradient flow is balanced between value and advantage streams preventing optimization bias"
      ],
      "key_claims_positions": [18, 20, 21],
      "questions_raised": [
        "Would using max(A) instead of mean(A) provide better worst-case action identification?",
        "How sensitive is performance to the specific aggregation formula used?"
      ],
      "questions_positions": [19, 22],
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
    # Import here to avoid circular dependency
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
