"""Resource discovery using HyperCLOVA X web search"""
import json
import uuid
import requests
from typing import Dict, Any, List
from ..model.GapSuggestion import GapSuggestion


def create_gap_suggestion_node(session, gap: GapSuggestion, target_node_id: str):
    """Create a GapSuggestion node in Neo4j and link it to target node"""
    
    gap_id = str(uuid.uuid4())
    
    session.run(
        """
        CREATE (g:GapSuggestion {
            id: $id,
            suggestion_text: $text,
            target_node_id: $target_node_id,
            target_file_id: $target_file_id,
            similarity_score: $similarity,
            created_at: datetime()
        })
        """,
        id=gap_id,
        text=gap.SuggestionText,
        target_node_id=gap.TargetNodeId,
        target_file_id=gap.TargetFileId,
        similarity=gap.SimilarityScore
    )
    
    # Link to target node
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (g:GapSuggestion {id: $gap_id})
        MERGE (n)-[:HAS_RESOURCE_SUGGESTION]->(g)
        """,
        node_id=target_node_id,
        gap_id=gap_id
    )
    
    return gap_id


def call_hyperclova_with_web_search(
    prompt: str,
    max_tokens: int,
    api_key: str,
    api_url: str,
    enable_web_search: bool = True
) -> Any:
    """
    Call HyperCLOVA X API with web search capability
    
    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response
        api_key: CLOVA API key
        api_url: CLOVA API URL
        enable_web_search: Whether to enable web search tool
    
    Returns:
        Parsed JSON response or dict
    """
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': str(uuid.uuid4()),
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    payload = {
        'messages': [
            {
                'role': 'system',
                'content': 'You are a research assistant that searches for academic papers. Return ONLY valid JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'maxTokens': max_tokens,
        'temperature': 0.3,
        'topP': 0.8
    }
    
    # Add tools if web search is enabled
    # Note: HyperCLOVA X web search API format may vary
    # This is a simplified version - adjust based on actual API
    if enable_web_search:
        payload['enableWebSearch'] = True
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract content from response
        if 'result' in data and 'message' in data['result']:
            content = data['result']['message'].get('content', '')
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                return json.loads(content)
            except:
                # Return as-is if not JSON
                return content
        
        return {}
    
    except Exception as e:
        print(f"  ⚠️  HyperCLOVA X error: {e}")
        return {}


def discover_resources_with_hyperclova(
    session,
    workspace_id: str,
    clova_api_key: str,
    clova_api_url: str
) -> int:
    """
    Use HyperCLOVA X web search to find academic resources
    NO ADDITIONAL API KEYS NEEDED!
    
    STRATEGY:
    - Select top 5 nodes with most evidence (cross-file aggregation)
    - Batch web search via HyperCLOVA X
    - Extract IEEE/Scholar URLs from results
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        clova_api_key: CLOVA API key
        clova_api_url: CLOVA API URL
    
    Returns:
        Number of suggestions created
    """
    
    print(f"\n🔍 Phase 7: Discovering academic resources...")
    
    # Find top nodes by evidence count (most merged)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE coalesce(n.evidence_count, 0) > 1
        RETURN n.id as id, 
               n.name as name, 
               n.synthesis as synthesis,
               coalesce(n.evidence_count, 0) as evidence,
               coalesce(n.confidence, 0) as confidence
        ORDER BY n.evidence_count DESC, n.confidence DESC
        LIMIT 5
        """,
        ws=workspace_id
    )
    
    top_nodes = [dict(r) for r in result]
    
    if not top_nodes:
        print(f"  ℹ️  No multi-file nodes found for resource discovery")
        return 0
    
    print(f"  📊 Selected {len(top_nodes)} top nodes for resource discovery")
    
    # Batch search prompt for HyperCLOVA X
    prompt = """Search the web for recent academic papers about these concepts. For each, find 2 papers from IEEE Xplore, Google Scholar, or arXiv.

Concepts:
"""
    
    for i, node in enumerate(top_nodes, 1):
        synthesis_preview = node['synthesis'][:100] if node['synthesis'] else "No description"
        prompt += f"{i}. {node['name']}: {synthesis_preview}...\n"
    
    prompt += """
For each concept, return the paper title and direct URL.

Return JSON array:
[
  {
    "concept_index": 1,
    "papers": [
      {"title": "Paper Title Here", "url": "https://ieeexplore.ieee.org/document/...", "source": "IEEE"},
      {"title": "Another Paper", "url": "https://scholar.google.com/...", "source": "Scholar"}
    ]
  }
]

IMPORTANT: 
- Use web search to find real, current papers
- Provide actual URLs to papers, not search pages
- Prioritize papers from 2023-2024
- Return ONLY the JSON array"""
    
    # Call HyperCLOVA X with web search enabled
    try:
        result = call_hyperclova_with_web_search(
            prompt=prompt,
            max_tokens=2000,
            api_key=clova_api_key,
            api_url=clova_api_url,
            enable_web_search=True
        )
        
        # Parse results
        if isinstance(result, list):
            suggestions_data = result
        elif isinstance(result, dict) and 'concepts' in result:
            suggestions_data = result['concepts']
        else:
            suggestions_data = []
        
        suggestion_count = 0
        
        for item in suggestions_data:
            concept_idx = item.get('concept_index', 0) - 1
            
            if concept_idx < 0 or concept_idx >= len(top_nodes):
                continue
            
            node_id = top_nodes[concept_idx]['id']
            node_name = top_nodes[concept_idx]['name']
            papers = item.get('papers', [])
            
            for paper in papers[:2]:  # Max 2 per concept
                title = paper.get('title', '')
                url = paper.get('url', '')
                source = paper.get('source', 'Unknown')
                
                if not title or not url:
                    continue
                
                # Validate URL format
                if not url.startswith('http'):
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
                
                print(f"  ✓ Added resource for '{node_name}': {title[:60]}...")
        
        print(f"✓ Created {suggestion_count} resource suggestions")
        return suggestion_count
    
    except Exception as e:
        print(f"  ⚠️  HyperCLOVA X web search error: {e}")
        return 0
