"""Neo4j operations - FIXED: Ultra-aggressive deduplication without embeddings"""
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import asdict

from ..model.Evidence import Evidence
from ..model.GapSuggestion import GapSuggestion


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


# ============================================
# TEXT-BASED SIMILARITY (NO EMBEDDING NEEDED)
# ============================================

def normalize_text(text: str) -> str:
    """Chuẩn hóa text để so sánh"""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Xóa ký tự đặc biệt
    text = re.sub(r'\s+', ' ', text)  # Xóa khoảng trắng thừa
    return text


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Tính similarity dựa trên word overlap"""
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    # Jaccard similarity
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Bonus cho substring match
    if normalize_text(text1) in normalize_text(text2) or normalize_text(text2) in normalize_text(text1):
        jaccard += 0.2
    
    return min(jaccard, 1.0)


def are_synonyms(text1: str, text2: str) -> bool:
    """Kiểm tra xem có phải synonyms không (rút gọn, viết tắt)"""
    
    # Common abbreviations trong AI/ML
    abbreviations = {
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'nn': 'neural network',
        'dl': 'deep learning',
        'nlp': 'natural language processing',
        'cv': 'computer vision',
        'cnn': 'convolutional neural network',
        'rnn': 'recurrent neural network',
        'gnn': 'graph neural network',
        'gpt': 'generative pre trained transformer',
        'bert': 'bidirectional encoder representations from transformers',
        'lstm': 'long short term memory',
        'gan': 'generative adversarial network',
        'rl': 'reinforcement learning',
        'svm': 'support vector machine',
        'knn': 'k nearest neighbors',
        'pca': 'principal component analysis',
        'sgd': 'stochastic gradient descent',
        'adam': 'adaptive moment estimation',
        'relu': 'rectified linear unit',
        'vae': 'variational autoencoder',
        'nas': 'neural architecture search',
        'few shot': 'few-shot learning',
        'zero shot': 'zero-shot learning',
        'self supervised': 'self-supervised learning',
        'semi supervised': 'semi-supervised learning',
        'transfer learning': 'tl',
        'meta learning': 'learning to learn',
        'continual learning': 'lifelong learning',
        'online learning': 'incremental learning'
    }
    
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    # Check direct abbreviation
    if norm1 in abbreviations and abbreviations[norm1] == norm2:
        return True
    if norm2 in abbreviations and abbreviations[norm2] == norm1:
        return True
    
    # Check reverse lookup
    for abbr, full in abbreviations.items():
        if (norm1 == abbr and norm2 == full) or (norm2 == abbr and norm1 == full):
            return True
    
    return False


# ============================================
# ULTRA-AGGRESSIVE DEDUPLICATION
# ============================================

def find_best_match_aggressive(session, workspace_id: str, concept_name: str, 
                               node_type: str, level: int) -> Optional[Dict]:
    """
    ULTRA-AGGRESSIVE matching strategy:
    1. Exact match (case-insensitive)
    2. Alias match
    3. Synonym/abbreviation match
    4. High similarity (>0.7)
    5. Medium similarity (>0.5) - Rất aggressive!
    
    Returns: {id, name, sim, match_type} or None
    """
    
    # STAGE 1: Exact match (nhanh nhất)
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws, type: $type, level: $level})
        WHERE toLower(n.name) = toLower($name)
        RETURN n.id as id, n.name as name, 1.0 as sim, 'exact' as match_type
        LIMIT 1
    """, ws=workspace_id, name=concept_name, type=node_type, level=level)
    
    record = result.single()
    if record:
        return dict(record)
    
    # STAGE 2: Alias match
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws, type: $type, level: $level})
        WHERE toLower($name) IN [x IN COALESCE(n.aliases, []) | toLower(x)]
        RETURN n.id as id, n.name as name, 1.0 as sim, 'alias' as match_type
        LIMIT 1
    """, ws=workspace_id, name=concept_name, type=node_type, level=level)
    
    record = result.single()
    if record:
        return dict(record)
    
    # STAGE 3: Synonym/abbreviation match
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws, type: $type, level: $level})
        RETURN n.id as id, n.name as name
    """, ws=workspace_id, type=node_type, level=level)
    
    for record in result:
        if are_synonyms(concept_name, record['name']):
            return {
                'id': record['id'],
                'name': record['name'],
                'sim': 0.95,
                'match_type': 'synonym'
            }
    
    # STAGE 4-5: Text similarity (AGGRESSIVE thresholds)
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws, type: $type, level: $level})
        RETURN n.id as id, n.name as name, n.synthesis as synthesis
    """, ws=workspace_id, type=node_type, level=level)
    
    best_match = None
    best_sim = 0.0
    
    for record in result:
        # Name similarity (weight 80%)
        name_sim = calculate_text_similarity(concept_name, record['name'])
        
        # Synthesis similarity (weight 20%) - nếu có
        synthesis_sim = 0.0
        if record.get('synthesis'):
            synthesis_sim = calculate_text_similarity(concept_name, record['synthesis'])
        
        total_sim = name_sim * 0.8 + synthesis_sim * 0.2
        
        if total_sim > best_sim:
            best_sim = total_sim
            best_match = {
                'id': record['id'],
                'name': record['name'],
                'sim': total_sim,
                'match_type': 'high_sim' if total_sim > 0.7 else 'medium_sim'
            }
    
    # AGGRESSIVE: Accept matches with similarity > 0.5
    if best_match and best_sim > 0.5:
        return best_match
    
    return None


def create_evidence_node_safe(session, evidence: Evidence, node_id: str) -> str:
    """Tạo Evidence node và link vào KnowledgeNode (LUÔN LUÔN)"""
    
    evidence_id = f"evidence-{uuid.uuid4().hex[:8]}"
    
    created_at = evidence.CreatedAt.isoformat() if hasattr(evidence.CreatedAt, 'isoformat') else str(evidence.CreatedAt)
    
    session.run("""
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
    
    # Link Evidence -> KnowledgeNode
    session.run("""
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (e:Evidence {id: $evidence_id})
        MERGE (n)-[:HAS_EVIDENCE]->(e)
    """, node_id=node_id, evidence_id=evidence_id)
    
    # Update node statistics
    session.run("""
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.source_count = n.source_count + 1,
            n.total_confidence = n.total_confidence + $confidence,
            n.updated_at = $updated_at
    """, node_id=node_id, confidence=evidence.Confidence, updated_at=now_iso())
    
    return evidence_id


def create_gap_suggestion_node(session, gap_suggestion: GapSuggestion, node_id: str) -> str:
    """Tạo GapSuggestion node và link vào KnowledgeNode"""

    suggestion_id = gap_suggestion.Id

    session.run("""
        CREATE (g:GapSuggestion {
            id: $id,
            suggestion_text: $suggestion_text,
            target_node_id: $target_node_id,
            target_file_id: $target_file_id,
            similarity_score: $similarity_score,
            created_at: $created_at
        })
    """,
        id=suggestion_id,
        suggestion_text=gap_suggestion.SuggestionText,
        target_node_id=node_id,
        target_file_id=gap_suggestion.TargetFileId,
        similarity_score=gap_suggestion.SimilarityScore,
        created_at=now_iso()
    )

    # Link GapSuggestion -> KnowledgeNode
    session.run("""
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (g:GapSuggestion {id: $suggestion_id})
        MERGE (n)-[:HAS_SUGGESTION]->(g)
    """, node_id=node_id, suggestion_id=suggestion_id)

    return suggestion_id


def create_gap_suggestion_safe(session, node_id: str, suggestion_text: str = None) -> str:
    """Tạo GapSuggestion cho leaf node"""
    
    suggestion_id = f"suggestion-{uuid.uuid4().hex[:8]}"
    
    # Get node name for better suggestion
    result = session.run("""
        MATCH (n:KnowledgeNode {id: $node_id})
        RETURN n.name as name
    """, node_id=node_id)
    
    record = result.single()
    node_name = record['name'] if record else "this topic"
    
    if not suggestion_text:
        suggestion_text = f"Further research needed on {node_name}"
    
    session.run("""
        CREATE (g:GapSuggestion {
            id: $id,
            suggestion_text: $suggestion_text,
            target_node_id: $target_node_id,
            target_file_id: $target_file_id,
            similarity_score: $similarity_score,
            created_at: $created_at
        })
    """,
        id=suggestion_id,
        suggestion_text=suggestion_text,
        target_node_id=node_id,
        target_file_id="",
        similarity_score=0.7,
        created_at=now_iso()
    )
    
    # Link GapSuggestion -> KnowledgeNode
    session.run("""
        MATCH (n:KnowledgeNode {id: $node_id})
        MATCH (g:GapSuggestion {id: $suggestion_id})
        MERGE (n)-[:HAS_SUGGESTION]->(g)
    """, node_id=node_id, suggestion_id=suggestion_id)
    
    return suggestion_id


# ============================================
# MAIN GRAPH CREATION (FIXED)
# ============================================

def create_hierarchical_graph_ultra_aggressive(
    session, workspace_id: str, structure: Dict, file_id: str,
    file_name: str, lang: str = 'ENG', processed_chunks: List[Dict] = None
) -> Dict[str, Any]:
    """
    FIXED VERSION:
    1. Ultra-aggressive deduplication (similarity > 0.5)
    2. Mọi node PHẢI có ít nhất 1 Evidence với DỮ LIỆU THẬT từ chunks
    3. Mọi leaf node PHẢI có GapSuggestion
    4. KHÔNG lưu embedding trong Neo4j
    
    Args:
        processed_chunks: List of analyzed chunks từ process_chunks_ultra_compact()
                         Format: [{'text': '...', 'topic': '...', 'concepts': [...], 'summary': '...'}]
    
    Returns: Stats về nodes created/merged/evidences/suggestions
    """
    
    stats = {
        'nodes_created': 0,
        'nodes_merged': 0,
        'exact_matches': 0,
        'synonym_matches': 0,
        'high_similarity_matches': 0,
        'medium_similarity_matches': 0,
        'total_evidences_created': 0,
        'total_suggestions_created': 0,
        'final_node_count': 0
    }
    
    created_nodes = []  # Track để check Evidence sau
    
    # Build concept -> chunks mapping (để lấy evidence text THẬT)
    concept_to_chunks = {}
    if processed_chunks:
        for chunk in processed_chunks:
            chunk_text = chunk.get('text', '')
            chunk_concepts = chunk.get('concepts', [])
            
            for concept in chunk_concepts:
                concept_normalized = normalize_text(concept)
                if concept_normalized not in concept_to_chunks:
                    concept_to_chunks[concept_normalized] = []
                concept_to_chunks[concept_normalized].append(chunk_text)
    
    def get_evidence_texts(concept_name: str, max_texts: int = 3) -> List[str]:
        """Lấy evidence texts THẬT từ chunks cho concept"""
        normalized = normalize_text(concept_name)
        
        # Exact match
        if normalized in concept_to_chunks:
            return concept_to_chunks[normalized][:max_texts]
        
        # Fuzzy match (tìm chunks có chứa concept name)
        matched_texts = []
        for norm_concept, texts in concept_to_chunks.items():
            if normalized in norm_concept or norm_concept in normalized:
                matched_texts.extend(texts)
                if len(matched_texts) >= max_texts:
                    break
        
        return matched_texts[:max_texts] if matched_texts else []
    
    def create_or_merge_node(name: str, synthesis: str, node_type: str, 
                            level: int, hierarchy_path: str = "") -> str:
        """
        Tạo hoặc merge node với ULTRA-AGGRESSIVE deduplication.
        LUÔN LUÔN tạo Evidence node với DỮ LIỆU THẬT từ document.
        
        Args:
            evidence_text: DỮ LIỆU THẬT từ document chunks (KHÔNG phải synthesis)
        """
        
        # Try find existing match
        match = find_best_match_aggressive(session, workspace_id, name, node_type, level)
        
        if match:
            # MERGE into existing node
            node_id = match['id']
            match_type = match['match_type']
            similarity = match['sim']
            
            # Update stats
            stats['nodes_merged'] += 1
            if match_type == 'exact':
                stats['exact_matches'] += 1
            elif match_type == 'synonym':
                stats['synonym_matches'] += 1
            elif match_type == 'high_sim':
                stats['high_similarity_matches'] += 1
            else:
                stats['medium_similarity_matches'] += 1
            
            # Update node: append synthesis, add file_id, add alias
            confidence_boost = {
                'exact': 1.0,
                'alias': 1.0,
                'synonym': 0.9,
                'high_sim': 0.7,
                'medium_sim': 0.5
            }.get(match_type, 0.5)
            
            session.run("""
                MATCH (n:KnowledgeNode {id: $id})
                SET n.synthesis = n.synthesis + '\\n\\n[' + $file_name + '] ' + $new_synthesis,
                    n.file_ids = CASE 
                        WHEN $file_id IN COALESCE(n.file_ids, []) THEN COALESCE(n.file_ids, [])
                        ELSE COALESCE(n.file_ids, []) + $file_id
                    END,
                    n.aliases = CASE 
                        WHEN NOT $name IN COALESCE(n.aliases, []) AND $name <> n.name
                        THEN COALESCE(n.aliases, []) + $name
                        ELSE COALESCE(n.aliases, [])
                    END,
                    n.updated_at = $updated_at
            """, id=node_id, new_synthesis=synthesis[:200], file_id=file_id,
                 file_name=file_name, name=name, updated_at=now_iso())
            
            print(f"    ♻️  MERGE ({match_type}, {similarity:.2f}): '{name}' → '{match['name']}'")
            
        else:
            # CREATE new node (NO EMBEDDING)
            node_id = f"{node_type}-{uuid.uuid4().hex[:8]}"
            stats['nodes_created'] += 1
            
            session.run("""
                CREATE (n:KnowledgeNode {
                    id: $id,
                    workspace_id: $ws,
                    name: $name,
                    type: $type,
                    level: $level,
                    synthesis: '[' + $file_name + '] ' + $synthesis,
                    file_ids: [$file_id],
                    aliases: [],
                    source_count: 0,
                    total_confidence: 0.0,
                    created_at: $created_at,
                    updated_at: $created_at
                })
            """,
                id=node_id,
                ws=workspace_id,
                name=name,
                type=node_type,
                level=level,
                synthesis=synthesis[:200],
                file_id=file_id,
                file_name=file_name,
                created_at=now_iso()
            )
            
            print(f"    ✨ CREATE: '{name}'")
        
        # BẮT BUỘC: Tạo Evidence với DỮ LIỆU THẬT từ document chunks
        evidence_texts = get_evidence_texts(name, max_texts=1)
        actual_evidence_text = evidence_texts[0] if evidence_texts else synthesis
        
        # Nếu không tìm được chunk text, fallback sang synthesis
        if not actual_evidence_text or len(actual_evidence_text) < 50:
            actual_evidence_text = synthesis
        
        evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            ChunkId=f"chunk-{uuid.uuid4().hex[:8]}",
            Text=actual_evidence_text[:2000],  # DỮ LIỆU THẬT từ PDF, max 2000 chars
            Page=1,  # TODO: Get from chunk metadata if available
            Confidence=0.8 if evidence_texts else 0.5,  # Lower confidence if fallback
            CreatedAt=datetime.now(),
            Language=lang,
            SourceLanguage=lang,
            HierarchyPath=hierarchy_path or name,
            Concepts=[name],
            KeyClaims=[synthesis[:200]] if synthesis else []
        )
        create_evidence_node_safe(session, evidence, node_id)
        stats['total_evidences_created'] += 1
        
        created_nodes.append(node_id)
        return node_id
    
    # Validate structure
    if not structure or not isinstance(structure, dict):
        print(f"⚠️  Invalid structure: {type(structure).__name__}")
        return stats
    
    print(f"\n🔗 Building graph for: {file_name}")
    
    # Level 0: Domain
    domain = structure.get('domain', {}) or {}
    domain_name = domain.get('name', 'Document Domain')
    domain_id = create_or_merge_node(
        domain_name,
        domain.get('synthesis', ''),
        'domain',
        0,
        hierarchy_path=domain_name
    )
    
    # Level 1: Categories
    for cat in structure.get('categories', []):
        cat_name = cat.get('name', '')
        if not cat_name:
            continue
        
        cat_hierarchy = f"{domain_name} > {cat_name}"
        cat_id = create_or_merge_node(
            cat_name,
            cat.get('synthesis', ''),
            'category',
            1,
            hierarchy_path=cat_hierarchy
        )
        
        # Link Domain -> Category
        session.run("""
            MATCH (d:KnowledgeNode {id: $did}), (c:KnowledgeNode {id: $cid})
            MERGE (d)-[:HAS_SUBCATEGORY]->(c)
        """, did=domain_id, cid=cat_id)
        
        # Level 2: Concepts
        for concept in cat.get('concepts', []):
            concept_name = concept.get('name', '')
            if not concept_name:
                continue
            
            concept_hierarchy = f"{cat_hierarchy} > {concept_name}"
            concept_id = create_or_merge_node(
                concept_name,
                concept.get('synthesis', ''),
                'concept',
                2,
                hierarchy_path=concept_hierarchy
            )
            
            # Link Category -> Concept
            session.run("""
                MATCH (c:KnowledgeNode {id: $cid}), (n:KnowledgeNode {id: $nid})
                MERGE (c)-[:CONTAINS_CONCEPT]->(n)
            """, cid=cat_id, nid=concept_id)
            
            # Level 3: Subconcepts
            for sub in concept.get('subconcepts', []):
                sub_name = sub.get('name', '')
                if not sub_name:
                    continue
                
                sub_hierarchy = f"{concept_hierarchy} > {sub_name}"
                sub_id = create_or_merge_node(
                    sub_name,
                    sub.get('synthesis', ''),
                    'subconcept',
                    3,
                    hierarchy_path=sub_hierarchy
                )
                
                # Link Concept -> Subconcept
                session.run("""
                    MATCH (c:KnowledgeNode {id: $cid}), (s:KnowledgeNode {id: $sid})
                    MERGE (c)-[:HAS_DETAIL]->(s)
                """, cid=concept_id, sid=sub_id)
    
    # POST-PROCESSING: Add GapSuggestion cho tất cả leaf nodes
    print(f"\n  📝 Adding suggestions to leaf nodes...")
    leaf_result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
        RETURN n.id as node_id, n.name as node_name
    """, ws=workspace_id)
    
    for record in leaf_result:
        create_gap_suggestion_safe(session, record['node_id'], 
                                   f"Further research needed on {record['node_name']}")
        stats['total_suggestions_created'] += 1
    
    # Final stats
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        RETURN count(n) as total
    """, ws=workspace_id)
    
    record = result.single()
    stats['final_node_count'] = record['total']
    
    print(f"\n✅ Graph built:")
    print(f"   Nodes created: {stats['nodes_created']}")
    print(f"   Nodes merged: {stats['nodes_merged']}")
    print(f"   Evidences: {stats['total_evidences_created']}")
    print(f"   Suggestions: {stats['total_suggestions_created']}")
    print(f"   Final count: {stats['final_node_count']}")
    
    return stats


# ============================================
# VALIDATION UTILITIES
# ============================================

def validate_graph_integrity(session, workspace_id: str) -> Dict:
    """
    Validate graph integrity:
    1. Mọi node có ít nhất 1 Evidence
    2. Mọi leaf node có GapSuggestion
    """
    
    # Check nodes without Evidence
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_EVIDENCE]->()
        RETURN count(n) as nodes_without_evidence
    """, ws=workspace_id)
    
    nodes_without_evidence = result.single()['nodes_without_evidence']
    
    # Check leaf nodes without GapSuggestion
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
          AND NOT (n)-[:HAS_SUGGESTION]->()
        RETURN count(n) as leaf_nodes_without_suggestion
    """, ws=workspace_id)
    
    leaf_nodes_without_suggestion = result.single()['leaf_nodes_without_suggestion']
    
    # Overall stats
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        WITH n, count(e) as evidence_count
        RETURN count(n) as total_nodes,
               avg(evidence_count) as avg_evidences_per_node,
               sum(CASE WHEN evidence_count > 1 THEN 1 ELSE 0 END) as nodes_with_multiple_evidences
    """, ws=workspace_id)
    
    record = result.single()
    
    validation = {
        'total_nodes': record['total_nodes'],
        'avg_evidences_per_node': round(record['avg_evidences_per_node'], 2),
        'nodes_with_multiple_evidences': record['nodes_with_multiple_evidences'],
        'nodes_without_evidence': nodes_without_evidence,
        'leaf_nodes_without_suggestion': leaf_nodes_without_suggestion,
        'is_valid': nodes_without_evidence == 0 and leaf_nodes_without_suggestion == 0
    }
    
    return validation


def fix_missing_relationships(session, workspace_id: str, file_id: str, file_name: str) -> Dict:
    """
    Fix nodes thiếu Evidence hoặc GapSuggestion
    """
    
    fixed = {
        'evidences_added': 0,
        'suggestions_added': 0
    }
    
    # Fix nodes without Evidence
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_EVIDENCE]->()
        RETURN n.id as node_id, n.name as node_name, n.synthesis as synthesis
    """, ws=workspace_id)
    
    for record in result:
        evidence = Evidence(
            SourceId=file_id,
            SourceName=file_name,
            ChunkId="",
            Text=record.get('synthesis', '')[:500],
            Page=1,
            Confidence=0.5,
            CreatedAt=datetime.now(),
            Language='ENG',
            SourceLanguage='ENG',
            HierarchyPath=record['node_name'],
            Concepts=[record['node_name']],
            KeyClaims=[]
        )
        create_evidence_node_safe(session, evidence, record['node_id'])
        fixed['evidences_added'] += 1
    
    # Fix leaf nodes without GapSuggestion
    result = session.run("""
        MATCH (n:KnowledgeNode {workspace_id: $ws})
        WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
          AND NOT (n)-[:HAS_SUGGESTION]->()
        RETURN n.id as node_id, n.name as node_name
    """, ws=workspace_id)
    
    for record in result:
        create_gap_suggestion_safe(session, record['node_id'])
        fixed['suggestions_added'] += 1
    
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
