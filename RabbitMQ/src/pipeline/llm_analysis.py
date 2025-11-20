"""
Enhanced LLM analysis optimized for deep hierarchical node merging
- Deep structure: 4-5 levels with rich node connections
- Optimized prompts with few-shot examples
- Hybrid async + ThreadPool for performance
- Centralized config for API keys and timeouts
"""

import json
import re
import uuid
from typing import Dict, Any, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import httpx
import time
from ..config import (
    # API Configuration
    CLOVA_API_KEY, CLOVA_API_URL, CLOVA_EMBEDDING_URL,
    PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET,CLOVA_API_TIMEOUT,
    
    # Pipeline Configuration
    CHUNK_SIZE, OVERLAP, MAX_CHUNKS, MIN_CHUNK_SIZE, EMBEDDING_BATCH_SIZE, QDRANT_BATCH_SIZE,
    MAX_SYNTHESIS_LENGTH, MAX_PDF_TEXT_EXTRACT,
    
    # Performance Configuration
    PDF_DOWNLOAD_TIMEOUT,
    MAX_RETRY_ATTEMPTS, MAX_PDF_PAGES,
    
    # Feature Flags
    FEATURE_TRANSLATION, FEATURE_RESOURCE_DISCOVERY,
    FEATURE_SEMANTIC_DEDUPLICATION,
    DEBUG_MODE,MAX_CHUNK_TEXT_LENGTH,
    BATCH_SIZE,
    
    # Validation
    CONFIG_VALID, CONFIG_SUMMARY,
    
    # Constants
    EMBEDDING_DIMENSION
)
# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_MESSAGE = """You are a knowledge extraction specialist optimized for creating deep, mergeable concept hierarchies.

CORE PRINCIPLES:
1. Generalization: Prefer broad, reusable terms over specific jargon
2. Deep Hierarchy: Create 4-5 levels of nested concepts for rich structure
3. Consistency: Use similar naming patterns across documents for easy merging
4. Conciseness: Balance brevity with informativeness in synthesis
5. Merge-Ready: Every node should be named to facilitate cross-document merging

OUTPUT: Always return valid JSON matching the requested schema exactly."""

EXTRACTION_PROMPT_TEMPLATE = """You are analyzing a document to create a DEEP hierarchical knowledge structure (4-5 levels) optimized for merging similar concepts across multiple documents.

DOCUMENT: {file_name}
LANGUAGE: {lang}
CONTENT (first 2500 chars):
---
{content}
---

TASK:
Extract key concepts and organize them into a 5-LEVEL DEEP hierarchy:
Level 1: Domain (root)
Level 2: Categories (major themes)
Level 3: Concepts (specific topics)
Level 4: Subconcepts (detailed aspects)
Level 5: Details (implementations/examples)

MERGING REQUIREMENTS:
1. Use GENERAL, REUSABLE node names
   ✓ Good: "Data Processing", "Machine Learning Algorithms", "API Design"
   ✗ Bad: "pandas_specific_function", "Our Company's ML Model", "Version 2.1 API"
   
2. Group similar concepts under the same parent for easy merging
   - Think: "Will another document have similar concepts?"
   - Use industry-standard terminology when possible
   
3. Create DEPTH over BREADTH
   - Prefer: 2 categories with 3 concepts each, 4 subconcepts each, 3 details each
   - Over: 6 categories with 1 concept each
   
4. Avoid document-specific or version-specific names

SYNTHESIS GUIDELINES (Character Limits):
- Domain (Level 1): 120-180 chars - Comprehensive overview of document's entire scope
- Category (Level 2): 100-150 chars - Major theme or topic area with context
- Concept (Level 3): 80-120 chars - Specific idea, method, or approach
- Subconcept (Level 4): 60-100 chars - Detailed aspect, component, or technique
- Detail (Level 5): 40-80 chars - Implementation detail, example, or specific instance

STRUCTURAL RULES:
✓ Minimum 2 categories per domain (maximum 4)
✓ Minimum 3 concepts per category (maximum 6)
✓ Minimum 3 subconcepts per concept (maximum 5)
✓ Minimum 2 details per subconcept (maximum 4)
✓ Every branch must reach at least level 4 (subconcepts)
✓ 60% of branches should reach level 5 (details)

NAMING CONVENTIONS:
- Use Title Case for all names
- Keep names concise (2-5 words)
- Avoid acronyms unless universally known (API, ML, AI OK)
- Use action verbs for process-related nodes ("Processing", "Analyzing")
- Use nouns for entity-related nodes ("Architecture", "Components")

OUTPUT FORMAT (strict JSON):
{{
  "domain": {{
    "name": "General Domain Name",
    "synthesis": "120-180 char comprehensive description of document's scope and purpose",
    "level": 1
  }},
  "categories": [
    {{
      "name": "Broad Category Name",
      "synthesis": "100-150 char description of this major theme with context",
      "level": 2,
      "concepts": [
        {{
          "name": "Specific Concept Name",
          "synthesis": "80-120 char explanation of this topic or method",
          "level": 3,
          "subconcepts": [
            {{
              "name": "Detailed Subconcept",
              "synthesis": "60-100 char description of this aspect or component",
              "level": 4,
              "details": [
                {{
                  "name": "Implementation Detail",
                  "synthesis": "40-80 char specific implementation or example",
                  "level": 5
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  ]
}}

EXAMPLE OUTPUT STRUCTURE:
{{
  "domain": {{
    "name": "Software Architecture Patterns",
    "synthesis": "Comprehensive guide to architectural patterns for building scalable, maintainable software systems with focus on microservices and distributed design",
    "level": 1
  }},
  "categories": [
    {{
      "name": "Distributed System Patterns",
      "synthesis": "Patterns for designing resilient distributed systems including service communication, data consistency, and fault tolerance strategies",
      "level": 2,
      "concepts": [
        {{
          "name": "Service Communication",
          "synthesis": "Methods and protocols for inter-service communication in distributed architectures including synchronous and asynchronous patterns",
          "level": 3,
          "subconcepts": [
            {{
              "name": "Synchronous Communication",
              "synthesis": "Direct request-response patterns using HTTP, gRPC for immediate data exchange between services",
              "level": 4,
              "details": [
                {{
                  "name": "REST API Design",
                  "synthesis": "RESTful endpoints with proper HTTP verbs and resource modeling",
                  "level": 5
                }},
                {{
                  "name": "gRPC Implementation",
                  "synthesis": "Protocol Buffers for efficient binary communication",
                  "level": 5
                }}
              ]
            }},
            {{
              "name": "Asynchronous Messaging",
              "synthesis": "Event-driven patterns using message queues and pub-sub for decoupled service interaction",
              "level": 4,
              "details": [
                {{
                  "name": "Message Queue Patterns",
                  "synthesis": "RabbitMQ, SQS for reliable asynchronous message delivery",
                  "level": 5
                }},
                {{
                  "name": "Event Streaming",
                  "synthesis": "Kafka, Kinesis for real-time event processing pipelines",
                  "level": 5
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  ]
}}

VALIDATION CHECKLIST (Must verify before returning):
✓ Every category has 3-6 concepts
✓ Every concept has 3-5 subconcepts
✓ At least 60% of subconcepts have 2-4 details
✓ All synthesis fields meet character limits
✓ Names are general and merge-friendly
✓ JSON is valid and complete
✓ Hierarchy reaches 4-5 levels deep
✓ No document-specific terminology in names

EDGE CASES:
- If content is too short: Create at least 2 categories with minimum structure
- If content is highly technical: Translate jargon to general terms in node names
- If multiple domains present: Choose the primary domain, list others in synthesis
- If uncertain about categorization: Prefer broader categories over narrow ones

Remember: DEPTH and MERGEABILITY are your top priorities. Every node should facilitate cross-document knowledge integration."""

CHUNK_ANALYSIS_PROMPT_TEMPLATE = """You are analyzing document chunks to map them to a pre-defined hierarchical structure, evaluating their merge potential.

STRUCTURE CONCEPTS (available nodes):
{structure_concepts}

CHUNKS TO ANALYZE:
{chunks_text}

TASK: For each chunk, determine:
1. PRIMARY_CONCEPT: Which structure concept best matches this chunk?
2. MERGE_POTENTIAL: How well does this chunk fit for merging?
   - "high": Chunk directly explains/extends the concept with substantial information
   - "medium": Chunk relates to concept but with different focus or partial overlap
   - "low": Chunk mentions concept tangentially or has minimal relevant content
3. SUMMARY: Concise description (max 80 chars) of chunk's key point
4. KEY_CLAIMS: 1-3 specific claims or facts from the chunk

EVALUATION CRITERIA:
HIGH merge_potential:
- Chunk provides core explanation of the concept
- Contains specific methods, algorithms, or implementations
- Includes quantitative data or concrete examples
- Directly extends understanding of the concept

MEDIUM merge_potential:
- Chunk discusses related topics with some overlap
- Mentions the concept in context of broader discussion
- Provides contextual information rather than direct explanation

LOW merge_potential:
- Chunk only mentions concept in passing
- Content is too generic or introductory
- Primarily metadata, headers, or navigation text
- Chunk is too short (< 50 chars)

FEW-SHOT EXAMPLES:

Example 1:
Input Chunk: "The pandas DataFrame provides a two-dimensional labeled data structure with columns of potentially different types. It supports operations like filtering, grouping, and merging, making it essential for data manipulation in Python."
Structure Concepts: ["Data Processing", "Machine Learning", "Visualization"]

Output: {{
  "chunk_index": 0,
  "primary_concept": "Data Processing",
  "merge_potential": "high",
  "summary": "pandas DataFrame structure and operations for data manipulation",
  "key_claims": [
    "Two-dimensional labeled data structure",
    "Supports filtering, grouping, merging operations",
    "Essential for Python data manipulation"
  ]
}}

Example 2:
Input Chunk: "In conclusion, we have explored various data science techniques and tools."
Structure Concepts: ["Data Processing", "Machine Learning", "Visualization"]

Output: {{
  "chunk_index": 1,
  "primary_concept": "Data Processing",
  "merge_potential": "low",
  "summary": "Generic conclusion statement about data science",
  "key_claims": ["Summary of data science exploration"]
}}

Example 3:
Input Chunk: "Neural networks learn by adjusting weights through backpropagation. The algorithm computes gradients using the chain rule, updating parameters via gradient descent to minimize loss function."
Structure Concepts: ["Data Processing", "Machine Learning", "Optimization Algorithms"]

Output: {{
  "chunk_index": 2,
  "primary_concept": "Optimization Algorithms",
  "merge_potential": "high",
  "summary": "Backpropagation and gradient descent in neural network training",
  "key_claims": [
    "Backpropagation adjusts weights through gradient computation",
    "Uses chain rule for gradient calculation",
    "Gradient descent minimizes loss function"
  ]
}}

NOW ANALYZE THESE CHUNKS:

RESPONSE FORMAT (strict JSON array):
[
  {{
    "chunk_index": 0,
    "primary_concept": "Exact concept name from structure",
    "merge_potential": "high|medium|low",
    "summary": "Specific 80-char summary of chunk content",
    "key_claims": ["Claim 1", "Claim 2", "Claim 3"]
  }}
]

EDGE CASES:
- If chunk < 50 chars: Set merge_potential to "low", summary to "Insufficient content"
- If no concept matches well: Choose CLOSEST concept, note mismatch in summary
- If chunk spans multiple concepts: Choose PRIMARY (most emphasized) concept only
- Avoid generic summaries like "discusses X" - be specific about WHAT is discussed
- If chunk is code: Summarize what the code DOES, not that it "contains code"

VALIDATION:
✓ Every chunk has an analysis
✓ All primary_concepts exist in structure
✓ Merge_potential ratings are justified by content
✓ Summaries are specific and within 80 chars
✓ Key_claims contain actual information, not meta-statements
✓ JSON array is valid and complete

Return ONLY the JSON array, no additional text."""

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response with multiple fallback strategies.
    Handles wrapped JSON, markdown code blocks, and embedded JSON.
    """
    if not text or not isinstance(text, str):
        return {}
    
    # Try direct JSON parse first
    try:
        return json.loads(text.strip())
    except:
        pass

    # Try various regex patterns
    patterns = [
        r'```json\s*(.*?)\s*```',  # Markdown JSON block
        r'```\s*(.*?)\s*```',       # Generic code block
        r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\}))*\}',  # Nested JSON object
        r'\[(?:[^\[\]]|(?:\[(?:[^\[\]]|(?:\[[^\[\]]*\])*)*\]))*\]'  # JSON array
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                if parsed:  # Ensure non-empty result
                    return parsed
            except:
                continue

    # Last resort: try to find any JSON-like structure
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            potential_json = text[start_idx:end_idx]
            return json.loads(potential_json)
    except:
        pass

    print(f"⚠️ Failed to extract JSON from response. First 200 chars: {text[:200]}")
    return {}

def validate_structure_depth(structure: Dict) -> Dict:
    """
    Validate and report on structure depth.
    Ensures minimum 4 levels, ideally 5 levels.
    """
    stats = {
        "total_nodes": 0,
        "depth_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        "avg_depth": 0,
        "min_depth": 5,
        "max_depth": 0,
        "validation_passed": True,
        "issues": []
    }
    
    def count_depth(node, current_depth):
        stats["total_nodes"] += 1
        stats["depth_distribution"][current_depth] = stats["depth_distribution"].get(current_depth, 0) + 1
        stats["max_depth"] = max(stats["max_depth"], current_depth)
        stats["min_depth"] = min(stats["min_depth"], current_depth)
        
        # Check children at each level
        if current_depth == 2 and "concepts" in node:
            for concept in node["concepts"]:
                count_depth(concept, 3)
        elif current_depth == 3 and "subconcepts" in node:
            for subconcept in node["subconcepts"]:
                count_depth(subconcept, 4)
        elif current_depth == 4 and "details" in node:
            for detail in node["details"]:
                count_depth(detail, 5)
    
    # Start counting from domain
    if "domain" in structure:
        count_depth(structure["domain"], 1)
    
    # Count categories
    for category in structure.get("categories", []):
        count_depth(category, 2)
    
    # Calculate average depth
    total_depth = sum(depth * count for depth, count in stats["depth_distribution"].items())
    stats["avg_depth"] = total_depth / max(stats["total_nodes"], 1)
    
    # Validation checks
    if stats["max_depth"] < 4:
        stats["validation_passed"] = False
        stats["issues"].append("Structure does not reach minimum depth of 4 levels")
    
    if stats["depth_distribution"].get(5, 0) < stats["total_nodes"] * 0.3:
        stats["issues"].append(f"Only {stats['depth_distribution'].get(5, 0)} nodes at level 5 (recommend 30%+ of total)")
    
    return stats

# ============================================================================
# LLM API FUNCTIONS
# ============================================================================

def call_llm_sync(prompt: str, max_tokens: int = 3000, 
                  system_message: str = SYSTEM_MESSAGE,
                  clova_api_key: str = "", 
                  clova_api_url: str = "") -> Any:
    """
    Synchronous LLM call with error handling and retry logic.
    """
    import requests

    if not clova_api_key:
        clova_api_key = CLOVA_API_KEY
    if not clova_api_url:
        clova_api_url = CLOVA_API_URL

    headers = {
        "Authorization": f"Bearer {clova_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8"
    }

    data = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "maxTokens": max_tokens,
        "topP": 0.8,
        "repeatPenalty": 1.1
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(
                clova_api_url, 
                json=data, 
                headers=headers, 
                timeout=CLOVA_API_TIMEOUT
            )
            if r.status_code == 200:
                content = r.json().get('result', {}).get('message', {}).get('content', '')
                result = extract_json_from_text(content)
                if result:  # Only return if we got valid JSON
                    return result
                print(f"⚠️ Attempt {attempt + 1}: Empty or invalid JSON response")
            else:
                print(f"⚠️ Attempt {attempt + 1}: HTTP {r.status_code}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}: Error - {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    return {}

async def call_llm_async(prompt: str, max_tokens: int = 2000,
                         system_message: str = SYSTEM_MESSAGE,
                         clova_api_key: str = "",
                         clova_api_url: str = "") -> Any:
    """
    Asynchronous LLM call for batch processing.
    """
    if not clova_api_key:
        clova_api_key = CLOVA_API_KEY
    if not clova_api_url:
        clova_api_url = CLOVA_API_URL

    headers = {
        "Authorization": f"Bearer {clova_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8"
    }

    data = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "maxTokens": max_tokens,
        "topP": 0.8,
        "repeatPenalty": 1.1
    }

    async with httpx.AsyncClient(timeout=CLOVA_API_TIMEOUT) as client:
        try:
            resp = await client.post(clova_api_url, json=data, headers=headers)
            content = resp.json().get('result', {}).get('message', {}).get('content', '')
            return extract_json_from_text(content)
        except Exception as e:
            print(f"⚠️ Async LLM error: {e}")
            return {}

# ============================================================================
# MAIN EXTRACTION FUNCTIONS
# ============================================================================

def extract_deep_merge_structure(
    full_text: str, 
    file_name: str, 
    lang: str = "en",
    clova_api_key: str = "", 
    clova_api_url: str = "",
    validate: bool = True
) -> Dict:
    """
    Extract deep hierarchical structure (4-5 levels) optimized for merging.
    
    Returns structure with:
    - Domain (Level 1)
    - Categories (Level 2) 
    - Concepts (Level 3)
    - Subconcepts (Level 4)
    - Details (Level 5)
    
    Args:
        full_text: Document content
        file_name: Name of the document
        lang: Language code (en, ko, etc.)
        clova_api_key: API key (uses config if not provided)
        clova_api_url: API URL (uses config if not provided)
        validate: Whether to validate structure depth
    
    Returns:
        Dict with hierarchical structure and optional validation stats
    """
    
    # Truncate content smartly (try to end at sentence)
    content = full_text[:2500]
    if len(full_text) > 2500:
        last_period = content.rfind('.')
        if last_period > 2000:
            content = content[:last_period + 1]
    
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        file_name=file_name,
        lang=lang,
        content=content
    )
    
    print(f"🔍 Extracting deep structure for: {file_name}")
    result = call_llm_sync(
        prompt, 
        max_tokens=4000,
        system_message=SYSTEM_MESSAGE,
        clova_api_key=clova_api_key, 
        clova_api_url=clova_api_url
    )
    
    if validate and result:
        stats = validate_structure_depth(result)
        print(f"📊 Structure Stats:")
        print(f"   Total nodes: {stats['total_nodes']}")
        print(f"   Depth range: {stats['min_depth']}-{stats['max_depth']}")
        print(f"   Average depth: {stats['avg_depth']:.2f}")
        print(f"   Level 5 nodes: {stats['depth_distribution'].get(5, 0)}")
        
        if not stats['validation_passed']:
            print(f"⚠️ Validation issues:")
            for issue in stats['issues']:
                print(f"   - {issue}")
        else:
            print("✅ Structure validation passed")
        
        result['_validation_stats'] = stats
    
    return result

def analyze_chunks_for_merging(
    chunks: List[Dict], 
    structure: Dict,
    clova_api_key: str = "", 
    clova_api_url: str = ""
) -> Dict[str, Any]:
    """
    Analyze chunks for merging with deep structure awareness.
    Uses hybrid async + ThreadPool for performance.
    
    Args:
        chunks: List of text chunks with metadata
        structure: Hierarchical structure from extract_deep_merge_structure
        clova_api_key: API key
        clova_api_url: API URL
    
    Returns:
        Dict with analysis_results containing chunk mappings
    """
    
    results = []
    
    # Extract all concept names from structure (all levels)
    structure_concepts = []
    
    # Add domain
    if structure.get('domain', {}).get('name'):
        structure_concepts.append(structure['domain']['name'])
    
    # Add categories and their nested concepts
    for cat in structure.get('categories', []):
        if cat.get('name'):
            structure_concepts.append(cat['name'])
        
        for concept in cat.get('concepts', []):
            if concept.get('name'):
                structure_concepts.append(concept['name'])
            
            for subconcept in concept.get('subconcepts', []):
                if subconcept.get('name'):
                    structure_concepts.append(subconcept['name'])
                
                for detail in subconcept.get('details', []):
                    if detail.get('name'):
                        structure_concepts.append(detail['name'])
    
    if not structure_concepts:
        print("⚠️ No structure concepts found")
        return {"analysis_results": []}
    
    print(f"📋 Analyzing {len(chunks)} chunks against {len(structure_concepts)} concepts")
    
    BATCH_SIZE = 10  # Define an appropriate default value for BATCH_SIZE
    MAX_CHUNK_TEXT = MAX_CHUNK_TEXT_LENGTH
    MAX_CONCURRENT_BATCHES = 5

    async def process_batch(batch_start: int, batch: List[Dict]) -> List[Dict]:
        """Process a batch of chunks asynchronously"""
        
        # Prepare chunks text
        chunks_text = ""
        for i, chunk in enumerate(batch):
            text = chunk.get('text', '')[:MAX_CHUNK_TEXT].replace('\n', ' ').strip()
            chunks_text += f"[Chunk {i}]: {text}\n\n"
        
        # Format structure concepts (show top 10 for context)
        concepts_display = ", ".join(structure_concepts[:10])
        if len(structure_concepts) > 10:
            concepts_display += f" ... and {len(structure_concepts) - 10} more"
        
        prompt = CHUNK_ANALYSIS_PROMPT_TEMPLATE.format(
            structure_concepts=concepts_display,
            chunks_text=chunks_text
        )
        
        llm_result = await call_llm_async(
            prompt,
            max_tokens=2000,
            system_message=SYSTEM_MESSAGE,
            clova_api_key=clova_api_key,
            clova_api_url=clova_api_url
        )
        
        # Process results
        batch_results = []
        if isinstance(llm_result, list):
            for analysis in llm_result:
                idx = analysis.get('chunk_index', 0)
                if idx < len(batch):
                    batch_results.append({
                        'chunk_index': batch_start + idx,
                        'text': batch[idx].get('text', ''),
                        'primary_concept': analysis.get('primary_concept', ''),
                        'merge_potential': analysis.get('merge_potential', 'medium'),
                        'summary': analysis.get('summary', batch[idx].get('text', '')[:80]),
                        'key_claims': analysis.get('key_claims', [])
                    })
        elif isinstance(llm_result, dict) and 'chunks' in llm_result:
            # Handle alternative response format
            for analysis in llm_result['chunks']:
                idx = analysis.get('chunk_index', 0)
                if idx < len(batch):
                    batch_results.append({
                        'chunk_index': batch_start + idx,
                        'text': batch[idx].get('text', ''),
                        'primary_concept': analysis.get('primary_concept', ''),
                        'merge_potential': analysis.get('merge_potential', 'medium'),
                        'summary': analysis.get('summary', batch[idx].get('text', '')[:80]),
                        'key_claims': analysis.get('key_claims', [])
                    })
        
        return batch_results

    async def run_all_batches():
        """Run all batches with concurrency control"""
        nonlocal results
        
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_BATCHES)
        
        tasks = []
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            # Run async function in thread pool
            task = loop.run_in_executor(
                executor, 
                lambda s=start, b=batch: asyncio.run(process_batch(s, b))
            )
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks)
        
        for br in batch_results:
            results.extend(br)
        
        executor.shutdown(wait=True)

    # Run the async batch processing
    asyncio.run(run_all_batches())
    
    print(f"✅ Analyzed {len(results)} chunks")
    
    # Calculate statistics
    high_potential = sum(1 for r in results if r.get('merge_potential') == 'high')
    medium_potential = sum(1 for r in results if r.get('merge_potential') == 'medium')
    low_potential = sum(1 for r in results if r.get('merge_potential') == 'low')
    
    print(f"📊 Merge Potential Distribution:")
    print(f"   High: {high_potential} ({high_potential/len(results)*100:.1f}%)")
    print(f"   Medium: {medium_potential} ({medium_potential/len(results)*100:.1f}%)")
    print(f"   Low: {low_potential} ({low_potential/len(results)*100:.1f}%)")
    
    return {
        "analysis_results": results,
        "statistics": {
            "total_chunks": len(results),
            "high_potential": high_potential,
            "medium_potential": medium_potential,
            "low_potential": low_potential
        }
    }

# ============================================================================
# MERGE CANDIDATE IDENTIFICATION
# ============================================================================

def identify_merge_candidates(
    structures: List[Dict],
    similarity_threshold: float = 0.75,
    clova_api_key: str = "",
    clova_api_url: str = ""
) -> List[Dict]:
    """
    Identify merge candidates across multiple document structures.
    Uses LLM to intelligently find semantically similar nodes.
    
    Args:
        structures: List of document structures from extract_deep_merge_structure
        similarity_threshold: Minimum similarity score (0.0-1.0) for merge candidates
        clova_api_key: API key
        clova_api_url: API URL
    
    Returns:
        List of merge candidate groups with similarity scores
    """
    
    if len(structures) < 2:
        print("⚠️ Need at least 2 structures to identify merge candidates")
        return []
    
    print(f"🔍 Identifying merge candidates across {len(structures)} structures...")
    
    # Extract all nodes from all structures with their paths
    all_nodes = []
    for doc_idx, structure in enumerate(structures):
        doc_name = structure.get('domain', {}).get('name', f'Document_{doc_idx}')
        
        # Extract nodes at each level
        def extract_nodes(node, level, path, parent_synthesis=""):
            node_info = {
                'doc_index': doc_idx,
                'doc_name': doc_name,
                'level': level,
                'name': node.get('name', ''),
                'synthesis': node.get('synthesis', ''),
                'path': path,
                'parent_synthesis': parent_synthesis
            }
            all_nodes.append(node_info)
            
            # Recursively extract children
            if level == 2:  # Category
                for concept in node.get('concepts', []):
                    extract_nodes(concept, 3, f"{path}/{concept.get('name', '')}", node.get('synthesis', ''))
            elif level == 3:  # Concept
                for subconcept in node.get('subconcepts', []):
                    extract_nodes(subconcept, 4, f"{path}/{subconcept.get('name', '')}", node.get('synthesis', ''))
            elif level == 4:  # Subconcept
                for detail in node.get('details', []):
                    extract_nodes(detail, 5, f"{path}/{detail.get('name', '')}", node.get('synthesis', ''))
        
        # Start from domain
        if structure.get('domain'):
            domain = structure['domain']
            all_nodes.append({
                'doc_index': doc_idx,
                'doc_name': doc_name,
                'level': 1,
                'name': domain.get('name', ''),
                'synthesis': domain.get('synthesis', ''),
                'path': domain.get('name', ''),
                'parent_synthesis': ''
            })
        
        # Extract categories and below
        for category in structure.get('categories', []):
            cat_name = category.get('name', '')
            extract_nodes(category, 2, f"{doc_name}/{cat_name}", structure.get('domain', {}).get('synthesis', ''))
    
    print(f"📊 Extracted {len(all_nodes)} nodes from all structures")
    
    # Group nodes by level for fair comparison
    nodes_by_level = {}
    for node in all_nodes:
        level = node['level']
        if level not in nodes_by_level:
            nodes_by_level[level] = []
        nodes_by_level[level].append(node)
    
    merge_candidates = []
    
    # Process each level separately
    for level, nodes in sorted(nodes_by_level.items()):
        if len(nodes) < 2:
            continue
        
        print(f"🔎 Analyzing level {level} ({len(nodes)} nodes)...")
        
        # Batch nodes for LLM analysis
        BATCH_SIZE = 20
        for batch_start in range(0, len(nodes), BATCH_SIZE):
            batch = nodes[batch_start:batch_start + BATCH_SIZE]
            
            # Prepare prompt
            nodes_text = ""
            for idx, node in enumerate(batch):
                nodes_text += f"""[Node {idx}]
Document: {node['doc_name']}
Level: {node['level']}
Name: {node['name']}
Synthesis: {node['synthesis']}
Path: {node['path']}
Parent Context: {node['parent_synthesis'][:100]}

"""
            
            prompt = f"""You are analyzing nodes from multiple documents to identify merge candidates.

NODES TO COMPARE (Level {level}):
{nodes_text}

TASK: Identify groups of nodes that should be merged together.

MERGE CRITERIA:
1. **Semantic Similarity**: Nodes discuss the same core concept, even with different terminology
   Example: "Data Processing" ≈ "Information Processing" ≈ "Data Manipulation"

2. **Hierarchical Consistency**: Nodes at the same level with similar parent contexts
   Example: Both are "subconcepts" under similar "concepts"

3. **Synthesis Overlap**: Descriptions cover similar ground with >70% conceptual overlap
   Example: "Methods for data cleaning" ≈ "Techniques for data preprocessing"

4. **Generalization Potential**: Can be merged into a common general term
   Example: "Python Lists", "Java ArrayList" → "Dynamic Arrays"

SIMILARITY SCORING:
- 0.95-1.0: Near-identical concepts, different phrasing (e.g., "ML" vs "Machine Learning")
- 0.85-0.94: Same core concept, minor scope differences (e.g., "Data Cleaning" vs "Data Preprocessing")
- 0.75-0.84: Related concepts that can be merged under general term (e.g., "REST API" vs "HTTP Services")
- 0.60-0.74: Somewhat related but distinct subconcepts
- Below 0.60: Too different to merge

DO NOT MERGE:
- Nodes with same name but completely different contexts
- Generic terms that appear everywhere ("Introduction", "Conclusion", "Overview")
- Nodes where merging would lose important distinctions

OUTPUT FORMAT (JSON array of merge groups):
[
  {{
    "merge_group_id": "unique_id_1",
    "merged_name": "Suggested general name for merged node",
    "similarity_score": 0.87,
    "level": {level},
    "nodes": [
      {{
        "node_index": 0,
        "doc_name": "Document name",
        "original_name": "Original node name",
        "synthesis": "Original synthesis"
      }},
      {{
        "node_index": 5,
        "doc_name": "Another document",
        "original_name": "Another node name",
        "synthesis": "Another synthesis"
      }}
    ],
    "merged_synthesis": "Combined synthesis that captures all nodes (150-200 chars)",
    "merge_rationale": "Why these nodes should merge (80 chars)"
  }}
]

EXAMPLES:

Example 1 - High Similarity (0.92):
{{
  "merge_group_id": "mg_001",
  "merged_name": "Data Processing Pipelines",
  "similarity_score": 0.92,
  "level": 3,
  "nodes": [
    {{"node_index": 0, "doc_name": "ETL Guide", "original_name": "Data Processing", "synthesis": "Methods for transforming raw data"}},
    {{"node_index": 3, "doc_name": "Analytics Manual", "original_name": "Data Pipeline Operations", "synthesis": "Techniques for data transformation"}}
  ],
  "merged_synthesis": "Comprehensive methods and techniques for transforming, processing, and moving data through analytical pipelines including ETL operations",
  "merge_rationale": "Both describe data transformation processes with similar scope"
}}

Example 2 - Medium Similarity (0.78):
{{
  "merge_group_id": "mg_002",
  "merged_name": "API Communication Patterns",
  "similarity_score": 0.78,
  "level": 4,
  "nodes": [
    {{"node_index": 1, "doc_name": "REST Guide", "original_name": "REST API Design", "synthesis": "RESTful service patterns"}},
    {{"node_index": 7, "doc_name": "Microservices", "original_name": "HTTP Service Communication", "synthesis": "HTTP-based inter-service calls"}}
  ],
  "merged_synthesis": "Patterns for HTTP-based service communication including RESTful design principles and inter-service API protocols",
  "merge_rationale": "Both cover HTTP-based service communication, mergeable under general API term"
}}

VALIDATION:
✓ Only include groups with similarity_score >= {similarity_threshold}
✓ Each group must have at least 2 nodes
✓ Merged_name should be general and inclusive
✓ Merged_synthesis should combine key points from all nodes
✓ No duplicate node_index values across groups

Return ONLY the JSON array of merge groups."""

            result = call_llm_sync(
                prompt,
                max_tokens=3000,
                system_message=SYSTEM_MESSAGE,
                clova_api_key=clova_api_key,
                clova_api_url=clova_api_url
            )
            
            if isinstance(result, list):
                # Filter by threshold and validate
                for group in result:
                    if group.get('similarity_score', 0) >= similarity_threshold:
                        # Map node indices back to actual nodes
                        actual_nodes = []
                        for node_ref in group.get('nodes', []):
                            idx = node_ref.get('node_index')
                            if idx < len(batch):
                                actual_node = batch[idx].copy()
                                actual_node['original_name'] = node_ref.get('original_name', '')
                                actual_nodes.append(actual_node)
                        
                        if len(actual_nodes) >= 2:
                            group['nodes'] = actual_nodes
                            merge_candidates.append(group)
    
    # Sort by similarity score (highest first)
    merge_candidates.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    print(f"✅ Found {len(merge_candidates)} merge candidate groups")
    
    # Print summary
    if merge_candidates:
        print(f"\n📋 Top Merge Candidates:")
        for i, group in enumerate(merge_candidates[:5]):
            print(f"{i+1}. {group.get('merged_name')} (similarity: {group.get('similarity_score', 0):.2f})")
            print(f"   Merging {len(group.get('nodes', []))} nodes from level {group.get('level')}")
            print(f"   Rationale: {group.get('merge_rationale', '')}")
            print()
    
    return merge_candidates

def apply_merge_candidates(
    structures: List[Dict],
    merge_candidates: List[Dict],
    min_confidence: float = 0.80
) -> List[Dict]:
    """
    Apply identified merge candidates to create unified structures.
    
    Args:
        structures: Original document structures
        merge_candidates: Merge candidates from identify_merge_candidates
        min_confidence: Minimum similarity score to actually perform merge
    
    Returns:
        List of structures with merged nodes
    """
    
    print(f"🔧 Applying {len(merge_candidates)} merge candidates (min confidence: {min_confidence})...")
    
    # Filter candidates by confidence
    candidates_to_apply = [
        c for c in merge_candidates 
        if c.get('similarity_score', 0) >= min_confidence
    ]
    
    print(f"📊 Applying {len(candidates_to_apply)} high-confidence merges")
    
    # TODO: Implement actual merging logic
    # This would involve:
    # 1. Creating a merged node with combined synthesis
    # 2. Updating references in parent nodes
    # 3. Combining child nodes intelligently
    # 4. Maintaining document provenance
    
    # For now, return original structures with merge metadata
    merged_structures = []
    for structure in structures:
        merged_structure = structure.copy()
        merged_structure['_applied_merges'] = len(candidates_to_apply)
        merged_structure['_merge_candidates'] = candidates_to_apply
        merged_structures.append(merged_structure)
    
    print(f"✅ Merge application complete")
    
    return merged_structures

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Alias for backward compatibility with existing code
extract_merge_optimized_structure = extract_deep_merge_structure
call_llm_merge_optimized = call_llm_sync