# RabbitMQ Worker System

This directory contains a scalable Python worker system for processing PDF documents using RabbitMQ and Firebase Realtime Database.

## Architecture

The system consists of:
- **5 Worker Instances**: Dockerized workers that process jobs concurrently
- **RabbitMQ Queue**: Queue named `pdf_jobs_queue` for job distribution
- **Pipeline Modules**: Modular processing steps for PDF analysis
- **Firebase**: Real-time job result storage

## Pipeline Steps

The worker processes PDFs through the following pipeline:

1. **PDF Extraction** (`src/pipeline/pdf_extraction.py`)
   - Downloads and extracts text from PDF
   - Detects document language (Korean, Japanese, Chinese, English)

2. **Smart Chunking** (`src/pipeline/chunking.py`)
   - Creates overlapping text chunks for better context
   - Maintains semantic boundaries

3. **LLM Analysis** (`src/pipeline/llm_analysis.py`)
   - Extracts hierarchical structure (domain → categories → concepts → subconcepts)
   - Analyzes chunks for concepts, claims, and questions

4. **Translation** (`src/pipeline/translation.py`)
   - Translates non-English content using Papago API

5. **Embedding Generation** (`src/pipeline/embedding.py`)
   - Creates 384-dimensional embeddings using CLOVA API
   - Calculates semantic similarity between chunks

6. **Neo4j Graph** (`src/pipeline/neo4j_graph.py`)
   - Creates hierarchical knowledge graph
   - Merges concepts across multiple documents
   - Stores evidence from multiple sources

7. **Qdrant Storage** (`src/pipeline/qdrant_storage.py`)
   - Stores chunks with embeddings in vector database
   - Enables semantic search

## Message Format

Workers listen for messages in this format:

```json
{
  "jobId": "unique-job-id",
  "workspaceId": "workspace-123",
  "filePaths": [
    "https://example.com/document.pdf",
    "https://example.com/another.pdf"
  ]
}
```

**Note**: Only the **first file** in `filePaths` is processed per job.

## Environment Variables

Required environment variables:

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=chameleon-01.lmq.cloudamqp.com
RABBITMQ_USERNAME=odgfvgev
RABBITMQ_PASSWORD=your-password
RABBITMQ_VHOST=odgfvgev

# API Keys
PAPAGO_CLIENT_ID=your-papago-client-id
PAPAGO_CLIENT_SECRET=your-papago-secret
CLOVA_API_KEY=your-clova-api-key

# Databases
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
NEO4J_URL=neo4j+ssc://your-neo4j-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Firebase
FIREBASE_DATABASE_URL=https://your-firebase.firebaseio.com/
```

## Running the Workers

### Using Docker Compose (Recommended)

1. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Ensure `serviceAccountKey.json` is in the RabbitMQ directory

3. Run 5 worker instances:
```bash
docker-compose -f docker-compose.workers.yml up --build
```

4. Scale workers (optional):
```bash
docker-compose -f docker-compose.workers.yml up --scale worker-1=10
```

### Running Locally

1. Install dependencies:
```bash
cd RabbitMQ
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export RABBITMQ_HOST=your-host
export CLOVA_API_KEY=your-key
# ... other variables
```

3. Run worker:
```bash
python worker.py
```

## Firebase Result Format

Results are pushed to Firebase at `job_results/{jobId}`:

```json
{
  "jobId": "unique-job-id",
  "status": "completed",
  "fileId": "generated-file-id",
  "nodes": 45,
  "chunks": 12,
  "sourceLanguage": "ko",
  "processingTimeMs": 15420
}
```

On error:
```json
{
  "jobId": "unique-job-id",
  "status": "failed",
  "error": "Error message",
  "traceback": "Full traceback..."
}
```

## Pipeline Configuration

Configurable via environment variables:

```bash
MAX_CHUNKS=12        # Maximum chunks to process per document
CHUNK_SIZE=2000      # Characters per chunk
OVERLAP=400          # Overlap between chunks
```

## Monitoring

Each worker logs:
- Job receipt and processing status
- Pipeline phase progress
- Processing time and statistics
- Errors and warnings

View logs:
```bash
docker-compose -f docker-compose.workers.yml logs -f worker-1
```

## Architecture Diagram

```
┌─────────────┐
│  RabbitMQ   │
│   Queue     │
└──────┬──────┘
       │
       ├───→ Worker 1 ──┐
       ├───→ Worker 2 ──┤
       ├───→ Worker 3 ──┼──→ Pipeline → Neo4j + Qdrant
       ├───→ Worker 4 ──┤
       └───→ Worker 5 ──┘
                │
                └──→ Firebase (Results)
```

## Development

### Adding New Pipeline Steps

1. Create module in `src/pipeline/`
2. Import in `worker.py`
3. Add to processing function
4. Update this README

### Testing

Test with a sample message:
```python
from src.rabbitmq_client import RabbitMQClient

client = RabbitMQClient(RABBITMQ_CONFIG)
client.connect()
client.publish_message("pdf_jobs_queue", {
    "jobId": "test-123",
    "workspaceId": "ws-test",
    "filePaths": ["https://example.com/test.pdf"]
})
```

## Troubleshooting

### Worker not connecting to RabbitMQ
- Check `RABBITMQ_HOST`, `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`
- Verify network connectivity

### Firebase errors
- Ensure `serviceAccountKey.json` exists and is valid
- Check `FIREBASE_DATABASE_URL`

### Neo4j connection issues
- Verify `NEO4J_URL` format: `neo4j+ssc://...`
- Check credentials and network access

### Out of memory
- Reduce `MAX_CHUNKS`
- Reduce `CHUNK_SIZE`
- Increase Docker memory limit

## License

See root LICENSE file.
