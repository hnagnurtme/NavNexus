"""
RabbitMQ Worker for processing PDF jobs
Listens to queue "pdf_jobs_queue" and processes PDF documents through the pipeline
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

# Pipeline modules
from src.pipeline.pdf_extraction import extract_pdf_fast
from src.pipeline.chunking import create_smart_chunks
from src.pipeline.embedding import create_embedding_via_clova, calculate_similarity
from src.pipeline.translation import translate_batch
from src.pipeline.llm_analysis import extract_hierarchical_structure, process_chunk_batch
from src.pipeline.neo4j_graph import create_hierarchical_graph, find_or_merge_node, add_evidence_to_node, update_node_synthesis, now_iso
from src.pipeline.qdrant_storage import store_chunks_in_qdrant

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
BATCH_SIZE = 3

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
# MAIN PROCESSING FUNCTION
# ================================
def process_pdf_job(workspace_id: str, pdf_url: str, file_name: str, job_id: str) -> Dict[str, Any]:
    """Process a single PDF through the pipeline"""
    start_time = datetime.now()
    file_id = str(uuid.uuid4())
    
    print(f"\n{'='*80}")
    print(f"🚀 PROCESSING PDF JOB")
    print(f"📄 File: {file_name}")
    print(f"🔖 Workspace: {workspace_id}")
    print(f"🆔 Job ID: {job_id}")
    print(f"{'='*80}\n")
    
    try:
        # PHASE 1: Extract PDF
        print(f"📄 Phase 1: Extracting PDF")
        full_text, lang = extract_pdf_fast(pdf_url, max_pages=25)
        
        # PHASE 2: Extract hierarchical structure
        print(f"\n📊 Phase 2: Extracting hierarchical structure (lang: {lang})")
        structure = extract_hierarchical_structure(full_text, file_name, lang, CLOVA_API_KEY, CLOVA_API_URL)
        
        # Translate structure to English if needed
        if lang != "en":
            print(f"🌐 Translating structure to English...")
            # Collect all text to translate
            texts_to_translate = []
            
            domain = structure.get("domain", {})
            texts_to_translate.extend([domain.get("name", ""), domain.get("synthesis", "")])
            
            for cat in structure.get("categories", []):
                texts_to_translate.extend([cat.get("name", ""), cat.get("synthesis", "")])
                for concept in cat.get("concepts", []):
                    texts_to_translate.extend([concept.get("name", ""), concept.get("synthesis", "")])
                    for sub in concept.get("subconcepts", []):
                        texts_to_translate.extend([
                            sub.get("name", ""), 
                            sub.get("synthesis", ""),
                            sub.get("evidence", "")
                        ])
            
            # Translate in batch
            translated = translate_batch([t for t in texts_to_translate if t], lang, "en", 
                                        PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
        
        # PHASE 3: Create Neo4j graph
        print(f"\n🔗 Phase 3: Creating hierarchical knowledge graph")
        with neo4j_driver.session() as session:
            node_ids = create_hierarchical_graph(
                session, workspace_id, structure, file_id, file_name, lang,
                CLOVA_API_KEY, CLOVA_API_URL
            )
            print(f"✓ Created/updated {len(node_ids)} nodes")
        
        # PHASE 4: Process chunks
        chunks = create_smart_chunks(full_text, CHUNK_SIZE, OVERLAP)[:MAX_CHUNKS]
        print(f"\n⚡ Phase 4: Processing {len(chunks)} chunks")
        
        all_chunks = []
        accumulated_concepts = []
        prev_embedding = None
        prev_chunk_id = ""
        
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(chunks))
            batch = chunks[batch_start:batch_end]
            
            batch_result = process_chunk_batch(batch, lang, accumulated_concepts, 
                                              CLOVA_API_KEY, CLOVA_API_URL)
            
            for chunk_data in batch_result.get("chunks", []):
                chunk_idx = chunk_data.get("chunk_index", 0)
                if chunk_idx >= len(chunks):
                    continue
                
                original_chunk = chunks[chunk_idx]
                chunk_id = str(uuid.uuid4())
                
                # Extract and translate if needed
                concepts_data = chunk_data.get("concepts", [])
                summary = chunk_data.get("summary", "")
                claims = chunk_data.get("key_claims", [])
                
                if lang != "en":
                    to_translate = [summary] + claims
                    to_translate.extend([c.get("name", "") for c in concepts_data])
                    to_translate.extend([c.get("synthesis", "") for c in concepts_data])
                    to_translate.extend([c.get("evidence", "") for c in concepts_data])
                    
                    translated = translate_batch(to_translate, lang, "en", 
                                                PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
                    
                    summary = translated[0] if translated else summary
                    claims = translated[1:len(claims)+1] if len(translated) > 1 else claims
                    
                    # Update concepts
                    offset = len(claims) + 1
                    for i, c in enumerate(concepts_data):
                        if offset + i*3 < len(translated):
                            c["name"] = translated[offset + i*3]
                            c["synthesis"] = translated[offset + i*3 + 1] if offset + i*3 + 1 < len(translated) else c.get("synthesis", "")
                            c["evidence"] = translated[offset + i*3 + 2] if offset + i*3 + 2 < len(translated) else c.get("evidence", "")
                
                # Link chunk concepts to graph nodes
                with neo4j_driver.session() as session:
                    for c in concepts_data:
                        concept_name = c.get("name", "")
                        if not concept_name:
                            continue
                        
                        # Find matching node
                        node_id = find_or_merge_node(
                            session, workspace_id, concept_name, 
                            c.get("type", "concept"), 
                            c.get("level", 2)
                        )
                        
                        # Add chunk as evidence
                        evidence = Evidence(
                            SourceId=file_id,
                            SourceName=file_name,
                            ChunkId=chunk_id,
                            Text=c.get("evidence", c.get("synthesis", "")),
                            Page=chunk_idx + 1,
                            Confidence=0.8,
                            CreatedAt=datetime.utcnow(),
                            KeyClaims=claims
                        )
                        
                        add_evidence_to_node(session, node_id, evidence)
                        update_node_synthesis(session, node_id, c.get("synthesis", ""), 
                                            CLOVA_API_KEY, CLOVA_API_URL)
                        
                        accumulated_concepts.append(concept_name)
                
                # Create embedding
                embedding = create_embedding_via_clova(summary, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
                
                # Calculate similarity
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
                    concepts=[c.get("name", "") for c in concepts_data],
                    topic=chunk_data.get("topic", "General"),
                    workspace_id=workspace_id,
                    language="en",
                    source_language=lang,
                    created_at=now_iso(),
                    hierarchy_path=f"{file_name} > Chunk {chunk_idx+1}",
                    chunk_index=chunk_idx,
                    prev_chunk_id=prev_chunk_id,
                    next_chunk_id="",
                    semantic_similarity_prev=semantic_sim,
                    overlap_with_prev=original_chunk["overlap_previous"][:200],
                    key_claims=claims,
                    questions_raised=chunk_data.get("questions", []),
                    evidence_strength=0.8
                )
                
                all_chunks.append((qdrant_chunk, embedding))
                
                # Update previous chunk
                if prev_chunk_id and all_chunks:
                    for i, (c, e) in enumerate(all_chunks):
                        if c.chunk_id == prev_chunk_id:
                            c.next_chunk_id = chunk_id
                            break
                
                prev_chunk_id = chunk_id
                prev_embedding = embedding
            
            gc.collect()
        
        # PHASE 5: Store in Qdrant
        print(f"\n💾 Phase 5: Storing {len(all_chunks)} chunks in Qdrant")
        store_chunks_in_qdrant(qdrant_client, workspace_id, all_chunks)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETED in {processing_time}ms ({processing_time/1000:.1f}s)")
        print(f"├─ Hierarchical nodes: {len(node_ids)}")
        print(f"├─ Chunks processed: {len(all_chunks)}")
        print(f"├─ Source language: {lang} → en")
        print(f"└─ File ID: {file_id}")
        print(f"{'='*80}\n")
        
        return {
            "status": "completed",
            "jobId": job_id,
            "fileId": file_id,
            "nodes": len(node_ids),
            "chunks": len(all_chunks),
            "sourceLanguage": lang,
            "processingTimeMs": processing_time
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
        
        # Process the PDF
        result = process_pdf_job(workspace_id, pdf_url, file_name, job_id)
        
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
    print("🤖 RabbitMQ Worker Starting...")
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