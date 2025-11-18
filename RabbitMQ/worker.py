"""
RabbitMQ Worker for processing PDF jobs - ULTRA-OPTIMIZED VERSION
Listens to queue "pdf_jobs_queue" and processes PDF documents through the pipeline

OPTIMIZATIONS:
- Pre-compute ALL embeddings in batch (Phase 3)
- Cascading deduplication during graph creation (Phase 4)
- Ultra-compact chunk processing with fixed context (Phase 5)
- Reuse embeddings from cache (Phase 6)
- Resource discovery with HyperCLOVA X web search (Phase 7)
"""
import os
import sys
import json
import uuid
import gc
import traceback
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rabbitmq_client import RabbitMQClient
from src.handler.firebase import FirebaseClient

# Pipeline modules - OPTIMIZED
from src.pipeline.pdf_extraction import extract_pdf_fast
from src.pipeline.chunking import create_smart_chunks
from src.pipeline.embedding import create_embedding_via_clova, calculate_similarity
from src.pipeline.translation import translate_batch, translate_structure, translate_chunk_analysis

# OPTIMIZED MODULES
from src.pipeline.embedding_cache import extract_all_concept_names, batch_create_embeddings
from src.pipeline.llm_analysis_optimized import extract_hierarchical_structure_compact, process_chunks_ultra_compact
from src.pipeline.neo4j_graph_optimized import create_hierarchical_graph_with_cascading_dedup
from src.pipeline.qdrant_storage_optimized import store_chunks_in_qdrant
from src.pipeline.resource_discovery import discover_resources_with_hyperclova

# Legacy modules for evidence handling
from src.pipeline.neo4j_graph import find_or_merge_node, add_evidence_to_node, now_iso

from src.model.Evidence import Evidence
from src.model.QdrantChunk import QdrantChunk

# External dependencies
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# ================================
# CONFIGURATION
# ================================
RABBITMQ_CONFIG = {
    "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
    "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
    "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
    "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
}

QUEUE_NAME = "pdf_jobs_queue"

# API Keys
PAPAGO_CLIENT_ID = os.getenv("PAPAGO_CLIENT_ID", "n655pea42q")
PAPAGO_CLIENT_SECRET = os.getenv("PAPAGO_CLIENT_SECRET", "ohkwEANXTPA7yfI8TGZ7KfiR4bNLbJmqIc6l2MUJ")
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-9063a257def64d469cfe961cb502988e5RNo")

# Database URLs
QDRANT_URL = os.getenv("QDRANT_URL", "https://4d5d9646-deff-46bb-82c5-1322542a487e.eu-west-2-0.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY4MjE5NzE1fQ.A-Ma6ZzfzR1EYnf3_YuUWPhXmAU-xJU2ZA-OL6oECJw")

NEO4J_URL = os.getenv("NEO4J_URL", "neo4j+ssc://daa013e6.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY")

# Firebase
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "https://navnexus-default-rtdb.firebaseio.com/")

# CLOVA
CLOVA_MODEL = "HCX-005"
CLOVA_API_URL = f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{CLOVA_MODEL}"
CLOVA_EMBEDDING_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/clir-emb-dolphin"

# Pipeline settings
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "12"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
OVERLAP = int(os.getenv("OVERLAP", "400"))

# ================================
# INITIALIZE CLIENTS
# ================================
print("🔧 Initializing clients...")

# Check for Firebase service account key
if not os.path.exists(FIREBASE_SERVICE_ACCOUNT):
    print("="*80)
    print("🔥 Firebase Service Account Key Not Found!")
    print(f"Error: The file '{FIREBASE_SERVICE_ACCOUNT}' was not found.")
    print("Please ensure that your 'serviceAccountKey.json' is placed in the root directory")
    print("of the RabbitMQ project, or set the 'FIREBASE_SERVICE_ACCOUNT' environment")
    print("variable to the correct path.")
    print("You can obtain this file from your Firebase project settings.")
    print("="*80)
    sys.exit(1)

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
firebase_client = FirebaseClient(FIREBASE_SERVICE_ACCOUNT, FIREBASE_DATABASE_URL)

print("✓ Connected to Qdrant, Neo4j & Firebase")


# ================================
# MAIN PROCESSING FUNCTION - OPTIMIZED
# ================================
def process_pdf_job_optimized(workspace_id: str, pdf_url: str, file_name: str, job_id: str) -> Dict[str, Any]:
    """
    Process a single PDF through the ULTRA-OPTIMIZED pipeline
    
    OPTIMIZATIONS APPLIED:
    1. Batch embedding creation (Phase 3)
    2. Cascading deduplication (Phase 4)
    3. Ultra-compact chunk processing (Phase 5)
    4. Embedding reuse (Phase 6)
    5. Resource discovery with web search (Phase 7)
    """
    start_time = datetime.now()
    file_id = str(uuid.uuid4())
    
    print(f"\n{'='*80}")
    print(f"🚀 PROCESSING PDF JOB - ULTRA-OPTIMIZED PIPELINE")
    print(f"📄 File: {file_name}")
    print(f"🔖 Workspace: {workspace_id}")
    print(f"🆔 Job ID: {job_id}")
    print(f"{'='*80}\n")
    
    # Optimization metrics
    metrics = {
        'embedding_calls': 0,
        'llm_calls': 0,
        'nodes_created': 0,
        'nodes_merged': 0,
        'chunks_processed': 0
    }
    
    try:
        # PHASE 1: Extract PDF
        print(f"📄 Phase 1: Extracting PDF")
        full_text, lang = extract_pdf_fast(pdf_url, max_pages=25)
        print(f"✓ Extracted {len(full_text)} chars, language: {lang}")
        
        # PHASE 2: Extract hierarchical structure (COMPACT - 100 char synthesis)
        # OPTIMIZATION: LLM processes in NATIVE LANGUAGE for better semantic understanding
        print(f"\n📊 Phase 2: Extracting COMPACT hierarchical structure (in {lang})")
        structure = extract_hierarchical_structure_compact(
            full_text, file_name, lang, 
            CLOVA_API_KEY, CLOVA_API_URL
        )
        metrics['llm_calls'] += 1
        
        if not structure or not structure.get('domain'):
            print(f"⚠️  No structure extracted, using fallback")
            structure = {
                'domain': {'name': file_name, 'synthesis': 'Document analysis'},
                'categories': []
            }
        
        # Translate structure to English if needed
        # OPTIMIZATION: Translate ONLY the output, not the input
        if lang != "en":
            print(f"🌐 Translating structure from {lang} to English...")
            structure = translate_structure(
                structure, lang, "en", 
                PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET
            )
            print(f"✓ Structure translated to English")
        
        # PHASE 3: Pre-compute & Cache ALL Embeddings (NEW!)
        print(f"\n⚡ Phase 3: Pre-computing embeddings cache (OPTIMIZATION)")
        concept_names = extract_all_concept_names(structure)
        print(f"  📊 Extracted {len(concept_names)} unique concept names")
        
        embeddings_cache = batch_create_embeddings(
            concept_names,
            CLOVA_API_KEY,
            CLOVA_EMBEDDING_URL,
            batch_size=50
        )
        metrics['embedding_calls'] += len(embeddings_cache)
        print(f"✓ Created embeddings cache with {len(embeddings_cache)} vectors")
        
        # PHASE 4: Create Neo4j graph with CASCADING DEDUPLICATION (NEW!)
        print(f"\n🔗 Phase 4: Creating graph with CASCADING deduplication (OPTIMIZATION)")
        with neo4j_driver.session() as session:
            dedup_stats = create_hierarchical_graph_with_cascading_dedup(
                session, workspace_id, structure, file_id, file_name,
                embeddings_cache
            )
            
            metrics['nodes_created'] = dedup_stats['nodes_created']
            metrics['nodes_merged'] = dedup_stats.get('exact_matches', 0) + dedup_stats.get('high_similarity_merges', 0)
            
            print(f"\n  📊 Deduplication Statistics:")
            print(f"     • Nodes created: {dedup_stats['nodes_created']}")
            print(f"     • Exact matches: {dedup_stats.get('exact_matches', 0)}")
            print(f"     • High similarity merges: {dedup_stats.get('high_similarity_merges', 0)}")
            print(f"     • Final count: {dedup_stats['final_count']}")
            
            node_ids = dedup_stats['node_ids']
        
        # PHASE 5: Process chunks (ULTRA-COMPACT - fixed 3-concept context, 10-chunk batches) (NEW!)
        # OPTIMIZATION: Process in NATIVE LANGUAGE then translate results
        chunks = create_smart_chunks(full_text, CHUNK_SIZE, OVERLAP)[:MAX_CHUNKS]
        print(f"\n⚡ Phase 5: Processing {len(chunks)} chunks in {lang} (ULTRA-COMPACT OPTIMIZATION)")
        
        chunk_analyses = process_chunks_ultra_compact(
            chunks, structure,
            CLOVA_API_KEY, CLOVA_API_URL,
            lang  # Pass language for native processing
        )
        metrics['llm_calls'] += (len(chunks) + 9) // 10  # Batch of 10
        metrics['chunks_processed'] = len(chunk_analyses)
        
        print(f"✓ Processed {len(chunk_analyses)} chunks in {(len(chunks) + 9) // 10} LLM calls")
        
        # Translate chunk analyses to English if needed
        if lang != "en":
            print(f"🌐 Translating chunk analyses from {lang} to English...")
            for i, chunk_data in enumerate(chunk_analyses):
                chunk_analyses[i] = translate_chunk_analysis(
                    chunk_data, lang, "en",
                    PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET
                )
            print(f"✓ Translated {len(chunk_analyses)} chunk analyses")
        
        # PHASE 6: Create Qdrant chunks (REUSE embeddings from cache) (OPTIMIZED!)
        print(f"\n💾 Phase 6: Creating Qdrant chunks (REUSING cached embeddings)")
        all_chunks = []
        prev_embedding = None
        prev_chunk_id = ""
        
        for chunk_data in chunk_analyses:
            chunk_idx = chunk_data.get('chunk_index', 0)
            if chunk_idx >= len(chunks):
                continue
            
            original_chunk = chunks[chunk_idx]
            chunk_id = str(uuid.uuid4())
            
            summary = chunk_data.get('summary', '')
            concepts = chunk_data.get('concepts', [])
            topic = chunk_data.get('topic', 'General')
            claims = chunk_data.get('key_claims', [])
            
            # OPTIMIZATION: Reuse embedding from cache if summary matches a concept
            # Otherwise create new embedding
            embedding = None
            for concept in concepts:
                if concept in embeddings_cache:
                    embedding = embeddings_cache[concept]
                    break
            
            if not embedding:
                # Create embedding for summary
                embedding = create_embedding_via_clova(summary, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
                metrics['embedding_calls'] += 1
            
            # Calculate similarity with previous chunk
            semantic_sim = 0.0
            if prev_embedding:
                semantic_sim = calculate_similarity(prev_embedding, embedding)
            
            # Create Qdrant chunk
            qdrant_chunk = QdrantChunk(
                chunk_id=chunk_id,
                paper_id=file_id,
                page=chunk_idx + 1,
                text=original_chunk["text"][:500],
                summary=summary,
                concepts=concepts,
                topic=topic,
                workspace_id=workspace_id,
                language="en",
                source_language=lang,
                created_at=now_iso(),
                hierarchy_path=f"{file_name} > Chunk {chunk_idx+1}",
                chunk_index=chunk_idx,
                prev_chunk_id=prev_chunk_id,
                next_chunk_id="",
                semantic_similarity_prev=semantic_sim,
                overlap_with_prev=original_chunk.get("overlap_previous", "")[:200],
                key_claims=claims,
                questions_raised=[],
                evidence_strength=0.8
            )
            
            all_chunks.append((qdrant_chunk, embedding))
            
            # Update previous chunk's next_chunk_id
            if prev_chunk_id:
                for i, (c, e) in enumerate(all_chunks):
                    if c.chunk_id == prev_chunk_id:
                        c.next_chunk_id = chunk_id
                        break
            
            prev_chunk_id = chunk_id
            prev_embedding = embedding
        
        # Store in Qdrant
        store_chunks_in_qdrant(qdrant_client, workspace_id, all_chunks)
        
        # PHASE 7: Resource Discovery with HyperCLOVA X Web Search (NEW!)
        print(f"\n🔍 Phase 7: Discovering academic resources (OPTIMIZATION)")
        with neo4j_driver.session() as session:
            resource_count = discover_resources_with_hyperclova(
                session, workspace_id,
                CLOVA_API_KEY, CLOVA_API_URL
            )
        
        metrics['llm_calls'] += 1  # Resource discovery call
        
        # Clean up
        gc.collect()
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETED in {processing_time}ms ({processing_time/1000:.1f}s)")
        print(f"\n📊 OPTIMIZATION METRICS:")
        print(f"├─ Embedding API calls: {metrics['embedding_calls']}")
        print(f"├─ LLM API calls: {metrics['llm_calls']}")
        print(f"├─ Nodes created: {metrics['nodes_created']}")
        print(f"├─ Nodes merged: {metrics['nodes_merged']}")
        print(f"├─ Chunks processed: {metrics['chunks_processed']}")
        print(f"├─ Resources found: {resource_count}")
        print(f"└─ File ID: {file_id}")
        print(f"{'='*80}\n")
        
        return {
            "status": "completed",
            "jobId": job_id,
            "fileId": file_id,
            "nodes": len(node_ids),
            "nodesCreated": metrics['nodes_created'],
            "nodesMerged": metrics['nodes_merged'],
            "chunks": len(all_chunks),
            "resources": resource_count,
            "sourceLanguage": lang,
            "processingTimeMs": processing_time,
            "optimizationMetrics": metrics
        }
    
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"\n❌ ERROR: {error_msg}")
        
        return {
            "status": "failed",
            "jobId": job_id,
            "error": error_msg,
            "traceback": traceback.format_exc()
        }


# ================================
# MESSAGE HANDLER
# ================================
def handle_job_message(message: Dict[str, Any]):
    """Handle incoming job message from RabbitMQ"""
    try:
        print(f"\n📥 Received job message: {json.dumps(message, indent=2)}")
        
        # Extract message fields
        workspace_id = message.get("workspaceId") or message.get("WorkspaceId")
        file_paths = message.get("filePaths") or message.get("FilePaths", [])
        job_id = message.get("jobId") or message.get("JobId") or str(uuid.uuid4())
        
        if not workspace_id:
            raise ValueError("Missing workspaceId in message")
        
        if not file_paths or len(file_paths) == 0:
            raise ValueError("Missing or empty filePaths in message")
        
        # Process only the first file
        pdf_url = file_paths[0]
        file_name = pdf_url.split('/')[-1]
        
        print(f"📌 Processing first file: {file_name}")
        
        # Process the PDF using OPTIMIZED pipeline
        result = process_pdf_job_optimized(workspace_id, pdf_url, file_name, job_id)
        
        # Push result to Firebase
        print(f"\n🔥 Pushing result to Firebase...")
        firebase_client.push_job_result(job_id, result)
        print(f"✓ Result pushed to Firebase for job {job_id}")
        
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"\n❌ Error handling job: {error_msg}")
        
        # Try to push error to Firebase
        try:
            job_id = message.get("jobId") or message.get("JobId") or "unknown"
            firebase_client.push_job_result(job_id, {
                "status": "failed",
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
        except:
            print("Failed to push error to Firebase")


# ================================
# MAIN
# ================================
def main():
    """Main worker loop"""
    print("\n" + "="*80)
    print("🤖 RabbitMQ Worker Starting - ULTRA-OPTIMIZED PIPELINE")
    print("="*80)
    
    # Connect to RabbitMQ
    rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
    rabbitmq_client.connect()
    rabbitmq_client.declare_queue(QUEUE_NAME)
    
    print(f"\n✓ Worker ready and listening to queue: {QUEUE_NAME}")
    print("="*80 + "\n")
    
    try:
        # Start consuming messages
        rabbitmq_client.consume_messages(QUEUE_NAME, handle_job_message)
    except KeyboardInterrupt:
        print("\n\n⚠ Worker interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Worker error: {e}")
        traceback.print_exc()
    finally:
        print("\n🔌 Closing connections...")
        rabbitmq_client.close()
        neo4j_driver.close()
        print("✓ Worker shut down gracefully")


if __name__ == "__main__":
    main()
