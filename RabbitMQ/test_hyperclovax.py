"""
HyperCLOVA X Resource Discovery Module with TTON
Applies Tree/Token-Based Thought Organization & Normalization
to reduce token usage by 30-80%
"""
import uuid
import requests
import json
from typing import Dict, Any, List

from src.model.GapSuggestion import GapSuggestion
from src.pipeline.neo4j_graph import create_gap_suggestion_node, now_iso


def compress_to_tton(nodes: List[Dict]) -> str:
    """
    Convert node data to TTON format (Tree/Token-Based representation)
    Reduces tokens by 30-80% compared to raw JSON/text
    
    TTON Format:
    N[id]│name│syn:synthesis│ev:count│cf:score
    
    Example:
    N[1]│Neural Networks│syn:Deep learning architectures...│ev:5│cf:0.92
    N[2]│Transformers│syn:Attention mechanisms for...│ev:4│cf:0.88
    
    Args:
        nodes: List of node dictionaries
        
    Returns:
        TTON-compressed string
    """
    tton_lines = []
    
    for i, node in enumerate(nodes, 1):
        # Extract and truncate fields
        name = node.get('name', 'Unknown')[:40]
        synthesis = node.get('synthesis', '')[:80]  # Shorter synthesis
        evidence = node.get('evidence', 0)
        confidence = node.get('confidence', 0.0)
        
        # Compact TTON format: N[index]│name│syn:text│ev:count│cf:score
        tton_line = f"N[{i}]│{name}│syn:{synthesis}│ev:{evidence}│cf:{confidence:.2f}"
        tton_lines.append(tton_line)
    
    return "\n".join(tton_lines)


def parse_tton_response(tton_text: str, original_nodes: List[Dict]) -> List[Dict]:
    """
    Parse TTON-formatted response back to structured data
    
    Expected TTON response format:
    N[1]│title:Paper Title│url:https://...│src:IEEE
    N[1]│title:Another Paper│url:https://...│src:Scholar
    N[2]│title:Paper Title│url:https://...│src:IEEE
    
    Args:
        tton_text: TTON response string
        original_nodes: Original node list for mapping indices
        
    Returns:
        List of parsed paper dictionaries
    """
    results = []
    
    for line in tton_text.strip().split('\n'):
        if not line.startswith('N['):
            continue
        
        try:
            # Parse: N[1]│title:...│url:...│src:...
            parts = line.split('│')
            
            # Extract index
            idx_str = parts[0].replace('N[', '').replace(']', '')
            concept_idx = int(idx_str) - 1
            
            if concept_idx < 0 or concept_idx >= len(original_nodes):
                continue
            
            # Parse key:value pairs
            paper = {'concept_index': concept_idx + 1}
            
            for part in parts[1:]:
                if ':' not in part:
                    continue
                
                key, value = part.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'title':
                    paper['title'] = value
                elif key == 'url':
                    paper['url'] = value
                elif key == 'src':
                    paper['source'] = value
            
            if 'title' in paper and 'url' in paper:
                results.append(paper)
        
        except Exception as e:
            print(f"  ⚠️  TTON parse error on line: {line[:50]}... ({e})")
            continue
    
    return results


def call_hyperclova_with_tton(prompt: str, max_tokens: int,
                               api_key: str, model: str = "HCX-005") -> Any:
    """
    Call HyperCLOVA X API with TTON-optimized prompt
    
    Args:
        prompt: TTON-compressed prompt
        max_tokens: Maximum tokens in response
        api_key: HyperCLOVA X API key
        model: Model name (HCX-005 or HCX-003)
        
    Returns:
        Raw response text or empty string on error
    """
    
    api_url = f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{model}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a research assistant. Use TTON format for responses. Return each paper as: N[idx]│title:...│url:...│src:IEEE/Scholar"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "topP": 0.8,
        "topK": 0,
        "temperature": 0.5,
        "maxTokens": max_tokens,
        "repetitionPenalty": 1.1,
        "includeAiFilters": True
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract content from response
        if 'result' in data and 'message' in data['result']:
            content = data['result']['message'].get('content', '')
            return content
        
        return ""
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️  HyperCLOVA X API error: {e}")
        return ""
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return ""


def discover_resources_with_hyperclova(session, workspace_id: str,
                                      clova_api_key: str, 
                                      clova_model: str = "HCX-005") -> int:
    """
    Use HyperCLOVA X with TTON to find academic resources
    Token reduction: 30-80% compared to raw JSON prompts
    
    TTON STRATEGY:
    - Compress node data to compact tree format (N[idx]│name│syn:...│ev:...│cf:...)
    - Request TTON response format from LLM
    - Parse TTON back to structured data
    - Store URLs in GapSuggestion.TargetFileId
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        clova_api_key: HyperCLOVA X API key
        clova_model: Model name (HCX-005 or HCX-003)
        
    Returns:
        Number of suggestions created
    """
    
    print("\n🔍 Discovering academic resources with HyperCLOVA X + TTON...")
    
    # Find top nodes by evidence count (most merged)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE n.evidence_count > 1  // Multi-file nodes only
        RETURN n.id as id, 
               n.name as name, 
               n.synthesis as synthesis,
               n.evidence_count as evidence,
               n.confidence as confidence
        ORDER BY n.evidence_count DESC, n.confidence DESC
        LIMIT 5
        """,
        ws=workspace_id
    )
    
    top_nodes = [dict(r) for r in result]
    
    if not top_nodes:
        print("  ℹ️  No multi-file nodes found, skipping resource discovery")
        return 0
    
    print(f"  📊 Found {len(top_nodes)} top nodes for resource discovery")
    
    # 🚀 TTON Compression
    tton_nodes = compress_to_tton(top_nodes)
    
    print(f"  🗜️  TTON compression applied:")
    print(f"     Original: ~{len(str(top_nodes))} chars")
    print(f"     TTON: ~{len(tton_nodes)} chars")
    print(f"     Reduction: ~{100 - (len(tton_nodes)/len(str(top_nodes))*100):.1f}%")
    
    # Compact TTON prompt
    prompt = f"""Search web for 2 recent papers (IEEE/Scholar, 2023-2024) per concept.

TTON Data:
{tton_nodes}

TTON Response Format:
N[idx]│title:Paper Title│url:https://ieeexplore.ieee.org/...│src:IEEE
N[idx]│title:Another Paper│url:https://scholar.google.com/...│src:Scholar

Rules:
- Real URLs only (not search pages)
- Use web search to find current papers
- 2 papers per N[idx]"""
    
    # Call HyperCLOVA X with TTON
    try:
        print("  🌐 Calling HyperCLOVA X API with TTON prompt...")
        
        response_text = call_hyperclova_with_tton(
            prompt=prompt,
            max_tokens=1500,
            api_key=clova_api_key,
            model=clova_model
        )
        
        if not response_text:
            print("  ⚠️  Empty response from API")
            return 0
        
        print(f"  📥 Received response ({len(response_text)} chars)")
        
        # Parse TTON response
        papers = parse_tton_response(response_text, top_nodes)
        
        suggestion_count = 0
        
        for paper in papers:
            concept_idx = paper.get('concept_index', 0) - 1
            
            if concept_idx < 0 or concept_idx >= len(top_nodes):
                continue
            
            node_id = top_nodes[concept_idx]['id']
            title = paper.get('title', '')
            url = paper.get('url', '')
            source = paper.get('source', 'Unknown')
            
            if not title or not url or not url.startswith('http'):
                continue
            
            # Create GapSuggestion with URL in TargetFileId
            gap = GapSuggestion(
                SuggestionText=f"[{source}] {title[:120]}",
                TargetNodeId=node_id,
                TargetFileId=url,  # Actual paper URL
                SimilarityScore=0.85  # High relevance (from top nodes)
            )
            
            create_gap_suggestion_node(session, gap, node_id)
            suggestion_count += 1
            
            print(f"  ✓ [{source}] {title[:60]}...")
            print(f"    {url}")
        
        print(f"\n✅ Created {suggestion_count} resource suggestions using TTON")
        return suggestion_count
    
    except Exception as e:
        print(f"⚠️  HyperCLOVA X + TTON error: {e}")
        import traceback
        traceback.print_exc()
        return 0


# 🧪 Test TTON compression
if __name__ == "__main__":
    # Sample nodes for testing
    test_nodes = [
        {
            "id": "n1",
            "name": "Neural Network Architectures",
            "synthesis": "Deep learning models with multiple layers that learn hierarchical representations from data",
            "evidence": 5,
            "confidence": 0.92
        },
        {
            "id": "n2",
            "name": "Transformer Models",
            "synthesis": "Attention-based architectures that revolutionized natural language processing tasks",
            "evidence": 4,
            "confidence": 0.88
        }
    ]
    
    print("🧪 TTON Compression Test:")
    print("\nOriginal JSON:")
    print(json.dumps(test_nodes, indent=2))
    
    print("\n🗜️  TTON Compressed:")
    tton = compress_to_tton(test_nodes)
    print(tton)
    
    print(f"\n📊 Token Reduction:")
    print(f"   Original: ~{len(json.dumps(test_nodes))} chars")
    print(f"   TTON: ~{len(tton)} chars")
    print(f"   Reduction: ~{100 - (len(tton)/len(json.dumps(test_nodes))*100):.1f}%")