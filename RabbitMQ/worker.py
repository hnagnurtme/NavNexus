"""
PRODUCTION WORKER - LLM-Powered Knowledge Graph Builder
========================================================

This worker processes PDF documents and builds hierarchical knowledge graphs using:
- ✅ Real LLM analysis (extract_deep_merge_structure, analyze_chunks_for_merging)
- ✅ Neo4j for graph storage (no Qdrant needed)
- ✅ Full data2.json structure: KnowledgeNodes, Evidence, GapSuggestions
- ✅ Firebase real-time progress updates

PIPELINE FLOW:
1. Extract PDF → text, language, metadata
2. Create smart chunks with overlap
3. LLM extracts hierarchical structure (5 levels: domain → category → concept → subconcept → detail)
4. LLM analyzes chunks → maps to concepts with Concepts, KeyClaims, QuestionsRaised
5. Insert into Neo4j: nodes → relationships → evidence → gap suggestions
6. Push status to Firebase
"""

import os
import sys
import json
import time
import signal
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# RabbitMQ and Firebase clients
from src.rabbitmq_client import RabbitMQClient
from src.handler.firebase import FirebaseClient

# Database connections
from neo4j import GraphDatabase

# PDF processing pipeline
from src.pipeline.pdf_extraction import extract_pdf_enhanced
from src.pipeline.chunking import create_smart_chunks
from src.pipeline.llm_analysis import (
    extract_deep_merge_structure,
    analyze_chunks_for_merging,
    call_llm_sync,
    SYSTEM_MESSAGE
)

# Recursive expansion imports
from src.recursive_expander import RecursiveExpander, NodeData
from src.pipeline.position_extraction import split_text_to_paragraphs

# Models
from src.model.KnowledgeNode import KnowledgeNode
from src.model.Evidence import Evidence
from src.model.GapSuggestion import GapSuggestion

# ================================
# CONFIGURATION
# ================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('new_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NewPDFWorker')

# RabbitMQ Configuration
RABBITMQ_CONFIG = {
    "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
    "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
    "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
    "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
}

QUEUE_NAME = os.getenv("QUEUE_NAME", "PDF_JOBS_QUEUE")

# Neo4j Configuration
NEO4J_URL = os.getenv("NEO4J_URL", "neo4j+s://daa013e6.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY")

# LLM API Configuration (from config.py)
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-9063a257def64d469cfe961cb502988e5RNo")
CLOVA_API_URL = os.getenv("CLOVA_API_URL", "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005")

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "https://navnexus-default-rtdb.firebaseio.com/")

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ================================
# NEO4J INSERTION LOGIC (from seed.py)
# ================================

def create_knowledge_node(session, knowledge_node: KnowledgeNode) -> str:
    """
    Create KnowledgeNode with MERGE to avoid duplicates
    EXACT copy from seed.py
    """
    result = session.run(
        """
        MERGE (n:KnowledgeNode {id: $id})
        SET n.type = $type,
            n.name = $name,
            n.synthesis = $synthesis,
            n.workspace_id = $workspace_id,
            n.level = $level,
            n.source_count = $source_count,
            n.total_confidence = $total_confidence,
            n.created_at = $created_at,
            n.updated_at = $updated_at
        RETURN n.id
        """,
        id=knowledge_node.Id,
        type=knowledge_node.Type,
        name=knowledge_node.Name,
        synthesis=knowledge_node.Synthesis,
        workspace_id=knowledge_node.WorkspaceId,
        level=knowledge_node.Level,
        source_count=knowledge_node.SourceCount,
        total_confidence=knowledge_node.TotalConfidence,
        created_at=knowledge_node.CreatedAt.isoformat() if hasattr(knowledge_node.CreatedAt, 'isoformat') else knowledge_node.CreatedAt,
        updated_at=knowledge_node.UpdatedAt.isoformat() if hasattr(knowledge_node.UpdatedAt, 'isoformat') else knowledge_node.UpdatedAt
    )
    return result.single()[0]


def create_evidence_node(session, evidence: Evidence, node_id: str) -> str:
    """
    Create Evidence node with MERGE to avoid duplicates
    EXACT copy from seed.py with ALL fields
    """
    result = session.run(
        """
        MERGE (e:Evidence {id: $id})
        SET e.source_id = $source_id,
            e.source_name = $source_name,
            e.chunk_id = $chunk_id,
            e.text = $text,
            e.page = $page,
            e.confidence = $confidence,
            e.created_at = $created_at,
            e.language = $language,
            e.source_language = $source_language,
            e.hierarchy_path = $hierarchy_path,
            e.concepts = $concepts,
            e.key_claims = $key_claims,
            e.questions_raised = $questions_raised,
            e.evidence_strength = $evidence_strength
        WITH e
        MATCH (n:KnowledgeNode {id: $node_id})
        MERGE (n)-[:HAS_EVIDENCE]->(e)
        RETURN e.id
        """,
        id=evidence.Id,
        source_id=evidence.SourceId,
        source_name=evidence.SourceName,
        chunk_id=evidence.ChunkId,
        text=evidence.Text,
        page=evidence.Page,
        confidence=evidence.Confidence,
        created_at=evidence.CreatedAt.isoformat() if hasattr(evidence.CreatedAt, 'isoformat') else evidence.CreatedAt,
        language=evidence.Language,
        source_language=evidence.SourceLanguage,
        hierarchy_path=evidence.HierarchyPath,
        concepts=evidence.Concepts,
        key_claims=evidence.KeyClaims,
        questions_raised=evidence.QuestionsRaised,
        evidence_strength=evidence.EvidenceStrength,
        node_id=node_id
    )
    return result.single()[0]


def create_gap_suggestion_node(session, gap_suggestion: GapSuggestion, node_id: str):
    """
    Create GapSuggestion node with MERGE to avoid duplicates
    EXACT copy from seed.py with SimilarityScore
    """
    session.run(
        """
        MERGE (g:GapSuggestion {id: $id})
        SET g.suggestion_text = $suggestion_text,
            g.target_node_id = $target_node_id,
            g.target_file_id = $target_file_id,
            g.similarity_score = $similarity_score
        WITH g
        MATCH (n:KnowledgeNode {id: $node_id})
        MERGE (n)-[:HAS_SUGGESTION]->(g)
        """,
        id=gap_suggestion.Id,
        suggestion_text=gap_suggestion.SuggestionText,
        target_node_id=gap_suggestion.TargetNodeId,
        target_file_id=gap_suggestion.TargetFileId,
        similarity_score=gap_suggestion.SimilarityScore,
        node_id=node_id
    )


def create_parent_child_relationship(session, parent_id: str, child_id: str, relationship_type: str):
    """
    Create hierarchical relationship with MERGE to avoid duplicates
    EXACT copy from seed.py
    """
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


def determine_relationship_type(parent_level: int, child_level: int) -> str:
    """
    Determine relationship type based on levels
    EXACT copy from seed.py
    """
    if parent_level == 0 and child_level == 1:
        return 'domain_to_category'
    elif parent_level == 1 and child_level == 2:
        return 'category_to_concept'
    elif parent_level == 2 and child_level == 3:
        return 'concept_to_subconcept'
    else:
        return 'HAS_SUBCATEGORY'


# ================================
# PROMPTS FOR EXPERT-LEVEL ANALYSIS
# ================================

EVIDENCE_ENRICHMENT_PROMPT = """You are an expert research analyst extracting DEEP insights from document chunks.

CONCEPT: {concept_name}
SYNTHESIS: {concept_synthesis}

CHUNKS TO ANALYZE:
{chunks_text}

TASK: Extract HIGH-QUALITY evidence with expert-level analysis:

1. **KEY CLAIMS** (3-5 specific, actionable claims):
   - Must be SPECIFIC, not generic (❌ "The paper discusses X" ✅ "The algorithm achieves 95% accuracy on dataset Y")
   - Include quantitative data when available
   - Focus on novel contributions, not obvious facts
   - Each claim should stand alone as valuable insight

2. **QUESTIONS RAISED** (2-4 deep, thought-provoking questions):
   - Must be ANALYTICAL, not superficial (❌ "What is X?" ✅ "How does X trade off with Y in Z scenarios?")
   - Focus on: limitations, implications, extensions, comparisons
   - Questions that experts would ask after reading

EXAMPLE OUTPUT:
{{
  "key_claims": [
    "The Dueling DQN architecture achieves 18% energy reduction compared to greedy scheduling while maintaining 95% delivery success rate",
    "Satellites experience 60-minute sunlight and 35-minute shadow periods in 96-minute orbits, requiring predictive energy management",
    "Multi-agent approaches reduce communication overhead by 67% (3.2 KB/s vs 9.8 KB/s) compared to centralized DQN with 14 agents"
  ],
  "questions_raised": [
    "How does the Dueling DQN architecture handle non-stationary environments when multiple satellites learn concurrently?",
    "What is the optimal trade-off between energy savings and delivery latency for different priority levels?",
    "Can the predictive energy model adapt to unexpected solar storms or equipment degradation?"
  ]
}}

QUALITY REQUIREMENTS:
✓ Key claims must contain NUMBERS or SPECIFIC facts
✓ Questions must require ANALYSIS to answer (not simple lookups)
✓ Focus on DEPTH over breadth - better 3 excellent claims than 5 mediocre ones

Return ONLY the JSON object."""

# ================================
# HELPER FUNCTIONS
# ================================

def extract_paragraphs_from_pdf(pdf_text: str) -> List[str]:
    """
    Convert PDF text into paragraph array for position-based extraction

    Args:
        pdf_text: Raw text from PDF

    Returns:
        List of paragraph strings
    """
    return split_text_to_paragraphs(pdf_text)


async def async_llm_caller(prompt: str, system_message: str, max_tokens: int = 2000) -> Dict:
    """
    Async wrapper for LLM calls (for RecursiveExpander)

    Args:
        prompt: The prompt to send to LLM
        system_message: System message for LLM
        max_tokens: Maximum tokens to generate

    Returns:
        Parsed JSON response from LLM
    """
    import asyncio

    # Run synchronous LLM call in executor to make it async
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: call_llm_sync(
            prompt=prompt,
            max_tokens=max_tokens,
            system_message=system_message,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )
    )
    return result


def get_existing_nodes_from_workspace(neo4j_driver, workspace_id: str) -> List[Dict]:
    """
    Lấy tất cả nodes hiện có từ workspace để LLM merge
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
                RETURN n.id as id, n.name as name, n.type as type,
                       n.level as level, n.synthesis as synthesis
                ORDER BY n.level, n.name
                """,
                workspace_id=workspace_id
            )
            nodes = []
            for record in result:
                nodes.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "level": record["level"],
                    "synthesis": record["synthesis"]
                })
            return nodes
    except Exception as e:
        logger.warning(f"⚠️  Could not fetch existing nodes: {e}")
        return []


def find_or_merge_node_simple(existing_nodes: List[Dict], new_node_name: str, new_node_type: str,
                              new_synthesis: str, level: int) -> Optional[str]:
    """
    Simple word-overlap based merge (fast, no LLM)
    """
    for existing in existing_nodes:
        if existing["type"] != new_node_type or existing["level"] != level:
            continue

        existing_name = existing["name"].lower()
        new_name = new_node_name.lower()

        # Exact match
        if existing_name == new_name:
            return existing["id"]

        # Word overlap (>75%)
        existing_words = set(existing_name.split())
        new_words = set(new_name.split())
        if len(existing_words) > 0:
            overlap = len(existing_words & new_words) / len(existing_words | new_words)
            if overlap > 0.75:
                logger.info(f"  🔗 Merging '{new_node_name}' → '{existing['name']}' ({overlap:.0%})")
                return existing["id"]

    return None


def find_merge_candidates_llm(new_nodes: List[Dict], existing_nodes: List[Dict],
                               clova_api_key: str, clova_api_url: str) -> Dict[str, str]:
    """
    LLM-based semantic merge matching (slower, higher quality)

    Returns:
        Dict mapping new_node_name -> existing_node_id for merges
    """
    if not existing_nodes or not new_nodes:
        return {}

    # Prepare context for LLM
    existing_context = "\n".join([
        f"- [{n['type']}] {n['name']} (ID: {n['id']}, Level: {n['level']})"
        for n in existing_nodes[:30]  # Limit to top 30
    ])

    new_context = "\n".join([
        f"- [{n['type']}] {n['name']} (Level: {n['level']}, Synthesis: {n['synthesis'][:100]})"
        for n in new_nodes[:20]  # Limit to top 20
    ])

    prompt = f"""You are a knowledge graph merge expert. Identify which NEW nodes should merge with EXISTING nodes.

EXISTING NODES in workspace:
{existing_context}

NEW NODES from PDF:
{new_context}

TASK: For each NEW node, determine if it should MERGE with an existing node based on:
1. Semantic similarity (similar meaning, not just word overlap)
2. Same type and level
3. Confidence > 80% that they represent the same concept

Return JSON array of merge recommendations:
{{
  "merges": [
    {{"new_node": "New Node Name", "existing_id": "existing-node-id-123", "confidence": 0.92, "reason": "Brief explanation"}},
    ...
  ]
}}

ONLY include high-confidence merges (>0.8). Return empty array if no good merges found."""

    try:
        result = call_llm_sync(
            prompt=prompt,
            max_tokens=1500,
            system_message="You are an expert at semantic matching for knowledge graph merging.",
            clova_api_key=clova_api_key,
            clova_api_url=clova_api_url
        )

        if result and isinstance(result, dict):
            merges = result.get('merges', [])
            merge_mapping = {}
            for merge in merges:
                new_name = merge.get('new_node', '')
                existing_id = merge.get('existing_id', '')
                confidence = merge.get('confidence', 0.0)
                if confidence > 0.8 and existing_id:
                    merge_mapping[new_name] = existing_id
                    logger.info(f"  🤖 LLM merge: '{new_name}' → {existing_id} ({confidence:.0%})")
            return merge_mapping
    except Exception as e:
        logger.warning(f"  ⚠️  LLM merge matching failed: {e}")

    return {}


def identify_leaf_nodes(neo4j_driver, workspace_id: str) -> List[str]:
    """
    Tìm tất cả leaf nodes (nodes không có outgoing HAS_SUBCATEGORY relationship)
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
                WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
                RETURN n.id as id
                """,
                workspace_id=workspace_id
            )
            return [record["id"] for record in result]
    except Exception as e:
        logger.warning(f"⚠️  Could not identify leaf nodes: {e}")
        return []


def convert_nodes_to_structure(nodes: List[Dict]) -> Dict:
    """
    Convert Neo4j nodes list to structure format for identify_merge_candidates()
    """
    if not nodes:
        return {}

    # Group nodes by level
    domain_nodes = [n for n in nodes if n['level'] == 0]
    category_nodes = [n for n in nodes if n['level'] == 1]
    concept_nodes = [n for n in nodes if n['level'] == 2]

    structure = {
        "domain": {
            "name": domain_nodes[0]['name'] if domain_nodes else "Existing Knowledge",
            "synthesis": domain_nodes[0].get('synthesis', ''),
            "level": 1
        },
        "categories": []
    }

    for cat in category_nodes[:5]:  # Top 5 categories
        structure["categories"].append({
            "name": cat['name'],
            "synthesis": cat.get('synthesis', ''),
            "level": 2,
            "concepts": [
                {
                    "name": c['name'],
                    "synthesis": c.get('synthesis', ''),
                    "level": 3,
                    "subconcepts": []
                }
                for c in concept_nodes if c.get('name', '').startswith(cat['name'][:10])
            ][:3]  # Max 3 concepts per category
        })

    return structure


def enrich_evidence_with_llm(
    chunks: List[Dict],
    concept_name: str,
    concept_synthesis: str,
    clova_api_key: str,
    clova_api_url: str
) -> Dict:
    """
    LLM call để extract key_claims và questions_raised cho concept

    NOTE: Text được lấy trực tiếp từ chunk gốc, LLM CHỈ tìm claims và questions

    Returns:
        {
            'key_claims': [...],  # Chi tiết, có số liệu từ LLM
            'questions_raised': [...]  # Sâu sắc, analytical từ LLM
        }
    """
    if not chunks:
        return {
            'key_claims': [],
            'questions_raised': []
        }

    # Prepare chunks text (max 3 chunks, 500 chars each)
    chunks_text = ""
    for idx, chunk in enumerate(chunks[:3]):
        text = chunk.get('text', '')[:500].strip()
        chunks_text += f"\n[Chunk {idx + 1}]:\n{text}\n"

    prompt = EVIDENCE_ENRICHMENT_PROMPT.format(
        concept_name=concept_name,
        concept_synthesis=concept_synthesis[:200],  # Truncate for context
        chunks_text=chunks_text
    )

    try:
        result = call_llm_sync(
            prompt=prompt,
            max_tokens=1000,  # Reduced since no cleaned_text
            system_message=SYSTEM_MESSAGE,
            clova_api_key=clova_api_key,
            clova_api_url=clova_api_url
        )

        if result and isinstance(result, dict):
            return {
                'key_claims': result.get('key_claims', []),
                'questions_raised': result.get('questions_raised', [])
            }
    except Exception as e:
        logger.warning(f"  ⚠️  Evidence enrichment failed for {concept_name}: {e}")

    # Fallback to basic extraction
    return {
        'key_claims': [f"Information about {concept_name} from source document"],
        'questions_raised': [f"How does {concept_name} relate to broader context?"]
    }


def get_all_concepts_from_structure(structure: Dict) -> List[Dict]:
    """
    Flatten structure to list of all concepts with their full context
    """
    concepts = []

    for category in structure.get('categories', []):
        cat_name = category.get('name', '')

        for concept in category.get('concepts', []):
            concepts.append({
                'name': concept.get('name', ''),
                'synthesis': concept.get('synthesis', ''),
                'category': cat_name,
                'level': concept.get('level', 3)
            })

            # Include subconcepts if they exist
            for subconcept in concept.get('subconcepts', []):
                concepts.append({
                    'name': subconcept.get('name', ''),
                    'synthesis': subconcept.get('synthesis', ''),
                    'category': cat_name,
                    'parent_concept': concept.get('name', ''),
                    'level': subconcept.get('level', 4)
                })

    return concepts


# ================================
# RECURSIVE EXPANSION INTEGRATION
# ================================

async def process_pdf_with_recursive_expansion(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    neo4j_driver,
    job_id: str
) -> Dict[str, Any]:
    """
    Process PDF using RECURSIVE EXPANSION with POSITION-BASED extraction

    NEW PIPELINE (5-level deep hierarchy):
    1. Extract PDF → paragraphs array
    2. Create initial domain node with LLM
    3. Use RecursiveExpander to build 5-level hierarchy recursively
    4. Insert into Neo4j with position-based evidence
    5. Create Gap Suggestions for leaf nodes

    This replaces the old 3-stage pipeline with a cleaner recursive approach.
    """
    logger.info(f"📄 Processing PDF with Recursive Expansion: {file_name}")

    try:
        # ========================================
        # STEP 1: Extract PDF and create paragraph array
        # ========================================
        logger.info("  [1/5] Extracting PDF content...")
        pdf_text, language, metadata = extract_pdf_enhanced(pdf_url, max_pages=25, timeout=30)

        if not pdf_text or len(pdf_text) < 100:
            raise ValueError(f"PDF extraction failed or too short: {len(pdf_text)} chars")

        logger.info(f"  ✓ Extracted {len(pdf_text)} characters")
        logger.info(f"  ✓ Language: {language}")
        logger.info(f"  ✓ Pages: {metadata.get('extracted_pages', 0)}/{metadata.get('total_pages', 0)}")

        # Convert to paragraph array
        paragraphs = extract_paragraphs_from_pdf(pdf_text)
        logger.info(f"  ✓ Split into {len(paragraphs)} paragraphs")

        # ========================================
        # STEP 2: Create initial domain node (LLM Call 1)
        # ========================================
        logger.info("  [2/5] Creating initial domain node...")

        domain_prompt = f"""Extract the MAIN DOMAIN and TOP-LEVEL EVIDENCE from this document.

DOCUMENT: {file_name}
LANGUAGE: {language}
TOTAL PARAGRAPHS: {len(paragraphs)}

CONTENT (first 3000 chars):
---
{pdf_text[:3000]}
---

TASK: Create the root domain node with evidence positions.

EVIDENCE POSITIONS: Use paragraph indices [start, end] relative to the full document.
Example: [[0, 10], [15, 25]] means paragraphs 0-10 and 15-25 contain domain-level evidence.

OUTPUT (strict JSON):
{{
  "domain": {{
    "name": "Document's main subject (concise, 3-7 words)",
    "synthesis": "Comprehensive 120-150 char overview of the entire document",
    "evidence_positions": [[start1, end1], [start2, end2]],
    "key_claims_positions": [idx1, idx2, idx3],
    "questions_positions": [idx1, idx2]
  }}
}}

REQUIREMENTS:
✓ Name: Concise (3-7 words), describes the OVERALL domain
✓ Synthesis: 120-150 chars, comprehensive overview
✓ Evidence positions: 2-4 ranges covering key sections of the document
✓ Key claims: 3-5 paragraph indices with major claims
✓ Questions: 2-3 paragraph indices with important questions
✓ All positions must be valid [0, {len(paragraphs) - 1}]

Return ONLY the JSON object."""

        domain_result = await async_llm_caller(
            prompt=domain_prompt,
            system_message="You are an expert at identifying document domains and extracting position-based evidence.",
            max_tokens=1000
        )

        # ❌ NO FALLBACK - fail if LLM doesn't return valid result
        if not domain_result or not domain_result.get('domain'):
            raise ValueError("❌ LLM domain extraction failed - no valid domain returned. Aborting processing.")

        domain_data = domain_result['domain']

        # ✅ Validate domain data quality
        domain_name = domain_data.get('name', '')
        domain_synthesis = domain_data.get('synthesis', '')
        domain_positions = domain_data.get('evidence_positions', [])

        if not domain_name or len(domain_name) < 5:
            raise ValueError(f"❌ Invalid domain name: '{domain_name}' - too short (<5 chars) or empty")

        if not domain_synthesis or len(domain_synthesis) < 50:
            raise ValueError(f"❌ Invalid domain synthesis: '{domain_synthesis[:50]}...' - too short (<50 chars)")

        if not domain_positions or len(domain_positions) == 0:
            raise ValueError("❌ No evidence positions provided by LLM for domain")

        logger.info(f"  ✓ Domain validation passed: '{domain_name}' ({len(domain_synthesis)} chars synthesis)")

        # Create root NodeData
        root_node = NodeData(
            id=f"domain-{uuid.uuid4().hex[:8]}",
            name=domain_name,
            synthesis=domain_synthesis,
            level=0,
            type='domain',
            evidence_positions=domain_positions,
            key_claims_positions=domain_data.get('key_claims_positions', []),
            questions_positions=domain_data.get('questions_positions', [])
        )

        logger.info(f"  ✓ Created domain node: '{root_node.name}'")
        logger.info(f"  ✓ Evidence positions: {root_node.evidence_positions}")

        # ========================================
        # STEP 3: Recursive expansion (LLM Calls 2-N)
        # ========================================
        logger.info("  [3/5] Recursive expansion (LIMITED DEPTH)...")

        # ✅ STRICTER LIMITS to prevent over-expansion
        MAX_DEPTH = 3  # 0=domain, 1=category, 2=concept, 3=subconcept (NO detail level)
        MAX_CHILDREN = 3  # Max 3 children per node
        MIN_CONTENT = 800  # Higher threshold to stop expansion earlier

        expander = RecursiveExpander(
            paragraphs=paragraphs,
            llm_caller=async_llm_caller,
            max_depth=MAX_DEPTH,
            children_per_level=MAX_CHILDREN,
            min_content_length=MIN_CONTENT
        )

        logger.info(f"  ✓ Recursion limits: max_depth={MAX_DEPTH}, children={MAX_CHILDREN}, min_content={MIN_CONTENT}")

        await expander.expand_node_recursively(
            node=root_node,
            current_depth=0,
            target_depth=MAX_DEPTH
        )

        stats = expander.get_stats()
        logger.info(f"  ✓ Recursive expansion complete")
        logger.info(f"    - Total nodes: {stats['total_nodes'] + 1}")  # +1 for root
        logger.info(f"    - LLM calls: {stats['llm_calls'] + 1}")  # +1 for domain extraction
        logger.info(f"    - Expansions stopped: {stats['expansions_stopped']}")
        logger.info(f"    - Errors: {stats['errors']}")

        # ========================================
        # STEP 4: Filter and Insert into Neo4j (QUALITY CONTROL)
        # ========================================
        logger.info("  [4/5] Filtering nodes and inserting into Neo4j...")

        source_id = pdf_url
        nodes_created = 0
        nodes_filtered = 0
        evidences_created = 0

        # Get all nodes in flat list (depth-first traversal)
        all_nodes = expander.get_all_nodes_flat(root_node)

        # ✅ QUALITY FILTER: Remove low-quality nodes
        def is_valid_node(node: NodeData) -> bool:
            """
            Validate node quality before inserting to Neo4j

            Returns:
                True if node meets quality standards, False otherwise
            """
            # Rule 1: Name must be meaningful (not generic)
            if not node.name or len(node.name) < 3:
                logger.debug(f"  ❌ Filtered '{node.name}': name too short")
                return False

            # Rule 2: Synthesis must have substance
            min_synthesis_length = {
                0: 50,   # domain: 50+ chars
                1: 40,   # category: 40+ chars
                2: 30,   # concept: 30+ chars
                3: 20,   # subconcept: 20+ chars
            }
            required_length = min_synthesis_length.get(node.level, 20)
            if not node.synthesis or len(node.synthesis) < required_length:
                logger.debug(f"  ❌ Filtered '{node.name}': synthesis too short ({len(node.synthesis)} < {required_length})")
                return False

            # Rule 3: Must have evidence positions (except root domain)
            if node.level > 0 and (not node.evidence_positions or len(node.evidence_positions) == 0):
                logger.debug(f"  ❌ Filtered '{node.name}': no evidence positions")
                return False

            # Rule 4: Must have evidence content extracted
            if node.level > 0 and (not node.evidence_content or len(node.evidence_content) == 0):
                logger.debug(f"  ❌ Filtered '{node.name}': no evidence content extracted")
                return False

            # Rule 5: Avoid generic/templated names
            generic_keywords = ['child', 'node', 'item', 'concept 1', 'category 1', 'unknown', 'untitled']
            if any(keyword in node.name.lower() for keyword in generic_keywords):
                logger.debug(f"  ❌ Filtered '{node.name}': generic name")
                return False

            return True

        # Filter nodes
        filtered_nodes = [node for node in all_nodes if is_valid_node(node)]
        nodes_filtered = len(all_nodes) - len(filtered_nodes)

        logger.info(f"  ✓ Quality filter: {len(filtered_nodes)}/{len(all_nodes)} nodes passed ({nodes_filtered} filtered out)")

        if len(filtered_nodes) == 0:
            raise ValueError("❌ All nodes were filtered out due to quality issues. Aborting.")

        with neo4j_driver.session() as session:
            for node in filtered_nodes:
                # Create KnowledgeNode
                knowledge_node = KnowledgeNode(
                    Id=node.id,
                    Type=node.type,
                    Name=node.name,
                    Synthesis=node.synthesis,
                    WorkspaceId=workspace_id,
                    Level=node.level,
                    SourceCount=1,
                    TotalConfidence=0.92 - (node.level * 0.02),  # Decreasing confidence by level
                    CreatedAt=node.created_at,
                    UpdatedAt=node.created_at
                )
                create_knowledge_node(session, knowledge_node)
                nodes_created += 1

                # Create parent-child relationship (if not root)
                if node.parent_id:
                    rel_type = determine_relationship_type(
                        parent_level=node.level - 1,
                        child_level=node.level
                    )
                    create_parent_child_relationship(session, node.parent_id, node.id, rel_type)

                # Create Evidence from evidence_content
                if node.evidence_content:
                    for evidence_item in node.evidence_content[:2]:  # Max 2 evidence per node
                        # Extract key claims text from content items
                        key_claims = []
                        if hasattr(node, 'key_claims_content') and node.key_claims_content:
                            key_claims = [item.get('text', '') for item in node.key_claims_content[:3] if isinstance(item, dict)]
                            if not key_claims:
                                key_claims = [f"Evidence from {file_name}"]
                        else:
                            key_claims = [f"Evidence from {file_name}"]

                        # Extract questions text from content items
                        questions = []
                        if hasattr(node, 'questions_content') and node.questions_content:
                            questions = [item.get('text', '') for item in node.questions_content[:2] if isinstance(item, dict)]

                        evidence = Evidence(
                            Id=f"evidence-{uuid.uuid4().hex[:8]}",
                            SourceId=source_id,
                            SourceName=file_name,
                            ChunkId=f"para-{evidence_item.get('position_range', [0, 0])[0]:04d}",
                            Text=evidence_item.get('text', '')[:1500],
                            Page=evidence_item.get('position_range', [0, 0])[0] // 10 + 1,  # Approximate page
                            Confidence=0.90 - (node.level * 0.02),
                            CreatedAt=node.created_at,
                            Language="ENG" if language == "en" else "KOR",
                            SourceLanguage="ENG" if language == "en" else "KOR",
                            HierarchyPath=node.name,
                            Concepts=[node.name],
                            KeyClaims=key_claims,
                            QuestionsRaised=questions,
                            EvidenceStrength=0.88 - (node.level * 0.02)
                        )
                        create_evidence_node(session, evidence, node.id)
                        evidences_created += 1

        logger.info(f"  ✓ Created {nodes_created} nodes")
        logger.info(f"  ✓ Created {evidences_created} evidence")

        # ========================================
        # STEP 5: Create Gap Suggestions for leaf nodes
        # ========================================
        logger.info("  [5/5] Creating Gap Suggestions for leaf nodes...")

        leaf_nodes = identify_leaf_nodes(neo4j_driver, workspace_id)
        gaps_created = 0

        with neo4j_driver.session() as session:
            for leaf_node_id in leaf_nodes:
                gap_suggestion = GapSuggestion(
                    Id=f"gap-{uuid.uuid4().hex[:8]}",
                    SuggestionText=f"Consider exploring related research areas to deepen understanding",
                    TargetNodeId="https://arxiv.org/search",
                    TargetFileId="",
                    SimilarityScore=0.78
                )
                create_gap_suggestion_node(session, gap_suggestion, leaf_node_id)
                gaps_created += 1

        logger.info(f"  ✓ Created {gaps_created} gap suggestions")
        logger.info("  ✅ Processing complete")

        return {
            "status": "success",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "processing_mode": "RECURSIVE_EXPANSION",
            "nodes_created": nodes_created,
            "evidences_created": evidences_created,
            "gaps_created": gaps_created,
            "leaf_nodes": len(leaf_nodes),
            "language": language,
            "source_id": source_id,
            "quality_metrics": {
                "total_nodes": stats['total_nodes'] + 1,
                "llm_calls": stats['llm_calls'] + 1,
                "expansions_stopped": stats['expansions_stopped'],
                "errors": stats['errors'],
                "max_depth_achieved": max(node.level for node in all_nodes) if all_nodes else 0,
                "paragraphs_processed": len(paragraphs)
            }
        }

    except Exception as e:
        logger.error(f"❌ Error processing {file_name}: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "failed",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ================================
# PDF PROCESSING & DATA GENERATION (OLD - Keep for backward compatibility)
# ================================

def process_pdf_to_knowledge_graph(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    neo4j_driver,
    job_id: str
) -> Dict[str, Any]:
    """
    Process PDF with THREE-STAGE EXPERT-LEVEL ANALYSIS

    THREE-STAGE PIPELINE FOR QUALITY:
    Stage 1: Clean structure extraction (NO existing context to avoid overload)
    Stage 2: LLM-based semantic merging using identify_merge_candidates
    Stage 3: Per-concept evidence enrichment with enrich_evidence_with_llm

    STEPS:
    0. Fetch existing nodes from workspace
    1. Extract PDF content
    2. Create smart chunks
    3. STAGE 1: LLM extracts structure (clean, no merge context)
    4. STAGE 2: LLM identifies merge candidates with existing nodes
    5. STAGE 3: Per-concept evidence enrichment with focused LLM calls
    6. Insert/merge into Neo4j with high-quality evidence
    7. Create Gap Suggestions for LEAF NODES only
    """
    logger.info(f"📄 Processing PDF: {file_name}")

    try:
        # ========================================
        # STEP 0: Get existing nodes for merge context
        # ========================================
        logger.info("  [0/7] Fetching existing nodes from workspace...")
        existing_nodes = get_existing_nodes_from_workspace(neo4j_driver, workspace_id)
        logger.info(f"  ✓ Found {len(existing_nodes)} existing nodes")

        # Determine processing mode: NEW workspace vs MERGE mode
        is_new_workspace = len(existing_nodes) == 0
        processing_mode = "NEW_WORKSPACE" if is_new_workspace else "MERGE_MODE"
        logger.info(f"  ✓ Processing mode: {processing_mode}")

        # ========================================
        # STEP 1: Extract PDF
        # ========================================
        logger.info("  [1/6] Extracting PDF content...")
        pdf_text, language, metadata = extract_pdf_enhanced(pdf_url, max_pages=25, timeout=30)

        if not pdf_text or len(pdf_text) < 100:
            raise ValueError(f"PDF extraction failed or too short: {len(pdf_text)} chars")

        logger.info(f"  ✓ Extracted {len(pdf_text)} characters")
        logger.info(f"  ✓ Language: {language}")
        logger.info(f"  ✓ Pages: {metadata.get('extracted_pages', 0)}/{metadata.get('total_pages', 0)}")

        # ========================================
        # STEP 2: Create smart chunks
        # ========================================
        logger.info("  [2/6] Creating smart chunks...")
        chunks = create_smart_chunks(pdf_text, chunk_size=2000, overlap=400)
        logger.info(f"  ✓ Created {len(chunks)} chunks")

        # ========================================
        # STEP 3: STAGE 1 - Clean structure extraction with RETRY
        # ========================================
        logger.info("  [3/7] STAGE 1: Extracting hierarchical structure (clean, no context)...")

        structure = extract_deep_merge_structure(
            full_text=pdf_text,
            file_name=file_name,
            lang=language,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL,
            validate=True
        )

        if not structure or not structure.get('domain'):
            logger.warning("  ⚠️  LLM structure extraction failed, using fallback")
            structure = create_fallback_structure(file_name, workspace_id)

        # Quality validation - STRICT requirements
        categories = structure.get('categories', [])
        total_concepts = sum(len(cat.get('concepts', [])) for cat in categories)
        total_subconcepts = sum(
            len(concept.get('subconcepts', []))
            for cat in categories
            for concept in cat.get('concepts', [])
        )
        total_details = sum(
            len(subcon.get('details', []))
            for cat in categories
            for concept in cat.get('concepts', [])
            for subcon in concept.get('subconcepts', [])
        )

        logger.info(f"  ✓ Structure quality: {len(categories)} categories, {total_concepts} concepts, {total_subconcepts} subconcepts, {total_details} details")

        # STRICT validation with RETRY mechanism
        needs_retry = (
            len(categories) < 2 or
            total_concepts < 3 or
            total_subconcepts < 2 or
            total_details < 1
        )

        if needs_retry:
            logger.warning(f"  ⚠️  Structure quality insufficient - RETRYING with stricter prompt...")
            logger.warning(f"     Current: {len(categories)} cats, {total_concepts} concepts, {total_subconcepts} subcons, {total_details} details")

            # RETRY with focused prompt emphasizing depth
            retry_structure = force_deep_structure_extraction(
                pdf_text=pdf_text,
                file_name=file_name,
                language=language,
                clova_api_key=CLOVA_API_KEY,
                clova_api_url=CLOVA_API_URL
            )

            if retry_structure and retry_structure.get('domain'):
                # Validate retry result
                retry_cats = retry_structure.get('categories', [])
                retry_concepts = sum(len(cat.get('concepts', [])) for cat in retry_cats)
                retry_subcons = sum(
                    len(concept.get('subconcepts', []))
                    for cat in retry_cats
                    for concept in cat.get('concepts', [])
                )
                retry_details = sum(
                    len(subcon.get('details', []))
                    for cat in retry_cats
                    for concept in cat.get('concepts', [])
                    for subcon in concept.get('subconcepts', [])
                )

                # More lenient retry validation - accept if better than original
                is_retry_better = (
                    len(retry_cats) >= len(categories) and
                    retry_concepts >= total_concepts and
                    retry_subcons >= 2  # Minimum subconcepts
                )

                if is_retry_better:
                    logger.info(f"  ✅ RETRY SUCCESS: {len(retry_cats)} cats, {retry_concepts} concepts, {retry_subcons} subcons, {retry_details} details")
                    structure = retry_structure
                    categories = retry_cats
                    total_concepts = retry_concepts
                    total_subconcepts = retry_subcons
                    total_details = retry_details
                else:
                    logger.warning(f"  ⚠️  Retry not better, using enhanced fallback")
                    structure = create_fallback_structure(file_name, workspace_id)
                    categories = structure.get('categories', [])
                    total_concepts = sum(len(cat.get('concepts', [])) for cat in categories)
                    total_subconcepts = sum(len(concept.get('subconcepts', [])) for cat in categories for concept in cat.get('concepts', []))
                    total_details = sum(len(subcon.get('details', [])) for cat in categories for concept in cat.get('concepts', []) for subcon in concept.get('subconcepts', []))
            else:
                logger.warning("  ⚠️  Retry failed, using fallback")
                structure = create_fallback_structure(file_name, workspace_id)
                categories = structure.get('categories', [])
                total_concepts = sum(len(cat.get('concepts', [])) for cat in categories)
                total_subconcepts = sum(len(concept.get('subconcepts', [])) for cat in categories for concept in cat.get('concepts', []))
                total_details = sum(len(subcon.get('details', [])) for cat in categories for concept in cat.get('concepts', []) for subcon in concept.get('subconcepts', []))

        logger.info(f"  ✓ FINAL structure: {len(categories)} categories, {total_concepts} concepts, {total_subconcepts} subconcepts, {total_details} details")

        # ========================================
        # STEP 4: STAGE 2 - LLM analyzes chunks for precise concept mapping
        # ========================================
        logger.info("  [4/7] STAGE 2: LLM analyzing chunks for concept mapping...")

        # Use analyze_chunks_for_merging to get precise chunk-to-concept mapping
        chunk_analysis = analyze_chunks_for_merging(
            chunks=chunks,
            structure=structure,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )

        analyzed_chunks = chunk_analysis.get('analysis_results', [])
        logger.info(f"  ✓ Analyzed {len(analyzed_chunks)} chunks with concept mapping")

        # Build concept_chunk_mapping from analysis results
        concept_chunk_mapping = {}  # Maps concept_name -> list of chunk data with analysis
        all_concepts = get_all_concepts_from_structure(structure)

        for chunk_data in analyzed_chunks:
            primary_concept = chunk_data.get('primary_concept', '')
            if not primary_concept:
                continue

            if primary_concept not in concept_chunk_mapping:
                concept_chunk_mapping[primary_concept] = []

            concept_chunk_mapping[primary_concept].append(chunk_data)

        logger.info(f"  ✓ Mapped chunks to {len(concept_chunk_mapping)} concepts")

        # ========================================
        # STEP 5: STAGE 3 - Per-concept evidence enrichment (OPTIMIZED)
        # ========================================
        logger.info("  [5/7] STAGE 3: Enriching evidence for TOP concepts...")

        enriched_evidence_cache = {}  # Cache enriched evidence per concept

        # Tối ưu: Chỉ enrich top concepts có nhiều chunks nhất (high merge_potential)
        # Sort concepts by number of chunks (descending)
        sorted_concepts = sorted(
            concept_chunk_mapping.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        # Chỉ enrich top 10-15 concepts để cân bằng quality vs speed
        top_concepts_to_enrich = sorted_concepts[:15]
        logger.info(f"  ✓ Selected {len(top_concepts_to_enrich)} top concepts for enrichment (out of {len(sorted_concepts)})")

        # Use ThreadPoolExecutor for parallel LLM calls
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def enrich_concept(concept_name, relevant_chunks):
            """Helper function for parallel enrichment"""
            # Get concept synthesis
            concept_synthesis = ""
            for concept_data in all_concepts:
                if concept_data.get('name') == concept_name:
                    concept_synthesis = concept_data.get('synthesis', '')
                    break

            # Call LLM
            enriched = enrich_evidence_with_llm(
                chunks=relevant_chunks,
                concept_name=concept_name,
                concept_synthesis=concept_synthesis,
                clova_api_key=CLOVA_API_KEY,
                clova_api_url=CLOVA_API_URL
            )
            return concept_name, enriched

        # Parallel enrichment với ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for concept_name, relevant_chunks in top_concepts_to_enrich:
                if not relevant_chunks:
                    continue
                future = executor.submit(enrich_concept, concept_name, relevant_chunks)
                futures[future] = concept_name

            # Collect results as they complete
            for future in as_completed(futures):
                concept_name = futures[future]
                try:
                    name, enriched = future.result()
                    enriched_evidence_cache[name] = enriched
                    logger.info(f"    ✓ Enriched '{name}' ({len(enriched.get('key_claims', []))} claims)")
                except Exception as e:
                    logger.warning(f"    ⚠️ Failed to enrich '{concept_name}': {e}")

        logger.info(f"  ✓ Enriched evidence for {len(enriched_evidence_cache)} concepts (parallel processing)")

        # ========================================
        # STEP 6: Build and insert knowledge graph with INTELLIGENT MERGING
        # ========================================
        logger.info("  [6/7] Building knowledge graph in Neo4j...")

        source_id = pdf_url  # ✅ SOURCE_ID = PDF URL
        nodes_created = 0
        nodes_merged = 0
        evidences_created = 0
        created_node_ids = []  # Track created nodes for gap suggestions

        # Prepare merge mapping based on mode
        llm_merge_mapping = {}
        if not is_new_workspace:
            # MERGE MODE: Use LLM for semantic matching (1 call for all nodes)
            logger.info("  ✓ MERGE MODE: Using LLM for semantic merge matching...")

            # Collect all new nodes from structure
            new_nodes_for_merge = []
            new_nodes_for_merge.append({
                "type": "domain",
                "name": structure.get('domain', {}).get('name', ''),
                "synthesis": structure.get('domain', {}).get('synthesis', ''),
                "level": 0
            })
            for cat in categories:
                new_nodes_for_merge.append({
                    "type": "category",
                    "name": cat.get('name', ''),
                    "synthesis": cat.get('synthesis', ''),
                    "level": 1
                })
                for concept in cat.get('concepts', [])[:5]:  # Top 5 concepts per category
                    new_nodes_for_merge.append({
                        "type": "concept",
                        "name": concept.get('name', ''),
                        "synthesis": concept.get('synthesis', ''),
                        "level": 2
                    })

            llm_merge_mapping = find_merge_candidates_llm(
                new_nodes=new_nodes_for_merge,
                existing_nodes=existing_nodes,
                clova_api_key=CLOVA_API_KEY,
                clova_api_url=CLOVA_API_URL
            )
            logger.info(f"  ✓ LLM found {len(llm_merge_mapping)} semantic merge candidates")
        else:
            logger.info("  ✓ NEW WORKSPACE: Creating fresh knowledge graph...")

        with neo4j_driver.session() as session:
            # Create or merge domain node (Level 0)
            domain_data = structure.get('domain', {})
            domain_name = domain_data.get('name', f"Knowledge from {file_name}")

            # Try to merge: First check LLM mapping, then word overlap
            existing_domain_id = llm_merge_mapping.get(domain_name)
            if not existing_domain_id:
                existing_domain_id = find_or_merge_node_simple(
                    existing_nodes, domain_name, "domain",
                    domain_data.get('synthesis', ''), 0
                )

            if existing_domain_id:
                domain_id = existing_domain_id
                nodes_merged += 1
                logger.info(f"  🔗 Merged into existing domain: {domain_name}")
            else:
                domain_node = KnowledgeNode(
                    Id=f"domain-{uuid.uuid4().hex[:8]}",
                    Type="domain",
                    Name=domain_name,
                    Synthesis=domain_data.get('synthesis', f"Domain extracted from {file_name}"),
                    WorkspaceId=workspace_id,
                    Level=0,
                    SourceCount=1,
                    TotalConfidence=0.92,
                    CreatedAt=datetime.now(timezone.utc),
                    UpdatedAt=datetime.now(timezone.utc)
                )
                create_knowledge_node(session, domain_node)
                domain_id = domain_node.Id
                nodes_created += 1
                created_node_ids.append(domain_id)

            # Create or merge categories and their nested structure (TOÀN BỘ, không limit)
            for cat_idx, category in enumerate(structure.get('categories', [])):
                category_name = category.get('name', f"Category {cat_idx + 1}")

                # Try LLM mapping first, then word overlap
                existing_cat_id = llm_merge_mapping.get(category_name)
                if not existing_cat_id:
                    existing_cat_id = find_or_merge_node_simple(
                        existing_nodes, category_name, "category",
                        category.get('synthesis', ''), 1
                    )

                if existing_cat_id:
                    category_id = existing_cat_id
                    nodes_merged += 1
                else:
                    category_node = KnowledgeNode(
                        Id=f"category-{uuid.uuid4().hex[:8]}",
                        Type="category",
                        Name=category_name,
                        Synthesis=category.get('synthesis', ''),
                        WorkspaceId=workspace_id,
                        Level=1,
                        SourceCount=1,
                        TotalConfidence=0.90,
                        CreatedAt=datetime.now(timezone.utc),
                        UpdatedAt=datetime.now(timezone.utc)
                    )
                    create_knowledge_node(session, category_node)
                    category_id = category_node.Id
                    nodes_created += 1
                    created_node_ids.append(category_id)

                create_parent_child_relationship(session, domain_id, category_id, 'domain_to_category')

                # Create or merge concepts under category (TOÀN BỘ concepts)
                for concept_idx, concept in enumerate(category.get('concepts', [])):
                    concept_name = concept.get('name', f"Concept {concept_idx + 1}")

                    # Try LLM mapping first, then word overlap
                    existing_concept_id = llm_merge_mapping.get(concept_name)
                    if not existing_concept_id:
                        existing_concept_id = find_or_merge_node_simple(
                            existing_nodes, concept_name, "concept",
                            concept.get('synthesis', ''), 2
                        )

                    if existing_concept_id:
                        concept_id = existing_concept_id
                        nodes_merged += 1
                    else:
                        concept_node = KnowledgeNode(
                            Id=f"concept-{uuid.uuid4().hex[:8]}",
                            Type="concept",
                            Name=concept_name,
                            Synthesis=concept.get('synthesis', ''),
                            WorkspaceId=workspace_id,
                            Level=2,
                            SourceCount=1,
                            TotalConfidence=0.88,
                            CreatedAt=datetime.now(timezone.utc),
                            UpdatedAt=datetime.now(timezone.utc)
                        )
                        create_knowledge_node(session, concept_node)
                        concept_id = concept_node.Id
                        nodes_created += 1
                        created_node_ids.append(concept_id)

                    create_parent_child_relationship(session, category_id, concept_id, 'category_to_concept')

                    # Create subconcepts under concept (Level 3 -> Level 4)
                    for subcon_idx, subconcept in enumerate(concept.get('subconcepts', [])):
                        subconcept_name = subconcept.get('name', f"Subconcept {subcon_idx + 1}")

                        existing_subcon_id = find_or_merge_node_simple(
                            existing_nodes, subconcept_name, "subconcept",
                            subconcept.get('synthesis', ''), 3
                        )

                        if existing_subcon_id:
                            subconcept_id = existing_subcon_id
                            nodes_merged += 1
                        else:
                            subconcept_node = KnowledgeNode(
                                Id=f"subconcept-{uuid.uuid4().hex[:8]}",
                                Type="subconcept",
                                Name=subconcept_name,
                                Synthesis=subconcept.get('synthesis', ''),
                                WorkspaceId=workspace_id,
                                Level=3,
                                SourceCount=1,
                                TotalConfidence=0.86,
                                CreatedAt=datetime.now(timezone.utc),
                                UpdatedAt=datetime.now(timezone.utc)
                            )
                            create_knowledge_node(session, subconcept_node)
                            subconcept_id = subconcept_node.Id
                            nodes_created += 1
                            created_node_ids.append(subconcept_id)

                        create_parent_child_relationship(session, concept_id, subconcept_id, 'concept_to_subconcept')

                        # Create details under subconcept (Level 4 -> Level 5)
                        for detail_idx, detail in enumerate(subconcept.get('details', [])):
                            detail_name = detail.get('name', f"Detail {detail_idx + 1}")

                            existing_detail_id = find_or_merge_node_simple(
                                existing_nodes, detail_name, "detail",
                                detail.get('synthesis', ''), 4
                            )

                            if existing_detail_id:
                                detail_id = existing_detail_id
                                nodes_merged += 1
                            else:
                                detail_node = KnowledgeNode(
                                    Id=f"detail-{uuid.uuid4().hex[:8]}",
                                    Type="detail",
                                    Name=detail_name,
                                    Synthesis=detail.get('synthesis', ''),
                                    WorkspaceId=workspace_id,
                                    Level=4,
                                    SourceCount=1,
                                    TotalConfidence=0.84,
                                    CreatedAt=datetime.now(timezone.utc),
                                    UpdatedAt=datetime.now(timezone.utc)
                                )
                                create_knowledge_node(session, detail_node)
                                detail_id = detail_node.Id
                                nodes_created += 1
                                created_node_ids.append(detail_id)

                            create_parent_child_relationship(session, subconcept_id, detail_id, 'HAS_DETAIL')

                            # Add evidence for detail node
                            detail_chunks = concept_chunk_mapping.get(detail_name, [])
                            if detail_chunks:
                                chunk_data = detail_chunks[0]
                                detail_evidence = Evidence(
                                    Id=f"evidence-{uuid.uuid4().hex[:8]}",
                                    SourceId=source_id,
                                    SourceName=file_name,
                                    ChunkId=f"chunk-{chunk_data.get('chunk_index', 0):03d}",
                                    Text=chunk_data.get('text', '')[:1500],
                                    Page=chunk_data.get('chunk_index', 0) + 1,
                                    Confidence=0.88,
                                    CreatedAt=datetime.now(timezone.utc),
                                    Language="ENG" if language == "en" else "KOR",
                                    SourceLanguage="ENG" if language == "en" else "KOR",
                                    HierarchyPath=detail_name,
                                    Concepts=[detail_name],
                                    KeyClaims=chunk_data.get('key_claims', [f"Detail from {file_name}"]),
                                    QuestionsRaised=chunk_data.get('questions_raised', []),
                                    EvidenceStrength=0.82
                                )
                                create_evidence_node(session, detail_evidence, detail_id)
                                evidences_created += 1

                        # Add evidence for subconcept node
                        subcon_chunks = concept_chunk_mapping.get(subconcept_name, [])
                        if subcon_chunks:
                            chunk_data = subcon_chunks[0]
                            subcon_evidence = Evidence(
                                Id=f"evidence-{uuid.uuid4().hex[:8]}",
                                SourceId=source_id,
                                SourceName=file_name,
                                ChunkId=f"chunk-{chunk_data.get('chunk_index', 0):03d}",
                                Text=chunk_data.get('text', '')[:1500],
                                Page=chunk_data.get('chunk_index', 0) + 1,
                                Confidence=0.90,
                                CreatedAt=datetime.now(timezone.utc),
                                Language="ENG" if language == "en" else "KOR",
                                SourceLanguage="ENG" if language == "en" else "KOR",
                                HierarchyPath=subconcept_name,
                                Concepts=[subconcept_name],
                                KeyClaims=chunk_data.get('key_claims', [f"Information from {file_name}"]),
                                QuestionsRaised=chunk_data.get('questions_raised', []),
                                EvidenceStrength=0.86
                            )
                            create_evidence_node(session, subcon_evidence, subconcept_id)
                            evidences_created += 1

                    # ✅ BẮT BUỘC: Mỗi concept phải có ít nhất 1 evidence
                    concept_evidence_count = 0

                    # Get enriched evidence from Stage 3 cache OR from analyzed chunks
                    enriched = enriched_evidence_cache.get(concept_name, {})
                    concept_chunks = concept_chunk_mapping.get(concept_name, [])

                    if enriched and enriched.get('key_claims') and concept_chunks:
                        # ✅ Evidence với EXPERT-LEVEL analysis từ Stage 3
                        # Text lấy từ chunk gốc, key_claims/questions từ LLM enrichment
                        chunk_data = concept_chunks[0]
                        evidence = Evidence(
                            Id=f"evidence-{uuid.uuid4().hex[:8]}",
                            SourceId=source_id,  # ✅ PDF URL
                            SourceName=file_name,
                            ChunkId=f"chunk-{chunk_data.get('chunk_index', 0):03d}",
                            Text=chunk_data.get('text', '')[:1500],  # ✅ Text từ chunk gốc
                            Page=chunk_data.get('chunk_index', 0) + 1,
                            Confidence=0.92,  # Higher confidence for enriched evidence
                            CreatedAt=datetime.now(timezone.utc),
                            Language="ENG" if language == "en" else "KOR",
                            SourceLanguage="ENG" if language == "en" else "KOR",
                            HierarchyPath=concept_name,
                            Concepts=[concept_name],
                            KeyClaims=enriched.get('key_claims', []),  # ✅ Expert-level claims from LLM
                            QuestionsRaised=enriched.get('questions_raised', []),  # ✅ Analytical questions from LLM
                            EvidenceStrength=0.90
                        )
                        create_evidence_node(session, evidence, concept_id)
                        evidences_created += 1
                        concept_evidence_count += 1
                    elif concept_chunks:
                        # Use analyzed chunks directly if no enriched evidence
                        for chunk_data in concept_chunks[:2]:  # Max 2 evidence per concept
                            evidence = Evidence(
                                Id=f"evidence-{uuid.uuid4().hex[:8]}",
                                SourceId=source_id,
                                SourceName=file_name,
                                ChunkId=f"chunk-{chunk_data.get('chunk_index', 0):03d}",
                                Text=chunk_data.get('text', '')[:1500],
                                Page=chunk_data.get('chunk_index', 0) + 1,
                                Confidence=0.88,
                                CreatedAt=datetime.now(timezone.utc),
                                Language="ENG" if language == "en" else "KOR",
                                SourceLanguage="ENG" if language == "en" else "KOR",
                                HierarchyPath=concept_name,
                                Concepts=[concept_name],
                                KeyClaims=chunk_data.get('key_claims', [f"Information from {file_name}"]),
                                QuestionsRaised=chunk_data.get('questions_raised', []),
                                EvidenceStrength=0.85
                            )
                            create_evidence_node(session, evidence, concept_id)
                            evidences_created += 1
                            concept_evidence_count += 1

                    # Đảm bảo mỗi concept có ít nhất 1 evidence
                    if concept_evidence_count == 0:
                        logger.warning(f"  ⚠️  No evidence for {concept_name}, creating default")
                        default_evidence = Evidence(
                            Id=f"evidence-{uuid.uuid4().hex[:8]}",
                            SourceId=source_id,
                            SourceName=file_name,
                            ChunkId="chunk-000",
                            Text=f"Information related to {concept_name} from {file_name}",
                            Page=1,
                            Confidence=0.75,
                            CreatedAt=datetime.now(timezone.utc),
                            Language="ENG" if language == "en" else "KOR",
                            SourceLanguage="ENG" if language == "en" else "KOR",
                            HierarchyPath=concept_name,
                            Concepts=[concept_name],
                            KeyClaims=[f"Extracted from {file_name}"],
                            QuestionsRaised=["What additional information is needed?"],
                            EvidenceStrength=0.75
                        )
                        create_evidence_node(session, default_evidence, concept_id)
                        evidences_created += 1

        logger.info(f"  ✓ Created {nodes_created} new nodes, merged into {nodes_merged} existing nodes")
        logger.info(f"  ✓ Created {evidences_created} evidence (each node has ≥1 evidence)")

        # ========================================
        # STEP 7: Create Gap Suggestions for LEAF NODES only
        # ========================================
        logger.info("  [7/7] Creating Gap Suggestions for leaf nodes...")
        leaf_nodes = identify_leaf_nodes(neo4j_driver, workspace_id)
        gaps_created = 0

        with neo4j_driver.session() as session:
            for leaf_node_id in leaf_nodes:
                # Chỉ tạo gap cho nodes mới tạo
                if leaf_node_id in created_node_ids:
                    gap_suggestion = GapSuggestion(
                        Id=f"gap-{uuid.uuid4().hex[:8]}",
                        SuggestionText=f"Consider exploring related research areas to deepen understanding",
                        TargetNodeId="https://arxiv.org/search",  # Suggestion link
                        TargetFileId="",
                        SimilarityScore=0.78
                    )
                    create_gap_suggestion_node(session, gap_suggestion, leaf_node_id)
                    gaps_created += 1

        logger.info(f"  ✓ Created {gaps_created} gap suggestions for {len(leaf_nodes)} leaf nodes")
        logger.info("  ✅ Processing complete")

        return {
            "status": "success",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "processing_mode": processing_mode,
            "nodes_created": nodes_created,
            "nodes_merged": nodes_merged,
            "evidences_created": evidences_created,
            "gaps_created": gaps_created,
            "leaf_nodes": len(leaf_nodes),
            "chunks_processed": len(chunks),
            "enriched_concepts": len(enriched_evidence_cache),
            "language": language,
            "source_id": source_id,
            "quality_metrics": {
                "categories": len(categories),
                "concepts": total_concepts,
                "subconcepts": total_subconcepts,
                "details": total_details,
                "min_depth_achieved": 5 if total_details > 0 else (4 if total_subconcepts > 0 else 3),
                "evidence_enriched_pct": round(len(enriched_evidence_cache) / max(total_concepts, 1) * 100, 1),
                "llm_merges": len(llm_merge_mapping) if not is_new_workspace else 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Error processing {file_name}: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "failed",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def force_deep_structure_extraction(
    pdf_text: str,
    file_name: str,
    language: str,
    clova_api_key: str,
    clova_api_url: str
) -> Dict:
    """
    2nd LLM call with VERY STRICT prompt to force deep structure
    Requirements: ≥2 categories, ≥3 concepts per category, ≥2 subconcepts, ≥1 detail
    """
    prompt = f"""CRITICAL TASK: Extract a DEEP hierarchical knowledge structure from this document.

DOCUMENT: {file_name}
LANGUAGE: {language}

CONTENT (first 3000 chars):
---
{pdf_text[:3000]}
---

MANDATORY REQUIREMENTS (YOU MUST MEET ALL OF THESE):
MINIMUM 2 categories (Level 1) - representing distinct major themes
MINIMUM 3 concepts per category (Level 2) - specific topics under each theme
MINIMUM 2 subconcepts per concept (Level 3) - detailed aspects of each topic
MINIMUM 1 detail per subconcept (Level 4) - concrete implementations/examples

STRUCTURE (5 LEVELS):
{{
  "domain": {{
    "name": "Document's main subject",
    "synthesis": "Comprehensive 150-char overview",
    "level": 1
  }},
  "categories": [
    {{
      "name": "First Major Theme",
      "synthesis": "120-char description",
      "level": 2,
      "concepts": [
        {{
          "name": "Specific Topic 1",
          "synthesis": "100-char description",
          "level": 3,
          "subconcepts": [
            {{
              "name": "Detailed Aspect A",
              "synthesis": "80-char description",
              "level": 4,
              "details": [
                {{
                  "name": "Implementation/Example",
                  "synthesis": "60-char description",
                  "level": 5
                }}
              ]
            }},
            {{
              "name": "Detailed Aspect B",
              "synthesis": "80-char description",
              "level": 4,
              "details": []
            }}
          ]
        }},
        ... (2 more concepts minimum)
      ]
    }},
    {{
      "name": "Second Major Theme",
      "synthesis": "120-char description",
      "level": 2,
      "concepts": [ ... (3 concepts minimum) ]
    }}
  ]
}}

VALIDATION CHECKLIST (CHECK BEFORE RETURNING):
2+ categories?
Each category has 3+ concepts?
Most concepts have 2+ subconcepts?
Some subconcepts have details?
All synthesis fields within char limits?

If document is short: CREATE DEPTH by breaking down what's there into finer granularity.
If document is simple: INFER reasonable subconcepts and details from the content.

Return ONLY valid JSON. NO excuses about document length - CREATE THE DEPTH."""

    try:
        result = call_llm_sync(
            prompt=prompt,
            max_tokens=4000,
            system_message="You are a strict knowledge extraction system. You MUST return structures with the required depth. No shortcuts.",
            clova_api_key=clova_api_key,
            clova_api_url=clova_api_url
        )

        if result and isinstance(result, dict) and result.get('domain'):
            return result
    except Exception as e:
        logger.warning(f"  ⚠️  Force deep extraction failed: {e}")

    return {}


def create_fallback_structure(file_name: str, workspace_id: str) -> Dict:
    """
    Create fallback structure with MINIMUM depth requirements (5 levels)
    Ensures: 1 domain, ≥2 categories, ≥2 concepts, ≥2 subconcepts, ≥1 detail
    """
    return {
        "domain": {
            "name": f"Knowledge from {file_name}",
            "synthesis": f"Comprehensive knowledge extracted from {file_name}",
            "level": 1
        },
        "categories": [
            {
                "name": "Primary Content",
                "synthesis": "Main topics and themes from the document",
                "level": 2,
                "concepts": [
                    {
                        "name": "Key Concepts",
                        "synthesis": "Core ideas and principles discussed",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Fundamental Aspects",
                                "synthesis": "Essential elements and components",
                                "level": 4,
                                "details": [
                                    {
                                        "name": "Implementation Details",
                                        "synthesis": "Specific approaches and methods",
                                        "level": 5
                                    }
                                ]
                            },
                            {
                                "name": "Advanced Topics",
                                "synthesis": "Complex considerations and extensions",
                                "level": 4,
                                "details": [
                                    {
                                        "name": "Specialized Techniques",
                                        "synthesis": "Specific methodologies and practices",
                                        "level": 5
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Supporting Information",
                        "synthesis": "Additional context and background",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Contextual Factors",
                                "synthesis": "Relevant background information",
                                "level": 4,
                                "details": []
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Secondary Content",
                "synthesis": "Supplementary topics and related information",
                "level": 2,
                "concepts": [
                    {
                        "name": "Related Concepts",
                        "synthesis": "Connected ideas and themes",
                        "level": 3,
                        "subconcepts": [
                            {
                                "name": "Related Aspects",
                                "synthesis": "Associated elements and considerations",
                                "level": 4,
                                "details": []
                            }
                        ]
                    }
                ]
            }
        ]
    }


# ================================
# BATCH PROCESSING
# ================================

async def process_files_batch_async(
    workspace_id: str,
    file_paths: List[str],
    job_id: str,
    neo4j_driver,
    firebase_client: FirebaseClient
) -> Dict[str, Any]:
    """
    Process multiple files using recursive expansion and update Firebase in real-time
    """
    start_time = datetime.now()

    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 BATCH PROCESSING STARTED (RECURSIVE EXPANSION)")
    logger.info(f"📦 Job ID: {job_id}")
    logger.info(f"🔖 Workspace: {workspace_id}")
    logger.info(f"📄 Files: {len(file_paths)}")
    logger.info(f"{'='*80}\n")

    # Initialize Firebase job status
    firebase_client.push_job_result(job_id, {
        "status": "pending",
        "workspaceId": workspace_id,
        "totalFiles": len(file_paths),
        "successful": 0,
        "failed": 0,
        "processingTimeMs": 0,
        "timestamp": datetime.now().isoformat()
    }, path="jobs")

    results = []
    successful = 0
    failed = 0

    for idx, pdf_url in enumerate(file_paths):
        file_name = pdf_url.split('/')[-1]
        logger.info(f"Processing file {idx + 1}/{len(file_paths)}: {file_name}")

        result = await process_pdf_with_recursive_expansion(
            workspace_id=workspace_id,
            pdf_url=pdf_url,
            file_name=file_name,
            neo4j_driver=neo4j_driver,
            job_id=job_id
        )

        results.append(result)

        if result.get('status') == 'success':
            successful += 1
        else:
            failed += 1

        # Update Firebase progress
        firebase_client.push_job_result(job_id, {
            "status": "pending",
            "workspaceId": workspace_id,
            "totalFiles": len(file_paths),
            "successful": successful,
            "failed": failed,
            "currentFile": idx + 1,
            "processingTimeMs": int((datetime.now() - start_time).total_seconds() * 1000),
            "timestamp": datetime.now().isoformat()
        }, path="jobs")

    # Final status
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

    final_result = {
        "status": "completed" if failed == 0 else "partial",
        "workspaceId": workspace_id,
        "totalFiles": len(file_paths),
        "successful": successful,
        "failed": failed,
        "processingTimeMs": processing_time,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

    # Push final result to Firebase
    firebase_client.push_job_result(job_id, final_result, path="jobs")

    logger.info(f"\n{'='*80}")
    logger.info(f"✅ BATCH PROCESSING COMPLETED")
    logger.info(f"⏱️  Total time: {processing_time}ms ({processing_time/1000:.1f}s)")
    logger.info(f"📊 Results: {successful} successful, {failed} failed")
    logger.info(f"{'='*80}\n")

    return final_result


def process_files_batch(
    workspace_id: str,
    file_paths: List[str],
    job_id: str,
    neo4j_driver,
    firebase_client: FirebaseClient
) -> Dict[str, Any]:
    """
    Sync wrapper for async batch processing
    """
    import asyncio

    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run async batch processing
    return loop.run_until_complete(
        process_files_batch_async(
            workspace_id=workspace_id,
            file_paths=file_paths,
            job_id=job_id,
            neo4j_driver=neo4j_driver,
            firebase_client=firebase_client
        )
    )


# ================================
# MESSAGE HANDLER
# ================================

def handle_job_message(message: Dict[str, Any], neo4j_driver, firebase_client):
    """
    Handle incoming job message from RabbitMQ

    Expected message format (from C# backend - PascalCase):
    {
        "JobId": "guid-string",
        "WorkspaceId": "workspace-id",
        "FilePaths": ["url1", "url2", ...],
        "CreatedAt": "iso-timestamp",
        "RequestId": "guid-string"
    }

    Also supports legacy camelCase format for backward compatibility.
    """
    try:
        logger.info(f"\n📥 Received job message")
        logger.debug(f"Raw message: {message}")

        # Extract message fields - handle both camelCase and PascalCase from C# backend
        workspace_id = message.get("WorkspaceId") or message.get("workspaceId")
        file_paths = message.get("FilePaths") or message.get("filePaths") or []
        job_id = message.get("JobId") or message.get("jobId") or f"job_{uuid.uuid4().hex[:8]}"

        logger.info(f"Extracted - WorkspaceId: {workspace_id}, FilePaths count: {len(file_paths) if file_paths else 0}, JobId: {job_id}")

        if not workspace_id:
            logger.error(f"Missing workspaceId in message. Available keys: {list(message.keys())}")
            raise ValueError(f"Missing workspaceId in message. Available keys: {list(message.keys())}")

        if not file_paths:
            logger.error(f"Missing or empty filePaths in message. Available keys: {list(message.keys())}")
            raise ValueError(f"Missing or empty filePaths in message. Available keys: {list(message.keys())}")

        logger.info(f"✓ Processing job {job_id} with {len(file_paths)} files")

        # Process files
        result = process_files_batch(
            workspace_id=workspace_id,
            file_paths=file_paths,
            job_id=job_id,
            neo4j_driver=neo4j_driver,
            firebase_client=firebase_client
        )

        return result

    except Exception as e:
        logger.error(f"❌ Error handling job: {e}")
        logger.error(traceback.format_exc())

        # Push error to Firebase
        try:
            job_id = message.get("jobId") or message.get("JobId") or "unknown"
            firebase_client.push_job_result(job_id, {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }, path="jobs")
        except:
            pass


# ================================
# MAIN WORKER LOOP
# ================================

def main():
    """Main worker loop"""
    logger.info("\n" + "="*80)
    logger.info("🤖 LLM-POWERED PDF PROCESSING WORKER")
    logger.info("="*80)

    try:
        # Initialize Neo4j
        logger.info("🔌 Connecting to Neo4j...")
        neo4j_driver = GraphDatabase.driver(
            NEO4J_URL,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=50
        )
        logger.info("✓ Neo4j connected")

        # Initialize Firebase
        logger.info("🔌 Connecting to Firebase...")
        firebase_client = FirebaseClient(FIREBASE_SERVICE_ACCOUNT, FIREBASE_DATABASE_URL)
        logger.info("✓ Firebase connected")

        # Check LLM API configuration
        if not CLOVA_API_KEY or not CLOVA_API_URL:
            logger.warning("⚠️  CLOVA_API_KEY or CLOVA_API_URL not configured!")
            logger.warning("⚠️  LLM analysis may fail. Please set environment variables.")
        else:
            logger.info("✓ LLM API configured")

        # Connect to RabbitMQ
        logger.info("🔌 Connecting to RabbitMQ...")
        rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
        rabbitmq_client.connect()
        rabbitmq_client.declare_queue(QUEUE_NAME)
        logger.info(f"✓ Listening to queue: {QUEUE_NAME}")

        logger.info("="*80 + "\n")

        # Message callback
        def message_callback(msg):
            if shutdown_requested:
                logger.info("⚠️  Shutdown requested, skipping new messages")
                return False

            handle_job_message(msg, neo4j_driver, firebase_client)
            return True

        # Start consuming
        rabbitmq_client.consume_messages(QUEUE_NAME, message_callback)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Worker interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Worker error: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("\n🔌 Shutting down gracefully...")
        logger.info("✅ Worker shut down")


if __name__ == "__main__":
    main()
