"""Neo4j knowledge graph operations - Semantic Merge Version"""
import json
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import asdict

from ..model.Evidence import Evidence
from ..model.GapSuggestion import GapSuggestion


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def normalize_concept_name(name: str) -> str:
    """Normalize concept name for matching"""
    return name.lower().strip().replace("  ", " ")


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Simple text similarity using word overlap"""
    words1 = set(normalize_concept_name(text1).split())
    words2 = set(normalize_concept_name(text2).split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def find_or_merge_node_semantic(session, workspace_id: str, name: str, type: str, level: int,
                                embedding_func=None, similarity_threshold: float = 0.85) -> Tuple[str, bool]:
    """
    Find existing node using semantic similarity or create new one.
    Returns (node_id, is_existing)
    """
    
    normalized_name = normalize_concept_name(name)
    
    # STEP 1: Try exact normalized match first (fast)
    result = session.run(
        """
        MATCH (n:KnowledgeNode)
        WHERE n.workspace_id = $workspace_id 
        AND n.type = $type 
        AND n.level = $level
        AND toLower(trim(n.name)) = $normalized_name
        RETURN n.id as id, n.name as name
        LIMIT 1
        """,
        workspace_id=workspace_id,
        type=type,
        level=level,
        normalized_name=normalized_name
    )
    
    record = result.single()
    if record:
        print(f"  ✓ Exact match: '{name}' → '{record['name']}'")
        return record["id"], True
    
    # STEP 2: Try semantic matching with existing nodes of same type/level
    result = session.run(
        """
        MATCH (n:KnowledgeNode)
        WHERE n.workspace_id = $workspace_id 
        AND n.type = $type 
        AND n.level = $level
        RETURN n.id as id, n.name as name
        """,
        workspace_id=workspace_id,
        type=type,
        level=level
    )
    
    candidates = [dict(record) for record in result]
    
    if candidates and embedding_func:
        # Use embedding similarity
        target_embedding = embedding_func(name)
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            candidate_embedding = embedding_func(candidate["name"])
            similarity = calculate_embedding_similarity(target_embedding, candidate_embedding)
            
            if similarity > best_score:
                best_score = similarity
                best_match = candidate
        
        if best_match and best_score >= similarity_threshold:
            print(f"  ✓ Semantic match ({best_score:.2f}): '{name}' → '{best_match['name']}'")
            return best_match["id"], True
    
    else:
        # Fallback to text similarity
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            similarity = calculate_text_similarity(name, candidate["name"])
            
            if similarity > best_score:
                best_score = similarity
                best_match = candidate
        
        if best_match and best_score >= similarity_threshold:
            print(f"  ✓ Text match ({best_score:.2f}): '{name}' → '{best_match['name']}'")
            return best_match["id"], True
    
    # STEP 3: Create new node if no match
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
    
    print(f"  + New node: '{name}'")
    return node_id, False


def calculate_embedding_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    if not emb1 or not emb2 or len(emb1) != len(emb2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(emb1, emb2))
    norm1 = sum(a * a for a in emb1) ** 0.5
    norm2 = sum(b * b for b in emb2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def create_evidence_node(session, evidence: Evidence, node_id: str) -> str:
    """Create Evidence node and link to KnowledgeNode"""
    
    evidence_id = f"evidence-{uuid.uuid4().hex[:8]}"
    
    created_at = evidence.CreatedAt.isoformat() if hasattr(evidence.CreatedAt, 'isoformat') else str(evidence.CreatedAt)
    
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
        id=evidence_id,
        source_id=evidence.SourceId,
        source_name=evidence.SourceName,
        chunk_id=evidence.ChunkId,
        text=evidence.Text,
        page=evidence.Page,
        confidence=evidence.Confidence,
        created_at=created_at,
        language=getattr(evidence, 'Language', 'ENG'),
        source_language=getattr(evidence, 'SourceLanguage', 'ENG'),
        hierarchy_path=getattr(evidence, 'HierarchyPath', ''),
        concepts=getattr(evidence, 'Concepts', []),
        key_claims=getattr(evidence, 'KeyClaims', []),
        questions_raised=getattr(evidence, 'QuestionsRaised', []),
        evidence_strength=getattr(evidence, 'EvidenceStrength', 0.0)
    )
    
    # Create HAS_EVIDENCE relationship
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (e:Evidence {id: $evidence_id})
        MERGE (n)-[:HAS_EVIDENCE]->(e)
        """,
        node_id=node_id,
        evidence_id=evidence_id
    )
    
    # Update node statistics
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.source_count = n.source_count + 1,
            n.total_confidence = n.total_confidence + $confidence,
            n.updated_at = $updated_at
        """,
        node_id=node_id,
        confidence=evidence.Confidence,
        updated_at=now_iso()
    )
    
    return evidence_id


def create_gap_suggestion_node(session, suggestion: GapSuggestion, node_id: str) -> str:
    """Create GapSuggestion node and link to KnowledgeNode"""
    
    suggestion_id = f"suggestion-{uuid.uuid4().hex[:8]}"
    
    session.run(
        """
        CREATE (g:GapSuggestion {
            id: $id,
            suggestion_text: $suggestion_text,
            target_node_id: $target_node_id,
            target_file_id: $target_file_id,
            similarity_score: $similarity_score
        })
        """,
        id=suggestion_id,
        suggestion_text=suggestion.SuggestionText,
        target_node_id=suggestion.TargetNodeId,
        target_file_id=suggestion.TargetFileId,
        similarity_score=suggestion.SimilarityScore
    )
    
    # Create HAS_SUGGESTION relationship
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (g:GapSuggestion {id: $suggestion_id})
        MERGE (n)-[:HAS_SUGGESTION]->(g)
        """,
        node_id=node_id,
        suggestion_id=suggestion_id
    )
    
    return suggestion_id


def add_evidence_to_node(session, node_id: str, evidence: Evidence):
    """Add evidence to existing node by creating Evidence node"""
    return create_evidence_node(session, evidence, node_id)


def is_leaf_node(session, node_id: str) -> bool:
    """Check if node is a leaf node (has no children)"""
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(child)
        RETURN count(child) as child_count
        """,
        node_id=node_id
    )
    
    record = result.single()
    return record and record["child_count"] == 0


def update_node_synthesis_smart(session, node_id: str, new_synthesis: str, 
                                source_name: str, clova_api_key: str, clova_api_url: str):
    """
    Smart synthesis update that merges perspectives from multiple sources.
    Keeps track of which source said what.
    """
    from .llm_analysis import call_llm_compact
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        RETURN n.synthesis as current_synthesis,
               collect(DISTINCT e.source_name) as sources
        """,
        node_id=node_id
    )
    
    record = result.single()
    if not record:
        return
    
    current = record["current_synthesis"]
    existing_sources = [s for s in record["sources"] if s]
    
    # If first synthesis, just set it
    if not current:
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $node_id})
            SET n.synthesis = $synthesis,
                n.updated_at = $updated_at
            """,
            node_id=node_id,
            synthesis=f"[{source_name}] {new_synthesis}",
            updated_at=now_iso()
        )
        return
    
    # Merge with existing synthesis
    merge_prompt = f"""You are synthesizing knowledge from multiple sources.

Current synthesis (from {len(existing_sources)} sources):
{current}

New perspective from [{source_name}]:
{new_synthesis}

Create a unified synthesis that:
1. Integrates all perspectives
2. Highlights agreements and differences
3. Attributes key points to sources
4. Max 3-4 sentences

Return JSON:
{{"unified": "synthesis text here", "key_insights": ["insight 1", "insight 2"]}}"""
    
    result = call_llm_compact(merge_prompt, max_tokens=400, 
                             clova_api_key=clova_api_key, 
                             clova_api_url=clova_api_url)
    
    unified = result.get("unified", f"{current}\n\n[{source_name}] {new_synthesis}")
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.synthesis = $synthesis,
            n.updated_at = $updated_at
        """,
        node_id=node_id,
        synthesis=unified,
        updated_at=now_iso()
    )


def create_hierarchical_graph(session, workspace_id: str, structure: Dict, 
                              file_id: str, file_name: str, lang: str,
                              clova_api_key: str, clova_api_url: str,
                              embedding_func=None) -> List[str]:
    """
    Create hierarchical graph from structure with SEMANTIC MERGING.
    Uses embedding similarity to merge nodes across documents.
    """
    
    now = now_iso()
    all_node_ids = []
    
    print(f"\n🔗 Building knowledge graph for: {file_name}")
    
    # Level 0: Domain (root)
    domain_data = structure.get("domain", {})
    domain_name = domain_data.get("name", "Document Domain")
    
    print(f"\n📁 Domain: {domain_name}")
    domain_id, is_existing = find_or_merge_node_semantic(
        session, workspace_id, domain_name, "domain", 0, embedding_func
    )
    all_node_ids.append(domain_id)
    
    # Add domain evidence
    domain_evidence = Evidence(
        SourceId=file_id,
        SourceName=file_name,
        ChunkId="",
        Text=domain_data.get("synthesis", ""),
        Page=1,
        Confidence=0.9,
        CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00')),
        Language=lang,
        SourceLanguage=lang,
        HierarchyPath=domain_name,
        KeyClaims=[domain_data.get("synthesis", "")]
    )
    add_evidence_to_node(session, domain_id, domain_evidence)
    update_node_synthesis_smart(session, domain_id, domain_data.get("synthesis", ""),
                                file_name, clova_api_key, clova_api_url)
    
    # Level 1: Categories
    for cat_data in structure.get("categories", []):
        cat_name = cat_data.get("name", "")
        if not cat_name:
            continue
        
        print(f"  📂 Category: {cat_name}")
        cat_id, is_existing = find_or_merge_node_semantic(
            session, workspace_id, cat_name, "category", 1, embedding_func
        )
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
        
        # Add evidence
        cat_hierarchy = f"{domain_name} > {cat_name}"
        cat_evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            ChunkId="",
            Text=cat_data.get("synthesis", ""),
            Page=1,
            Confidence=0.85,
            CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00')),
            Language=lang,
            SourceLanguage=lang,
            HierarchyPath=cat_hierarchy,
            KeyClaims=[cat_data.get("synthesis", "")]
        )
        add_evidence_to_node(session, cat_id, cat_evidence)
        update_node_synthesis_smart(session, cat_id, cat_data.get("synthesis", ""),
                                    file_name, clova_api_key, clova_api_url)
        
        # Level 2: Concepts
        for concept_data in cat_data.get("concepts", []):
            concept_name = concept_data.get("name", "")
            if not concept_name:
                continue
            
            print(f"    💡 Concept: {concept_name}")
            concept_id, is_existing = find_or_merge_node_semantic(
                session, workspace_id, concept_name, "concept", 2, embedding_func
            )
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
            
            # Add evidence
            concept_hierarchy = f"{cat_hierarchy} > {concept_name}"
            concept_evidence = Evidence(
                SourceId=file_id,
                SourceName=file_name,
                ChunkId="",
                Text=concept_data.get("synthesis", ""),
                Page=1,
                Confidence=0.8,
                CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00')),
                Language=lang,
                SourceLanguage=lang,
                HierarchyPath=concept_hierarchy,
                Concepts=[concept_name],
                KeyClaims=[concept_data.get("synthesis", "")]
            )
            add_evidence_to_node(session, concept_id, concept_evidence)
            update_node_synthesis_smart(session, concept_id, concept_data.get("synthesis", ""),
                                        file_name, clova_api_key, clova_api_url)
            
            # Level 3: Subconcepts
            for subconcept_data in concept_data.get("subconcepts", []):
                subconcept_name = subconcept_data.get("name", "")
                if not subconcept_name:
                    continue
                
                print(f"      🔸 Subconcept: {subconcept_name}")
                subconcept_id, is_existing = find_or_merge_node_semantic(
                    session, workspace_id, subconcept_name, "subconcept", 3, embedding_func
                )
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
                
                # Add evidence
                subconcept_hierarchy = f"{concept_hierarchy} > {subconcept_name}"
                subconcept_evidence = Evidence(
                    SourceId=file_id,
                    SourceName=file_name,
                    ChunkId="",
                    Text=subconcept_data.get("evidence", subconcept_data.get("synthesis", "")),
                    Page=1,
                    Confidence=0.75,
                    CreatedAt=datetime.fromisoformat(now.replace('Z', '+00:00')),
                    Language=lang,
                    SourceLanguage=lang,
                    HierarchyPath=subconcept_hierarchy,
                    Concepts=[concept_name, subconcept_name],
                    KeyClaims=[subconcept_data.get("evidence", "")],
                    EvidenceStrength=0.75
                )
                add_evidence_to_node(session, subconcept_id, subconcept_evidence)
                update_node_synthesis_smart(session, subconcept_id, subconcept_data.get("synthesis", ""),
                                           file_name, clova_api_key, clova_api_url)
    
    print(f"✓ Graph built: {len(all_node_ids)} nodes")
    return all_node_ids


def get_node_with_relationships(session, node_id: str) -> Optional[Dict]:
    """Get node with all its relationships"""
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(child:KnowledgeNode)
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(evidence:Evidence)
        OPTIONAL MATCH (n)-[:HAS_SUGGESTION]->(suggestion:GapSuggestion)
        RETURN n,
               collect(DISTINCT child) as children,
               collect(DISTINCT evidence) as evidences,
               collect(DISTINCT suggestion) as suggestions
        """,
        node_id=node_id
    )
    
    record = result.single()
    if not record:
        return None
    
    return {
        "node": dict(record["n"]),
        "children": [dict(c) for c in record["children"] if c],
        "evidences": [dict(e) for e in record["evidences"] if e],
        "suggestions": [dict(s) for s in record["suggestions"] if s]
    }