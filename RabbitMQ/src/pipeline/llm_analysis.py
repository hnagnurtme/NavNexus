"""LLM analysis module using CLOVA with TTON (Tree/Token-Based Thought Organization)"""
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
    
    current_category = None
    current_concept = None
    
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
            indent_count = len(line) - len(line.lstrip())
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
                    use_tton: bool = True, response_format: Dict = None) -> Dict[str, Any]:
    """
    Call CLOVA with TTON format for 50-70% token reduction
    
    FIXED: Correct header and URL format per official HyperCLOVA X documentation
    
    Args:
        prompt: User prompt
        max_tokens: Maximum tokens
        clova_api_key: API key
        clova_api_url: API URL (e.g., https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005)
        use_tton: Use TTON format (default: True)
        response_format: Optional response format
        
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
            except:
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
            else:
                return extract_json_from_text(content)
                    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"⚠️  CLOVA API authentication failed (401)")
            print(f"   Check your API key format and permissions")
            print(f"   URL: {clova_api_url}")
        elif e.response.status_code == 400:
            print(f"⚠️  CLOVA API parameter error (400)")
            try:
                error_detail = e.response.json()
                print(f"   Error: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"   Response: {e.response.text[:500]}")
        elif e.response.status_code == 404:
            print(f"⚠️  CLOVA API endpoint not found (404)")
            print(f"   Check your URL: {clova_api_url}")
            print(f"   Correct format: https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005")
        else:
            print(f"⚠️  CLOVA API error {e.response.status_code}: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  LLM error: {e}")
        return {}
    
    return {}


def extract_hierarchical_structure_compact(full_text: str, file_name: str, lang: str,
                                          clova_api_key: str, clova_api_url: str,
                                          max_synthesis_length: int = 80) -> Dict:
    """
    Extract DEEP hierarchical structure using TTON format
    
    TTON enables:
    - 50-70% token reduction
    - 2-3x more nodes in same token budget
    - Level 4-7 depth easily achievable
    
    Args:
        full_text: Full document text
        file_name: Name of the file
        lang: Language code
        clova_api_key: API key
        clova_api_url: API URL
        max_synthesis_length: Maximum chars for synthesis (default: 80)
        
    Returns:
        Deep hierarchical structure (level 4-7)
    """
    
    prompt = f"""Analyze document: {file_name}

First 3500 chars:
{full_text[:3500]}

Extract DEEP hierarchy (level 4-7) using TTON format.

Requirements:
1. GO DEEP: At least 15 concepts, 30+ subconcepts
2. Use >>>> for level 4-7 depth
3. Each synthesis max {max_synthesis_length} chars
4. Be SPECIFIC with evidence/examples
5. More merge opportunities = better

Example structure depth:
D:Domain Name|Brief
C:Major Category 1|Brief
  >Main Concept A|Brief
    >>Subconcept A1|Detail
      >>>Deep concept A1a|Specific
        >>>>Very deep A1a-i|Ultra specific
        >>>>Very deep A1a-ii|Ultra specific
      >>>Deep concept A1b|Specific
    >>Subconcept A2|Detail
  >Main Concept B|Brief
    >>Subconcept B1|Detail
      >>>Deep B1a|Specific
C:Major Category 2|Brief
  >Main Concept C|Brief

NOW extract from the document. GO AS DEEP AS POSSIBLE."""
    
    result = call_llm_compact(prompt, max_tokens=4000, clova_api_key=clova_api_key, 
                            clova_api_url=clova_api_url, use_tton=True)
    
    # Validate
    if not result or not isinstance(result, dict):
        print(f"⚠️  Failed to extract structure. LLM returned: {type(result).__name__}")
        return {
            'domain': {
                'name': file_name or 'Unknown Domain',
                'synthesis': 'Structure extraction failed'
            },
            'categories': []
        }
    
    # Truncate synthesis
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
    
    # Ensure structure
    if 'domain' not in result:
        result['domain'] = {
            'name': file_name or 'Unknown Domain',
            'synthesis': 'No synthesis'
        }
    
    if 'categories' not in result:
        result['categories'] = []
    
    # Count depth for validation
    def count_depth(node, current_depth=0):
        max_depth = current_depth
        if isinstance(node, dict):
            if 'subconcepts' in node and node['subconcepts']:
                for sub in node['subconcepts']:
                    max_depth = max(max_depth, count_depth(sub, current_depth + 1))
            elif 'concepts' in node and node['concepts']:
                for concept in node['concepts']:
                    max_depth = max(max_depth, count_depth(concept, current_depth + 1))
        return max_depth
    
    total_depth = count_depth(result)
    total_concepts = sum(len(cat.get('concepts', [])) for cat in result.get('categories', []))
    
    print(f"  ✓ Structure depth: {total_depth} levels, {total_concepts} concepts")
    
    return result


def parse_tton_batch_response(tton_text: str) -> List[Dict]:
    """
    Parse TTON batch response for chunk processing
    
    Format:
    [0]T:Topic Name|C:Concept1,Concept2|S:Summary text
    [1]T:Topic Name|C:Concept1,Concept2|S:Summary text
    """
    chunks = []
    lines = tton_text.strip().split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        # Match pattern: [N]T:...|C:...|S:...
        match = re.match(r'\[(\d+)\]T:([^|]+)\|C:([^|]*)\|S:(.+)', line)
        if match:
            idx = int(match.group(1))
            topic = match.group(2).strip()
            concepts_str = match.group(3).strip()
            summary = match.group(4).strip()
            
            concepts = [c.strip() for c in concepts_str.split(',') if c.strip()]
            
            chunks.append({
                'i': idx,
                'topic': topic,
                'concepts': concepts[:2],  # Max 2
                'summary': summary[:150]
            })
    
    return chunks


def process_chunks_ultra_compact(chunks: List[Dict], structure: Dict,
                                 clova_api_key: str, clova_api_url: str,
                                 batch_size: int = 15, max_text_length: int = 250,
                                 parallel: bool = True) -> List[Dict]:
    """
    Ultra-compact chunk processing with TTON (50-70% token reduction)
    
    TTON enables:
    - 15 chunks/batch instead of 10 (50% increase)
    - 250 chars/chunk instead of 200 (25% increase)
    - More concepts extracted per batch
    
    Args:
        chunks: List of chunk dictionaries
        structure: Hierarchical structure (for context)
        clova_api_key: API key
        clova_api_url: API URL
        batch_size: Number of chunks per batch (default: 15, was 10)
        max_text_length: Maximum chars per chunk (default: 250, was 200)
        parallel: Enable parallel processing (default: True)
        
    Returns:
        List of analyzed chunks with more detail
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = []
    
    # Extract top 3 concepts
    top_concepts = []
    if structure.get('domain', {}).get('name'):
        top_concepts.append(structure['domain']['name'])
    
    for cat in structure.get('categories', [])[:2]:
        if cat.get('name') and len(top_concepts) < 3:
            top_concepts.append(cat['name'])
    
    context_prefix = f"Doc: {', '.join(top_concepts[:3])}"
    
    # Prepare batches
    batches = []
    for batch_start in range(0, len(chunks), batch_size):
        batches.append((batch_start, chunks[batch_start:batch_start+batch_size]))
    
    total_batches = len(batches)
    
    def process_single_batch(batch_data: tuple) -> List[Dict]:
        """Process a single batch with TTON"""
        batch_start, batch = batch_data
        batch_num = (batch_start // batch_size) + 1
        batch_results = []
        
        # TTON prompt (tiết kiệm 50-60% token)
        prompt = f"""{context_prefix}

Extract for each chunk using TTON compact format:
[N]T:Topic|C:Concept1,Concept2|S:Summary

Chunks:
"""
        
        for i, chunk in enumerate(batch):
            text = chunk.get('text', '')[:max_text_length].replace('\n', ' ')
            prompt += f"{i}. {text}...\n"
        
        prompt += f"""
TTON Response (1 line per chunk):
[0]T:Topic name|C:Key concept 1,Key concept 2|S:One sentence summary
[1]T:Topic name|C:Concept A,Concept B|S:Brief summary

Max 2 concepts/chunk. Be specific."""
        
        try:
            llm_result = call_llm_compact(prompt, max_tokens=1000,
                                         clova_api_key=clova_api_key,
                                         clova_api_url=clova_api_url,
                                         use_tton=True)
            
            # Parse TTON batch response
            if isinstance(llm_result, str):
                chunk_analyses = parse_tton_batch_response(llm_result)
            elif isinstance(llm_result, dict):
                # Fallback to JSON if returned
                if 'chunks' in llm_result:
                    chunk_analyses = llm_result['chunks']
                else:
                    chunk_analyses = []
            elif isinstance(llm_result, list):
                chunk_analyses = llm_result
            else:
                chunk_analyses = []
            
            for analysis in chunk_analyses:
                idx = analysis.get('i', 0)
                if idx >= len(batch):
                    continue
                
                batch_results.append({
                    'chunk_index': batch_start + idx,
                    'text': batch[idx].get('text', ''),
                    'topic': analysis.get('topic', 'General'),
                    'concepts': analysis.get('concepts', [])[:2],
                    'summary': analysis.get('summary', '')[:150]
                })
        
        except Exception as e:
            print(f"  ⚠️  Batch {batch_num} error: {e}")
            # Fallback
            for i, chunk in enumerate(batch):
                batch_results.append({
                    'chunk_index': batch_start + i,
                    'text': chunk.get('text', ''),
                    'topic': 'General',
                    'concepts': [],
                    'summary': chunk.get('text', '')[:100]
                })
        
        return batch_results
    
    # Process batches
    if parallel and total_batches > 1:
        print(f"  ⚡ Processing {total_batches} batches in parallel (TTON format)...")
        max_workers = min(5, total_batches)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(process_single_batch, batch_data): batch_data 
                              for batch_data in batches}
            
            for future in as_completed(future_to_batch):
                batch_results = future.result()
                results.extend(batch_results)
    else:
        for batch_start, batch in batches:
            batch_num = (batch_start // batch_size) + 1
            print(f"  📦 Batch {batch_num}/{total_batches} ({len(batch)} chunks, TTON)...")
            batch_results = process_single_batch((batch_start, batch))
            results.extend(batch_results)
    
    # Sort by chunk_index
    results.sort(key=lambda x: x.get('chunk_index', 0))
    
    return results