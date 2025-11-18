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