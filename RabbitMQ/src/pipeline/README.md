# Pipeline Module Documentation

This document provides an overview of the functions available in the `src/pipeline` module, detailing their purpose, parameters, and return types.

## `translation.py`

### `validate_language_codes`

Validate if language codes are supported by Papago

**Parameters:**
- `source`: Source language code
- `target`: Target language code
**Returns:** `bool`
: 

### `split_text_semantically`

Split text at semantic boundaries (sentences, paragraphs) instead of fixed length

**Parameters:**
- `text`: Text to split
- `max_length`: Maximum length per chunk
**Returns:** `List[str]`
: List of semantically split text chunks

### `translate_with_retry`

Translate single text with retry logic and proper error handling

**Parameters:**
- `text`: Text to translate
- `source`: Source language code
- `target`: Target language code
- `papago_client_id`: Papago API client ID
- `papago_client_secret`: Papago API secret
- `max_retries`: Maximum retry attempts
- `retry_delay`: Delay between retries in seconds
**Returns:** `Optional[str]`
: Translated text or None if failed

### `translate_batch_enhanced`

Enhanced batch translation with better error handling and rate limiting

**Parameters:**
- `texts`: List of texts to translate
- `source`: Source language code
- `target`: Target language code
- `papago_client_id`: Papago API client ID
- `papago_client_secret`: Papago API secret
- `max_workers`: Maximum concurrent translations (for future async implementation)
**Returns:** `List[str]`
: List of translated texts (original text if translation failed)

### `translate_structure_enhanced`

Enhanced structure translation with better error handling

**Parameters:**
- `structure`: Hierarchical structure to translate
- `source`: Source language code
- `target`: Target language code
- `papago_client_id`: Papago API client ID
- `papago_client_secret`: Papago API secret
**Returns:** `Dict[str, Any]`
: Translated structure with metadata

### `translate_chunk_analysis_enhanced`

Enhanced chunk analysis translation with metadata

**Parameters:**
- `chunk_data`: Chunk analysis data
- `source`: Source language code
- `target`: Target language code
- `papago_client_id`: Papago API client ID
- `papago_client_secret`: Papago API secret
**Returns:** `Dict[str, Any]`
: Translated chunk analysis with metadata

### `get_translation_supported_languages`

Get dictionary of supported language codes and their names

**Parameters:**

**Returns:** `Dict[str, str]`
: 

## `resource_discovery.py`

### `create_gap_suggestion_node`

Create a GapSuggestion node in Neo4j with proper transaction handling

**Parameters:**
- `session`: Any
- `gap`: GapSuggestion
- `target_node_id`: str
**Returns:** `str`
: 

### `validate_academic_url`

Validate if URL looks like a legitimate academic source

**Parameters:**
- `url`: str
**Returns:** `bool`
: 

### `generate_research_queries`

Generate specific search queries for academic resources

**Parameters:**
- `node_name`: str
- `synthesis`: str
**Returns:** `List[str]`
: Return top 5 queries

### `call_hyperclova_for_resource_suggestions`

Use HyperCLOVA to suggest relevant academic resources based on knowledge

**Parameters:**
- `node_name`: str
- `synthesis`: str
- `max_tokens`: int
- `api_key`: str
- `api_url`: str
**Returns:** `List[Dict[str, str]]`
: 

### `discover_resources_via_knowledge_analysis`

Practical resource discovery using knowledge graph analysis

**Parameters:**
- `session`: Any
- `workspace_id`: str
- `clova_api_key`: str
- `clova_api_url`: str
**Returns:** `int`
: Number of suggestions created

### `suggest_cross_domain_resources`

Identify potential interdisciplinary research opportunities

**Parameters:**
- `session`: Any
- `workspace_id`: str
**Returns:** `int`
: 

### `get_resource_discovery_stats`

Get statistics about resource discovery suggestions

**Parameters:**
- `session`: Any
- `workspace_id`: str
**Returns:** `Dict[str, Any]`
: 

## `qdrant_storage.py`

### `ensure_collection_exists`

Ensure Qdrant collection exists with proper configuration

**Parameters:**
- `qdrant_client`: QdrantClient
- `workspace_id`: Workspace identifier
- `vector_size`: Expected vector dimension
**Returns:** `str`
: Collection name

### `validate_embedding`

Validate embedding dimensions and values

**Parameters:**
- `embedding`: List[float]
- `expected_size`: int
**Returns:** `bool`
: 

### `store_chunks_in_qdrant`

Store chunks with embeddings in Qdrant with enhanced error handling

**Parameters:**
- `qdrant_client`: QdrantClient
- `workspace_id`: Workspace identifier
- `chunks_with_embeddings`: List[Tuple[QdrantChunk, List[float]]]
- `batch_size`: Number of points to upsert in one batch
- `max_retries`: Maximum number of retry attempts
**Returns:** `Dict[str, Any]`
: Dictionary with operation results and statistics

### `search_similar_chunks`

Search for similar chunks in Qdrant

**Parameters:**
- `qdrant_client`: QdrantClient
- `workspace_id`: Workspace identifier
- `query_embedding`: Query embedding vector
- `limit`: Maximum number of results
- `score_threshold`: Minimum similarity score
- `filter_by_paper_id`: Optional paper ID filter
**Returns:** `List[Dict[str, Any]]`
: List of search results with scores and payloads

### `get_collection_stats`

Get statistics for a workspace collection

**Parameters:**
- `qdrant_client`: QdrantClient
- `workspace_id`: Workspace identifier
**Returns:** `Dict[str, Any]`
: Collection statistics

### `delete_workspace_collection`

Delete a workspace collection

**Parameters:**
- `qdrant_client`: QdrantClient
- `workspace_id`: Workspace identifier
**Returns:** `bool`
: Success status

## `pdf_extraction.py`

### `extract_pdf_enhanced`

Enhanced PDF extraction with better text processing and language detection

**Parameters:**
- `pdf_url`: URL of the PDF file
- `max_pages`: Maximum number of pages to extract
- `timeout`: Request timeout in seconds
- `chunk_size`: Download chunk size
**Returns:** `Tuple[str, str, Dict]`
: Tuple of (full_text, detected_language, metadata)

### `download_pdf_with_progress`

Download PDF with progress tracking and error handling

**Parameters:**
- `pdf_url`: str
- `timeout`: int
- `chunk_size`: int
**Returns:** `Optional[io.BytesIO]`
: 

### `extract_text_from_pdf`

Extract text from PDF using multiple strategies

**Parameters:**
- `pdf_bytes`: io.BytesIO
- `max_pages`: int
**Returns:** `Dict`
: 

### `clean_page_text`

Clean and format text from a single page

**Parameters:**
- `text`: str
- `page_num`: int
**Returns:** `str`
: 

### `clean_extracted_text`

Final cleaning of extracted text

**Parameters:**
- `text`: str
**Returns:** `str`
: 

### `detect_language_enhanced`

Enhanced language detection with confidence scoring

**Parameters:**
- `text`: str
**Returns:** `Dict`
: Dict with 'language' and 'confidence'

### `get_pdf_metadata`

Extract PDF metadata if available

**Parameters:**
- `pdf_bytes`: io.BytesIO
**Returns:** `Dict`
: 

## `chunking.py`

### `create_smart_chunks`

Create overlapping chunks with semantic boundaries

**Parameters:**
- `text`: Input text to chunk
- `chunk_size`: Target chunk size in characters
- `overlap`: Overlap size between chunks
- `min_chunk_size`: Minimum chunk size to avoid too small chunks
**Returns:** `List[Dict]`
: List of chunk dictionaries with text and metadata

### `get_semantic_overlap`

Extract overlap text that respects semantic boundaries

**Parameters:**
- `text`: Text to extract overlap from
- `overlap_size`: Target overlap size in characters
**Returns:** `str`
: Overlap text that ends at sentence/paragraph boundary

### `merge_small_chunks`

Merge chunks that are too small with their neighbors

**Parameters:**
- `chunks`: List of chunk dictionaries
- `min_size`: Minimum chunk size requirement
**Returns:** `List[Dict]`
: Merged chunks list

### `calculate_chunk_stats`

Calculate statistics about chunks

**Parameters:**
- `chunks`: List of chunk dictionaries
**Returns:** `Dict`
: Dictionary with chunk statistics

## `embedding.py`

### `create_embedding_via_clova`

Create 384-dim embedding using CLOVA API

**Parameters:**
- `text`: str
- `clova_api_key`: str
- `clova_embedding_url`: str
**Returns:** `List[float]`
: 

### `create_hash_embedding`

Fallback: Deterministic embedding from text hash

**Parameters:**
- `text`: str
- `dim`: int
**Returns:** `List[float]`
: 

### `calculate_similarity`

Cosine similarity

**Parameters:**
- `vec1`: List[float]
- `vec2`: List[float]
**Returns:** `float`
: 

## `embedding_cache.py`

### `extract_all_concept_names`

Extract all unique concept names from hierarchical structure

**Parameters:**
- `structure`: Hierarchical structure dict with domain, categories, concepts, subconcepts
**Returns:** `List[str]`
: List of unique concept names

### `batch_create_embeddings`

Create embeddings for multiple texts in batches with deduplication

**Parameters:**
- `texts`: List[str]
- `clova_api_key`: API key for CLOVA
- `clova_embedding_url`: URL for embedding API
- `batch_size`: Number of texts to process at once (default 50)
**Returns:** `Dict[str, List[float]]`
: Dictionary mapping text -> embedding vector

## `llm_analysis.py`

### `extract_json_from_text`

Extract JSON from LLM response

**Parameters:**
- `text`: str
**Returns:** `Dict[str, Any]`
: 

### `call_llm_merge_optimized`

LLM call optimized for merging

**Parameters:**
- `prompt`: str
- `max_tokens`: int
- `clova_api_key`: str
- `clova_api_url`: str
**Returns:** `Any`
: 

### `extract_merge_optimized_structure`

Structure extraction tối ưu cho merging

**Parameters:**
- `full_text`: str
- `file_name`: str
- `lang`: str
- `clova_api_key`: str
- `clova_api_url`: str
**Returns:** `Dict`
: 

### `analyze_chunks_for_merging`

Phân tích chunks với focus TỐI ĐA trên merging

**Parameters:**
- `chunks`: List[Dict]
- `structure`: Dict
- `clova_api_key`: str
- `clova_api_url`: str
**Returns:** `Dict[str, List[List[str]]]`
: 

### `identify_merge_candidates`

Phân tích merge candidates giữa existing nodes và new structure

**Parameters:**
- `existing_nodes`: List[Dict]
- `new_structure`: Dict
- `clova_api_key`: str
- `clova_api_url`: str
**Returns:** `Dict[str, List[List[str]]]`
: 

## `neo4j_graph.py`

### `now_iso`

**Parameters:**

**Returns:** `Any`
: 

### `find_best_match`

Cascading search: Exact → Very High (>0.90) → High (>0.80) → Medium (>0.70)

**Parameters:**
- `session`: Any
- `workspace_id`: str
- `concept_name`: str
- `embedding`: List[float]
**Returns:** `Optional[Dict[str, Any]]`
: 

### `create_evidence_node`

Create a separate Evidence node with all fields

**Parameters:**
- `session`: Any
- `evidence`: Evidence
**Returns:** `str`
: 

### `create_gap_suggestion_node`

Create a separate GapSuggestion node and link to KnowledgeNode

**Parameters:**
- `session`: Any
- `gap_suggestion`: GapSuggestion
- `knowledge_node_id`: str
**Returns:** `None`
: 

### `create_knowledge_node`

Create KnowledgeNode with linked Evidence node

**Parameters:**
- `session`: Any
- `knowledge_node`: KnowledgeNode
- `evidence`: Evidence
- `embedding`: List[float]
**Returns:** `str`
: 

### `update_knowledge_node_after_merge`

Update KnowledgeNode after merging with new evidence

**Parameters:**
- `session`: Any
- `node_id`: str
- `new_synthesis`: str
- `source_name`: str
**Returns:** `None`
: 

### `create_or_merge_knowledge_node`

Create new KnowledgeNode or merge into existing with proper entity structure

**Parameters:**
- `session`: Neo4j session
- `workspace_id`: Workspace ID
- `knowledge_node`: KnowledgeNode object
- `evidence`: Evidence object
- `embedding`: Pre-computed embedding vector
**Returns:** `Optional[str]`
: Node ID (str) or None if failed

### `create_parent_child_relationship`

Create hierarchical relationship between KnowledgeNodes

**Parameters:**
- `session`: Any
- `parent_id`: str
- `child_id`: str
- `relationship_type`: str
**Returns:** `None`
: 

### `create_hierarchical_knowledge_graph`

Create hierarchical knowledge graph with proper entity structure

**Parameters:**
- `session`: Neo4j session
- `workspace_id`: Workspace ID
- `structure`: Hierarchical structure from LLM
- `file_id`: Source file ID
- `file_name`: Source file name
- `embeddings_cache`: Pre-computed embeddings {name: vector}
**Returns:** `Dict[str, Any]`
: Dict with statistics about node creation/merging

### `add_gap_suggestions_to_node`

Add GapSuggestion nodes to a KnowledgeNode

**Parameters:**
- `session`: Any
- `knowledge_node_id`: str
- `gap_suggestions`: List[GapSuggestion]
**Returns:** `None`
: 

### `get_knowledge_node_with_evidence`

Retrieve KnowledgeNode with all its Evidence nodes

**Parameters:**
- `session`: Any
- `node_id`: str
**Returns:** `Optional[Tuple[KnowledgeNode, List[Evidence]]]`
: 
