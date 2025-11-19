"""Practical resource discovery using knowledge graph analysis"""
import json
import uuid
import requests
import re
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from datetime import datetime

from ..model.GapSuggestion import GapSuggestion


def create_gap_suggestion_node(session, gap: GapSuggestion, target_node_id: str) -> str:
    """Create a GapSuggestion node in Neo4j with proper transaction handling"""
    
    gap_id = f"gap_{uuid.uuid4().hex[:8]}"
    
    try:
        # Use transaction for atomic operations
        with session.begin_transaction() as tx:
            # Create GapSuggestion node
            tx.run(
                """
                CREATE (g:GapSuggestion {
                    id: $id,
                    suggestion_text: $text,
                    target_node_id: $target_node_id,
                    target_file_id: $target_file_id,
                    similarity_score: $similarity,
                    created_at: datetime(),
                    suggestion_type: "resource_recommendation"
                })
                """,
                id=gap_id,
                text=gap.SuggestionText,
                target_node_id=gap.TargetNodeId,
                target_file_id=gap.TargetFileId,
                similarity=gap.SimilarityScore
            )
            
            # Link to target KnowledgeNode
            tx.run(
                """
                MATCH (n:KnowledgeNode {id: $node_id})
                MATCH (g:GapSuggestion {id: $gap_id})
                MERGE (n)-[:HAS_SUGGESTION {type: "resource"}]->(g)
                """,
                node_id=target_node_id,
                gap_id=gap_id
            )
        
        return gap_id
        
    except Exception as e:
        print(f"❌ Failed to create gap suggestion: {e}")
        raise


def validate_academic_url(url: str) -> bool:
    """Validate if URL looks like a legitimate academic source"""
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Parse URL for domain validation
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Known academic domains
    academic_domains = [
        'ieeexplore.ieee.org',
        'scholar.google.com',
        'arxiv.org',
        'acm.org',
        'springer.com',
        'sciencedirect.com',
        'researchgate.net',
        'doi.org',
        'pmc.ncbi.nlm.nih.gov',
        'dl.acm.org'
    ]
    
    # Check if domain contains academic indicators
    academic_indicators = [
        'arxiv', 'ieee', 'acm', 'springer', 'sciencedirect',
        'researchgate', 'scholar', 'academic', 'research',
        'journal', 'conference', 'proceedings'
    ]
    
    # Exact domain match
    if domain in academic_domains:
        return True
    
    # Partial domain match
    if any(indicator in domain for indicator in academic_indicators):
        return True
    
    # Check path for academic patterns
    path = parsed.path.lower()
    academic_path_patterns = [
        r'/document/',
        r'/paper/',
        r'/publication/',
        r'/doi/',
        r'/abs/',
        r'/pdf/'
    ]
    
    return any(re.search(pattern, path) for pattern in academic_path_patterns)


def generate_research_queries(node_name: str, synthesis: str) -> List[str]:
    """Generate specific search queries for academic resources"""
    
    queries = []
    
    # Base queries
    base_queries = [
        f"recent research papers about {node_name}",
        f"{node_name} academic publications 2023 2024",
        f"systematic review {node_name}",
        f"{node_name} state of the art"
    ]
    
    # Extract key terms from synthesis for more specific queries
    words = re.findall(r'\b[a-zA-Z]{5,}\b', synthesis.lower())
    significant_terms = [word for word in words if word not in 
                        ['about', 'research', 'paper', 'study', 'method']]
    
    if significant_terms:
        terms_str = " ".join(significant_terms[:3])
        queries.extend([
            f"{node_name} {terms_str} recent papers",
            f"{terms_str} in {node_name} research"
        ])
    
    queries.extend(base_queries)
    return queries[:5]  # Return top 5 queries


def call_hyperclova_for_resource_suggestions(
    node_name: str,
    synthesis: str,
    max_tokens: int,
    api_key: str,
    api_url: str
) -> List[Dict[str, str]]:
    """
    Use HyperCLOVA to suggest relevant academic resources based on knowledge
    
    STRATEGY: Ask LLM to recommend specific paper types/topics based on the node content
    rather than hallucinating fake URLs.
    """
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-NCP-CLOVASTUDIO-REQUEST-ID': str(uuid.uuid4()),
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # Generate search queries for better context
    search_queries = generate_research_queries(node_name, synthesis)
    
    prompt = f"""Based on this knowledge node, recommend specific academic resources:

NODE: {node_name}
DESCRIPTION: {synthesis[:500]}

SEARCH QUERIES to find relevant papers:
{chr(10).join(f"- {q}" for q in search_queries)}

Recommend 2-3 SPECIFIC types of academic resources that would be most relevant.
For each, provide:
- Specific paper topics or titles to look for
- Relevant conferences/journals
- Key researchers in this area

Return JSON:
{{
  "resources": [
    {{
      "type": "survey_paper|technical_paper|dataset|tool",
      "description": "Specific recommendation",
      "suggested_queries": ["query1", "query2"],
      "relevance_score": 0.9
    }}
  ]
}}"""

    payload = {
        'messages': [
            {
                'role': 'system',
                'content': 'You are an academic research assistant. Recommend specific, actionable resources. Return valid JSON only.'
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
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        content = data.get('result', {}).get('message', {}).get('content', '')
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result.get('resources', [])
        
        return []
        
    except Exception as e:
        print(f"  ⚠️  HyperCLOVA API error: {e}")
        return []


def discover_resources_via_knowledge_analysis(
    session,
    workspace_id: str,
    clova_api_key: str,
    clova_api_url: str
) -> int:
    """
    Practical resource discovery using knowledge graph analysis
    Focus on leaf nodes (nodes without children relationships) that don't have existing GapSuggestions
    
    STRATEGY:
    - Find leaf nodes (no outgoing HAS_SUBCATEGORY, CONTAINS_CONCEPT, HAS_DETAIL relationships)
    - Ensure nodes don't have existing GapSuggestions
    - Generate specific search recommendations for each leaf node
    - Create one GapSuggestion per leaf node
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        clova_api_key: CLOVA API key
        clova_api_url: CLOVA API URL
    
    Returns:
        Number of suggestions created
    """
    
    print(f"\n🔍 Phase 7: Analyzing leaf nodes for resource discovery...")
    
    # Find leaf nodes (nodes without children relationships) that don't have existing GapSuggestions
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(:KnowledgeNode)
        AND NOT (n)-[:HAS_SUGGESTION]->(:GapSuggestion)
        AND size(n.synthesis) > 30
        RETURN n.id as id, 
               n.name as name, 
               n.synthesis as synthesis,
               n.type as type,
               n.level as level,
               n.source_count as source_count,
               n.created_at as created_at
        ORDER BY n.level DESC, n.source_count DESC
        LIMIT 15
        """,
        ws=workspace_id
    )
    
    leaf_nodes = [dict(r) for r in result]
    
    if not leaf_nodes:
        print("  ℹ️  No suitable leaf nodes found for resource analysis")
        return 0
    
    print(f"  📊 Found {len(leaf_nodes)} leaf nodes without suggestions")
    
    suggestion_count = 0
    
    for node in leaf_nodes:
        node_id = node['id']
        node_name = node['name']
        synthesis = node['synthesis']
        node_type = node['type']
        level = node['level']
        
        print(f"  🔍 Analyzing {node_type} leaf node (level {level}): {node_name}")
        
        try:
            # Get resource recommendations from LLM
            resources = call_hyperclova_for_resource_suggestions(
                node_name=node_name,
                synthesis=synthesis,
                max_tokens=1200,
                api_key=clova_api_key,
                api_url=clova_api_url
            )
            
            # Take only the first (most relevant) resource for this leaf node
            if resources:
                resource = resources[0]
                resource_type = resource.get('type', 'technical_paper')
                description = resource.get('description', '')
                relevance = resource.get('relevance_score', 0.7)
                
                if description:
                    # Create search query reference
                    suggested_queries = resource.get('suggested_queries', [])
                    search_context = f"Queries: {', '.join(suggested_queries[:2])}" if suggested_queries else "Check recent publications"
                    
                    # Create GapSuggestion object
                    gap_suggestion = GapSuggestion(
                        Id=f"gap_{uuid.uuid4().hex[:8]}",
                        SuggestionText=f"[{resource_type.upper()}] {description[:120]}",
                        TargetNodeId=node_id,
                        TargetFileId=f"search://{search_context}",
                        SimilarityScore=float(relevance)
                    )
                    
                    # Use the existing create_gap_suggestion_node function
                    create_gap_suggestion_node(session, gap_suggestion, node_id)
                    suggestion_count += 1
                    
                    print(f"    ✓ Created suggestion for {node_type} leaf node: {node_name}")
                else:
                    print(f"    ⚠️  No valid description for node {node_name}")
            else:
                print(f"    ⚠️  No resources returned for node {node_name}")
            
            # Rate limiting between API calls
            time.sleep(1.5)
            
        except Exception as e:
            print(f"    ❌ Failed to analyze leaf node {node_name}: {e}")
            continue
    
    print(f"✓ Created {suggestion_count} resource suggestions for leaf nodes")
    
    return suggestion_count

def suggest_cross_domain_resources(session, workspace_id: str) -> int:
    """
    Identify potential interdisciplinary research opportunities
    """
    
    result = session.run(
        """
        MATCH (n1:KnowledgeNode {workspace_id: $ws})
        MATCH (n2:KnowledgeNode {workspace_id: $ws})
        WHERE n1.id < n2.id
        AND n1.level <= 2 AND n2.level <= 2  // Higher level concepts
        AND NOT (n1)-[:RELATED_TO]-(n2)
        WITH n1, n2,
             reduce(score = 0.0, word IN split(toLower(n1.name), ' ') | 
                 score + CASE WHEN word IN split(toLower(n2.name), ' ') THEN 1.0 ELSE 0.0 END
             ) as name_similarity
        WHERE name_similarity = 0  // Different domains
        RETURN n1.id as id1, n1.name as name1, 
               n2.id as id2, n2.name as name2,
               name_similarity
        ORDER BY n1.evidence_count + n2.evidence_count DESC
        LIMIT 5
        """,
        ws=workspace_id
    )
    
    cross_domain_pairs = [dict(r) for r in result]
    suggestions_created = 0
    
    for pair in cross_domain_pairs:
        # Create suggestion for interdisciplinary research
        gap = GapSuggestion(
            SuggestionText=f"Interdisciplinary research: {pair['name1']} + {pair['name2']}",
            TargetNodeId=pair['id1'],
            TargetFileId="search://interdisciplinary applications",
            SimilarityScore=0.6
        )
        
        try:
            create_gap_suggestion_node(session, gap, pair['id1'])
            suggestions_created += 1
            print(f"    🌉 Suggested interdisciplinary: {pair['name1']} + {pair['name2']}")
        except Exception as e:
            print(f"    ⚠️  Failed to create cross-domain suggestion: {e}")
    
    return suggestions_created


def get_resource_discovery_stats(session, workspace_id: str) -> Dict[str, Any]:
    """Get statistics about resource discovery suggestions"""
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})-[:HAS_SUGGESTION]->(g:GapSuggestion)
        WHERE g.suggestion_type = "resource_recommendation"
        RETURN count(g) as total_suggestions,
               count(DISTINCT n) as nodes_with_suggestions,
               avg(g.similarity_score) as avg_relevance
        """,
        ws=workspace_id
    )
    
    record = result.single()
    if record:
        return dict(record)
    
    return {"total_suggestions": 0, "nodes_with_suggestions": 0, "avg_relevance": 0.0}