"""
HyperCLOVA X Resource Discovery Module
Discovers academic resources (IEEE, Google Scholar) using web search
"""
import uuid
import requests
import json
from typing import Dict, Any, List

from ..model.GapSuggestion import GapSuggestion
from .neo4j_graph import create_evidence_node_safe, now_iso


def call_hyperclova_with_web_search(prompt: str, max_tokens: int,
                                    api_key: str, api_url: str,
                                    enable_web_search: bool = True) -> Any:
    """
    Call HyperCLOVA X API with web search capability
    
    Args:
        prompt: User prompt
        max_tokens: Maximum tokens in response
        api_key: HyperCLOVA X API key
        api_url: API endpoint URL
        enable_web_search: Enable web search tool
        
    Returns:
        Parsed response (list or dict) or empty dict on error
    """
    
    headers = {
        'X-NCP-CLOVASTUDIO-API-KEY': api_key,
        'X-NCP-APIGW-API-KEY': api_key,
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json; charset=utf-8',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': str(uuid.uuid4())
    }
    
    payload = {
        'messages': [
            {
                'role': 'system',
                'content': 'You are a research assistant that searches for academic papers. Return only valid JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'maxTokens': max_tokens,
        'temperature': 0.3,
        'topP': 0.8,
        'repeatPenalty': 1.2
    }
    
    # Add web search tool if enabled
    if enable_web_search:
        payload['tools'] = [
            {
                'type': 'web_search',
                'enabled': True
            }
        ]
    
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
            except json.JSONDecodeError:
                print(f"⚠️  Could not parse response as JSON: {content[:200]}")
                return {}
        
        return {}
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️  HyperCLOVA X API error: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return {}


def discover_resources_with_hyperclova(session, workspace_id: str,
                                      clova_api_key: str, clova_api_url: str) -> int:
    """
    Use HyperCLOVA X web search to find academic resources
    NO ADDITIONAL API KEYS NEEDED!
    
    STRATEGY:
    - Select top 5 nodes with most evidence (cross-file aggregation)
    - Batch web search via HyperCLOVA X
    - Extract IEEE/Scholar URLs from results
    - Store in GapSuggestion.TargetFileId field
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        clova_api_key: HyperCLOVA X API key
        clova_api_url: API endpoint URL
        
    Returns:
        Number of suggestions created
    """
    
    print("\n🔍 Discovering academic resources with HyperCLOVA X web search...")
    from src.model.Evidence import Evidence
    
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
    
    # Batch search prompt for HyperCLOVA X
    prompt = """Search the web for recent academic papers about these concepts. For each, find 2 papers from IEEE Xplore or Google Scholar.

Concepts:
"""
    
    for i, node in enumerate(top_nodes, 1):
        synthesis = node.get('synthesis', '')[:100]
        prompt += f"{i}. {node['name']}: {synthesis}...\n"
    
    prompt += """
For each concept, return the paper title and direct URL.

Return JSON:
[
  {
    "concept_index": 1,
    "papers": [
      {"title": "...", "url": "https://ieeexplore.ieee.org/...", "source": "IEEE"},
      {"title": "...", "url": "https://scholar.google.com/...", "source": "Scholar"}
    ]
  }
]

IMPORTANT: 
- Use web search to find real, current papers
- Provide actual URLs, not search pages
- Prioritize papers from 2023-2024
"""
    
    # Call HyperCLOVA X with web search enabled
    try:
        print("  🌐 Calling HyperCLOVA X web search API...")
        
        result_data = call_hyperclova_with_web_search(
            prompt=prompt,
            max_tokens=2000,
            api_key=clova_api_key,
            api_url=clova_api_url,
            enable_web_search=True  # KEY: Enable web search
        )
        
        suggestions_data = result_data if isinstance(result_data, list) else []
        suggestion_count = 0
        
        for item in suggestions_data:
            concept_idx = item.get('concept_index', 0) - 1
            
            if concept_idx < 0 or concept_idx >= len(top_nodes):
                continue
            
            node_id = top_nodes[concept_idx]['id']
            papers = item.get('papers', [])
            
            print(f"\n  📚 Resources for '{top_nodes[concept_idx]['name']}':")
            
            for paper in papers[:2]:  # Max 2 per concept
                title = paper.get('title', '')
                url = paper.get('url', '')
                source = paper.get('source', 'Unknown')
                
                if not title or not url:
                    continue
                
                # Validate URL
                if not url.startswith('http'):
                    print(f"    ⚠️  Invalid URL: {url}")
                    continue
                
                # Create GapSuggestion with URL in TargetFileId
                gap = GapSuggestion(
                    SuggestionText=f"[{source}] {title[:120]}",
                    TargetNodeId=node_id,
                    TargetFileId=url,  # Actual paper URL
                    SimilarityScore=0.85  # High relevance (from top nodes)
                )
                
                evidence = Evidence(
                    Text=gap.SuggestionText,
                )
                create_evidence_node_safe(session, evidence, node_id)
                suggestion_count += 1
                
                print(f"    ✓ [{source}] {title[:60]}...")
                print(f"      {url}")
        
        print(f"\n✅ Created {suggestion_count} resource suggestions")
        return suggestion_count
    
    except Exception as e:
        print(f"⚠️  HyperCLOVA X web search error: {e}")
        import traceback
        traceback.print_exc()
        return 0
