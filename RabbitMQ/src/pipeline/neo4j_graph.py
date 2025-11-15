"""Neo4j knowledge graph operations"""
import json
import uuid
from typing import Dict, List
from datetime import datetime, timezone
from dataclasses import asdict

from ..model.Evidence import Evidence


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def normalize_concept_name(name: str) -> str:
    """Normalize concept name for matching across PDFs"""
    return name.lower().strip().replace("  ", " ")


def find_or_merge_node(session, workspace_id: str, name: str, type: str, level: int) -> str:
    """Find existing node or create new one. Returns node ID."""
    
    normalized_name = normalize_concept_name(name)
    
    # Try to find existing node with similar name
    result = session.run(
        """
        MATCH (n:KnowledgeNode)
        WHERE n.workspace_id = $workspace_id 
        AND n.type = $type 
        AND n.level = $level
        AND toLower(trim(n.name)) = $normalized_name
        RETURN n.id as id
        LIMIT 1
        """,
        workspace_id=workspace_id,
        type=type,
        level=level,
        normalized_name=normalized_name
    )
    
    record = result.single()
    if record:
        return record["id"]
    
    # Create new node
    node_id = f"{type}-{uuid.uuid4().hex[:8]}"
    session.run(
        """
        CREATE (n:KnowledgeNode {
            id: $id,
            name: $name,
            type: $type,
            level: $level,
            workspace_id: $workspace_id,
            synthesis: '',
            source_count: 0,
            total_confidence: 0.0,
            created_at: $created_at,
            updated_at: $created_at
        })
        """,
        id=node_id,
        name=name,
        type=type,
        level=level,
        workspace_id=workspace_id,
        created_at=now_iso()
    )
    
    return node_id


def add_evidence_to_node(session, node_id: str, evidence: Evidence):
    """Add evidence to existing node"""
    
    # Convert evidence to JSON string for Neo4j storage
    evidence_dict = {
        'source_id': evidence.SourceId,
        'source_name': evidence.SourceName,
        'chunk_id': evidence.ChunkId,
        'text': evidence.Text,
        'page': evidence.Page,
        'confidence': evidence.Confidence,
        'created_at': evidence.CreatedAt.isoformat() if hasattr(evidence.CreatedAt, 'isoformat') else str(evidence.CreatedAt),
        'claims': evidence.KeyClaims
    }
    evidence_json = json.dumps(evidence_dict, ensure_ascii=False)
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.evidences = coalesce(n.evidences, []) + [$evidence_json],
            n.source_count = size(coalesce(n.evidences, [])) + 1,
            n.total_confidence = coalesce(n.total_confidence, 0.0) + $confidence,
            n.updated_at = $updated_at
        """,
        node_id=node_id,
        evidence_json=evidence_json,
        confidence=evidence.Confidence,
        updated_at=now_iso()
    )


def update_node_synthesis(session, node_id: str, new_synthesis: str, clova_api_key: str, clova_api_url: str):
    """Update synthesis by merging with existing"""
    from .llm_analysis import call_llm_compact
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        RETURN n.synthesis as current_synthesis, n.evidences as evidences
        """,
        node_id=node_id
    )
    
    record = result.single()
    if not record:
        return
    
    current = record["current_synthesis"]
    evidences_json = record["evidences"] or []
    
    # Parse evidences
    evidences = []
    for ev_json in evidences_json:
        try:
            evidences.append(json.loads(ev_json))
        except:
            pass
    
    # If first synthesis, just set it
    if not current or len(evidences) <= 1:
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $node_id})
            SET n.synthesis = $synthesis
            """,
            node_id=node_id,
            synthesis=new_synthesis
        )
        return
    
    # Merge syntheses using LLM
    merge_prompt = f"""Merge these perspectives about the same concept:

Existing: {current}

New: {new_synthesis}

Return unified synthesis (2-3 sentences max):
{{"unified": "..."}}"""
    
    result = call_llm_compact(merge_prompt, max_tokens=300, clova_api_key=clova_api_key, clova_api_url=clova_api_url)
    unified = result.get("unified", new_synthesis)
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.synthesis = $synthesis
        """,
        node_id=node_id,
        synthesis=unified
    )


def create_hierarchical_graph(session, workspace_id: str, structure: Dict, 
                              file_id: str, file_name: str, lang: str,
                              clova_api_key: str, clova_api_url: str) -> List[str]:
    """Create hierarchical graph from structure, merging with existing nodes"""
    
    now = now_iso()
    all_node_ids = []
    
    # Level 0: Domain (root)
    domain_data = structure.get("domain", {})
    domain_name = domain_data.get("name", "Document Domain")
    
    domain_id = find_or_merge_node(session, workspace_id, domain_name, "domain", 0)
    all_node_ids.append(domain_id)
    
    # Add domain evidence
    domain_evidence = Evidence(
        SourceId=file_id,
        SourceName=file_name,
        ChunkId="",
        Text=domain_data.get("synthesis", ""),
        Page=1,
        Confidence=0.9,
        CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00'))
    )
    add_evidence_to_node(session, domain_id, domain_evidence)
    update_node_synthesis(session, domain_id, domain_data.get("synthesis", ""), clova_api_key, clova_api_url)
    
    # Level 1: Categories
    for cat_data in structure.get("categories", []):
        cat_name = cat_data.get("name", "")
        if not cat_name:
            continue
        
        cat_id = find_or_merge_node(session, workspace_id, cat_name, "category", 1)
        all_node_ids.append(cat_id)
        
        # Link to domain
        session.run(
            """
            MATCH (parent:KnowledgeNode {id: $parent_id})
            MATCH (child:KnowledgeNode {id: $child_id})
            MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
            """,
            parent_id=domain_id,
            child_id=cat_id
        )
        
        # Add category evidence
        cat_evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            ChunkId="",
            Text=cat_data.get("synthesis", ""),
            Page=1,
            Confidence=0.85,
            CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00'))
        )
        add_evidence_to_node(session, cat_id, cat_evidence)
        update_node_synthesis(session, cat_id, cat_data.get("synthesis", ""), clova_api_key, clova_api_url)
        
        # Level 2: Concepts
        for concept_data in cat_data.get("concepts", []):
            concept_name = concept_data.get("name", "")
            if not concept_name:
                continue
            
            concept_id = find_or_merge_node(session, workspace_id, concept_name, "concept", 2)
            all_node_ids.append(concept_id)
            
            # Link to category
            session.run(
                """
                MATCH (parent:KnowledgeNode {id: $parent_id})
                MATCH (child:KnowledgeNode {id: $child_id})
                MERGE (parent)-[:CONTAINS_CONCEPT]->(child)
                """,
                parent_id=cat_id,
                child_id=concept_id
            )
            
            # Add concept evidence
            concept_evidence = Evidence(
                SourceId=file_id,
                SourceName=file_name,
                ChunkId="",
                Text=concept_data.get("synthesis", ""),
                Page=1,
                Confidence=0.8,
                CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00'))
            )
            add_evidence_to_node(session, concept_id, concept_evidence)
            update_node_synthesis(session, concept_id, concept_data.get("synthesis", ""), clova_api_key, clova_api_url)
            
            # Level 3: Subconcepts
            for subconcept_data in concept_data.get("subconcepts", []):
                subconcept_name = subconcept_data.get("name", "")
                if not subconcept_name:
                    continue
                
                subconcept_id = find_or_merge_node(session, workspace_id, subconcept_name, "subconcept", 3)
                all_node_ids.append(subconcept_id)
                
                # Link to concept
                session.run(
                    """
                    MATCH (parent:KnowledgeNode {id: $parent_id})
                    MATCH (child:KnowledgeNode {id: $child_id})
                    MERGE (parent)-[:HAS_DETAIL]->(child)
                    """,
                    parent_id=concept_id,
                    child_id=subconcept_id
                )
                
                # Add subconcept evidence with actual text
                subconcept_evidence = Evidence(
                    SourceId=file_id,
                    SourceName=file_name,
                    ChunkId="",
                    Text=subconcept_data.get("evidence", subconcept_data.get("synthesis", "")),
                    Page=1,
                    Confidence=0.75,
                    CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00')),
                    KeyClaims=[subconcept_data.get("evidence", "")]
                )
                add_evidence_to_node(session, subconcept_id, subconcept_evidence)
                update_node_synthesis(session, subconcept_id, subconcept_data.get("synthesis", ""), clova_api_key, clova_api_url)
    
    return all_node_ids
