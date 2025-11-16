"""LLM analysis module using CLOVA"""
import json
import re
import uuid
import requests
from typing import Dict, Any, List


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    try:
        return json.loads(text)
    except:
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
            except:
                continue
    
    return {}


def call_llm_compact(prompt: str, max_tokens: int = 2000, 
                    clova_api_key: str = "", clova_api_url: str = "") -> Dict[str, Any]:
    """Call CLOVA with compact prompts"""
    headers = {
        "Authorization": f"Bearer {clova_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON. No markdown, no explanations."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "maxTokens": max_tokens,
        "topP": 0.8
    }
    
    try:
        r = requests.post(clova_api_url, json=data, headers=headers, timeout=60)
        if r.status_code == 200:
            content = r.json().get('result', {}).get('message', {}).get('content', '')
            parsed = extract_json_from_text(content)
            if parsed:
                return parsed
    except Exception as e:
        print(f"⚠ LLM error: {e}")
    
    return {}


def extract_hierarchical_structure(full_text: str, file_name: str, lang: str,
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


def process_chunk_batch(chunks: List[Dict], lang: str, accumulated_concepts: List[str],
                       clova_api_key: str, clova_api_url: str) -> Dict:
    """Process multiple chunks at once"""
    
    concept_ctx = ", ".join(accumulated_concepts[-15:]) if accumulated_concepts else "None"
    
    chunk_texts = []
    for i, c in enumerate(chunks):
        overlap = f"[OVERLAP: {c['overlap_previous'][-150:]}]" if c['overlap_previous'] else ""
        chunk_texts.append(f"## CHUNK {c['index']+1}\n{overlap}\n{c['text'][:1800]}")
    
    combined = "\n\n".join(chunk_texts)
    
    prompt = f"""Analyze these {len(chunks)} chunks. Known concepts: {concept_ctx}

{combined}

For EACH chunk extract:
1. Core concepts (2-3 max, hierarchical)
2. Key claims (1-2 sentences, specific)
3. Questions raised
4. Topic

Return JSON:
{{
  "chunks": [
    {{
      "chunk_index": 0,
      "topic": "...",
      "concepts": [{{"name": "...", "type": "theory/method/finding", "level": 2, "synthesis": "1 sentence", "evidence": "specific quote"}}],
      "key_claims": ["claim 1", "claim 2"],
      "questions": ["what's unclear"],
      "summary": "2 sentences"
    }}
  ]
}}

Be specific."""
    
    return call_llm_compact(prompt, max_tokens=3000, clova_api_key=clova_api_key, clova_api_url=clova_api_url)


def extract_hierarchical_structure_compact(full_text: str, file_name: str, lang: str,
                                          clova_api_key: str, clova_api_url: str,
                                          max_synthesis_length: int = 100) -> Dict:
    """
    Extract hierarchical structure with COMPACT synthesis (max 100 chars per concept)
    Optimization: Reduces context window size by 60-70%
    
    Args:
        full_text: Full document text
        file_name: Name of the file
        lang: Language code
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
            
            for key, value in node.items():
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
            
            # Extract chunk analyses from result
            if isinstance(llm_result, dict) and 'chunks' in llm_result:
                chunk_analyses = llm_result['chunks']
            elif isinstance(llm_result, list):
                chunk_analyses = llm_result
            else:
                chunk_analyses = []
            
            for analysis in chunk_analyses:
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
