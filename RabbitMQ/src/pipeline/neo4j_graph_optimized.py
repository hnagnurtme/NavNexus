"""Optimized Neo4j knowledge graph operations with cascading deduplication"""
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import asdict

from ..model.Evidence import Evidence


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def find_best_match(
    session, 
    workspace_id: str, 
    concept_name: str, 
    embedding: List[float]
) -> Optional[Dict[str, Any]]:
    """
    Cascading search: Exact → Very High (>0.90) → High (>0.80) → Medium (>0.70)
    
    Args:
        session: Neo4j session
        workspace_id: Workspace identifier
        concept_name: Name of the concept to match
        embedding: Embedding vector for semantic matching
    
    Returns:
        Dict with keys: id, name, sim, match_type (or None if no match)
    """
    
    # STAGE 1: Exact name match (case-insensitive, fastest)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE toLower(n.name) = toLower($name)
           OR toLower($name) IN [x IN coalesce(n.aliases, []) | toLower(x)]
        RETURN n.id as id, n.name as name, 1.0 as sim, 'exact' as match_type
        LIMIT 1
        """,
        ws=workspace_id,
        name=concept_name
    )
    
    record = result.single()
    if record:
        return dict(record)
    
    # STAGE 2-4: Semantic similarity with cascading thresholds
    for threshold, match_type in [(0.90, 'very_high'), (0.80, 'high'), (0.70, 'medium')]:
        result = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $ws})
            WHERE n.embedding IS NOT NULL
            WITH n, 
                 reduce(dot = 0.0, i IN range(0, size(n.embedding)-1) | 
                     dot + n.embedding[i] * $emb[i]
                 ) as sim
            WHERE sim > $threshold
            RETURN n.id as id, n.name as name, sim, $match_type as match_type
            ORDER BY sim DESC
            LIMIT 1
            """,
            ws=workspace_id,
            emb=embedding,
            threshold=threshold,
            match_type=match_type
        )
        
        record = result.single()
        if record:
            return dict(record)
    
    return None


def create_or_merge_node(
    session,
    workspace_id: str,
    name: str,
    synthesis: str,
    node_type: str,
    level: int,
    file_id: str,
    file_name: str,
    embeddings_cache: Dict[str, List[float]]
) -> Optional[str]:
    """
    Create new node or merge into existing with evidence tracking
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        name: Concept name
        synthesis: Synthesis text (will be truncated to 200 chars)
        node_type: Type of node (domain, category, concept, subconcept)
        level: Hierarchy level (0=domain, 1=category, 2=concept, 3=subconcept)
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings cache
    
    Returns:
        Node ID (str) or None if failed
    """
    
    if not name or not name.strip():
        return None
    
    # Get embedding from cache
    embedding = embeddings_cache.get(name)
    if not embedding:
        print(f"    ⚠️  No embedding for '{name}', skipping")
        return None
    
    # Normalize and validate synthesis
    synthesis = synthesis.strip() if synthesis else ""
    if len(synthesis) < 10:  # Ensure synthesis has meaningful content
        synthesis = f"Information about {name}"
    synthesis = synthesis[:200]  # Truncate to 200 chars
    
    # Try to find existing match
    match = find_best_match(session, workspace_id, name, embedding)
    
    if match:
        # MERGE: Add evidence to existing node
        node_id = match['id']
        match_type = match['match_type']
        similarity = match['sim']
        
        # Calculate confidence boost based on match quality
        confidence_boost = {
            'exact': 1.0,
            'very_high': 0.9,
            'high': 0.8,
            'medium': 0.6
        }.get(match_type, 0.5)
        
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $id})
            SET n.synthesis = CASE 
                    WHEN size(n.synthesis) > 0 
                    THEN n.synthesis + '\\n\\n[' + $file_name + '] ' + $new_synthesis
                    ELSE '[' + $file_name + '] ' + $new_synthesis
                END,
                n.file_ids = CASE
                    WHEN NOT $file_id IN coalesce(n.file_ids, [])
                    THEN coalesce(n.file_ids, []) + $file_id
                    ELSE n.file_ids
                END,
                n.evidence_count = coalesce(n.evidence_count, 1) + 1,
                n.confidence = coalesce(n.confidence, 0.5) + $confidence_boost,
                n.updated_at = datetime(),
                n.aliases = CASE 
                    WHEN NOT $name IN coalesce(n.aliases, []) AND $name <> n.name
                    THEN coalesce(n.aliases, []) + $name
                    ELSE coalesce(n.aliases, [])
                END
            """,
            id=node_id,
            new_synthesis=synthesis,
            file_id=file_id,
            file_name=file_name,
            name=name,
            confidence_boost=confidence_boost
        )
        
        print(f"    ♻️  MERGE ({match_type}, sim={similarity:.2f}): '{name}' → '{match['name']}'")
        
        return node_id
    
    else:
        # CREATE: New node
        node_id = f"{node_type}-{uuid.uuid4().hex[:8]}"
        
        session.run(
            """
            CREATE (n:KnowledgeNode {
                id: $id,
                workspace_id: $ws,
                name: $name,
                type: $type,
                level: $level,
                synthesis: '[' + $file_name + '] ' + $synthesis,
                embedding: $embedding,
                file_ids: [$file_id],
                evidence_count: 1,
                confidence: 0.5,
                aliases: [],
                source_count: 0,
                total_confidence: 0.0,
                created_at: datetime(),
                updated_at: datetime()
            })
            """,
            id=node_id,
            ws=workspace_id,
            name=name,
            type=node_type,
            level=level,
            synthesis=synthesis,
            embedding=embedding,
            file_id=file_id,
            file_name=file_name
        )
        
        print(f"    ✨ CREATE: '{name}'")
        
        return node_id


def create_hierarchical_graph_with_cascading_dedup(
    session,
    workspace_id: str,
    structure: Dict,
    file_id: str,
    file_name: str,
    embeddings_cache: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Ultra-aggressive deduplication with cascading similarity thresholds
    
    STRATEGY:
    1. Exact name match (fastest)
    2. Very high similarity (>0.90) - obvious duplicates
    3. High similarity (>0.80) - semantic equivalents
    4. Medium similarity (>0.70) - related concepts (merge with caution)
    
    EVIDENCE TRACKING:
    - Each merged node tracks: file_ids[], aliases[], confidence_scores[]
    - Synthesis accumulated from all sources
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        structure: Hierarchical structure from LLM
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings {name: vector}
    
    Returns:
        Dict with statistics about node creation/merging
    """
    
    stats = {
        'nodes_created': 0,
        'exact_matches': 0,
        'high_similarity_merges': 0,
        'medium_similarity_merges': 0,
        'final_count': 0,
        'node_ids': []
    }
    
    # Track initial count
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as initial_count
        """,
        ws=workspace_id
    )
    initial_count = result.single()['initial_count'] if result.single() else 0
    
    # Level 0: Domain (root)
    domain = structure.get('domain', {})
    domain_id = None
    
    if domain.get('name'):
        domain_id = create_or_merge_node(
            session, workspace_id,
            domain['name'],
            domain.get('synthesis', ''),
            'domain', 0,
            file_id, file_name,
            embeddings_cache
        )
        
        if domain_id:
            stats['node_ids'].append(domain_id)
    
    # Level 1: Categories
    for cat in structure.get('categories', []):
        if not cat.get('name'):
            continue
        
        cat_id = create_or_merge_node(
            session, workspace_id,
            cat['name'],
            cat.get('synthesis', ''),
            'category', 1,
            file_id, file_name,
            embeddings_cache
        )
        
        if cat_id:
            stats['node_ids'].append(cat_id)
            
            # Link to domain
            if domain_id:
                session.run(
                    """
                    MATCH (parent:KnowledgeNode {id: $parent_id})
                    MATCH (child:KnowledgeNode {id: $child_id})
                    MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
                    """,
                    parent_id=domain_id,
                    child_id=cat_id
                )
        
        # Level 2: Concepts
        for concept in cat.get('concepts', []):
            if not concept.get('name'):
                continue
            
            concept_id = create_or_merge_node(
                session, workspace_id,
                concept['name'],
                concept.get('synthesis', ''),
                'concept', 2,
                file_id, file_name,
                embeddings_cache
            )
            
            if concept_id:
                stats['node_ids'].append(concept_id)
                
                # Link to category
                if cat_id:
                    session.run(
                        """
                        MATCH (parent:KnowledgeNode {id: $parent_id})
                        MATCH (child:KnowledgeNode {id: $child_id})
                        MERGE (parent)-[:CONTAINS_CONCEPT]->(child)
                        """,
                        parent_id=cat_id,
                        child_id=concept_id
                    )
            
            # Level 3: Subconcepts
            for sub in concept.get('subconcepts', []):
                if not sub.get('name'):
                    continue
                
                sub_id = create_or_merge_node(
                    session, workspace_id,
                    sub['name'],
                    sub.get('synthesis', ''),
                    'subconcept', 3,
                    file_id, file_name,
                    embeddings_cache
                )
                
                if sub_id:
                    stats['node_ids'].append(sub_id)
                    
                    # Link to concept
                    if concept_id:
                        session.run(
                            """
                            MATCH (parent:KnowledgeNode {id: $parent_id})
                            MATCH (child:KnowledgeNode {id: $child_id})
                            MERGE (parent)-[:HAS_DETAIL]->(child)
                            """,
                            parent_id=concept_id,
                            child_id=sub_id
                        )
    
    # Calculate final count
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as total
        """,
        ws=workspace_id
    )
    stats['final_count'] = result.single()['total']
    stats['nodes_created'] = stats['final_count'] - initial_count
    
    # Calculate merge statistics from unique node IDs
    unique_nodes = set(stats['node_ids'])
    total_processed = len(stats['node_ids'])
    stats['exact_matches'] = total_processed - len(unique_nodes)
    
    return stats
