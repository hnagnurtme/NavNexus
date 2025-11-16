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


# def calculate_embedding_similarity(emb1: List[float], emb2: List[float]) -> float:
#     """Calculate cosine similarity between two embeddings"""
#     if not emb1 or not emb2 or len(emb1) != len(emb2):
#         return 0.0
    
#     dot_product = sum(a * b for a, b in zip(emb1, emb2))
#     norm1 = sum(a * a for a in emb1) ** 0.5
#     norm2 = sum(b * b for b in emb2) ** 0.5
    
#     if norm1 == 0 or norm2 == 0:
#         return 0.0
    
#     return dot_product / (norm1 * norm2)


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
"""Post-processing deduplication phase using LLM"""
import json
from typing import Dict, List, Tuple
from datetime import datetime


def batch_deduplicate_nodes(session, workspace_id: str, clova_api_key: str, 
                            clova_api_url: str, embedding_func) -> Dict:
    """
    Phase 6: Intelligent deduplication using LLM to identify semantic duplicates.
    Scans all nodes once and merges similar ones.
    """
    from .llm_analysis import call_llm_compact
    
    print(f"\n🔍 Phase 6: Post-processing deduplication")
    
    results = {
        "scanned": 0,
        "merged": 0,
        "merge_groups": []
    }
    
    # Process by level and type to avoid cross-level merging
    levels = [
        ("domain", 0),
        ("category", 1),
        ("concept", 2),
        ("subconcept", 3)
    ]
    
    for node_type, level in levels:
        print(f"\n  Scanning {node_type} (level {level})...")
        
        # Get all nodes of this type
        result = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $workspace_id, type: $type, level: $level})
            RETURN n.id as id, n.name as name, n.synthesis as synthesis
            ORDER BY n.name
            """,
            workspace_id=workspace_id,
            type=node_type,
            level=level
        )
        
        nodes = [dict(record) for record in result]
        results["scanned"] += len(nodes)
        
        if len(nodes) < 2:
            continue
        
        # Find duplicates using LLM in batches
        merge_groups = find_duplicate_groups_llm(nodes, clova_api_key, clova_api_url, embedding_func)
        
        # Execute merges
        for group in merge_groups:
            if len(group) < 2:
                continue
            
            # Pick canonical node (first one or one with most evidences)
            canonical_id = pick_canonical_node(session, group)
            to_merge = [nid for nid in group if nid != canonical_id]
            
            print(f"    Merging {len(to_merge)} nodes into {canonical_id}")
            
            for merge_id in to_merge:
                merge_nodes(session, canonical_id, merge_id)
                results["merged"] += 1
            
            results["merge_groups"].append({
                "canonical": canonical_id,
                "merged": to_merge
            })
    
    print(f"\n  ✓ Scanned {results['scanned']} nodes, merged {results['merged']} duplicates")
    return results


def find_duplicate_groups_llm(nodes: List[Dict], clova_api_key: str, 
                              clova_api_url: str, embedding_func) -> List[List[str]]:
    """
    Use LLM to identify groups of semantically similar nodes.
    Returns list of groups, where each group is list of node IDs to merge.
    """
    from .llm_analysis import call_llm_compact
    
    if len(nodes) < 2:
        return []
    
    # STEP 1: Quick embedding-based filtering
    # Group nodes that are very similar (>0.90 similarity)
    candidate_groups = []
    processed = set()
    
    for i, node_a in enumerate(nodes):
        if node_a["id"] in processed:
            continue
        
        group = [node_a["id"]]
        emb_a = embedding_func(node_a["name"])
        
        for j, node_b in enumerate(nodes[i+1:], i+1):
            if node_b["id"] in processed:
                continue
            
            emb_b = embedding_func(node_b["name"])
            similarity = calculate_embedding_similarity(emb_a, emb_b)
            
            if similarity > 0.90:  # Very high threshold
                group.append(node_b["id"])
                processed.add(node_b["id"])
        
        if len(group) > 1:
            candidate_groups.append(group)
        processed.add(node_a["id"])
    
    if not candidate_groups:
        return []
    
    # STEP 2: LLM validation for each candidate group
    # Batch multiple groups into one LLM call
    validated_groups = []
    
    for batch_start in range(0, len(candidate_groups), 5):  # Process 5 groups at a time
        batch = candidate_groups[batch_start:batch_start+5]
        
        # Prepare LLM prompt
        groups_data = []
        for group_idx, group in enumerate(batch):
            group_nodes = [n for n in nodes if n["id"] in group]
            groups_data.append({
                "group_id": group_idx,
                "nodes": [{"id": n["id"], "name": n["name"], "synthesis": n.get("synthesis", "")} for n in group_nodes]
            })
        
        prompt = f"""Analyze these groups of potentially duplicate concept nodes. For each group, determine if the nodes are truly referring to the SAME concept and should be merged.

Groups to analyze:
{json.dumps(groups_data, indent=2, ensure_ascii=False)}

Rules:
- Merge if: Same core concept, just different wording (e.g., "ML" vs "Machine Learning", "Neural Nets" vs "Neural Networks")
- Keep separate if: Related but distinct concepts (e.g., "Supervised Learning" vs "Unsupervised Learning")
- Keep separate if: Different levels of specificity (e.g., "AI" vs "Deep Learning")

Return JSON array of groups to merge:
{{
  "merge_groups": [
    {{
      "group_id": 0,
      "should_merge": true,
      "reason": "Same concept, different names",
      "node_ids": ["id1", "id2"]
    }}
  ]
}}"""
        
        result = call_llm_compact(prompt, max_tokens=1000, 
                                 clova_api_key=clova_api_key, 
                                 clova_api_url=clova_api_url)
        
        # Parse LLM decision
        merge_decisions = result.get("merge_groups", [])
        for decision in merge_decisions:
            if decision.get("should_merge", False):
                node_ids = decision.get("node_ids", [])
                if len(node_ids) > 1:
                    validated_groups.append(node_ids)
                    print(f"      ✓ Merge: {decision.get('reason', 'No reason')}")
    
    return validated_groups


def calculate_embedding_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Calculate cosine similarity"""
    if not emb1 or not emb2 or len(emb1) != len(emb2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(emb1, emb2))
    norm1 = sum(a * a for a in emb1) ** 0.5
    norm2 = sum(b * b for b in emb2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def pick_canonical_node(session, node_ids: List[str]) -> str:
    """
    Pick the best node to keep from a group.
    Criteria: most evidences, then earliest created
    """
    result = session.run(
        """
        MATCH (n:KnowledgeNode)
        WHERE n.id IN $node_ids
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        WITH n, count(e) as evidence_count
        RETURN n.id as id, 
               n.name as name,
               evidence_count, 
               n.created_at as created_at
        ORDER BY evidence_count DESC, created_at ASC
        LIMIT 1
        """,
        node_ids=node_ids
    )
    
    record = result.single()
    if record:
        print(f"      Canonical: {record['name']} ({record['evidence_count']} evidences)")
        return record["id"]
    
    return node_ids[0]  # Fallback


def merge_nodes(session, canonical_id: str, merge_id: str):
    """
    Merge merge_id into canonical_id:
    1. Move all evidences
    2. Move all child relationships
    3. Move all parent relationships
    4. Move all suggestions
    5. Update synthesis
    6. Delete merged node
    """
    
    # 1. Move evidences
    session.run(
        """
        MATCH (merge:KnowledgeNode {id: $merge_id})-[r:HAS_EVIDENCE]->(e:Evidence)
        MATCH (canonical:KnowledgeNode {id: $canonical_id})
        DELETE r
        MERGE (canonical)-[:HAS_EVIDENCE]->(e)
        """,
        canonical_id=canonical_id,
        merge_id=merge_id
    )
    
    # 2. Move child relationships
    session.run(
        """
        MATCH (merge:KnowledgeNode {id: $merge_id})-[r:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(child)
        MATCH (canonical:KnowledgeNode {id: $canonical_id})
        DELETE r
        MERGE (canonical)-[:CONTAINS_CONCEPT]->(child)
        """,
        canonical_id=canonical_id,
        merge_id=merge_id
    )
    
    # 3. Move parent relationships
    session.run(
        """
        MATCH (parent)-[r:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(merge:KnowledgeNode {id: $merge_id})
        MATCH (canonical:KnowledgeNode {id: $canonical_id})
        DELETE r
        MERGE (parent)-[:CONTAINS_CONCEPT]->(canonical)
        """,
        canonical_id=canonical_id,
        merge_id=merge_id
    )
    
    # 4. Move suggestions
    session.run(
        """
        MATCH (merge:KnowledgeNode {id: $merge_id})-[r:HAS_SUGGESTION]->(g:GapSuggestion)
        MATCH (canonical:KnowledgeNode {id: $canonical_id})
        DELETE r
        MERGE (canonical)-[:HAS_SUGGESTION]->(g)
        """,
        canonical_id=canonical_id,
        merge_id=merge_id
    )
    
    # 5. Update canonical node statistics
    session.run(
        """
        MATCH (canonical:KnowledgeNode {id: $canonical_id})
        OPTIONAL MATCH (canonical)-[:HAS_EVIDENCE]->(e:Evidence)
        WITH canonical, count(DISTINCT e) as evidence_count, sum(e.confidence) as total_conf
        SET canonical.source_count = evidence_count,
            canonical.total_confidence = total_conf,
            canonical.updated_at = $updated_at
        """,
        canonical_id=canonical_id,
        updated_at=datetime.now().isoformat()
    )
    
    # 6. Delete merged node
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $merge_id})
        DETACH DELETE n
        """,
        merge_id=merge_id
    )


def deduplicate_across_workspace(session, workspace_id: str, clova_api_key: str,
                                 clova_api_url: str, embedding_func) -> Dict:
    """
    Smart deduplication that handles common patterns:
    - Abbreviations: "ML" → "Machine Learning"
    - Synonyms: "Neural Nets" → "Neural Networks"
    - Case variations: "deep learning" → "Deep Learning"
    """
    
    print(f"\n🧹 Smart Deduplication Across Workspace")
    
    # Common abbreviation mappings (you can expand this)
    common_patterns = {
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "nn": "neural network",
        "cnn": "convolutional neural network",
        "rnn": "recurrent neural network",
        "nlp": "natural language processing",
        "cv": "computer vision",
        "dl": "deep learning"
    }
    
    results = batch_deduplicate_nodes(session, workspace_id, 
                                     clova_api_key, clova_api_url, 
                                     embedding_func)
    
    return results


def get_deduplication_report(session, workspace_id: str) -> Dict:
    """Get statistics after deduplication"""
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        WITH n, count(DISTINCT e.source_id) as source_count
        RETURN n.type as type,
               count(n) as node_count,
               sum(CASE WHEN source_count > 1 THEN 1 ELSE 0 END) as merged_count,
               avg(source_count) as avg_sources_per_node
        ORDER BY n.type
        """,
        workspace_id=workspace_id
    )
    
    stats = {}
    for record in result:
        stats[record["type"]] = {
            "total_nodes": record["node_count"],
            "merged_nodes": record["merged_count"],
            "avg_sources": round(record["avg_sources_per_node"], 2)
        }
    
    return stats

# ============================================
# ULTRA-OPTIMIZED CASCADING DEDUPLICATION
# ============================================

def find_best_match(session, workspace_id: str, concept_name: str, 
                   embedding: List[float], thresholds: Dict[str, float]) -> Optional[Dict]:
    """
    Cascading search: Exact → Very High → High → Medium similarity
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        concept_name: Name of concept to match
        embedding: Embedding vector
        thresholds: Dict with keys: very_high, high, medium
        
    Returns:
        Dict with keys: id, name, sim, match_type or None
    """
    
    # STAGE 1: Exact name match (case-insensitive)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE toLower(n.name) = toLower($name)
           OR toLower($name) IN [x IN COALESCE(n.aliases, []) | toLower(x)]
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
    for threshold, match_type in [
        (thresholds.get('very_high', 0.90), 'very_high'),
        (thresholds.get('high', 0.80), 'high'),
        (thresholds.get('medium', 0.70), 'medium')
    ]:
        # Note: This requires Neo4j GDS plugin with cosine similarity
        # For now, use Python-based similarity check
        result = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $ws})
            WHERE n.embedding IS NOT NULL
            RETURN n.id as id, n.name as name, n.embedding as embedding
            """,
            ws=workspace_id
        )
        
        best_match = None
        best_sim = 0.0
        
        for record in result:
            node_embedding = record.get('embedding')
            if not node_embedding:
                continue
            
            # Calculate cosine similarity
            from ..pipeline.embedding import calculate_similarity
            sim = calculate_similarity(embedding, node_embedding)
            
            if sim > best_sim and sim > threshold:
                best_sim = sim
                best_match = {
                    'id': record['id'],
                    'name': record['name'],
                    'sim': sim,
                    'match_type': match_type
                }
        
        if best_match:
            return best_match
    
    return None


def create_or_merge_node(session, workspace_id: str, name: str, synthesis: str,
                        node_type: str, file_id: str, file_name: str,
                        embeddings_cache: Dict[str, List[float]],
                        thresholds: Dict[str, float],
                        stats: Dict[str, int]) -> Optional[str]:
    """
    Create new node or merge into existing with evidence tracking
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        name: Concept name
        synthesis: Synthesis text
        node_type: Type of node (domain, category, concept, subconcept)
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings
        thresholds: Similarity thresholds
        stats: Statistics dict to update
        
    Returns:
        Node ID or None if error
    """
    
    if not name or not name.strip():
        return None
    
    embedding = embeddings_cache.get(name)
    if not embedding:
        print(f"    ⚠️  No embedding for '{name}'")
        return None
    
    match = find_best_match(session, workspace_id, name, embedding, thresholds)
    
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
        
        # Update existing node
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $id})
            SET n.synthesis = CASE 
                    WHEN n.synthesis IS NULL OR n.synthesis = '' 
                    THEN '[' + $file_name + '] ' + $new_synthesis
                    ELSE n.synthesis + '\\n\\n[' + $file_name + '] ' + $new_synthesis
                END,
                n.file_ids = CASE
                    WHEN COALESCE(n.file_ids, []) = []
                    THEN [$file_id]
                    WHEN NOT $file_id IN COALESCE(n.file_ids, [])
                    THEN COALESCE(n.file_ids, []) + $file_id
                    ELSE n.file_ids
                END,
                n.evidence_count = COALESCE(n.evidence_count, 1) + 1,
                n.confidence = COALESCE(n.confidence, 0.5) + $confidence_boost,
                n.last_updated = $timestamp,
                n.aliases = CASE 
                    WHEN NOT $name IN COALESCE(n.aliases, []) AND $name <> n.name
                    THEN COALESCE(n.aliases, []) + $name
                    ELSE COALESCE(n.aliases, [])
                END
            """,
            id=node_id,
            new_synthesis=synthesis[:200],
            file_id=file_id,
            file_name=file_name,
            name=name,
            confidence_boost=confidence_boost,
            timestamp=now_iso()
        )
        
        # Update stats
        if match_type == 'exact':
            stats['exact_matches'] = stats.get('exact_matches', 0) + 1
        elif match_type in ['very_high', 'high']:
            stats['high_similarity_merges'] = stats.get('high_similarity_merges', 0) + 1
        else:
            stats['medium_similarity_merges'] = stats.get('medium_similarity_merges', 0) + 1
        
        print(f"    ♻️  MERGE ({match_type}, sim={similarity:.2f}): '{name}' → '{match['name']}'")
        
    else:
        # CREATE: New node
        node_id = str(uuid.uuid4())
        stats['nodes_created'] = stats.get('nodes_created', 0) + 1
        
        session.run(
            """
            CREATE (n:KnowledgeNode {
                id: $id,
                workspace_id: $ws,
                name: $name,
                type: $type,
                synthesis: '[' + $file_name + '] ' + $synthesis,
                embedding: $embedding,
                file_ids: [$file_id],
                evidence_count: 1,
                confidence: 0.5,
                aliases: [],
                created_at: $timestamp,
                last_updated: $timestamp
            })
            """,
            id=node_id,
            ws=workspace_id,
            name=name,
            type=node_type,
            synthesis=synthesis[:200],
            embedding=embedding,
            file_id=file_id,
            file_name=file_name,
            timestamp=now_iso()
        )
        
        print(f"    ✨ CREATE: '{name}'")
    
    return node_id


def create_hierarchical_graph_with_cascading_dedup(
    session, workspace_id: str, structure: Dict, file_id: str,
    file_name: str, embeddings_cache: Dict[str, List[float]],
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, int]:
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
        structure: Hierarchical structure dict
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings
        thresholds: Custom thresholds (optional)
        
    Returns:
        Statistics dict with counts
    """
    
    if thresholds is None:
        from ..config import (
            SEMANTIC_MERGE_THRESHOLD_VERY_HIGH,
            SEMANTIC_MERGE_THRESHOLD_HIGH,
            SEMANTIC_MERGE_THRESHOLD_MEDIUM
        )
        thresholds = {
            'very_high': SEMANTIC_MERGE_THRESHOLD_VERY_HIGH,
            'high': SEMANTIC_MERGE_THRESHOLD_HIGH,
            'medium': SEMANTIC_MERGE_THRESHOLD_MEDIUM
        }
    
    stats = {
        'nodes_created': 0,
        'exact_matches': 0,
        'high_similarity_merges': 0,
        'medium_similarity_merges': 0,
        'final_count': 0
    }
    
    print(f"\n📊 Building graph with cascading deduplication (thresholds: {thresholds})")
    
    # Process domain
    domain = structure.get('domain', {})
    domain_id = None
    if domain.get('name'):
        print(f"\n  🌐 Domain: {domain.get('name')}")
        domain_id = create_or_merge_node(
            session, workspace_id,
            domain.get('name', ''),
            domain.get('synthesis', '')[:200],
            'domain',
            file_id, file_name,
            embeddings_cache, thresholds, stats
        )
    
    # Process categories
    for cat in structure.get('categories', []):
        if not cat.get('name'):
            continue
        
        print(f"\n  📁 Category: {cat.get('name')}")
        cat_id = create_or_merge_node(
            session, workspace_id,
            cat.get('name', ''),
            cat.get('synthesis', '')[:200],
            'category',
            file_id, file_name,
            embeddings_cache, thresholds, stats
        )
        
        if domain_id and cat_id:
            session.run(
                """
                MATCH (d:KnowledgeNode {id: $did}), (c:KnowledgeNode {id: $cid})
                MERGE (d)-[:HAS_SUBCATEGORY]->(c)
                """,
                did=domain_id, cid=cat_id
            )
        
        # Process concepts
        for concept in cat.get('concepts', []):
            if not concept.get('name'):
                continue
            
            print(f"\n    💡 Concept: {concept.get('name')}")
            concept_id = create_or_merge_node(
                session, workspace_id,
                concept.get('name', ''),
                concept.get('synthesis', '')[:200],
                'concept',
                file_id, file_name,
                embeddings_cache, thresholds, stats
            )
            
            if cat_id and concept_id:
                session.run(
                    """
                    MATCH (c:KnowledgeNode {id: $cid}), (n:KnowledgeNode {id: $nid})
                    MERGE (c)-[:CONTAINS_CONCEPT]->(n)
                    """,
                    cid=cat_id, nid=concept_id
                )
            
            # Process subconcepts
            for sub in concept.get('subconcepts', []):
                if not sub.get('name'):
                    continue
                
                print(f"\n      🔸 Subconcept: {sub.get('name')}")
                sub_id = create_or_merge_node(
                    session, workspace_id,
                    sub.get('name', ''),
                    sub.get('synthesis', '')[:200],
                    'subconcept',
                    file_id, file_name,
                    embeddings_cache, thresholds, stats
                )
                
                if concept_id and sub_id:
                    session.run(
                        """
                        MATCH (c:KnowledgeNode {id: $cid}), (s:KnowledgeNode {id: $sid})
                        MERGE (c)-[:HAS_DETAIL]->(s)
                        """,
                        cid=concept_id, sid=sub_id
                    )
    
    # Calculate final count
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as total
        """,
        ws=workspace_id
    )
    record = result.single()
    stats['final_count'] = record['total'] if record else 0
    
    print(f"\n✅ Graph construction complete:")
    print(f"   - New nodes created: {stats['nodes_created']}")
    print(f"   - Exact matches: {stats['exact_matches']}")
    print(f"   - High similarity merges: {stats['high_similarity_merges']}")
    print(f"   - Medium similarity merges: {stats['medium_similarity_merges']}")
    print(f"   - Total nodes in workspace: {stats['final_count']}")
    
    return stats


# ============================================
# ULTRA-OPTIMIZED CASCADING DEDUPLICATION
# ============================================

def find_best_match(session, workspace_id: str, concept_name: str, 
                   embedding: List[float], thresholds: Dict[str, float]) -> Optional[Dict]:
    """
    Cascading search: Exact → Very High → High → Medium similarity
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        concept_name: Name of concept to match
        embedding: Embedding vector
        thresholds: Dict with keys: very_high, high, medium
        
    Returns:
        Dict with keys: id, name, sim, match_type or None
    """
    
    # STAGE 1: Exact name match (case-insensitive)
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE toLower(n.name) = toLower($name)
           OR toLower($name) IN [x IN COALESCE(n.aliases, []) | toLower(x)]
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
    for threshold, match_type in [
        (thresholds.get('very_high', 0.90), 'very_high'),
        (thresholds.get('high', 0.80), 'high'),
        (thresholds.get('medium', 0.70), 'medium')
    ]:
        # Note: This requires Neo4j GDS plugin with cosine similarity
        # For now, use Python-based similarity check
        result = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $ws})
            WHERE n.embedding IS NOT NULL
            RETURN n.id as id, n.name as name, n.embedding as embedding
            """,
            ws=workspace_id
        )
        
        best_match = None
        best_sim = 0.0
        
        for record in result:
            node_embedding = record.get('embedding')
            if not node_embedding:
                continue
            
            # Calculate cosine similarity
            from ..pipeline.embedding import calculate_similarity
            sim = calculate_similarity(embedding, node_embedding)
            
            if sim > best_sim and sim > threshold:
                best_sim = sim
                best_match = {
                    'id': record['id'],
                    'name': record['name'],
                    'sim': sim,
                    'match_type': match_type
                }
        
        if best_match:
            return best_match
    
    return None


def create_or_merge_node(session, workspace_id: str, name: str, synthesis: str,
                        node_type: str, file_id: str, file_name: str,
                        embeddings_cache: Dict[str, List[float]],
                        thresholds: Dict[str, float],
                        stats: Dict[str, int]) -> Optional[str]:
    """
    Create new node or merge into existing with evidence tracking
    
    Args:
        session: Neo4j session
        workspace_id: Workspace ID
        name: Concept name
        synthesis: Synthesis text
        node_type: Type of node (domain, category, concept, subconcept)
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings
        thresholds: Similarity thresholds
        stats: Statistics dict to update
        
    Returns:
        Node ID or None if error
    """
    
    if not name or not name.strip():
        return None
    
    embedding = embeddings_cache.get(name)
    if not embedding:
        print(f"    ⚠️  No embedding for '{name}'")
        return None
    
    match = find_best_match(session, workspace_id, name, embedding, thresholds)
    
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
        
        # Update existing node
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $id})
            SET n.synthesis = CASE 
                    WHEN n.synthesis IS NULL OR n.synthesis = '' 
                    THEN '[' + $file_name + '] ' + $new_synthesis
                    ELSE n.synthesis + '\\n\\n[' + $file_name + '] ' + $new_synthesis
                END,
                n.file_ids = CASE
                    WHEN COALESCE(n.file_ids, []) = []
                    THEN [$file_id]
                    WHEN NOT $file_id IN COALESCE(n.file_ids, [])
                    THEN COALESCE(n.file_ids, []) + $file_id
                    ELSE n.file_ids
                END,
                n.evidence_count = COALESCE(n.evidence_count, 1) + 1,
                n.confidence = COALESCE(n.confidence, 0.5) + $confidence_boost,
                n.last_updated = $timestamp,
                n.aliases = CASE 
                    WHEN NOT $name IN COALESCE(n.aliases, []) AND $name <> n.name
                    THEN COALESCE(n.aliases, []) + $name
                    ELSE COALESCE(n.aliases, [])
                END
            """,
            id=node_id,
            new_synthesis=synthesis[:200],
            file_id=file_id,
            file_name=file_name,
            name=name,
            confidence_boost=confidence_boost,
            timestamp=now_iso()
        )
        
        # Update stats
        if match_type == 'exact':
            stats['exact_matches'] = stats.get('exact_matches', 0) + 1
        elif match_type in ['very_high', 'high']:
            stats['high_similarity_merges'] = stats.get('high_similarity_merges', 0) + 1
        else:
            stats['medium_similarity_merges'] = stats.get('medium_similarity_merges', 0) + 1
        
        print(f"    ♻️  MERGE ({match_type}, sim={similarity:.2f}): '{name}' → '{match['name']}'")
        
    else:
        # CREATE: New node
        node_id = str(uuid.uuid4())
        stats['nodes_created'] = stats.get('nodes_created', 0) + 1
        
        session.run(
            """
            CREATE (n:KnowledgeNode {
                id: $id,
                workspace_id: $ws,
                name: $name,
                type: $type,
                synthesis: '[' + $file_name + '] ' + $synthesis,
                embedding: $embedding,
                file_ids: [$file_id],
                evidence_count: 1,
                confidence: 0.5,
                aliases: [],
                created_at: $timestamp,
                last_updated: $timestamp
            })
            """,
            id=node_id,
            ws=workspace_id,
            name=name,
            type=node_type,
            synthesis=synthesis[:200],
            embedding=embedding,
            file_id=file_id,
            file_name=file_name,
            timestamp=now_iso()
        )
        
        print(f"    ✨ CREATE: '{name}'")
    
    return node_id


def create_hierarchical_graph_with_cascading_dedup(
    session, workspace_id: str, structure: Dict, file_id: str,
    file_name: str, embeddings_cache: Dict[str, List[float]],
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, int]:
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
        structure: Hierarchical structure dict
        file_id: Source file ID
        file_name: Source file name
        embeddings_cache: Pre-computed embeddings
        thresholds: Custom thresholds (optional)
        
    Returns:
        Statistics dict with counts
    """
    
    if thresholds is None:
        from ..config import (
            SEMANTIC_MERGE_THRESHOLD_VERY_HIGH,
            SEMANTIC_MERGE_THRESHOLD_HIGH,
            SEMANTIC_MERGE_THRESHOLD_MEDIUM
        )
        thresholds = {
            'very_high': SEMANTIC_MERGE_THRESHOLD_VERY_HIGH,
            'high': SEMANTIC_MERGE_THRESHOLD_HIGH,
            'medium': SEMANTIC_MERGE_THRESHOLD_MEDIUM
        }
    
    stats = {
        'nodes_created': 0,
        'exact_matches': 0,
        'high_similarity_merges': 0,
        'medium_similarity_merges': 0,
        'final_count': 0
    }
    
    print(f"\n📊 Building graph with cascading deduplication (thresholds: {thresholds})")
    
    # Process domain
    domain = structure.get('domain', {})
    domain_id = None
    if domain.get('name'):
        print(f"\n  🌐 Domain: {domain.get('name')}")
        domain_id = create_or_merge_node(
            session, workspace_id,
            domain.get('name', ''),
            domain.get('synthesis', '')[:200],
            'domain',
            file_id, file_name,
            embeddings_cache, thresholds, stats
        )
    
    # Process categories
    for cat in structure.get('categories', []):
        if not cat.get('name'):
            continue
        
        print(f"\n  📁 Category: {cat.get('name')}")
        cat_id = create_or_merge_node(
            session, workspace_id,
            cat.get('name', ''),
            cat.get('synthesis', '')[:200],
            'category',
            file_id, file_name,
            embeddings_cache, thresholds, stats
        )
        
        if domain_id and cat_id:
            session.run(
                """
                MATCH (d:KnowledgeNode {id: $did}), (c:KnowledgeNode {id: $cid})
                MERGE (d)-[:HAS_SUBCATEGORY]->(c)
                """,
                did=domain_id, cid=cat_id
            )
        
        # Process concepts
        for concept in cat.get('concepts', []):
            if not concept.get('name'):
                continue
            
            print(f"\n    💡 Concept: {concept.get('name')}")
            concept_id = create_or_merge_node(
                session, workspace_id,
                concept.get('name', ''),
                concept.get('synthesis', '')[:200],
                'concept',
                file_id, file_name,
                embeddings_cache, thresholds, stats
            )
            
            if cat_id and concept_id:
                session.run(
                    """
                    MATCH (c:KnowledgeNode {id: $cid}), (n:KnowledgeNode {id: $nid})
                    MERGE (c)-[:CONTAINS_CONCEPT]->(n)
                    """,
                    cid=cat_id, nid=concept_id
                )
            
            # Process subconcepts
            for sub in concept.get('subconcepts', []):
                if not sub.get('name'):
                    continue
                
                print(f"\n      🔸 Subconcept: {sub.get('name')}")
                sub_id = create_or_merge_node(
                    session, workspace_id,
                    sub.get('name', ''),
                    sub.get('synthesis', '')[:200],
                    'subconcept',
                    file_id, file_name,
                    embeddings_cache, thresholds, stats
                )
                
                if concept_id and sub_id:
                    session.run(
                        """
                        MATCH (c:KnowledgeNode {id: $cid}), (s:KnowledgeNode {id: $sid})
                        MERGE (c)-[:HAS_DETAIL]->(s)
                        """,
                        cid=concept_id, sid=sub_id
                    )
    
    # Calculate final count
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as total
        """,
        ws=workspace_id
    )
    record = result.single()
    stats['final_count'] = record['total'] if record else 0
    
    print(f"\n✅ Graph construction complete:")
    print(f"   - New nodes created: {stats['nodes_created']}")
    print(f"   - Exact matches: {stats['exact_matches']}")
    print(f"   - High similarity merges: {stats['high_similarity_merges']}")
    print(f"   - Medium similarity merges: {stats['medium_similarity_merges']}")
    print(f"   - Total nodes in workspace: {stats['final_count']}")
    
    return stats
