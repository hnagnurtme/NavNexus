"""Optimized Neo4j knowledge graph operations with proper entity structure"""
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import asdict

from ..model.KnowledgeNode import KnowledgeNode
from ..model.Evidence import Evidence
from ..model.GapSuggestion import GapSuggestion


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
    """
    # STAGE 1: Exact name match (case-insensitive, fastest)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE toLower(n.name) = toLower($name)
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


def create_evidence_node(session, evidence: Evidence) -> str:
    """Create a separate Evidence node with all fields"""
    session.run(
        """
        CREATE (e:Evidence {
            id: $id,
            source_id: $source_id,
            source_name: $source_name,
            chunk_id: $chunk_id,
            text: $text,
            page: $page,
            confidence: $confidence,
            created_at: $created_at,
            language: $language,
            source_language: $source_language,
            hierarchy_path: $hierarchy_path,
            concepts: $concepts,
            key_claims: $key_claims,
            questions_raised: $questions_raised,
            evidence_strength: $evidence_strength
        })
        """,
        **asdict(evidence)
    )
    return evidence.Id


def create_gap_suggestion_node(session, gap_suggestion: GapSuggestion, knowledge_node_id: str):
    """Create a separate GapSuggestion node and link to KnowledgeNode"""
    session.run(
        """
        CREATE (g:GapSuggestion {
            id: $id,
            suggestion_text: $suggestion_text,
            target_node_id: $target_node_id,
            target_file_id: $target_file_id,
            similarity_score: $similarity_score
        })
        WITH g
        MATCH (n:KnowledgeNode {id: $knowledge_node_id})
        CREATE (n)-[:HAS_SUGGESTION]->(g)
        """,
        **asdict(gap_suggestion),
        knowledge_node_id=knowledge_node_id
    )


def create_knowledge_node(
    session,
    knowledge_node: KnowledgeNode,
    evidence: Evidence,
    embedding: List[float]
) -> str:
    """Create KnowledgeNode with linked Evidence node"""
    
    # Create KnowledgeNode with proper fields
    session.run(
        """
        CREATE (n:KnowledgeNode {
            id: $id,
            type: $type,
            name: $name,
            synthesis: $synthesis,
            workspace_id: $workspace_id,
            level: $level,
            source_count: $source_count,
            total_confidence: $total_confidence,
            created_at: $created_at,
            updated_at: $updated_at,
            embedding: $embedding
        })
        """,
        id=knowledge_node.Id,
        type=knowledge_node.Type,
        name=knowledge_node.Name,
        synthesis=knowledge_node.Synthesis,
        workspace_id=knowledge_node.WorkspaceId,
        level=knowledge_node.Level,
        source_count=knowledge_node.SourceCount,
        total_confidence=knowledge_node.TotalConfidence,
        created_at=knowledge_node.CreatedAt,
        updated_at=knowledge_node.UpdatedAt,
        embedding=embedding
    )
    
    # Create Evidence node and establish relationship
    evidence_id = create_evidence_node(session, evidence)
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (e:Evidence {id: $evidence_id})
        CREATE (n)-[:HAS_EVIDENCE]->(e)
        """,
        node_id=knowledge_node.Id,
        evidence_id=evidence_id
    )
    
    return knowledge_node.Id


def update_knowledge_node_after_merge(
    session,
    node_id: str,
    new_synthesis: str,
    source_name: str
):
    """Update KnowledgeNode after merging with new evidence"""
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $id})
        SET n.synthesis = CASE 
                WHEN size(n.synthesis) > 0 
                THEN n.synthesis + '\\n\\n[' + $source_name + '] ' + $new_synthesis
                ELSE '[' + $source_name + '] ' + $new_synthesis
            END,
            n.source_count = n.source_count + 1,
            n.updated_at = datetime()
        """,
        id=node_id,
        new_synthesis=new_synthesis,
        source_name=source_name
    )


def create_or_merge_knowledge_node(
    session,
    workspace_id: str,
    knowledge_node: KnowledgeNode,
    evidence: Evidence,
    embedding: List[float]
) -> Optional[str]:
    """
    Create new KnowledgeNode or merge into existing with proper entity structure
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        knowledge_node: KnowledgeNode object
        evidence: Evidence object  
        embedding: Pre-computed embedding vector
    
    Returns:
        Node ID (str) or None if failed
    """
    
    if not knowledge_node.Name or not knowledge_node.Name.strip():
        return None
    
    if not embedding:
        print(f"    ⚠️  No embedding for '{knowledge_node.Name}', skipping")
        return None
    
    # Try to find existing match
    match = find_best_match(session, workspace_id, knowledge_node.Name, embedding)
    
    if match:
        # MERGE: Update existing node and create new evidence
        node_id = match['id']
        match_type = match['match_type']
        similarity = match['sim']
        
        # Update the existing KnowledgeNode
        update_knowledge_node_after_merge(
            session, node_id, knowledge_node.Synthesis, evidence.SourceName
        )
        
        # Create new Evidence node and link to existing KnowledgeNode
        evidence_id = create_evidence_node(session, evidence)
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $node_id})
            MATCH (e:Evidence {id: $evidence_id})
            CREATE (n)-[:HAS_EVIDENCE]->(e)
            """,
            node_id=node_id,
            evidence_id=evidence_id
        )
        
        print(f"    ♻️  MERGE ({match_type}, sim={similarity:.2f}): '{knowledge_node.Name}' → '{match['name']}'")
        
        return node_id
    
    else:
        # CREATE: New KnowledgeNode with Evidence
        knowledge_node.Id = f"{knowledge_node.Type}-{uuid.uuid4().hex[:8]}"
        knowledge_node.SourceCount = 1  # Initial source count
        
        node_id = create_knowledge_node(session, knowledge_node, evidence, embedding)
        print(f"    ✨ CREATE: '{knowledge_node.Name}'")
        
        return node_id


def create_parent_child_relationship(
    session,
    parent_id: str,
    child_id: str,
    relationship_type: str
):
    """Create hierarchical relationship between KnowledgeNodes"""
    
    relationship_map = {
        'domain_to_category': 'HAS_SUBCATEGORY',
        'category_to_concept': 'CONTAINS_CONCEPT', 
        'concept_to_subconcept': 'HAS_DETAIL'
    }
    
    cypher_relationship = relationship_map.get(relationship_type, 'HAS_SUBCATEGORY')
    
    session.run(
        f"""
        MATCH (parent:KnowledgeNode {{id: $parent_id}})
        MATCH (child:KnowledgeNode {{id: $child_id}})
        MERGE (parent)-[:{cypher_relationship}]->(child)
        """,
        parent_id=parent_id,
        child_id=child_id
    )


def create_hierarchical_knowledge_graph(
    session,
    workspace_id: str,
    structure: Dict,
    file_id: str,
    file_name: str,
    embeddings_cache: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Create hierarchical knowledge graph with proper entity structure
    
    STRATEGY:
    - Create separate Evidence nodes for each KnowledgeNode
    - Maintain proper relationships between entities
    - Support cascading deduplication
    
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
        'evidence_created': 0,
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
    record = result.single()
    initial_count = record['initial_count'] if record else 0
    
    # Level 0: Domain (root)
    domain = structure.get('domain', {})
    domain_id = None
    
    if domain.get('name'):
        # Create KnowledgeNode for domain
        domain_node = KnowledgeNode(
            Name=domain['name'],
            Synthesis=domain.get('synthesis', ''),
            Type='domain',
            Level=0,
            WorkspaceId=workspace_id
        )
        
        # Create Evidence for domain
        domain_evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            Text=domain.get('synthesis', '')
        )
        
        domain_embedding = embeddings_cache.get(domain['name'])
        if domain_embedding is not None:
            domain_id = create_or_merge_knowledge_node(
                session, workspace_id, domain_node, domain_evidence, domain_embedding
            )
        else:
            print(f"    ⚠️  No embedding for domain '{domain_node.Name}', skipping")
            domain_id = None
        
        if domain_id:
            stats['node_ids'].append(domain_id)
            stats['evidence_created'] += 1
    
    # Level 1: Categories
    for cat in structure.get('categories', []):
        if not cat.get('name'):
            continue
        
        # Create KnowledgeNode for category
        category_node = KnowledgeNode(
            Name=cat['name'],
            Synthesis=cat.get('synthesis', ''),
            Type='category',
            Level=1,
            WorkspaceId=workspace_id
        )
        
        # Create Evidence for category
        category_evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            Text=cat.get('synthesis', '')
        )
        
        category_embedding = embeddings_cache.get(cat['name'])
        if category_embedding is not None:
            cat_id = create_or_merge_knowledge_node(
                session, workspace_id, category_node, category_evidence, category_embedding
            )
        else:
            print(f"    ⚠️  No embedding for category '{category_node.Name}', skipping")
            continue
        
        if cat_id:
            stats['node_ids'].append(cat_id)
            stats['evidence_created'] += 1
            
            # Link to domain
            if domain_id:
                create_parent_child_relationship(
                    session, domain_id, cat_id, 'domain_to_category'
                )
        
        # Level 2: Concepts
        for concept in cat.get('concepts', []):
            if not concept.get('name'):
                continue
            
            # Create KnowledgeNode for concept
            concept_node = KnowledgeNode(
                Name=concept['name'],
                Synthesis=concept.get('synthesis', ''),
                Type='concept',
                Level=2,
                WorkspaceId=workspace_id
            )
            
            # Create Evidence for concept
            concept_evidence = Evidence(
                SourceId=file_id,
                SourceName=file_name,
                Text=concept.get('synthesis', '')
            )
            
            concept_embedding = embeddings_cache.get(concept['name'])
            if concept_embedding is not None:
                concept_id = create_or_merge_knowledge_node(
                    session, workspace_id, concept_node, concept_evidence, concept_embedding
                )
            else:
                print(f"    ⚠️  No embedding for concept '{concept_node.Name}', skipping")
                continue
            
            if concept_id:
                stats['node_ids'].append(concept_id)
                stats['evidence_created'] += 1
                
                # Link to category
                if cat_id:
                    create_parent_child_relationship(
                        session, cat_id, concept_id, 'category_to_concept'
                    )
            
            # Level 3: Subconcepts
            for sub in concept.get('subconcepts', []):
                if not sub.get('name'):
                    continue
                
                # Create KnowledgeNode for subconcept
                subconcept_node = KnowledgeNode(
                    Name=sub['name'],
                    Synthesis=sub.get('synthesis', ''),
                    Type='subconcept',
                    Level=3,
                    WorkspaceId=workspace_id
                )
                
                # Create Evidence for subconcept
                subconcept_evidence = Evidence(
                    SourceId=file_id,
                    SourceName=file_name,
                    Text=sub.get('synthesis', '')
                )
                
                subconcept_embedding = embeddings_cache.get(sub['name'])
                if subconcept_embedding is not None:
                    sub_id = create_or_merge_knowledge_node(
                        session, workspace_id, subconcept_node, subconcept_evidence, subconcept_embedding
                    )
                else:
                    print(f"    ⚠️  No embedding for subconcept '{subconcept_node.Name}', skipping")
                    continue
                
                
                if sub_id:
                    stats['node_ids'].append(sub_id)
                    stats['evidence_created'] += 1
                    
                    # Link to concept
                    if concept_id:
                        create_parent_child_relationship(
                            session, concept_id, sub_id, 'concept_to_subconcept'
                        )
    
    # Calculate final statistics
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as total
        """,
        ws=workspace_id
    )
    stats['final_count'] = result.single()['total']
    stats['nodes_created'] = stats['final_count'] - initial_count
    
    # Calculate merge statistics
    unique_nodes = set(stats['node_ids'])
    total_processed = len(stats['node_ids'])
    stats['exact_matches'] = total_processed - len(unique_nodes)
    
    return stats


def add_gap_suggestions_to_node(
    session,
    knowledge_node_id: str,
    gap_suggestions: List[GapSuggestion]
):
    """Add GapSuggestion nodes to a KnowledgeNode"""
    for gap_suggestion in gap_suggestions:
        create_gap_suggestion_node(session, gap_suggestion, knowledge_node_id)


def get_knowledge_node_with_evidence(
    session,
    node_id: str
) -> Optional[Tuple[KnowledgeNode, List[Evidence]]]:
    """Retrieve KnowledgeNode with all its Evidence nodes"""
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        RETURN n, collect(e) as evidences
        """,
        node_id=node_id
    )
    
    record = result.single()
    if not record:
        return None
    
    node_data = record['n']
    evidence_nodes = record['evidences']
    
    # Convert to KnowledgeNode object
    knowledge_node = KnowledgeNode(
        Id=node_data.get('id', ''),
        Type=node_data.get('type', ''),
        Name=node_data.get('name', ''),
        Synthesis=node_data.get('synthesis', ''),
        WorkspaceId=node_data.get('workspace_id', ''),
        Level=node_data.get('level', 0),
        SourceCount=node_data.get('source_count', 0),
        TotalConfidence=node_data.get('total_confidence', 0.0),
        CreatedAt=node_data.get('created_at', datetime.now(timezone.utc)),
        UpdatedAt=node_data.get('updated_at', datetime.now(timezone.utc))
    )
    
    # Convert to Evidence objects
    evidences = []
    for evidence_data in evidence_nodes:
        evidence = Evidence(
            Id=evidence_data.get('id', ''),
            SourceId=evidence_data.get('source_id', ''),
            SourceName=evidence_data.get('source_name', ''),
            ChunkId=evidence_data.get('chunk_id', ''),
            Text=evidence_data.get('text', ''),
            Page=evidence_data.get('page', 0),
            Confidence=evidence_data.get('confidence', 0.0),
            CreatedAt=evidence_data.get('created_at', datetime.now(timezone.utc)),
            Language=evidence_data.get('language', 'ENG'),
            SourceLanguage=evidence_data.get('source_language', 'ENG'),
            HierarchyPath=evidence_data.get('hierarchy_path', ''),
            Concepts=evidence_data.get('concepts', []),
            KeyClaims=evidence_data.get('key_claims', []),
            QuestionsRaised=evidence_data.get('questions_raised', []),
            EvidenceStrength=evidence_data.get('evidence_strength', 0.0)
        )
        evidences.append(evidence)
    
    return knowledge_node, evidences