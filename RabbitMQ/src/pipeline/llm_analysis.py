"""LLM analysis module using CLOVA with TTON (Tree/Token-Based Thought Organization)"""
import json
import re
import uuid
from typing import Any, Dict, List, Optional

import requests


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    try:
        return json.loads(text)
    except Exception:
        pass

    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except Exception:
                continue

    return {}


def parse_tton_to_json(tton_text: str) -> Dict[str, Any]:
    """
    Parse TTON format to JSON

    TTON Format (tiết kiệm 50-70% token):
    D:Domain Name|Short synthesis
    C:Category 1|Brief desc
      >Concept A|What it means
        >>Subconcept 1|Detail
        >>Subconcept 2|Detail
      >Concept B|What it means
    C:Category 2|Brief desc
      >Concept C|Meaning
    """
    lines = tton_text.strip().split('\n')
    result = {
        'domain': {'name': 'Unknown', 'synthesis': ''},
        'categories': []
    }

    current_category: Optional[Dict[str, Any]] = None
    current_concept: Optional[Dict[str, Any]] = None

    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        # Domain level
        if line.startswith('D:'):
            parts = line[2:].split('|', 1)
            result['domain'] = {
                'name': parts[0].strip(),
                'synthesis': parts[1].strip() if len(parts) > 1 else ''
            }

        # Category level
        elif line.startswith('C:'):
            parts = line[2:].split('|', 1)
            current_category = {
                'name': parts[0].strip(),
                'synthesis': parts[1].strip() if len(parts) > 1 else '',
                'concepts': []
            }
            result['categories'].append(current_category)
            current_concept = None

        # Concept level (1 level indent: >)
        elif line.strip().startswith('>') and not line.strip().startswith('>>'):
            if current_category is None:
                continue
            assert isinstance(current_category, dict) # Added for pylint
            content = line.strip()[1:].strip()  # Remove >
            parts = content.split('|', 1)
            current_concept = {
                'name': parts[0].strip(),
                'synthesis': parts[1].strip() if len(parts) > 1 else '',
                'subconcepts': []
            }
            current_category['concepts'].append(current_concept)

        # Subconcept level (2+ levels indent: >>)
        elif line.strip().startswith('>>'):
            if current_concept is None:
                continue
            assert isinstance(current_concept, dict) # Added for pylint
            # Count số dấu >
            stripped = line.strip()
            level = 0
            while stripped.startswith('>'):
                level += 1
                stripped = stripped[1:]

            content = stripped.strip()
            parts = content.split('|', 1)
            subconcept = {
                'name': parts[0].strip(),
                'synthesis': parts[1].strip() if len(parts) > 1 else '',
                'level': level
            }

            # Nested subconcepts (level 3+)
            if level > 2:
                subconcept['subconcepts'] = []

            current_concept['subconcepts'].append(subconcept)

    return result


def call_llm_compact(prompt: str, max_tokens: int = 2000,
                    clova_api_key: str = "", clova_api_url: str = "",
                    use_tton: bool = True) -> Dict[str, Any]:
    """
    Call CLOVA with TTON format for 50-70% token reduction

    FIXED: Correct header and URL format per official HyperCLOVA X documentation

    Args:
        prompt: User prompt
        max_tokens: Maximum tokens
        clova_api_key: API key
        clova_api_url: API URL (e.g., https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005)
        use_tton: Use TTON format (default: True)

    Returns:
        Parsed JSON response
    """
    if not clova_api_key:
        print("⚠️  CLOVA API key is missing!")
        return {}

    # CORRECT HEADER FORMAT per official documentation
    headers = {
        "Authorization": f"Bearer {clova_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8",  # Added charset
        "Accept": "application/json"
    }

    # System prompt cho TTON format
    if use_tton:
        system_content = """You use TTON format to maximize detail with minimal tokens.

TTON Format Rules:
- D: = Domain (1 line)
- C: = Category (1 line)
- > = Concept (indent 2 spaces)
- >> = Subconcept level 2 (indent 4 spaces)
- >>> = Subconcept level 3 (indent 6 spaces)
- >>>> = Subconcept level 4+ (indent 8+ spaces)
- Use | to separate name from synthesis
- Keep synthesis SHORT (max 80 chars)

Example:
D:Machine Learning|Study of algorithms that improve through experience
C:Supervised Learning|Learning from labeled data
  >Classification|Predicting discrete categories
    >>Binary Classification|Two classes only
      >>>Logistic Regression|Linear model for probability
      >>>SVM|Maximum margin classifier
    >>Multi-class|More than two classes
  >Regression|Predicting continuous values
    >>Linear Regression|Fitting straight line
    >>Neural Networks|Deep learning approach

GO DEEP (level 4-7). Be SPECIFIC. More nodes = better."""
    else:
        system_content = "You are a JSON-only assistant. Return ONLY valid JSON."

    data = {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "maxTokens": max_tokens,
        "topP": 0.8,
        "topK": 0,  # Added topK
        "repeatPenalty": 1.1,
        "includeAiFilters": True  # Added safety filter
    }

    try:
        # Use json.dumps to ensure proper encoding
        r = requests.post(clova_api_url, data=json.dumps(data), headers=headers, timeout=60)

        # Debug info
        if r.status_code != 200:
            print(f"⚠️  HTTP Status: {r.status_code}")
            print(f"   URL: {clova_api_url}")
            try:
                error_data = r.json()
                print(f"   Error: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except Exception:
                print(f"   Response: {r.text[:500]}")

        r.raise_for_status()

        if r.status_code == 200:
            response_data = r.json()

            # HyperCLOVA X response format: result.message.content
            content = response_data.get('result', {}).get('message', {}).get('content', '')

            if not content:
                print(f"⚠️  Empty content in response")
                print(f"   Full response: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")
                return {}

            if use_tton:
                # Parse TTON format
                parsed = parse_tton_to_json(content)
                if parsed and parsed.get('domain', {}).get('name') != 'Unknown':
                    return parsed
                # Fallback to JSON if TTON parsing fails
                return extract_json_from_text(content)

            return extract_json_from_text(content)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"⚠️  CLOVA API authentication failed (401)")
            print("   Check your API key format and permissions")
            print(f"   URL: {clova_api_url}")
        elif e.response.status_code == 400:
            print(f"⚠️  CLOVA API parameter error (400)")
            try:
                error_detail = e.response.json()
                print(f"   Error: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except Exception:
                print(f"   Response: {e.response.text[:500]}")
        elif e.response.status_code == 404:
            print(f"⚠️  CLOVA API endpoint not found (404)")
            print(f"   Check your URL: {clova_api_url}")
            print("   Correct format: https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005")
        else:
            print(f"⚠️  CLOVA API error {e.response.status_code}: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  LLM error: {e}")
        return {}

    return {}

def extract_hierarchical_structure(full_text: str, file_name: str,
                                   clova_api_key: str, clova_api_url: str) -> Dict:
    """Extract multi-level hierarchical structure from document"""

    prompt = f"""Document: {file_name}
First 3000 characters:
{full_text[:3000]}

Extract a DEEP hierarchical structure with multiple levels:

{{
  "domain": {{
    "name": "Main domain/field",
    "synthesis": "1-2 sentences about the overall domain"
  }},
  "categories": [
    {{
      "name": "Category 1 (e.g., Methodology, Theory, Results)",
      "synthesis": "Brief description",
      "concepts": [
        {{
          "name": "Concept name",
          "synthesis": "What this concept means",
          "subconcepts": [
            {{
              "name": "Detailed subconcept",
              "synthesis": "Specific aspect",
              "evidence": "Direct quote or specific claim from text"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Make it DEEP (3-4 levels) and specific. Each node needs clear evidence."""

    return call_llm_compact(prompt, max_tokens=3000, clova_api_key=clova_api_key, clova_api_url=clova_api_url)


def extract_hierarchical_structure_compact(full_text: str, file_name: str,
                                          clova_api_key: str, clova_api_url: str,
                                          max_synthesis_length: int = 100) -> Dict:
    """
    Extract hierarchical structure with COMPACT synthesis (max 100 chars per concept)
    Optimization: Reduces context window size by 60-70%

    Args:
        full_text: Full document text
        file_name: Name of the file
        clova_api_key: API key
        clova_api_url: API URL
        max_synthesis_length: Maximum characters for synthesis (default: 100)

    Returns:
        Hierarchical structure with compact synthesis
    """

    prompt = f"""Document: {file_name}
First 3000 characters:
{full_text[:3000]}

Extract a hierarchical structure. IMPORTANT: Keep synthesis VERY SHORT (max {max_synthesis_length} chars each).

{{
  "domain": {{
    "name": "Main domain/field",
    "synthesis": "1 sentence max {max_synthesis_length} chars"
  }},
  "categories": [
    {{
      "name": "Category name",
      "synthesis": "Brief, max {max_synthesis_length} chars",
      "concepts": [
        {{
          "name": "Concept name",
          "synthesis": "Short description, max {max_synthesis_length} chars",
          "subconcepts": [
            {{
              "name": "Subconcept name",
              "synthesis": "Very brief, max {max_synthesis_length} chars"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Be specific but CONCISE. No long explanations."""

    result = call_llm_compact(prompt, max_tokens=2000, clova_api_key=clova_api_key, clova_api_url=clova_api_url)

    # Truncate all synthesis fields to max_synthesis_length
    def _truncate_synthesis(node: Dict):
        if isinstance(node, dict):
            if 'synthesis' in node and isinstance(node['synthesis'], str):
                node['synthesis'] = node['synthesis'][:max_synthesis_length]

            for _, value in node.items():
                if isinstance(value, dict):
                    _truncate_synthesis(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _truncate_synthesis(item)

    _truncate_synthesis(result)
    return result


def process_chunks_ultra_compact(chunks: List[Dict], structure: Dict,
                                 clova_api_key: str, clova_api_url: str,
                                 batch_size: int = 10, max_text_length: int = 200) -> List[Dict]:
    """
    Ultra-compact chunk processing with FIXED context window and batch processing

    OPTIMIZATIONS:
    - Fixed 3-concept context (not growing)
    - Truncate chunk text to 200 chars
    - Process 10 chunks per LLM call
    - Extract only: topic + 2 concepts + summary

    Args:
        chunks: List of chunk dictionaries
        structure: Hierarchical structure (for context)
        clova_api_key: API key
        clova_api_url: API URL
        batch_size: Number of chunks per batch (default: 10)
        max_text_length: Maximum chars per chunk text (default: 200)

    Returns:
        List of analyzed chunk results
    """

    results = []

    # Extract ONLY top 3 concepts from structure (FIXED context)
    top_concepts = []

    if structure.get('domain', {}).get('name'):
        top_concepts.append(structure['domain']['name'])

    for cat in structure.get('categories', [])[:2]:  # Top 2 categories only
        if cat.get('name') and len(top_concepts) < 3:
            top_concepts.append(cat['name'])

    context_prefix = f"Doc: {', '.join(top_concepts[:3])}"

    # Batch process: 10 chunks at a time
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start:batch_start+batch_size]
        batch_num = (batch_start // batch_size) + 1

        print(f"  📦 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

        # Ultra-compact prompt
        prompt = f"""{context_prefix}

Extract for each chunk (keep concise):
- 1 topic
- 2 key concepts max
- 1 summary (1 sentence)

Chunks:
"""

        for i, chunk in enumerate(batch):
            # CRITICAL: Truncate to max_text_length chars
            text = chunk.get('text', '')[:max_text_length].replace('\n', ' ')
            prompt += f"{i}. {text}...\n"

        prompt += f"""
JSON: [{{"i":0,"topic":"...","concepts":["...","..."],"summary":"..."}}]
Max 2 concepts, 1 sentence summary each."""

        # Single LLM call for entire batch
        try:
            llm_result = call_llm_compact(prompt, max_tokens=800,
                                         clova_api_key=clova_api_key,
                                         clova_api_url=clova_api_url)

            chunk_analyses = []
            if isinstance(llm_result, dict) and 'chunks' in llm_result:
                # If LLM returns a dict with a 'chunks' key, use its value
                if isinstance(llm_result['chunks'], list):
                    chunk_analyses = llm_result['chunks']
                else:
                    print(f"  ⚠️  Expected 'chunks' to be a list, got {type(llm_result['chunks'])}")
            elif isinstance(llm_result, list):
                # If LLM returns a list directly, use it
                chunk_analyses = llm_result
            else:
                print(f"  ⚠️  LLM result is not a dict with 'chunks' or a list, got {type(llm_result)}")

            # Now, ensure each item in chunk_analyses is a dict before processing
            if chunk_analyses:
                for analysis in chunk_analyses:
                    if not isinstance(analysis, dict):
                        print(f"  ⚠️  Skipping non-dict analysis: {analysis}")
                        continue

                    idx = analysis.get('i', 0)
                    if idx >= len(batch):
                        continue

                    results.append({
                        'chunk_index': batch_start + idx,
                        'text': batch[idx].get('text', ''),
                        'topic': analysis.get('topic', 'General'),
                        'concepts': analysis.get('concepts', [])[:2],  # Max 2
                        'summary': analysis.get('summary', '')[:150]  # Max 150 chars
                    })
            else:
                # No analyses from LLM - use fallback for all chunks in batch
                print(f"  ⚠️  No LLM results, using fallback for {len(batch)} chunks")
                for chunk in batch:
                    results.append({
                        'chunk_index': batch_start + batch.index(chunk),
                        'text': chunk.get('text', ''),
                        'topic': 'General',
                        'concepts': [],
                        'summary': chunk.get('text', '')[:100]
                    })

        except Exception as e:
            print(f"  ⚠️  Batch processing error: {e}")
            # Fallback: Add with minimal data
            for i, chunk in enumerate(batch):
                results.append({
                    'chunk_index': batch_start + i,
                    'text': chunk.get('text', ''),
                    'topic': 'General',
                    'concepts': [],
                    'summary': chunk.get('text', '')[:100]
                })

    return results