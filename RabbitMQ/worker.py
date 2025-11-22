# "PRODUCTION WORKER - LLM-Powered Knowledge Graph Builder (REFINED)
# =================================================================

# This worker processes PDF documents and builds hierarchical knowledge graphs using a streamlined,
# recursive expansion pipeline.

# PIPELINE FLOW:
# 1.  **Extract**: PDF text is extracted and split into paragraphs for position-based analysis.
# 2.  **Initialize**: An LLM call creates the initial top-level "domain" node for the document.
# 3.  **Expand**: A `RecursiveExpander` class recursively explores the document, building a
#     deep, 4-level hierarchy (domain → category → concept → subconcept) with
#     position-based evidence.
# 4.  **Filter & Insert**: Low-quality nodes are filtered out. Valid nodes and their
#     corresponding evidence are inserted into Neo4j.
# 5.  **Suggest Gaps**: For each leaf node in the new structure, an LLM call generates
#     insightful "gap suggestions" to guide further exploration.
# 6.  **Update Status**: Real-time progress is pushed to Firebase.
# "

import os
import sys
import json
import time
import signal
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# RabbitMQ and Firebase clients
from src.rabbitmq_client import RabbitMQClient
from src.handler.firebase import FirebaseClient

# Database connections
from neo4j import GraphDatabase

# PDF processing pipeline
from src.pipeline.pdf_extraction import extract_pdf_enhanced
from src.pipeline.llm_analysis import call_llm_sync, SYSTEM_MESSAGE

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

# LLM API Configuration
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
# NEO4J INSERTION LOGIC
# ================================

def create_knowledge_node(session, knowledge_node: KnowledgeNode) -> str:
    """Creates or updates a KnowledgeNode in Neo4j."""
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
        created_at=knowledge_node.CreatedAt.isoformat(),
        updated_at=knowledge_node.UpdatedAt.isoformat()
    )
    return result.single()[0]


def create_evidence_node(session, evidence: Evidence, node_id: str) -> str:
    """Creates an Evidence node and links it to a KnowledgeNode."""
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
        created_at=evidence.CreatedAt.isoformat(),
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
    """Creates a GapSuggestion node and links it to a KnowledgeNode."""
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
    """Creates a hierarchical relationship between two KnowledgeNodes."""
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
    """Determines the relationship type based on node levels."""
    if parent_level == 0 and child_level == 1:
        return 'domain_to_category'
    elif parent_level == 1 and child_level == 2:
        return 'category_to_concept'
    elif parent_level == 2 and child_level == 3:
        return 'concept_to_subconcept'
    else:
        return 'HAS_SUBCATEGORY'


# ================================
# PROMPTS
# ================================

GAP_SUGGESTION_BATCH_PROMPT = """You are an expert research advisor identifying knowledge gaps and suggesting specific research directions.

DOCUMENT CONTEXT:
- Source: {file_name}
- Domain: {domain_name}
- Language: {language}

LEAF NODES (concepts needing expansion):
{nodes_context}

TASK: For EACH leaf node above, generate exactly 1 SMART gap suggestion that:
1. Identifies what's MISSING or UNEXPLORED in this specific concept
2. Suggests a SPECIFIC research question or investigation direction
3. Provides a REALISTIC target resource URL (arxiv.org, scholar.google.com, or specific database)

OUTPUT FORMAT (strict JSON):
{{
  "suggestions": [
    {{
      "node_id": "node-id-from-input",
      "node_name": "Node Name",
      "suggestion_text": "Specific gap or research question (50-100 chars)",
      "target_url": "https://arxiv.org/search/?query=relevant+search+terms",
      "similarity_score": 0.85
    }}
  ]
}}

REQUIREMENTS:
✓ Generate exactly ONE suggestion per input node
✓ Suggestion text must be SPECIFIC and ACTIONABLE (not generic "learn more about X")
✓ Must EXTEND knowledge beyond what's in the document
✓ Target URLs must be realistic search queries or known resources
✓ Similarity score (0.70-0.95) reflects how relevant the suggestion is to the node
✓ Higher scores (0.85+) for directly related topics, lower (0.70-0.80) for tangential explorations

Return ONLY the JSON object with suggestions array."""


# ================================
# HELPER FUNCTIONS
# ================================

def extract_paragraphs_from_pdf(pdf_text: str) -> List[str]:
    """Converts PDF text into a list of paragraphs."""
    return split_text_to_paragraphs(pdf_text)


async def async_llm_caller(prompt: str, system_message: str, max_tokens: int = 2000) -> Dict:
    """Async wrapper for synchronous LLM calls."""
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


def identify_leaf_nodes(neo4j_driver, workspace_id: str) -> List[Dict]:
    """
    Finds all leaf nodes and returns their data for generating gap suggestions.
    A leaf node is one with no outgoing hierarchical relationships.
    """
    logger.info(f"  🔎 Identifying leaf nodes for workspace: {workspace_id}")
    try:
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
                WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
                OPTIONAL MATCH (p:KnowledgeNode)-[]->(n)
                RETURN n.id as id, n.name as name, n.synthesis as synthesis, p.name as parent_name
                """,
                workspace_id=workspace_id
            )
            # Use a dictionary to ensure unique nodes by ID, as a node might have multiple parents
            nodes = {}
            for record in result:
                if record["id"] not in nodes:
                    nodes[record["id"]] = {
                        "id": record["id"],
                        "name": record["name"],
                        "synthesis": record["synthesis"],
                        "parent_name": record["parent_name"]
                    }
            
            leaf_node_list = list(nodes.values())
            logger.info(f"  ✓ Found {len(leaf_node_list)} unique leaf nodes.")
            return leaf_node_list
    except Exception as e:
        logger.warning(f"⚠️  Could not identify leaf nodes: {e}")
        return []


async def generate_gap_suggestions_batch(
    leaf_nodes: List[Dict],
    file_name: str,
    domain_name: str,
    language: str,
    batch_size: int = 5
) -> Dict[str, Dict]:
    """
    Generate gap suggestions for multiple leaf nodes in BATCHES using LLM.

    Args:
        leaf_nodes: List of dicts with 'id', 'name', 'synthesis', 'parent_name'
        file_name: Source document name
        domain_name: Domain/topic of the document
        language: Document language
        batch_size: Number of nodes to process per LLM call (default 5)

    Returns:
        Dict mapping node_id -> {suggestion_text, target_url, similarity_score}
    """
    if not leaf_nodes:
        return {}

    logger.info(f"  🤖 Generating gap suggestions for {len(leaf_nodes)} leaf nodes (batch_size={batch_size})...")

    gap_suggestions = {}
    total_batches = (len(leaf_nodes) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(leaf_nodes), batch_size):
        batch = leaf_nodes[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1

        logger.info(f"    Processing batch {batch_num}/{total_batches} ({len(batch)} nodes)...")

        # Prepare nodes context for this batch
        nodes_context = "\n".join([
            f"[{i+1}] ID: {node['id']}, Name: {node['name']}, Synthesis: {node.get('synthesis', 'N/A')[:100]}, Parent: {node.get('parent_name', 'N/A')}"
            for i, node in enumerate(batch)
        ])

        prompt = GAP_SUGGESTION_BATCH_PROMPT.format(
            file_name=file_name,
            domain_name=domain_name,
            language=language,
            nodes_context=nodes_context
        )

        try:
            result = await async_llm_caller(
                prompt=prompt,
                system_message="You are an expert research advisor identifying knowledge gaps and research directions.",
                max_tokens=1000
            )

            if result and isinstance(result, dict) and 'suggestions' in result:
                suggestions = result['suggestions']
                logger.info(f"      ✓ LLM generated {len(suggestions)} gap suggestions")

                for suggestion in suggestions:
                    node_id = suggestion.get('node_id')
                    if node_id:
                        gap_suggestions[node_id] = {
                            'suggestion_text': suggestion.get('suggestion_text', ''),
                            'target_url': suggestion.get('target_url', 'https://arxiv.org/search'),
                            'similarity_score': suggestion.get('similarity_score', 0.75)
                        }
            else:
                logger.warning(f"      ⚠️  LLM response invalid for batch {batch_num}, using fallback")
                # Fallback for this batch
                for node in batch:
                    gap_suggestions[node['id']] = {
                        'suggestion_text': f"Explore advanced topics and applications of {node['name']}",
                        'target_url': f"https://scholar.google.com/scholar?q={node['name'].replace(' ', '+')}",
                        'similarity_score': 0.70
                    }

        except Exception as e:
            logger.warning(f"      ⚠️  LLM batch {batch_num} failed: {e}, using fallback")
            # Fallback for failed batch
            for node in batch:
                gap_suggestions[node['id']] = {
                    'suggestion_text': f"Explore advanced topics and applications of {node['name']}",
                    'target_url': f"https://scholar.google.com/scholar?q={node['name'].replace(' ', '+')}",
                    'similarity_score': 0.70
                }

    logger.info(f"  ✓ Generated {len(gap_suggestions)} gap suggestions across {total_batches} batches")
    return gap_suggestions


# ================================
# RECURSIVE EXPANSION PIPELINE
# ================================

async def run_recursive_expansion_pipeline(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    neo4j_driver,
    job_id: str
) -> Dict[str, Any]:
    """
    Processes a single PDF using the streamlined recursive expansion pipeline.
    """
    logger.info(f"📄 Processing PDF with Recursive Expansion: {file_name}")
    start_time = time.time()

    try:
        # STEP 1: Extract PDF and create paragraph array
        logger.info("  [1/5] Extracting PDF content...")
        pdf_text, language, metadata = extract_pdf_enhanced(pdf_url, max_pages=25, timeout=30)
        if not pdf_text or len(pdf_text) < 100:
            raise ValueError(f"PDF extraction failed or text is too short ({len(pdf_text)} chars)")
        paragraphs = extract_paragraphs_from_pdf(pdf_text)
        logger.info(f"  ✓ Extracted {len(pdf_text)} chars into {len(paragraphs)} paragraphs.")

        # STEP 2: Create initial domain node via LLM
        logger.info("  [2/5] Creating initial domain node...")
        domain_prompt = f"""Extract the MAIN DOMAIN from this document.

DOCUMENT: {file_name}
CONTENT (first 3000 chars):
---
{pdf_text[:3000]}
---

TASK: Create the root domain node.
OUTPUT (strict JSON):
{{
  "domain": {{
    "name": "Document's main subject (concise, 3-7 words)",
    "synthesis": "Comprehensive 120-150 char overview of the entire document",
    "evidence_positions": [[0, {min(10, len(paragraphs)-1)}]],
    "key_claims_positions": [],
    "questions_positions": []
  }}
}} """
        domain_result = await async_llm_caller(
            prompt=domain_prompt,
            system_message="You are an expert at identifying document domains.",
            max_tokens=1000
        )
        if not domain_result or not domain_result.get('domain'):
            raise ValueError("LLM domain extraction failed.")
        
        domain_data = domain_result['domain']
        root_node = NodeData(
            id=f"domain-{uuid.uuid4().hex[:8]}",
            name=domain_data.get('name', file_name),
            synthesis=domain_data.get('synthesis', ''),
            level=0, type='domain',
            evidence_positions=domain_data.get('evidence_positions', []),
            key_claims_positions=domain_data.get('key_claims_positions', []),
            questions_positions=domain_data.get('questions_positions', [])
        )
        logger.info(f"  ✓ Created domain node: '{root_node.name}'")

        # STEP 3: Recursive expansion
        logger.info("  [3/5] Starting recursive expansion...")
        expander = RecursiveExpander(
            paragraphs=paragraphs,
            llm_caller=async_llm_caller,
            max_depth=2,  # 0:domain, 1:category, 2:concept (3 levels total)
            children_per_level=2,  # Each node has 2 children: 1 + 2 + 4 + 8 = 15 nodes
            min_content_length=800
        )
        await expander.expand_node_recursively(node=root_node, current_depth=0, target_depth=2)
        stats = expander.get_stats()
        logger.info(f"  ✓ Recursive expansion complete. Total nodes: {stats['total_nodes'] + 1}, LLM calls: {stats['llm_calls'] + 1}")

        # STEP 4: Filter and Insert into Neo4j
        logger.info("  [4/5] Filtering nodes and inserting into Neo4j...")
        source_id = pdf_url  # ✅ SOURCE_ID = PDF URL
        nodes_created, evidences_created = 0, 0
        all_nodes = expander.get_all_nodes_flat(root_node)
        
        # Simple quality filter
        filtered_nodes = [n for n in all_nodes if n.name and len(n.synthesis) > 20]
        logger.info(f"  ✓ Quality filter: {len(filtered_nodes)}/{len(all_nodes)} nodes passed.")

        if not filtered_nodes:
            raise ValueError("All nodes were filtered out due to low quality.")

        with neo4j_driver.session() as session:
            for node in filtered_nodes:
                knode = KnowledgeNode(
                    Id=node.id, Type=node.type, Name=node.name, Synthesis=node.synthesis,
                    WorkspaceId=workspace_id, Level=node.level, SourceCount=1,
                    TotalConfidence=0.9 - (node.level * 0.03),
                    CreatedAt=node.created_at, UpdatedAt=node.created_at
                )
                create_knowledge_node(session, knode)
                nodes_created += 1

                if node.parent_id:
                    rel_type = determine_relationship_type(node.level - 1, node.level)
                    create_parent_child_relationship(session, node.parent_id, node.id, rel_type)

                if node.evidence_content:
                    for item in node.evidence_content[:2]: # Limit evidence per node
                        evidence = Evidence(
                            Id=f"evidence-{uuid.uuid4().hex[:8]}", SourceId=source_id, SourceName=file_name,
                            ChunkId=f"para-{item.get('position_range', [0,0])[0]:04d}",
                            Text=item.get('text', '')[:1500],
                            Page=item.get('position_range', [0,0])[0] // 10 + 1, # Approximate page
                            Confidence=0.88 - (node.level * 0.03),
                            CreatedAt=node.created_at,
                            Language="ENG" if language == "en" else "KOR",
                            SourceLanguage="ENG" if language == "en" else "KOR",
                            HierarchyPath=node.name,
                            Concepts=[node.name],
                            KeyClaims=[c.get('text', '') for c in node.key_claims_content[:3] if isinstance(c, dict)],
                            QuestionsRaised=[q.get('text', '') for q in node.questions_content[:2] if isinstance(q, dict)],
                            EvidenceStrength=0.85 - (node.level * 0.03)
                        )
                        create_evidence_node(session, evidence, node.id)
                        evidences_created += 1
        
        logger.info(f"  ✓ Created {nodes_created} nodes and {evidences_created} evidences.")

        # STEP 5: Create Gap Suggestions for leaf nodes with BATCH LLM calls
        logger.info("  [5/5] Creating LLM-powered Gap Suggestions for leaf nodes...")
        leaf_nodes_data = identify_leaf_nodes(neo4j_driver, workspace_id)
        gaps_created = 0

        if not leaf_nodes_data:
            logger.info("  ✓ No leaf nodes found to create gap suggestions.")
        else:
            # Generate gap suggestions in BATCHES (5 nodes per LLM call)
            gap_suggestions_map = await generate_gap_suggestions_batch(
                leaf_nodes=leaf_nodes_data,
                file_name=file_name,
                domain_name=root_node.name,  # Use domain from root_node
                language=language,
                batch_size=5
            )

            # Insert gap suggestions into Neo4j
            with neo4j_driver.session() as session:
                for node_id, gap_data in gap_suggestions_map.items():
                    gap = GapSuggestion(
                        Id=f"gap-{uuid.uuid4().hex[:8]}",
                        SuggestionText=gap_data['suggestion_text'],
                        TargetNodeId=gap_data['target_url'],  # Target URL for research
                        TargetFileId=source_id,
                        SimilarityScore=gap_data['similarity_score']
                    )
                    create_gap_suggestion_node(session, gap, node_id)
                    gaps_created += 1

        # Calculate total LLM calls
        gap_batch_calls = (len(leaf_nodes_data) + 4) // 5 if leaf_nodes_data else 0  # Ceiling division by batch_size=5
        total_llm_calls = stats['llm_calls'] + 1 + gap_batch_calls  # recursive + domain + gap batches

        logger.info(f"  ✓ Created {gaps_created} LLM-powered gap suggestions (batch mode).")
        logger.info(f"  📊 Total LLM calls: {total_llm_calls} (domain=1, recursive={stats['llm_calls']}, gap_batches={gap_batch_calls})")
        logger.info(f"  ✅ Processing complete in {time.time() - start_time:.2f}s")

        return {
            "status": "success", "file_name": file_name, "pdf_url": pdf_url,
            "processing_mode": "RECURSIVE_EXPANSION_OPTIMIZED",
            "nodes_created": nodes_created, "evidences_created": evidences_created,
            "gaps_created": gaps_created, "language": language,
            "quality_metrics": {
                "total_nodes": stats['total_nodes'] + 1,
                "llm_calls": total_llm_calls,
                "llm_calls_breakdown": {
                    "domain_extraction": 1,
                    "recursive_expansion": stats['llm_calls'],
                    "gap_suggestions": gap_batch_calls
                },
                "max_depth_achieved": max(n.level for n in all_nodes) if all_nodes else 0,
                "leaf_nodes": len(leaf_nodes_data) if leaf_nodes_data else 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Error processing {file_name}: {e}")
        logger.error(traceback.format_exc())
        return {"status": "failed", "file_name": file_name, "error": str(e)}


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
    Processes multiple files using the recursive expansion pipeline and updates Firebase.
    """
    start_time = datetime.now()
    logger.info(f"\n{'='*80}\n🚀 BATCH PROCESSING STARTED (RECURSIVE V2)\n" \
                f"📦 Job ID: {job_id}\n🔖 Workspace: {workspace_id}\n📄 Files: {len(file_paths)}\n{'='*80}\n")

    firebase_client.push_job_result(job_id, {
        "status": "pending", "workspaceId": workspace_id, "totalFiles": len(file_paths),
        "successful": 0, "failed": 0, "timestamp": datetime.now().isoformat()
    }, path="jobs")

    results, successful, failed = [], 0, 0

    for idx, pdf_url in enumerate(file_paths):
        file_name = pdf_url.split('/')[-1]
        logger.info(f"Processing file {idx + 1}/{len(file_paths)}: {file_name}")

        result = await run_recursive_expansion_pipeline(
            workspace_id=workspace_id, pdf_url=pdf_url, file_name=file_name,
            neo4j_driver=neo4j_driver, job_id=job_id
        )
        results.append(result)

        if result.get('status') == 'success':
            successful += 1
        else:
            failed += 1

        firebase_client.push_job_result(job_id, {
            "status": "pending", "successful": successful, "failed": failed,
            "currentFile": idx + 1,
            "processingTimeMs": int((datetime.now() - start_time).total_seconds() * 1000)
        }, path=f"jobs/{job_id}")

    processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    final_status = "completed" if failed == 0 else "partial"
    final_result = {
        "status": final_status, "workspaceId": workspace_id, "totalFiles": len(file_paths),
        "successful": successful, "failed": failed, "processingTimeMs": processing_time_ms,
        "results": results, "timestamp": datetime.now().isoformat()
    }

    firebase_client.push_job_result(job_id, final_result, path="jobs")
    logger.info(f"\n{'='*80}\n✅ BATCH PROCESSING {final_status.upper()}\n" 
                f"⏱️  Total time: {processing_time_ms/1000:.2f}s\n" 
                f"📊 Results: {successful} successful, {failed} failed\n{'='*80}\n")
    return final_result


def process_files_batch(
    workspace_id: str,
    file_paths: List[str],
    job_id: str,
    neo4j_driver,
    firebase_client: FirebaseClient
) -> Dict[str, Any]:
    """Sync wrapper for async batch processing."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        process_files_batch_async(
            workspace_id=workspace_id, file_paths=file_paths, job_id=job_id,
            neo4j_driver=neo4j_driver, firebase_client=firebase_client
        )
    )


# ================================
# MESSAGE HANDLER
# ================================

def handle_job_message(message: Dict[str, Any], neo4j_driver, firebase_client):
    """Handles an incoming job message from RabbitMQ."""
    try:
        logger.info(f"\n📥 Received job message")
        logger.debug(f"Raw message: {message}")

        workspace_id = message.get("WorkspaceId") or message.get("workspaceId")
        file_paths = message.get("FilePaths") or message.get("filePaths") or []
        job_id = message.get("JobId") or message.get("jobId") or f"job_{uuid.uuid4().hex[:8]}"

        if not all([workspace_id, file_paths, job_id]):
            logger.error(f"❌ Invalid message: missing workspaceId, filePaths, or jobId. Keys: {list(message.keys())}")
            return

        logger.info(f"Extracted - JobId: {job_id}, WorkspaceId: {workspace_id}, Files: {len(file_paths)}")
        
        process_files_batch(
            workspace_id=workspace_id,
            file_paths=file_paths,
            job_id=job_id,
            neo4j_driver=neo4j_driver,
            firebase_client=firebase_client
        )

    except Exception as e:
        logger.error(f"❌ Unhandled error in handle_job_message: {e}")
        logger.error(traceback.format_exc())


# ================================
# MAIN WORKER LOOP
# ================================

def main():
    """Initializes clients and starts the main worker loop."""
    global shutdown_requested
    try:
        rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
        rabbitmq_client.connect()
        rabbitmq_client.declare_queue(QUEUE_NAME)

        neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        firebase_client = FirebaseClient(FIREBASE_SERVICE_ACCOUNT, FIREBASE_DATABASE_URL)
    except Exception as e:
        logger.critical(f"❌ Failed to initialize clients: {e}", exc_info=True)
        return

    logger.info("✅ Worker initialized successfully. Waiting for messages...")

    # Define callback for message consumption
    def message_callback(message):
        handle_job_message(message, neo4j_driver, firebase_client)

    try:
        # Start consuming messages
        rabbitmq_client.consume_messages(QUEUE_NAME, message_callback)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"❌ An error occurred in the main loop: {e}", exc_info=True)

    logger.info("Shutting down worker...")
    rabbitmq_client.close()
    neo4j_driver.close()
    logger.info("✅ Worker shut down gracefully.")


if __name__ == "__main__":
    main()