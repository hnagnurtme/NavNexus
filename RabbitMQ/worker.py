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
import threading
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
from src.pipeline.neo4j_graph import create_hierarchical_graph, add_evidence_to_node, now_iso
from src.pipeline.qdrant_storage import store_chunks_in_qdrant

from src.model.Evidence import Evidence
from src.model.QdrantChunk import QdrantChunk

# External dependencies
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from fastapi import FastAPI
import uvicorn

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
PAPAGO_CLIENT_ID = os.getenv("PAPAGO_CLIENT_ID", "")
PAPAGO_CLIENT_SECRET = os.getenv("PAPAGO_CLIENT_SECRET", "")
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")

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

# Health check port
HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", "8000"))

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
# FASTAPI HEALTH CHECK SERVER
# ================================
health_app = FastAPI()

@health_app.get("/health")
async def health_check():
    return {"status": "ok"}

def start_health_check_server():
    """Starts the FastAPI health check server."""
    print(f"🩺 Starting health check server on port {HEALTH_CHECK_PORT}...")
    uvicorn.run(health_app, host="0.0.0.0", port=HEALTH_CHECK_PORT, log_level="warning")


# ================================
# MAIN PROCESSING FUNCTION
# ================================
# def process_pdf_job(workspace_id: str, pdf_url: str, file_name: str, job_id: str) -> Dict[str, Any]:
#     """Process a single PDF through the pipeline"""
#     start_time = datetime.now()
#     file_id = str(uuid.uuid4())
    
#     print(f"\n{'='*80}")
#     print(f"🚀 PROCESSING PDF JOB")
#     print(f"📄 File: {file_name}")
#     print(f"🔖 Workspace: {workspace_id}")
#     print(f"🆔 Job ID: {job_id}")
#     print(f"{'='*80}\n")
    
#     try:
#         # =================================================================
#         # PHASE 1: Extract PDF
#         # =================================================================
#         print(f"📄 Phase 1: Extracting PDF")
#         full_text, lang = extract_pdf_fast(pdf_url, max_pages=25)
#         print(f"✓ Extracted {len(full_text)} chars, language: {lang}")
        
#         # =================================================================
#         # PHASE 2: Extract + Translate Hierarchical Structure
#         # =================================================================
#         print(f"\n📊 Phase 2: Extracting hierarchical structure")
#         structure = extract_hierarchical_structure(full_text, file_name, lang, CLOVA_API_KEY, CLOVA_API_URL)
        
#         # Translate entire structure to English if needed
#         if lang != "en":
#             print(f"🌐 Translating structure from {lang} to English...")
#             structure = translate_structure_to_english(structure, lang, PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
#             print(f"✓ Structure translated")
        
#         # =================================================================
#         # PHASE 3: Create Neo4j Knowledge Graph with Semantic Merging
#         # =================================================================
#         print(f"\n🔗 Phase 3: Creating hierarchical knowledge graph with semantic merging")
        
#         # Create embedding function for semantic matching
#         def create_concept_embedding(text: str):
#             return create_embedding_via_clova(text, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
        
#         with neo4j_driver.session() as session:
#             node_ids = create_hierarchical_graph(
#                 session, workspace_id, structure, file_id, file_name, lang,
#                 CLOVA_API_KEY, CLOVA_API_URL,
#                 embedding_func=create_concept_embedding
#             )
#             print(f"✓ Created/updated {len(node_ids)} nodes in Neo4j")
        
#         # =================================================================
#         # PHASE 4: Process Chunks for Qdrant
#         # =================================================================
#         chunks = create_smart_chunks(full_text, CHUNK_SIZE, OVERLAP)[:MAX_CHUNKS]
#         print(f"\n⚡ Phase 4: Processing {len(chunks)} chunks for Qdrant")
        
#         all_qdrant_chunks = []
#         accumulated_concepts = []
#         prev_embedding = None
#         prev_chunk_id = ""
        
#         for batch_start in range(0, len(chunks), BATCH_SIZE):
#             batch_end = min(batch_start + BATCH_SIZE, len(chunks))
#             batch = chunks[batch_start:batch_end]
            
#             print(f"  Processing batch {batch_start//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1}...")
            
#             batch_result = process_chunk_batch(batch, lang, accumulated_concepts, 
#                                               CLOVA_API_KEY, CLOVA_API_URL)
            
#             for chunk_data in batch_result.get("chunks", []):
#                 chunk_idx = chunk_data.get("chunk_index", 0)
#                 if chunk_idx >= len(chunks):
#                     continue
                
#                 original_chunk = chunks[chunk_idx]
#                 chunk_id = str(uuid.uuid4())
                
#                 # Extract chunk analysis
#                 concepts_data = chunk_data.get("concepts", [])
#                 summary = chunk_data.get("summary", "")
#                 claims = chunk_data.get("key_claims", [])
#                 questions = chunk_data.get("questions", [])
#                 topic = chunk_data.get("topic", "General")
                
#                 # Translate chunk content if needed
#                 if lang != "en":
#                     to_translate = [summary, topic] + claims + questions
#                     to_translate.extend([c.get("name", "") for c in concepts_data])
                    
#                     translated = translate_batch([t for t in to_translate if t], lang, "en", 
#                                                 PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
                    
#                     if translated:
#                         idx = 0
#                         summary = translated[idx] if idx < len(translated) else summary
#                         idx += 1
#                         topic = translated[idx] if idx < len(translated) else topic
#                         idx += 1
                        
#                         claims = translated[idx:idx+len(claims)] if idx+len(claims) <= len(translated) else claims
#                         idx += len(claims)
                        
#                         questions = translated[idx:idx+len(questions)] if idx+len(questions) <= len(translated) else questions
#                         idx += len(questions)
                        
#                         # Translate concept names
#                         for i, c in enumerate(concepts_data):
#                             if idx + i < len(translated):
#                                 c["name"] = translated[idx + i]
                
#                 # Update accumulated concepts
#                 accumulated_concepts.extend([c.get("name", "") for c in concepts_data])
#                 accumulated_concepts = list(set(accumulated_concepts))[-50:]  # Keep last 50 unique
                
#                 # Create embedding from summary
#                 embedding = create_embedding_via_clova(summary, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
                
#                 # Calculate semantic similarity with previous chunk
#                 semantic_sim = 0.0
#                 if prev_embedding:
#                     semantic_sim = calculate_similarity(prev_embedding, embedding)
                
#                 # Build hierarchy path
#                 hierarchy_path = f"{file_name}"
#                 if concepts_data:
#                     hierarchy_path += f" > {concepts_data[0].get('name', 'Chunk')}"
#                 hierarchy_path += f" > Chunk {chunk_idx+1}"
                
#                 # Create Qdrant chunk with all fields
#                 qdrant_chunk = QdrantChunk(
#                     chunk_id=chunk_id,
#                     paper_id=file_id,
#                     page=chunk_idx + 1,
#                     text=original_chunk["text"][:500],
#                     summary=summary,
#                     concepts=[c.get("name", "") for c in concepts_data if c.get("name")],
#                     topic=topic,
#                     workspace_id=workspace_id,
#                     language="en",
#                     source_language=lang,
#                     created_at=now_iso(),
#                     hierarchy_path=hierarchy_path,
#                     chunk_index=chunk_idx,
#                     prev_chunk_id=prev_chunk_id,
#                     next_chunk_id="",  # Will be updated
#                     semantic_similarity_prev=semantic_sim,
#                     overlap_with_prev=original_chunk.get("overlap_previous", "")[:200],
#                     key_claims=claims,
#                     questions_raised=questions,
#                     evidence_strength=0.8
#                 )
                
#                 all_qdrant_chunks.append((qdrant_chunk, embedding))
                
#                 # Update previous chunk's next_chunk_id
#                 if prev_chunk_id and len(all_qdrant_chunks) > 1:
#                     all_qdrant_chunks[-2][0].next_chunk_id = chunk_id
                
#                 prev_chunk_id = chunk_id
#                 prev_embedding = embedding
            
#             gc.collect()
        
#         print(f"✓ Processed {len(all_qdrant_chunks)} chunks")
        
#         # =================================================================
#         # PHASE 5: Store Chunks in Qdrant
#         # =================================================================
#         print(f"\n💾 Phase 5: Storing {len(all_qdrant_chunks)} chunks in Qdrant")
#         store_chunks_in_qdrant(qdrant_client, workspace_id, all_qdrant_chunks)
#         print(f"✓ Stored in Qdrant collection: {workspace_id}")
        
#         # =================================================================
#         # PHASE 6: Gap Analysis & Suggestions
#         # =================================================================
#         print(f"\n🔍 Phase 6: Analyzing knowledge gaps")
#         with neo4j_driver.session() as session:
#             gap_count = analyze_and_add_gaps(
#                 session, workspace_id, file_id, 
#                 CLOVA_API_KEY, CLOVA_API_URL
#             )
#             print(f"✓ Added {gap_count} gap suggestions to leaf nodes")
        
#         # =================================================================
#         # SUMMARY
#         # =================================================================
#         processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
#         print(f"\n{'='*80}")
#         print(f"✅ COMPLETED in {processing_time}ms ({processing_time/1000:.1f}s)")
#         print(f"├─ Neo4j Nodes: {len(node_ids)}")
#         print(f"├─ Qdrant Chunks: {len(all_qdrant_chunks)}")
#         print(f"├─ Gap Suggestions: {gap_count}")
#         print(f"├─ Language: {lang} → en")
#         print(f"└─ File ID: {file_id}")
#         print(f"{'='*80}\n")
        
#         return {
#             "status": "completed",
#             "jobId": job_id,
#             "fileId": file_id,
#             "fileName": file_name,
#             "workspaceId": workspace_id,
#             "nodes": len(node_ids),
#             "chunks": len(all_qdrant_chunks),
#             "gaps": gap_count,
#             "sourceLanguage": lang,
#             "targetLanguage": "en",
#             "processingTimeMs": processing_time
#         }
    
#     except Exception as e:
#         error_msg = str(e)
#         traceback.print_exc()
#         print(f"\n❌ ERROR: {error_msg}")
        
#         return {
#             "status": "failed",
#             "jobId": job_id,
#             "fileId": file_id,
#             "fileName": file_name,
#             "error": error_msg,
#             "traceback": traceback.format_exc()
#         }


# # =================================================================
# # HELPER FUNCTIONS
# # =================================================================

# def translate_structure_to_english(structure: Dict, source_lang: str, 
#                                    client_id: str, client_secret: str) -> Dict:
#     """Translate entire structure to English in one batch"""
#     texts_to_translate = []
    
#     # Collect all texts
#     domain = structure.get("domain", {})
#     texts_to_translate.extend([
#         domain.get("name", ""),
#         domain.get("synthesis", "")
#     ])
    
#     for cat in structure.get("categories", []):
#         texts_to_translate.extend([
#             cat.get("name", ""),
#             cat.get("synthesis", "")
#         ])
        
#         for concept in cat.get("concepts", []):
#             texts_to_translate.extend([
#                 concept.get("name", ""),
#                 concept.get("synthesis", "")
#             ])
            
#             for sub in concept.get("subconcepts", []):
#                 texts_to_translate.extend([
#                     sub.get("name", ""),
#                     sub.get("synthesis", ""),
#                     sub.get("evidence", "")
#                 ])
    
#     # Translate batch
#     translated = translate_batch([t for t in texts_to_translate if t], 
#                                 source_lang, "en", client_id, client_secret)
    
#     if not translated:
#         return structure
    
#     # Reassign translations
#     idx = 0
#     domain["name"] = translated[idx] if idx < len(translated) else domain.get("name", "")
#     idx += 1
#     domain["synthesis"] = translated[idx] if idx < len(translated) else domain.get("synthesis", "")
#     idx += 1
    
#     for cat in structure.get("categories", []):
#         cat["name"] = translated[idx] if idx < len(translated) else cat.get("name", "")
#         idx += 1
#         cat["synthesis"] = translated[idx] if idx < len(translated) else cat.get("synthesis", "")
#         idx += 1
        
#         for concept in cat.get("concepts", []):
#             concept["name"] = translated[idx] if idx < len(translated) else concept.get("name", "")
#             idx += 1
#             concept["synthesis"] = translated[idx] if idx < len(translated) else concept.get("synthesis", "")
#             idx += 1
            
#             for sub in concept.get("subconcepts", []):
#                 sub["name"] = translated[idx] if idx < len(translated) else sub.get("name", "")
#                 idx += 1
#                 sub["synthesis"] = translated[idx] if idx < len(translated) else sub.get("synthesis", "")
#                 idx += 1
#                 sub["evidence"] = translated[idx] if idx < len(translated) else sub.get("evidence", "")
#                 idx += 1
    
#     return structure


# def analyze_and_add_gaps(session, workspace_id: str, file_id: str,
#                          clova_api_key: str, clova_api_url: str) -> int:
#     """Analyze knowledge gaps and add suggestions to leaf nodes"""
#     from src.pipeline.llm_analysis import call_llm_compact
#     from src.pipeline.neo4j_graph import GapSuggestion, create_gap_suggestion_node
    
#     # Find all leaf nodes
#     result = session.run(
#         """
#         MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
#         WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
#         RETURN n.id as node_id, n.name as node_name, n.synthesis as synthesis
#         """,
#         workspace_id=workspace_id
#     )
    
#     leaf_nodes = [dict(record) for record in result]
#     gap_count = 0
    
#     for node in leaf_nodes:
#         node_id = node["node_id"]
#         node_name = node["node_name"]
#         synthesis = node["synthesis"]
        
#         if not synthesis:
#             continue
        
#         # Generate gap suggestions using LLM
#         gap_prompt = f"""Analyze this knowledge node and suggest 2-3 specific questions or topics that would deepen understanding:

# Node: {node_name}
# Content: {synthesis}

# Return JSON:
# {{"suggestions": ["question 1", "question 2", "question 3"]}}"""
        
#         result = call_llm_compact(gap_prompt, max_tokens=200, 
#                                  clova_api_key=clova_api_key, 
#                                  clova_api_url=clova_api_url)
        
#         suggestions = result.get("suggestions", [])
        
#         # Create GapSuggestion nodes
#         for suggestion_text in suggestions[:3]:  # Max 3
#             gap = GapSuggestion(
#                 SuggestionText=suggestion_text,
#                 TargetNodeId=node_id,
#                 TargetFileId=file_id,
#                 SimilarityScore=0.0
#             )
            
#             create_gap_suggestion_node(session, gap, node_id)
#             gap_count += 1
    
#     return gap_count

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

def process_pdf_job(workspace_id: str, pdf_url: str, file_name: str, job_id: str) -> Dict[str, Any]:
    """Process a single PDF through the pipeline with smart deduplication"""
    from src.pipeline.neo4j_graph import deduplicate_across_workspace
    
    start_time = datetime.now()
    file_id = str(uuid.uuid4())
    
    print(f"\n{'='*80}")
    print(f"🚀 PROCESSING PDF JOB")
    print(f"📄 File: {file_name}")
    print(f"🔖 Workspace: {workspace_id}")
    print(f"🆔 Job ID: {job_id}")
    print(f"{'='*80}\n")
    
    try:
        # =================================================================
        # PHASE 1: Extract PDF
        # =================================================================
        print(f"📄 Phase 1: Extracting PDF")
        full_text, lang = extract_pdf_fast(pdf_url, max_pages=25)
        print(f"✓ Extracted {len(full_text)} chars, language: {lang}")
        
        # =================================================================
        # PHASE 2: Extract + Translate Hierarchical Structure
        # =================================================================
        print(f"\n📊 Phase 2: Extracting hierarchical structure")
        structure = extract_hierarchical_structure(full_text, file_name, lang, CLOVA_API_KEY, CLOVA_API_URL)
        
        # Translate entire structure to English if needed
        if lang != "en":
            print(f"🌐 Translating structure from {lang} to English...")
            structure = translate_structure_to_english(structure, lang, PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
            print(f"✓ Structure translated")
        
        # =================================================================
        # PHASE 3: Create Neo4j Knowledge Graph with Semantic Merging
        # =================================================================
        print(f"\n🔗 Phase 3: Creating hierarchical knowledge graph with semantic merging")
        
        # Create embedding function for semantic matching
        def create_concept_embedding(text: str):
            return create_embedding_via_clova(text, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
        
        with neo4j_driver.session() as session:
            node_ids = create_hierarchical_graph(
                session, workspace_id, structure, file_id, file_name, lang,
                CLOVA_API_KEY, CLOVA_API_URL,
                embedding_func=create_concept_embedding
            )
            print(f"✓ Created/updated {len(node_ids)} nodes in Neo4j")
        
        # =================================================================
        # PHASE 4: Process Chunks for Qdrant
        # =================================================================
        chunks = create_smart_chunks(full_text, CHUNK_SIZE, OVERLAP)[:MAX_CHUNKS]
        print(f"\n⚡ Phase 4: Processing {len(chunks)} chunks for Qdrant")
        
        all_qdrant_chunks = []
        accumulated_concepts = []
        prev_embedding = None
        prev_chunk_id = ""
        
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(chunks))
            batch = chunks[batch_start:batch_end]
            
            print(f"  Processing batch {batch_start//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1}...")
            
            batch_result = process_chunk_batch(batch, lang, accumulated_concepts, 
                                              CLOVA_API_KEY, CLOVA_API_URL)
            
            for chunk_data in batch_result.get("chunks", []):
                chunk_idx = chunk_data.get("chunk_index", 0)
                if chunk_idx >= len(chunks):
                    continue
                
                original_chunk = chunks[chunk_idx]
                chunk_id = str(uuid.uuid4())
                
                # Extract chunk analysis
                concepts_data = chunk_data.get("concepts", [])
                summary = chunk_data.get("summary", "")
                claims = chunk_data.get("key_claims", [])
                questions = chunk_data.get("questions", [])
                topic = chunk_data.get("topic", "General")
                
                # Translate chunk content if needed
                if lang != "en":
                    to_translate = [summary, topic] + claims + questions
                    to_translate.extend([c.get("name", "") for c in concepts_data])
                    
                    translated = translate_batch([t for t in to_translate if t], lang, "en", 
                                                PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET)
                    
                    if translated:
                        idx = 0
                        summary = translated[idx] if idx < len(translated) else summary
                        idx += 1
                        topic = translated[idx] if idx < len(translated) else topic
                        idx += 1
                        
                        claims = translated[idx:idx+len(claims)] if idx+len(claims) <= len(translated) else claims
                        idx += len(claims)
                        
                        questions = translated[idx:idx+len(questions)] if idx+len(questions) <= len(translated) else questions
                        idx += len(questions)
                        
                        # Translate concept names
                        for i, c in enumerate(concepts_data):
                            if idx + i < len(translated):
                                c["name"] = translated[idx + i]
                
                # Update accumulated concepts
                accumulated_concepts.extend([c.get("name", "") for c in concepts_data])
                accumulated_concepts = list(set(accumulated_concepts))[-50:]  # Keep last 50 unique
                
                # Create embedding from summary
                embedding = create_embedding_via_clova(summary, CLOVA_API_KEY, CLOVA_EMBEDDING_URL)
                
                # Calculate semantic similarity with previous chunk
                semantic_sim = 0.0
                if prev_embedding:
                    semantic_sim = calculate_similarity(prev_embedding, embedding)
                
                # Build hierarchy path
                hierarchy_path = f"{file_name}"
                if concepts_data:
                    hierarchy_path += f" > {concepts_data[0].get('name', 'Chunk')}"
                hierarchy_path += f" > Chunk {chunk_idx+1}"
                
                # Create Qdrant chunk with all fields
                qdrant_chunk = QdrantChunk(
                    chunk_id=chunk_id,
                    paper_id=file_id,
                    page=chunk_idx + 1,
                    text=original_chunk["text"][:500],
                    summary=summary,
                    concepts=[c.get("name", "") for c in concepts_data if c.get("name")],
                    topic=topic,
                    workspace_id=workspace_id,
                    language="en",
                    source_language=lang,
                    created_at=now_iso(),
                    hierarchy_path=hierarchy_path,
                    chunk_index=chunk_idx,
                    prev_chunk_id=prev_chunk_id,
                    next_chunk_id="",  # Will be updated
                    semantic_similarity_prev=semantic_sim,
                    overlap_with_prev=original_chunk.get("overlap_previous", "")[:200],
                    key_claims=claims,
                    questions_raised=questions,
                    evidence_strength=0.8
                )
                
                all_qdrant_chunks.append((qdrant_chunk, embedding))
                
                # Update previous chunk's next_chunk_id
                if prev_chunk_id and len(all_qdrant_chunks) > 1:
                    all_qdrant_chunks[-2][0].next_chunk_id = chunk_id
                
                prev_chunk_id = chunk_id
                prev_embedding = embedding
            
            gc.collect()
        
        print(f"✓ Processed {len(all_qdrant_chunks)} chunks")
        
        # =================================================================
        # PHASE 5: Store Chunks in Qdrant
        # =================================================================
        print(f"\n💾 Phase 5: Storing {len(all_qdrant_chunks)} chunks in Qdrant")
        store_chunks_in_qdrant(qdrant_client, workspace_id, all_qdrant_chunks)
        print(f"✓ Stored in Qdrant collection: {workspace_id}")
        
        # =================================================================
        # PHASE 6: Post-Processing Deduplication (Smart Merge)
        # =================================================================
        print(f"\n🧹 Phase 6: Smart deduplication across workspace")
        with neo4j_driver.session() as session:
            dedup_results = deduplicate_across_workspace(
                session, workspace_id, 
                CLOVA_API_KEY, CLOVA_API_URL,
                create_concept_embedding
            )
            print(f"✓ Scanned {dedup_results['scanned']} nodes, merged {dedup_results['merged']} duplicates")
        
        # =================================================================
        # PHASE 7: Gap Analysis & Suggestions
        # =================================================================
        print(f"\n🔍 Phase 7: Analyzing knowledge gaps")
        with neo4j_driver.session() as session:
            gap_count = analyze_and_add_gaps(
                session, workspace_id, file_id, 
                CLOVA_API_KEY, CLOVA_API_URL
            )
            print(f"✓ Added {gap_count} gap suggestions to leaf nodes")
        
        # =================================================================
        # SUMMARY
        # =================================================================
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETED in {processing_time}ms ({processing_time/1000:.1f}s)")
        print(f"├─ Neo4j Nodes: {len(node_ids)}")
        print(f"├─ Deduplicated: {dedup_results['merged']} merged")
        print(f"├─ Qdrant Chunks: {len(all_qdrant_chunks)}")
        print(f"├─ Gap Suggestions: {gap_count}")
        print(f"├─ Language: {lang} → en")
        print(f"└─ File ID: {file_id}")
        print(f"{'='*80}\n")
        
        return {
            "status": "completed",
            "jobId": job_id,
            "fileId": file_id,
            "fileName": file_name,
            "workspaceId": workspace_id,
            "nodes": len(node_ids),
            "deduplicated": dedup_results['merged'],
            "chunks": len(all_qdrant_chunks),
            "gaps": gap_count,
            "sourceLanguage": lang,
            "targetLanguage": "en",
            "processingTimeMs": processing_time
        }
    
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"\n❌ ERROR: {error_msg}")
        
        return {
            "status": "failed",
            "jobId": job_id,
            "fileId": file_id,
            "fileName": file_name,
            "error": error_msg,
            "traceback": traceback.format_exc()
        }


# =================================================================
# HELPER FUNCTIONS
# =================================================================

def translate_structure_to_english(structure: Dict, source_lang: str, 
                                   client_id: str, client_secret: str) -> Dict:
    """Translate entire structure to English in one batch"""
    texts_to_translate = []
    
    # Collect all texts
    domain = structure.get("domain", {})
    texts_to_translate.extend([
        domain.get("name", ""),
        domain.get("synthesis", "")
    ])
    
    for cat in structure.get("categories", []):
        texts_to_translate.extend([
            cat.get("name", ""),
            cat.get("synthesis", "")
        ])
        
        for concept in cat.get("concepts", []):
            texts_to_translate.extend([
                concept.get("name", ""),
                concept.get("synthesis", "")
            ])
            
            for sub in concept.get("subconcepts", []):
                texts_to_translate.extend([
                    sub.get("name", ""),
                    sub.get("synthesis", ""),
                    sub.get("evidence", "")
                ])
    
    # Translate batch
    translated = translate_batch([t for t in texts_to_translate if t], 
                                source_lang, "en", client_id, client_secret)
    
    if not translated:
        return structure
    
    # Reassign translations
    idx = 0
    domain["name"] = translated[idx] if idx < len(translated) else domain.get("name", "")
    idx += 1
    domain["synthesis"] = translated[idx] if idx < len(translated) else domain.get("synthesis", "")
    idx += 1
    
    for cat in structure.get("categories", []):
        cat["name"] = translated[idx] if idx < len(translated) else cat.get("name", "")
        idx += 1
        cat["synthesis"] = translated[idx] if idx < len(translated) else cat.get("synthesis", "")
        idx += 1
        
        for concept in cat.get("concepts", []):
            concept["name"] = translated[idx] if idx < len(translated) else concept.get("name", "")
            idx += 1
            concept["synthesis"] = translated[idx] if idx < len(translated) else concept.get("synthesis", "")
            idx += 1
            
            for sub in concept.get("subconcepts", []):
                sub["name"] = translated[idx] if idx < len(translated) else sub.get("name", "")
                idx += 1
                sub["synthesis"] = translated[idx] if idx < len(translated) else sub.get("synthesis", "")
                idx += 1
                sub["evidence"] = translated[idx] if idx < len(translated) else sub.get("evidence", "")
                idx += 1
    
    return structure


def analyze_and_add_gaps(session, workspace_id: str, file_id: str,
                         clova_api_key: str, clova_api_url: str) -> int:
    """Analyze knowledge gaps and add suggestions to leaf nodes"""
    from src.pipeline.llm_analysis import call_llm_compact
    from src.model.GapSuggestion import GapSuggestion
    from src.pipeline.neo4j_graph import create_gap_suggestion_node
    
    
    # Find all leaf nodes
    result = session.run(
        """
        MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
        WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
        RETURN n.id as node_id, n.name as node_name, n.synthesis as synthesis
        """,
        workspace_id=workspace_id
    )
    
    leaf_nodes = [dict(record) for record in result]
    gap_count = 0
    
    for node in leaf_nodes:
        node_id = node["node_id"]
        node_name = node["node_name"]
        synthesis = node["synthesis"]
        
        if not synthesis:
            continue
        
        # Generate gap suggestions using LLM
        gap_prompt = f"""Analyze this knowledge node and suggest 2-3 specific questions or topics that would deepen understanding:

Node: {node_name}
Content: {synthesis}

Return JSON:
{{"suggestions": ["question 1", "question 2", "question 3"]}}"""
        
        result = call_llm_compact(gap_prompt, max_tokens=200, 
                                 clova_api_key=clova_api_key, 
                                 clova_api_url=clova_api_url)
        
        suggestions = result.get("suggestions", [])
        
        # Create GapSuggestion nodes
        for suggestion_text in suggestions[:3]:  # Max 3
            gap = GapSuggestion(
                SuggestionText=suggestion_text,
                TargetNodeId=node_id,
                TargetFileId=file_id,
                SimilarityScore=0.0
            )
            
            create_gap_suggestion_node(session, gap, node_id)
            gap_count += 1
    
    return gap_count
# ================================
# MAIN
# ================================
def main():
    """Main worker loop"""
    print("\n" + "="*80)
    print("🤖 RabbitMQ Worker Starting...")
    print("="*80)
    
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=start_health_check_server, daemon=True)
    health_thread.start()

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
