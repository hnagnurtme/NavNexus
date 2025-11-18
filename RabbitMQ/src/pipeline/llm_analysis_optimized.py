"""Ultra-compact LLM analysis with minimal context and batch processing"""
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
                    clova_api_key: str = "", clova_api_url: str = "") -> Any:
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


def extract_hierarchical_structure_compact(
    full_text: str, 
    file_name: str, 
    lang: str,
    clova_api_key: str, 
    clova_api_url: str
) -> Dict:
    """
    Extract hierarchical structure with COMPACT synthesis (100 chars max per concept)
    
    Args:
        full_text: Document text
        file_name: Name of the file
        lang: Language code
        clova_api_key: API key
        clova_api_url: API URL
    
    Returns:
        Hierarchical structure with compact synthesis
    """
    
    prompt = f"""Document: {file_name}
First 2500 characters:
{full_text[:2500]}

Extract a hierarchical structure. KEEP SYNTHESIS VERY SHORT (max 100 chars each):

{{
  "domain": {{
    "name": "Main domain/field",
    "synthesis": "1 sentence, max 100 chars"
  }},
  "categories": [
    {{
      "name": "Category 1",
      "synthesis": "Brief, max 100 chars",
      "concepts": [
        {{
          "name": "Concept name",
          "synthesis": "Short description, max 100 chars",
          "subconcepts": [
            {{
              "name": "Detailed subconcept",
              "synthesis": "Very brief, max 100 chars"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Make it DEEP (3-4 levels) but CONCISE. Max 100 chars per synthesis."""
    
    return call_llm_compact(prompt, max_tokens=3000, clova_api_key=clova_api_key, clova_api_url=clova_api_url)


def process_chunks_ultra_compact(
    chunks: List[Dict], 
    structure: Dict,
    clova_api_key: str, 
    clova_api_url: str
) -> List[Dict]:
    """
    Minimal context window with batch processing
    
    OPTIMIZATIONS:
    - Fixed 3-concept context (not growing)
    - Truncate chunk text to 200 chars
    - Process 10 chunks per LLM call
    - Extract only: topic + 2 concepts + summary
    
    Args:
        chunks: List of text chunks
        structure: Document structure (to extract top concepts)
        clova_api_key: API key
        clova_api_url: API URL
    
    Returns:
        List of analyzed chunk data
    """
    
    results = []
    
    # Extract ONLY top 3 concepts from structure (fixed context)
    top_concepts = []
    for cat in structure.get('categories', [])[:2]:  # Top 2 categories
        if cat.get('name'):
            top_concepts.append(cat['name'])
        if len(top_concepts) >= 3:
            break
    
    context_prefix = f"Doc: {', '.join(top_concepts[:3])}" if top_concepts else "Doc context"
    
    # Batch process: 10 chunks at a time
    BATCH_SIZE = 10
    
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start:batch_start+BATCH_SIZE]
        
        # Ultra-compact prompt
        prompt = f"""{context_prefix}

Extract for each chunk (keep it SHORT):
- 1 topic
- 2 key concepts (max)
- 1 summary (1 sentence)

Chunks:
"""
        
        for i, chunk in enumerate(batch):
            # CRITICAL: Truncate to 200 chars
            text = chunk['text'][:200].replace('\n', ' ')
            prompt += f"{i}. {text}...\n"
        
        prompt += """
Return JSON array:
[{"i":0,"topic":"...","concepts":["...","..."],"summary":"..."}]

Keep it brief."""
        
        # Single LLM call for 10 chunks
        try:
            llm_result = call_llm_compact(
                prompt, 
                max_tokens=800,
                clova_api_key=clova_api_key,
                clova_api_url=clova_api_url
            )
            
            # Handle both dict and list responses
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
                    'text': batch[idx]['text'],
                    'topic': analysis.get('topic', 'General'),
                    'concepts': analysis.get('concepts', [])[:2],  # Max 2
                    'summary': analysis.get('summary', '')[:150],  # Max 150 chars
                    'key_claims': analysis.get('claims', [])[:2],  # Max 2 claims
                    'questions': []  # Removed to save space
                })
        
        except Exception as e:
            print(f"  ⚠️  Batch processing error: {e}")
            # Fallback: Add with minimal data
            for i, chunk in enumerate(batch):
                results.append({
                    'chunk_index': batch_start + i,
                    'text': chunk['text'],
                    'topic': 'General',
                    'concepts': [],
                    'summary': chunk['text'][:100],
                    'key_claims': [],
                    'questions': []
                })
    
    return results
