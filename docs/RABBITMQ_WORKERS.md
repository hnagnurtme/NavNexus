# RabbitMQ Worker System - Implementation Guide

## Overview

This implementation provides a **scalable Python worker system** that processes PDF documents through a comprehensive NLP pipeline using RabbitMQ for job distribution and Firebase Realtime Database for result storage.

## System Architecture

```
┌──────────────────┐
│   Frontend/API   │
│                  │
└────────┬─────────┘
         │ Publishes job
         ▼
┌──────────────────┐
│    RabbitMQ      │
│ pdf_jobs_queue   │
└────────┬─────────┘
         │
         ├────────────────┐
         │                │
         ▼                ▼
    ┌────────┐      ┌────────┐
    │Worker 1│ ...  │Worker 5│
    └───┬────┘      └───┬────┘
        │               │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │   Pipeline    │
        │               │
        │ 1. Extract    │
        │ 2. Chunk      │
        │ 3. Analyze    │
        │ 4. Translate  │
        │ 5. Embed      │
        │ 6. Graph      │
        │ 7. Store      │
        └───────┬───────┘
                │
        ┌───────┴────────────┐
        ▼                    ▼
    ┌────────┐          ┌─────────┐
    │ Neo4j  │          │ Qdrant  │
    │ Graph  │          │ Vector  │
    └───┬────┘          └────┬────┘
        │                    │
        └────────┬───────────┘
                 ▼
         ┌──────────────┐
         │   Firebase   │
         │   Results    │
         └──────────────┘
```

## Core Components

### 1. Worker (`worker.py`)

The main worker process that:
- Connects to RabbitMQ and listens to `pdf_jobs_queue`
- Processes incoming job messages
- Orchestrates the entire pipeline
- Handles errors and pushes results to Firebase

**Key Features:**
- Auto-reconnect to RabbitMQ on connection loss
- Graceful shutdown handling
- Comprehensive logging
- Message acknowledgment for reliability

### 2. Pipeline Modules (`src/pipeline/`)

Modular processing steps extracted from the monolithic `main_pipeline.py`:

#### a. `pdf_extraction.py`
- Downloads PDF from URL
- Extracts text using PyMuPDF
- Detects document language (Korean, Japanese, Chinese, English)
- Handles up to 25 pages by default

#### b. `chunking.py`
- Creates smart, overlapping text chunks
- Maintains semantic boundaries (paragraph-based)
- Configurable chunk size (default: 2000 chars)
- Overlap for context (default: 400 chars)

#### c. `embedding.py`
- Generates 384-dimensional embeddings using CLOVA API
- Fallback to hash-based embeddings if API fails
- Calculates cosine similarity between chunks
- Normalized vectors for consistent similarity scores

#### d. `translation.py`
- Translates non-English content to English using Papago API
- Batch translation support
- Handles long texts by splitting
- Graceful degradation if API unavailable

#### e. `llm_analysis.py`
- Extracts hierarchical document structure using CLOVA LLM
- Analyzes chunks for concepts, claims, and questions
- Batch processing for efficiency
- JSON extraction from LLM responses

#### f. `neo4j_graph.py`
- Creates hierarchical knowledge graph
- Merges concepts across multiple documents
- Stores evidence from multiple sources
- Updates synthesis when new evidence arrives
- 4-level hierarchy: Domain → Category → Concept → Subconcept

#### g. `qdrant_storage.py`
- Stores chunks with embeddings in Qdrant
- Creates collections per workspace
- Batch upload for efficiency
- Indexes for fast retrieval

### 3. Data Models (`src/model/`)

Existing models reused from the original implementation:

- **Evidence**: Represents evidence from a specific source
- **KnowledgeNode**: Multi-level knowledge node with evidence
- **QdrantChunk**: Chunk with metadata for vector storage

### 4. Supporting Services

#### RabbitMQ Client (`src/rabbitmq_client.py`)
- Handles connection to RabbitMQ
- Supports both URL and dictionary configuration
- Message publishing and consuming
- Automatic message acknowledgment

#### Firebase Client (`src/handler/firebase.py`)
- Pushes job results to Firebase Realtime Database
- Uses jobId as key for easy tracking
- Stores both success and error results

## Message Flow

### Input Message Format

```json
{
  "jobId": "unique-job-identifier",
  "workspaceId": "workspace-123",
  "filePaths": [
    "https://storage.example.com/document1.pdf",
    "https://storage.example.com/document2.pdf"
  ]
}
```

**Important**: Only the **first file** in `filePaths` is processed.

### Output Result Format

**Success:**
```json
{
  "status": "completed",
  "jobId": "unique-job-identifier",
  "fileId": "generated-file-uuid",
  "nodes": 45,
  "chunks": 12,
  "sourceLanguage": "ko",
  "processingTimeMs": 15420
}
```

**Failure:**
```json
{
  "status": "failed",
  "jobId": "unique-job-identifier",
  "error": "PDF extraction failed: Connection timeout",
  "traceback": "Full Python traceback..."
}
```

## Processing Pipeline Details

### Phase 1: PDF Extraction
1. Download PDF from URL
2. Extract text from up to 25 pages
3. Detect language from content
4. Return full text and language code

### Phase 2: Structure Extraction
1. Send first 3000 chars to LLM
2. Extract hierarchical structure (domain → categories → concepts → subconcepts)
3. Translate structure to English if needed
4. Store structure for graph creation

### Phase 3: Knowledge Graph Creation
1. Create/merge domain node in Neo4j
2. Create/merge category nodes and link to domain
3. Create/merge concept nodes and link to categories
4. Create/merge subconcept nodes and link to concepts
5. Add evidence to each node
6. Update synthesis by merging perspectives

### Phase 4: Chunk Processing
1. Create smart chunks with overlap
2. Process chunks in batches of 3
3. For each chunk:
   - Extract concepts, claims, questions
   - Translate to English if needed
   - Link chunk concepts to graph nodes
   - Add chunk as evidence to nodes
   - Generate embedding
   - Calculate similarity with previous chunk
4. Build linked list of chunks (prev/next references)

### Phase 5: Vector Storage
1. Ensure Qdrant collection exists for workspace
2. Create PointStruct for each chunk with embedding
3. Batch upload all chunks to Qdrant
4. Index by workspace_id for filtering

## Configuration

### Environment Variables

**Required:**
- `RABBITMQ_HOST`: RabbitMQ server host
- `RABBITMQ_USERNAME`: RabbitMQ username
- `RABBITMQ_PASSWORD`: RabbitMQ password
- `CLOVA_API_KEY`: CLOVA AI API key
- `NEO4J_PASSWORD`: Neo4j database password
- `QDRANT_API_KEY`: Qdrant API key

**Optional (with defaults):**
- `RABBITMQ_VHOST`: Virtual host (default: odgfvgev)
- `PAPAGO_CLIENT_ID`: Papago translation client ID
- `PAPAGO_CLIENT_SECRET`: Papago translation secret
- `QDRANT_URL`: Qdrant instance URL
- `NEO4J_URL`: Neo4j instance URL
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `FIREBASE_DATABASE_URL`: Firebase database URL
- `MAX_CHUNKS`: Maximum chunks per document (default: 12)
- `CHUNK_SIZE`: Characters per chunk (default: 2000)
- `OVERLAP`: Overlap between chunks (default: 400)

### Firebase Service Account

Place `serviceAccountKey.json` in the `RabbitMQ/` directory. This file contains Firebase credentials.

## Deployment

### Docker Compose (Recommended)

1. **Configure environment:**
   ```bash
   cp RabbitMQ/.env.example RabbitMQ/.env
   # Edit .env with your credentials
   ```

2. **Add Firebase credentials:**
   ```bash
   # Place serviceAccountKey.json in RabbitMQ/
   ```

3. **Run workers:**
   ```bash
   docker-compose -f docker-compose.workers.yml up --build
   ```

4. **Scale workers (optional):**
   ```bash
   docker-compose -f docker-compose.workers.yml up --scale worker-1=10
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   cd RabbitMQ
   pip install -r requirements.txt
   ```

2. **Set environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   source .env
   ```

3. **Run worker:**
   ```bash
   python worker.py
   ```

### Using Development Helper

```bash
cd RabbitMQ

# Install dependencies
./dev.sh install

# Check syntax
./dev.sh check

# Run worker locally
./dev.sh worker

# Publish test message
./dev.sh test

# Run with Docker Compose
./dev.sh compose
```

## Testing

### Manual Test

1. **Start workers:**
   ```bash
   docker-compose -f docker-compose.workers.yml up
   ```

2. **Publish test message:**
   ```bash
   cd RabbitMQ
   python test_publisher.py
   ```

3. **Monitor logs:**
   ```bash
   docker-compose -f docker-compose.workers.yml logs -f worker-1
   ```

4. **Check Firebase:**
   - Navigate to Firebase Console
   - Open Realtime Database
   - Look for `job_results/{jobId}`

### Integration Test

Use the frontend or API to:
1. Create a workspace
2. Upload a PDF document
3. Trigger processing job
4. Monitor job status in Firebase
5. Query results from Neo4j and Qdrant

## Monitoring and Debugging

### Log Levels

Workers log at different levels:
- **INFO**: Normal operation (job received, phase started, phase completed)
- **WARNING**: Non-fatal issues (translation API unavailable, using fallback)
- **ERROR**: Fatal errors (PDF extraction failed, database connection lost)

### Common Issues

1. **Worker not connecting to RabbitMQ:**
   - Check `RABBITMQ_HOST`, `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`
   - Verify network connectivity
   - Check RabbitMQ server status

2. **Firebase authentication error:**
   - Verify `serviceAccountKey.json` is present and valid
   - Check `FIREBASE_DATABASE_URL`
   - Ensure Firebase Realtime Database is enabled

3. **Neo4j connection timeout:**
   - Verify `NEO4J_URL` format: `neo4j+ssc://...`
   - Check credentials
   - Ensure Neo4j database is running

4. **Out of memory:**
   - Reduce `MAX_CHUNKS`
   - Reduce `CHUNK_SIZE`
   - Increase Docker memory limit
   - Process fewer workers concurrently

5. **CLOVA API rate limit:**
   - Reduce number of workers
   - Implement exponential backoff
   - Contact CLOVA support for rate limit increase

## Performance Optimization

### Recommended Settings

**For small documents (<10 pages):**
- `MAX_CHUNKS=8`
- `CHUNK_SIZE=1500`
- `OVERLAP=300`

**For large documents (>20 pages):**
- `MAX_CHUNKS=15`
- `CHUNK_SIZE=2500`
- `OVERLAP=500`

**Worker scaling:**
- 1-2 workers: Development
- 3-5 workers: Production (low load)
- 5-10 workers: Production (high load)
- 10+ workers: Enterprise (requires API rate limit increase)

### Database Optimization

**Neo4j:**
- Index on `workspace_id` and `type`
- Regular cleanup of old/unused nodes
- Monitor query performance

**Qdrant:**
- Use workspace-specific collections
- Enable payload indexing on `workspace_id`
- Regular backup of collections

## Security Considerations

1. **Never commit credentials:**
   - Use `.env` for local development
   - Use environment variables in production
   - Add `.env` to `.gitignore`

2. **Firebase service account:**
   - Keep `serviceAccountKey.json` secure
   - Add to `.gitignore`
   - Use secret management in production

3. **Database access:**
   - Use strong passwords
   - Enable SSL/TLS for connections
   - Restrict network access to databases

4. **API keys:**
   - Rotate regularly
   - Monitor usage for anomalies
   - Implement rate limiting

## Future Enhancements

- [ ] Add retry logic with exponential backoff
- [ ] Implement dead letter queue for failed jobs
- [ ] Add metrics collection (Prometheus/Grafana)
- [ ] Support for multiple file processing
- [ ] Webhook notifications on job completion
- [ ] Priority queues for urgent jobs
- [ ] Horizontal pod autoscaling for Kubernetes
- [ ] Distributed tracing with OpenTelemetry

## Troubleshooting

See `RabbitMQ/README.md` for detailed troubleshooting steps.

## License

See root LICENSE file.
