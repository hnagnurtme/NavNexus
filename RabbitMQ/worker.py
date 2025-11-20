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
    analyze_chunks_for_merging
)

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

QUEUE_NAME = os.getenv("QUEUE_NAME", "pdf_jobs_queue")

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
# PDF PROCESSING & DATA GENERATION
# ================================

def process_pdf_to_knowledge_graph(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    neo4j_driver,
    job_id: str
) -> Dict[str, Any]:
    """
    Process PDF using REAL LLM analysis and generate knowledge graph matching data2.json structure

    PIPELINE FLOW:
    1. Extract PDF content (text, language, metadata)
    2. Create smart chunks with semantic boundaries
    3. LLM extracts hierarchical structure (domain → categories → concepts → subconcepts → details)
    4. LLM analyzes chunks → maps to concepts with Concepts, KeyClaims, QuestionsRaised
    5. Insert into Neo4j: nodes → relationships → evidence → gap suggestions
    """
    logger.info(f"📄 Processing PDF: {file_name}")

    try:
        # ========================================
        # STEP 1: Extract PDF
        # ========================================
        logger.info("  [1/5] Extracting PDF content...")
        pdf_text, language, metadata = extract_pdf_enhanced(pdf_url, max_pages=25, timeout=30)

        if not pdf_text or len(pdf_text) < 100:
            raise ValueError(f"PDF extraction failed or too short: {len(pdf_text)} chars")

        logger.info(f"  ✓ Extracted {len(pdf_text)} characters")
        logger.info(f"  ✓ Language: {language}")
        logger.info(f"  ✓ Pages: {metadata.get('extracted_pages', 0)}/{metadata.get('total_pages', 0)}")

        # ========================================
        # STEP 2: Create smart chunks
        # ========================================
        logger.info("  [2/5] Creating smart chunks...")
        chunks = create_smart_chunks(pdf_text, chunk_size=2000, overlap=400)
        logger.info(f"  ✓ Created {len(chunks)} chunks")

        # ========================================
        # STEP 3: LLM extracts hierarchical structure
        # ========================================
        logger.info("  [3/5] Extracting hierarchical structure with LLM...")
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

        logger.info(f"  ✓ Extracted structure with {len(structure.get('categories', []))} categories")

        # ========================================
        # STEP 4: LLM analyzes chunks for evidence
        # ========================================
        logger.info("  [4/5] Analyzing chunks with LLM for evidence...")
        chunk_analysis = analyze_chunks_for_merging(
            chunks=chunks,
            structure=structure,
            clova_api_key=CLOVA_API_KEY,
            clova_api_url=CLOVA_API_URL
        )

        analyzed_chunks = chunk_analysis.get('analysis_results', [])
        logger.info(f"  ✓ Analyzed {len(analyzed_chunks)} chunks")

        # ========================================
        # STEP 5: Build and insert knowledge graph into Neo4j
        # ========================================
        logger.info("  [5/5] Building knowledge graph in Neo4j...")

        source_id = f"pdf-{uuid.uuid4().hex[:8]}"
        nodes_created = 0
        evidences_created = 0

        with neo4j_driver.session() as session:
            # Create domain node (Level 0)
            domain_data = structure.get('domain', {})
            domain_node = KnowledgeNode(
                Id=f"domain-{uuid.uuid4().hex[:8]}",
                Type="domain",
                Name=domain_data.get('name', f"Knowledge from {file_name}"),
                Synthesis=domain_data.get('synthesis', f"Domain extracted from {file_name}"),
                WorkspaceId=workspace_id,
                Level=0,
                SourceCount=1,
                TotalConfidence=0.92,
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc)
            )
            create_knowledge_node(session, domain_node)
            nodes_created += 1

            # Create categories and their nested structure
            for cat_idx, category in enumerate(structure.get('categories', [])[:3]):  # Limit to 3 categories
                category_node = KnowledgeNode(
                    Id=f"category-{uuid.uuid4().hex[:8]}",
                    Type="category",
                    Name=category.get('name', f"Category {cat_idx + 1}"),
                    Synthesis=category.get('synthesis', ''),
                    WorkspaceId=workspace_id,
                    Level=1,
                    SourceCount=1,
                    TotalConfidence=0.90,
                    CreatedAt=datetime.now(timezone.utc),
                    UpdatedAt=datetime.now(timezone.utc)
                )
                create_knowledge_node(session, category_node)
                create_parent_child_relationship(session, domain_node.Id, category_node.Id, 'domain_to_category')
                nodes_created += 1

                # Create concepts under category
                for concept_idx, concept in enumerate(category.get('concepts', [])[:3]):  # Limit to 3 concepts
                    concept_node = KnowledgeNode(
                        Id=f"concept-{uuid.uuid4().hex[:8]}",
                        Type="concept",
                        Name=concept.get('name', f"Concept {concept_idx + 1}"),
                        Synthesis=concept.get('synthesis', ''),
                        WorkspaceId=workspace_id,
                        Level=2,
                        SourceCount=1,
                        TotalConfidence=0.88,
                        CreatedAt=datetime.now(timezone.utc),
                        UpdatedAt=datetime.now(timezone.utc)
                    )
                    create_knowledge_node(session, concept_node)
                    create_parent_child_relationship(session, category_node.Id, concept_node.Id, 'category_to_concept')
                    nodes_created += 1

                    # Create evidence for this concept from analyzed chunks
                    concept_name = concept.get('name', '')
                    matching_chunks = [
                        chunk for chunk in analyzed_chunks
                        if chunk.get('primary_concept') == concept_name
                    ][:3]  # Max 3 evidence per concept

                    for chunk_data in matching_chunks:
                        evidence = Evidence(
                            Id=f"evidence-{uuid.uuid4().hex[:8]}",
                            SourceId=source_id,
                            SourceName=file_name,
                            ChunkId=f"chunk-{chunk_data.get('chunk_index', 0):03d}",
                            Text=chunk_data.get('text', '')[:1000],  # Limit text length
                            Page=chunk_data.get('chunk_index', 0) + 1,
                            Confidence=0.9,
                            CreatedAt=datetime.now(timezone.utc),
                            Language="ENG" if language == "en" else "KOR",
                            SourceLanguage="ENG" if language == "en" else "KOR",
                            HierarchyPath=concept_name,
                            Concepts=[concept_name],
                            KeyClaims=chunk_data.get('key_claims', []),
                            QuestionsRaised=[],
                            EvidenceStrength=0.85
                        )
                        create_evidence_node(session, evidence, concept_node.Id)
                        evidences_created += 1

                    # Create gap suggestion for concept
                    gap_suggestion = GapSuggestion(
                        Id=f"gap-{uuid.uuid4().hex[:8]}",
                        SuggestionText=f"Explore deeper research on {concept_name} to enhance understanding",
                        TargetNodeId="",
                        TargetFileId="",
                        SimilarityScore=0.75
                    )
                    create_gap_suggestion_node(session, gap_suggestion, concept_node.Id)

        logger.info(f"  ✓ Created {nodes_created} nodes and {evidences_created} evidence")
        logger.info("  ✓ Processing complete")

        return {
            "status": "completed",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "nodes_created": nodes_created,
            "evidences_created": evidences_created,
            "gaps_created": nodes_created,  # One gap per concept
            "chunks_processed": len(analyzed_chunks),
            "language": language
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


def create_fallback_structure(file_name: str, workspace_id: str) -> Dict:
    """
    Create a simple fallback structure when LLM extraction fails
    """
    return {
        "domain": {
            "name": f"Knowledge from {file_name}",
            "synthesis": f"Document content extracted from {file_name}",
            "level": 1
        },
        "categories": [
            {
                "name": "Main Topics",
                "synthesis": "Primary topics discussed in the document",
                "level": 2,
                "concepts": [
                    {
                        "name": "Core Concepts",
                        "synthesis": "Key concepts and ideas from the document",
                        "level": 3,
                        "subconcepts": []
                    }
                ]
            }
        ]
    }


# ================================
# BATCH PROCESSING
# ================================

def process_files_batch(
    workspace_id: str,
    file_paths: List[str],
    job_id: str,
    neo4j_driver,
    firebase_client: FirebaseClient
) -> Dict[str, Any]:
    """
    Process multiple files and update Firebase in real-time
    """
    start_time = datetime.now()

    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 BATCH PROCESSING STARTED")
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

        result = process_pdf_to_knowledge_graph(
            workspace_id=workspace_id,
            pdf_url=pdf_url,
            file_name=file_name,
            neo4j_driver=neo4j_driver,
            job_id=job_id
        )

        results.append(result)

        if result.get('status') == 'completed':
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


# ================================
# MESSAGE HANDLER
# ================================

def handle_job_message(message: Dict[str, Any], neo4j_driver, firebase_client):
    """
    Handle incoming job message from RabbitMQ
    """
    try:
        logger.info(f"\n📥 Received job message")

        # Extract message fields
        workspace_id = message.get("workspaceId") or message.get("WorkspaceId")
        file_paths = message.get("filePaths") or message.get("FilePaths", [])
        job_id = message.get("jobId") or message.get("JobId") or f"job_{uuid.uuid4().hex[:8]}"

        if not workspace_id or not file_paths:
            raise ValueError("Missing workspaceId or filePaths in message")

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
