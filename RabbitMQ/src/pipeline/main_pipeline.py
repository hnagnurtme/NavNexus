import os
import gc
import uuid
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

# Import configuration
from config import (
    # API Configuration
    CLOVA_API_KEY, CLOVA_API_URL, CLOVA_EMBEDDING_URL,
    PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET,
    
    # Pipeline Configuration
    CHUNK_SIZE, OVERLAP, MAX_CHUNKS, MIN_CHUNK_SIZE,
    BATCH_SIZE, EMBEDDING_BATCH_SIZE, QDRANT_BATCH_SIZE,
    MAX_SYNTHESIS_LENGTH, MAX_PDF_TEXT_EXTRACT,
    
    # Performance Configuration
    PDF_DOWNLOAD_TIMEOUT,
    MAX_RETRY_ATTEMPTS, MAX_PDF_PAGES,
    
    # Feature Flags
    FEATURE_TRANSLATION, FEATURE_RESOURCE_DISCOVERY,
    FEATURE_SEMANTIC_DEDUPLICATION,
    DEBUG_MODE,
    
    # Validation
    CONFIG_VALID, CONFIG_SUMMARY,
    
    # Constants
    EMBEDDING_DIMENSION
)

# Import pipeline modules
from .pdf_extraction import extract_pdf_enhanced
from .chunking import create_smart_chunks, calculate_chunk_stats
from .llm_analysis import (
    extract_merge_optimized_structure, 
    analyze_chunks_for_merging,
)
from .embedding_cache import batch_create_embeddings, extract_all_concept_names
from .embedding import create_embedding_via_clova, calculate_similarity
from .neo4j_graph import (
    create_hierarchical_knowledge_graph,
)
from .qdrant_storage import (
    store_chunks_in_qdrant,
    search_similar_chunks,
    get_collection_stats
)
from .translation import (
    translate_structure_enhanced,
    translate_chunk_analysis_enhanced,
    validate_language_codes
)
from .resource_discovery import (
    discover_resources_via_knowledge_analysis,
    get_resource_discovery_stats
)

from ..model.QdrantChunk import QdrantChunk


class PipelineMetrics:
    """Metrics collector for pipeline processing"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'phases_completed': [],
            'embedding_calls': 0,
            'llm_calls': 0,
            'translation_requests': 0,
            'nodes_created': 0,
            'nodes_merged': 0,
            'chunks_processed': 0,
            'resources_discovered': 0,
            'errors_encountered': [],
            'warnings': []
        }
    
    def add_phase(self, phase_name: str):
        """Add completed phase"""
        self.metrics['phases_completed'].append(phase_name)
    
    def increment_embedding_calls(self, count: int = 1):
        """Increment embedding call counter"""
        self.metrics['embedding_calls'] += count
    
    def increment_llm_calls(self, count: int = 1):
        """Increment LLM call counter"""
        self.metrics['llm_calls'] += count
    
    def increment_translation_requests(self, count: int = 1):
        """Increment translation request counter"""
        self.metrics['translation_requests'] += count
    
    def add_error(self, error: str, phase: str):
        """Add error with phase context"""
        self.metrics['errors_encountered'].append({
            'phase': phase,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_warning(self, warning: str, phase: str):
        """Add warning with phase context"""
        self.metrics['warnings'].append({
            'phase': phase,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_processing_time(self) -> int:
        """Get total processing time in milliseconds"""
        return int((datetime.now() - self.start_time).total_seconds() * 1000)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        total_phases = 8  # Total expected phases
        completed_phases = len(self.metrics['phases_completed'])
        success_rate = completed_phases / total_phases if total_phases > 0 else 0.0
        
        return {
            **self.metrics,
            'processing_time_ms': self.get_processing_time(),
            'success_rate': success_rate
        }


def validate_pipeline_inputs(workspace_id: str, pdf_url: str, file_name: str) -> Dict[str, Any]:
    """
    Validate pipeline input parameters
    
    Args:
        workspace_id: Workspace identifier
        pdf_url: PDF URL to process
        file_name: Name of the file
    
    Returns:
        Validation results
    """
    validation_results = {
        'valid': True,
        'errors': []
    }
    
    if not workspace_id or not workspace_id.strip():
        validation_results['valid'] = False
        validation_results['errors'].append('Workspace ID is required')
    
    if not pdf_url or not pdf_url.strip():
        validation_results['valid'] = False
        validation_results['errors'].append('PDF URL is required')
    elif not pdf_url.startswith(('http://', 'https://')):
        validation_results['valid'] = False
        validation_results['errors'].append('PDF URL must be a valid HTTP/HTTPS URL')
    
    if not file_name or not file_name.strip():
        validation_results['valid'] = False
        validation_results['errors'].append('File name is required')
    
    return validation_results


def create_enhanced_fallback_structure(file_name: str, full_text: str, language: str) -> Dict[str, Any]:
    """
    Create enhanced fallback structure when LLM extraction fails
    
    Args:
        file_name: Name of the file
        full_text: Extracted text content
        language: Detected language
    
    Returns:
        Fallback structure
    """
    # Extract meaningful content for fallback
    sentences = [s.strip() for s in full_text.split('.') if len(s.strip()) > 30]
    
    # Ensure we have a proper iterable of strings for join
    synthesis_text = '. '.join(sentences[:3]) + '.' if sentences else f"Content from {file_name}"
    
    # Truncate to max synthesis length
    synthesis = synthesis_text[:MAX_SYNTHESIS_LENGTH]
    
    return {
        'domain': {
            'name': os.path.splitext(file_name)[0].replace('_', ' ').title(),
            'synthesis': synthesis,
            'level': 0
        },
        'categories': [
            {
                'name': 'Key Concepts',
                'synthesis': 'Main concepts and topics discussed in the document',
                'level': 1,
                'concepts': [
                    {
                        'name': 'General Topics',
                        'synthesis': 'Various topics and concepts covered in the document',
                        'level': 2,
                        'subconcepts': [
                            {
                                'name': 'Detailed Information',
                                'synthesis': 'Specific details and information from the document',
                                'level': 3
                            }
                        ]
                    }
                ]
            }
        ],
        '_metadata': {
            'fallback': True,
            'original_language': language,
            'created_at': datetime.now().isoformat()
        }
    }


def cleanup_partial_data(workspace_id: str, file_id: str, neo4j_driver, qdrant_client):
    """
    Clean up partial data in case of processing failure
    
    Args:
        workspace_id: Workspace identifier
        file_id: File identifier
        neo4j_driver: Neo4j driver instance
        qdrant_client: Qdrant client instance
    """
    try:
        print(f"🧹 Cleaning up partial data for file {file_id}...")
        
        # Clean Neo4j data
        with neo4j_driver.session() as session:
            # Delete KnowledgeNodes associated with this file
            session.run(
                """
                MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
                WHERE n.id STARTS WITH $file_prefix
                DETACH DELETE n
                """,
                workspace_id=workspace_id,
                file_prefix=f"{file_id}-"
            )
            
            # Delete Evidence nodes
            session.run(
                """
                MATCH (e:Evidence {source_id: $file_id})
                DETACH DELETE e
                """,
                file_id=file_id
            )
            
            # Delete GapSuggestions
            session.run(
                """
                MATCH (g:GapSuggestion)
                WHERE g.target_file_id = $file_id
                DETACH DELETE g
                """,
                file_id=file_id
            )
        
        # Note: Qdrant cleanup is more complex as we don't store file_id directly
        # We rely on workspace-based collections
        
        print("✓ Cleanup completed")
        
    except Exception as e:
        print(f"⚠️ Cleanup error (non-critical): {e}")


def process_pdf_to_knowledge_graph(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    job_id: str,
    neo4j_driver,
    qdrant_client,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhanced main pipeline for processing PDF documents into knowledge graphs
    
    Args:
        workspace_id: Workspace identifier
        pdf_url: URL of PDF to process
        file_name: Name of the file
        job_id: Job identifier for tracking
        neo4j_driver: Neo4j driver instance
        qdrant_client: Qdrant client instance
        config: Additional configuration overrides
    
    Returns:
        Processing results with detailed metrics
    """
    
    # Validate configuration first
    if not CONFIG_VALID:
        return {
            "status": "failed",
            "jobId": job_id,
            "error": f"Configuration invalid: {CONFIG_SUMMARY.get('error', 'Unknown error')}",
            "timestamp": datetime.now().isoformat()
        }
    
    # Validate inputs
    input_validation = validate_pipeline_inputs(workspace_id, pdf_url, file_name)
    if not input_validation['valid']:
        return {
            "status": "failed",
            "jobId": job_id,
            "error": f"Input validation failed: {', '.join(input_validation['errors'])}",
            "timestamp": datetime.now().isoformat()
        }
    
    # Merge configuration
    default_config = {
        'max_pages': MAX_PDF_PAGES,
        'chunk_size': CHUNK_SIZE,
        'overlap': OVERLAP,
        'max_chunks': MAX_CHUNKS,
        'timeout': PDF_DOWNLOAD_TIMEOUT,
        'enable_translation': FEATURE_TRANSLATION,
        'enable_resource_discovery': FEATURE_RESOURCE_DISCOVERY,
        'enable_semantic_deduplication': FEATURE_SEMANTIC_DEDUPLICATION
    }
    final_config = {**default_config, **(config or {})}
    
    # Initialize metrics and state
    metrics = PipelineMetrics()
    file_id = f"file_{uuid.uuid4().hex[:8]}"
    processing_state = {
        'file_id': file_id,
        'neo4j_processed': False,
        'qdrant_processed': False,
        'language': 'en',
        'structure_extracted': False
    }
    
    # Initialize variables to avoid unbound errors
    node_ids: List[str] = []
    all_chunks_with_embeddings: List[Tuple[QdrantChunk, List[float]]] = []
    chunks: List[Dict[str, Any]] = []
    chunk_analyses: List[Dict[str, Any]] = []
    
    print(f"\n{'='*80}")
    print(f"🚀 KNOWLEDGE GRAPH PIPELINE - ENHANCED")
    print(f"📄 File: {file_name}")
    print(f"🔖 Workspace: {workspace_id}")
    print(f"🆔 Job: {job_id}")
    print(f"🆔 File ID: {file_id}")
    print(f"{'='*80}\n")
    
    try:
        # PHASE 1: Enhanced PDF Extraction
        print(f"📄 Phase 1: Enhanced PDF Extraction")
        try:
            full_text, language, pdf_metadata = extract_pdf_enhanced(
                pdf_url,
                max_pages=final_config['max_pages'],
                timeout=final_config['timeout']
            )
            
            if not full_text or len(full_text.strip()) < 100:
                raise ValueError("PDF extraction failed - insufficient text extracted")
                
            processing_state['language'] = language
            print(f"✓ Extracted {len(full_text)} characters")
            print(f"✓ Detected language: {language} (confidence: {pdf_metadata.get('language_confidence', 0):.2f})")
            metrics.add_phase('pdf_extraction')
            
        except Exception as e:
            metrics.add_error(str(e), 'pdf_extraction')
            raise
        
        # PHASE 2: Structure Extraction with Enhanced Fallback
        print(f"\n📊 Phase 2: Merge-Optimized Structure Extraction")
        try:
            structure = extract_merge_optimized_structure(
                full_text[:MAX_PDF_TEXT_EXTRACT],  # Limit text for LLM
                file_name,
                language,
                CLOVA_API_KEY,
                CLOVA_API_URL
            )
            metrics.increment_llm_calls(1)
            
            # Validate structure
            if not structure or not structure.get('domain') or not structure.get('categories'):
                print("⚠️ Structure extraction failed, using enhanced fallback")
                structure = create_enhanced_fallback_structure(file_name, full_text, language)
                processing_state['structure_extracted'] = False
                metrics.add_warning("Used fallback structure", 'structure_extraction')
            else:
                processing_state['structure_extracted'] = True
                print(f"✓ Extracted structure: {structure['domain']['name']}")
                print(f"✓ Categories: {len(structure['categories'])}")
            
            metrics.add_phase('structure_extraction')
            
        except Exception as e:
            metrics.add_error(str(e), 'structure_extraction')
            # Create fallback structure and continue
            structure = create_enhanced_fallback_structure(file_name, full_text, language)
            processing_state['structure_extracted'] = False
            metrics.add_warning(f"Fallback due to: {str(e)}", 'structure_extraction')
        
        # PHASE 3: Translation (if needed and enabled)
        if (language != "en" and 
            final_config['enable_translation'] and 
            validate_language_codes(language, "en")):
            
            print(f"\n🌐 Phase 3: Translation ({language} → en)")
            try:
                structure = translate_structure_enhanced(
                    structure, language, "en",
                    PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET
                )
                metrics.increment_translation_requests(1)
                print("✓ Structure translated to English")
                metrics.add_phase('translation')
                
            except Exception as e:
                metrics.add_error(str(e), 'translation')
                metrics.add_warning("Translation failed, continuing with original", 'translation')
        
        # PHASE 4: Embedding Cache Preparation
        print(f"\n⚡ Phase 4: Embedding Cache Preparation")
        try:
            concept_names = extract_all_concept_names(structure)
            print(f"📊 Extracted {len(concept_names)} unique concept names")
            
            embeddings_cache = batch_create_embeddings(
                concept_names,
                CLOVA_API_KEY,
                CLOVA_EMBEDDING_URL,
                batch_size=EMBEDDING_BATCH_SIZE
            )
            metrics.increment_embedding_calls(len(embeddings_cache))
            print(f"✓ Created embeddings cache: {len(embeddings_cache)} vectors")
            metrics.add_phase('embedding_cache')
            
        except Exception as e:
            metrics.add_error(str(e), 'embedding_cache')
            # Continue with empty cache
            embeddings_cache = {}
            metrics.add_warning("Using empty embeddings cache", 'embedding_cache')
        
        # PHASE 5: Knowledge Graph Creation
        print(f"\n🔗 Phase 5: Knowledge Graph Creation")
        try:
            with neo4j_driver.session() as session:
                graph_stats = create_hierarchical_knowledge_graph(
                    session, workspace_id, structure, file_id, file_name, embeddings_cache
                )
                
                metrics.metrics['nodes_created'] = graph_stats.get('nodes_created', 0)
                metrics.metrics['nodes_merged'] = graph_stats.get('exact_matches', 0) + graph_stats.get('high_similarity_merges', 0)
                processing_state['neo4j_processed'] = True
                
                print(f"📊 Graph Statistics:")
                print(f"  ├─ Nodes created: {graph_stats.get('nodes_created', 0)}")
                print(f"  ├─ Evidence created: {graph_stats.get('evidence_created', 0)}")
                print(f"  ├─ Exact matches: {graph_stats.get('exact_matches', 0)}")
                print(f"  ├─ High similarity merges: {graph_stats.get('high_similarity_merges', 0)}")
                print(f"  └─ Final count: {graph_stats.get('final_count', 0)}")
                
                node_ids = graph_stats.get('node_ids', [])
            
            metrics.add_phase('knowledge_graph')
            
        except Exception as e:
            metrics.add_error(str(e), 'knowledge_graph')
            raise  # Critical phase, cannot continue
        
        # PHASE 6: Chunk Processing and Analysis
        print(f"\n⚡ Phase 6: Enhanced Chunk Processing")
        try:
            # Create chunks
            chunks = create_smart_chunks(
                full_text,
                chunk_size=final_config['chunk_size'],
                overlap=final_config['overlap'],
                min_chunk_size=MIN_CHUNK_SIZE
            )[:final_config['max_chunks']]
            
            chunk_stats = calculate_chunk_stats(chunks)
            print(f"📊 Created {len(chunks)} chunks")
            print(f"  └─ Stats: {chunk_stats}")
            
            # Analyze chunks
            raw_chunk_analyses = analyze_chunks_for_merging(
                chunks, structure,
                CLOVA_API_KEY, CLOVA_API_URL
            )
            # Convert raw_chunk_analyses to the expected type
            chunk_analyses = [
                {"chunk_index": idx, "data": data}
                for idx, data in enumerate(raw_chunk_analyses.get("chunks", []))
            ]
            metrics.increment_llm_calls(max(1, len(chunks) // BATCH_SIZE))
            metrics.metrics['chunks_processed'] = len(chunk_analyses)
            
            print(f"✓ Analyzed {len(chunk_analyses)} chunks")
            
            # Translate chunk analyses if needed
            if (language != "en" and 
                final_config['enable_translation'] and 
                validate_language_codes(language, "en")):
                
                print(f"🌐 Translating chunk analyses...")
                translated_count = 0
                for i, chunk_data in enumerate(chunk_analyses):
                    if not isinstance(chunk_data, dict):
                        metrics.add_warning(f"Chunk {i} is not a dictionary, skipping translation", 'chunk_translation')
                        continue
                        
                    try:
                        chunk_analyses[i] = translate_chunk_analysis_enhanced(
                            chunk_data, language, "en",
                            PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET
                        )
                        translated_count += 1
                    except Exception as e:
                        metrics.add_warning(f"Chunk {i} translation failed: {str(e)}", 'chunk_translation')
                        continue
                
                metrics.increment_translation_requests(translated_count)
                print(f"✓ Translated {translated_count}/{len(chunk_analyses)} chunk analyses")
            
            metrics.add_phase('chunk_analysis')
            
        except Exception as e:
            metrics.add_error(str(e), 'chunk_analysis')
            # Continue with empty chunk analyses
            chunks = []
            chunk_analyses = []
            metrics.add_warning("Chunk analysis failed, continuing without chunks", 'chunk_analysis')
        
        # PHASE 7: Vector Storage
        print(f"\n💾 Phase 7: Vector Storage")
        try:
            all_chunks_with_embeddings = []
            prev_embedding = None
            prev_chunk_id = ""
            
            for i, chunk_data in enumerate(chunk_analyses):
                # Skip if chunk_data is not a dictionary
                if not isinstance(chunk_data, dict):
                    continue
                    
                # Get the original chunk, ensuring we don't go out of bounds
                if i < len(chunks):
                    original_chunk = chunks[i]
                else:
                    # Create a minimal fallback chunk
                    original_chunk = {"text": "", "overlap_previous": ""}
                
                chunk_idx = chunk_data.get('chunk_index', i)
                chunk_id = f"{file_id}_chunk_{chunk_idx}"
                
                # Normalize data with proper type checking
                summary = ""
                if isinstance(chunk_data.get('summary'), str):
                    summary = chunk_data['summary'].strip() 
                if not summary and isinstance(original_chunk.get("text"), str):
                    summary = original_chunk["text"][:150].strip()
                
                concepts = []
                if isinstance(chunk_data.get('concepts'), list):
                    concepts = [str(c).strip() for c in chunk_data['concepts'] if c and str(c).strip()]
                
                topic = "General"
                if isinstance(chunk_data.get('topic'), str):
                    topic = chunk_data['topic'].strip()
                
                claims = []
                if isinstance(chunk_data.get('key_claims'), list):
                    claims = [str(c).strip() for c in chunk_data['key_claims'] if c and str(c).strip()]
                
                questions = []
                if isinstance(chunk_data.get('questions'), list):
                    questions = [str(q).strip() for q in chunk_data['questions'] if q and str(q).strip()]
                
                confidence = 0.7
                if isinstance(chunk_data.get('confidence'), (int, float)):
                    confidence = float(chunk_data['confidence'])
                
                # Smart embedding reuse
                embedding = None
                for concept in concepts:
                    if concept in embeddings_cache:
                        embedding = embeddings_cache[concept]
                        break
                
                if not embedding:
                    try:
                        embedding = create_embedding_via_clova(
                            summary, 
                            CLOVA_API_KEY, 
                            CLOVA_EMBEDDING_URL
                        )
                        metrics.increment_embedding_calls(1)
                    except Exception as e:
                        metrics.add_warning(f"Embedding failed for chunk {i}, using zero vector", 'embedding_creation')
                        embedding = [0.0] * EMBEDDING_DIMENSION
                
                # Calculate semantic similarity
                semantic_sim = calculate_similarity(prev_embedding, embedding) if prev_embedding else 0.0
                
                # Create Qdrant chunk
                qdrant_chunk = QdrantChunk(
                    chunk_id=chunk_id,
                    paper_id=file_id,
                    page=chunk_idx + 1,
                    text=original_chunk.get("text", "")[:1000] if isinstance(original_chunk.get("text"), str) else "",
                    summary=summary,
                    concepts=concepts,
                    topic=topic,
                    workspace_id=workspace_id,
                    language="en",
                    source_language=language,
                    created_at=datetime.now().isoformat(),
                    hierarchy_path=f"{file_name} > Chunk {chunk_idx+1}",
                    chunk_index=chunk_idx,
                    prev_chunk_id=prev_chunk_id,
                    next_chunk_id="",
                    semantic_similarity_prev=semantic_sim,
                    overlap_with_prev=original_chunk.get("overlap_previous", "")[:200] if isinstance(original_chunk.get("overlap_previous"), str) else "",
                    key_claims=claims,
                    questions_raised=questions,
                    evidence_strength=confidence
                )
                
                all_chunks_with_embeddings.append((qdrant_chunk, embedding))
                
                # Update previous chunk linkage
                if prev_chunk_id:
                    for existing_chunk, _ in all_chunks_with_embeddings:
                        if existing_chunk.chunk_id == prev_chunk_id:
                            existing_chunk.next_chunk_id = chunk_id
                            break
                
                prev_chunk_id = chunk_id
                prev_embedding = embedding
            
            # Store in Qdrant
            if all_chunks_with_embeddings:
                qdrant_result = store_chunks_in_qdrant(
                    qdrant_client, workspace_id, all_chunks_with_embeddings,
                    batch_size=QDRANT_BATCH_SIZE, max_retries=MAX_RETRY_ATTEMPTS
                )
                
                if qdrant_result.get('success'):
                    processing_state['qdrant_processed'] = True
                    stored_count = qdrant_result['stats'].get('stored_count', 0)
                    print(f"✓ Stored {stored_count} chunks in Qdrant")
                else:
                    metrics.add_warning(f"Qdrant storage issues: {qdrant_result.get('error')}", 'vector_storage')
            else:
                print("⚠️ No chunks to store in Qdrant")
            
            metrics.add_phase('vector_storage')
            
        except Exception as e:
            metrics.add_error(str(e), 'vector_storage')
            metrics.add_warning("Vector storage failed", 'vector_storage')
        
        # PHASE 8: Resource Discovery (if enabled)
        if final_config['enable_resource_discovery']:
            print(f"\n🔍 Phase 8: Knowledge-Based Resource Discovery")
            try:
                with neo4j_driver.session() as session:
                    resource_count = discover_resources_via_knowledge_analysis(
                        session, workspace_id,
                        CLOVA_API_KEY, CLOVA_API_URL
                    )
                    metrics.increment_llm_calls(1)
                    metrics.metrics['resources_discovered'] = resource_count
                    print(f"✓ Discovered {resource_count} resource suggestions")
                
                metrics.add_phase('resource_discovery')
                
            except Exception as e:
                metrics.add_error(str(e), 'resource_discovery')
                metrics.add_warning("Resource discovery failed", 'resource_discovery')
        
        # Final cleanup and results compilation
        gc.collect()
        
        # Compile final results
        processing_time = metrics.get_processing_time()
        metrics_summary = metrics.get_summary()
        
        print(f"\n{'='*80}")
        print(f"✅ PROCESSING COMPLETED SUCCESSFULLY")
        print(f"⏱️  Total time: {processing_time}ms ({processing_time/1000:.1f}s)")
        print(f"\n📊 DETAILED METRICS:")
        print(f"├─ Phases completed: {len(metrics_summary['phases_completed'])}/8")
        print(f"├─ Embedding API calls: {metrics_summary['embedding_calls']}")
        print(f"├─ LLM API calls: {metrics_summary['llm_calls']}")
        print(f"├─ Translation requests: {metrics_summary['translation_requests']}")
        print(f"├─ Nodes created: {metrics_summary['nodes_created']}")
        print(f"├─ Nodes merged: {metrics_summary['nodes_merged']}")
        print(f"├─ Chunks processed: {metrics_summary['chunks_processed']}")
        print(f"├─ Resources discovered: {metrics_summary['resources_discovered']}")
        print(f"├─ Source language: {processing_state['language']}")
        print(f"├─ Structure quality: {'Good' if processing_state['structure_extracted'] else 'Fallback'}")
        print(f"└─ Success rate: {metrics_summary['success_rate']:.1%}")
        
        if metrics_summary['warnings']:
            print(f"\n⚠️  WARNINGS ({len(metrics_summary['warnings'])}):")
            for warning in metrics_summary['warnings'][:3]:  # Show first 3
                print(f"   • {warning['phase']}: {warning['warning']}")
        
        if metrics_summary['errors_encountered']:
            print(f"\n❌ ERRORS ({len(metrics_summary['errors_encountered'])}):")
            for error in metrics_summary['errors_encountered'][:3]:  # Show first 3
                print(f"   • {error['phase']}: {error['error']}")
        
        print(f"{'='*80}\n")
        
        return {
            "status": "completed",
            "jobId": job_id,
            "fileId": file_id,
            "workspaceId": workspace_id,
            "processingTimeMs": processing_time,
            "metrics": metrics_summary,
            "results": {
                "nodesTotal": len(node_ids),
                "nodesCreated": metrics_summary['nodes_created'],
                "nodesMerged": metrics_summary['nodes_merged'],
                "chunksStored": len(all_chunks_with_embeddings),
                "resourcesDiscovered": metrics_summary['resources_discovered'],
                "sourceLanguage": processing_state['language'],
                "structureQuality": "good" if processing_state['structure_extracted'] else "fallback",
                "phasesCompleted": metrics_summary['phases_completed']
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ PROCESSING FAILED: {error_msg}")
        
        if DEBUG_MODE:
            traceback.print_exc()
        
        # Cleanup partial data
        try:
            cleanup_partial_data(workspace_id, file_id, neo4j_driver, qdrant_client)
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup also failed: {cleanup_error}")
        
        return {
            "status": "failed",
            "jobId": job_id,
            "fileId": file_id,
            "error": error_msg,
            "phasesCompleted": metrics.metrics['phases_completed'],
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc() if DEBUG_MODE else "Hidden in production"
        }


def get_pipeline_status(workspace_id: str, file_id: str, neo4j_driver, qdrant_client) -> Dict[str, Any]:
    """
    Get status of processed pipeline results
    
    Args:
        workspace_id: Workspace identifier
        file_id: File identifier
        neo4j_driver: Neo4j driver instance
        qdrant_client: Qdrant client instance
    
    Returns:
        Pipeline status information
    """
    try:
        # Get Neo4j stats
        with neo4j_driver.session() as session:
            # Count KnowledgeNodes for this file
            node_result = session.run(
                """
                MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
                WHERE n.id STARTS WITH $file_prefix
                RETURN count(n) as node_count
                """,
                workspace_id=workspace_id,
                file_prefix=f"{file_id}-"
            )
            node_count = node_result.single()['node_count'] if node_result else 0
            
            # Count Evidence nodes
            evidence_result = session.run(
                """
                MATCH (e:Evidence {source_id: $file_id})
                RETURN count(e) as evidence_count
                """,
                file_id=file_id
            )
            evidence_count = evidence_result.single()['evidence_count'] if evidence_result else 0
            
            # Get resource discovery stats
            resource_stats = get_resource_discovery_stats(session, workspace_id)
        
        # Get Qdrant stats
        qdrant_stats = get_collection_stats(qdrant_client, workspace_id)
        
        return {
            "status": "available",
            "fileId": file_id,
            "workspaceId": workspace_id,
            "stats": {
                "knowledgeNodes": node_count,
                "evidenceNodes": evidence_count,
                "resourceSuggestions": resource_stats.get('total_suggestions', 0),
                "vectorChunks": qdrant_stats.get('vectors_count', 0) if isinstance(qdrant_stats, dict) else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "fileId": file_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Export main function
__all__ = ['process_pdf_to_knowledge_graph', 'get_pipeline_status', 'PipelineMetrics']