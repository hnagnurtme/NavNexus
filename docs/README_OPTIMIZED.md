# 🚀 Optimized PDF Knowledge Graph Worker

## Overview
Worker xử lý PDF thành knowledge graph với **10-15 LLM calls**, sử dụng **Recursive Expansion Pipeline** và **LLM-powered Gap Suggestions**.

---

## 🎯 Key Features

### ✅ Optimized Pipeline
- **Single recursive flow** thay vì 3-stage phức tạp
- **10-15 LLM calls/PDF** (giảm 50% so với trước)
- **Position-based evidence extraction** (paragraph-level)
- **Quality filters** loại bỏ low-quality nodes

### ✅ Smart Gap Suggestions
- **Batch processing**: 5 nodes/call thay vì 1 node/call
- **LLM-generated suggestions** với specific research directions
- **Target URLs** cho arxiv.org, scholar.google.com
- **Similarity scores** tính toán bởi LLM

### ✅ Production Ready
- **Graceful error handling** với fallbacks
- **Real-time Firebase updates**
- **Comprehensive logging**
- **Metrics tracking** (LLM calls, processing time, quality)

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Code Size** | 772 lines (giảm 63%) |
| **LLM Calls** | 10-15/PDF (giảm 50%) |
| **Processing Speed** | ~30-40s/PDF (nhanh hơn 50%) |
| **Gap Quality** | 100% LLM-powered |
| **Memory Usage** | <1GB/worker |

---

## 🔧 Installation

### 1. Dependencies
```bash
pip install neo4j firebase-admin pika requests
```

### 2. Environment Variables
```bash
export NEO4J_URL="neo4j+s://your-db.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"

export RABBITMQ_HOST="your-rabbitmq-host.cloudamqp.com"
export RABBITMQ_USERNAME="your-username"
export RABBITMQ_PASSWORD="your-password"

export CLOVA_API_KEY="nv-your-api-key"
export CLOVA_API_URL="https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005"

export FIREBASE_SERVICE_ACCOUNT="serviceAccountKey.json"
export FIREBASE_DATABASE_URL="https://your-project.firebaseio.com/"
```

### 3. Run Worker
```bash
cd RabbitMQ
python worker.py
```

---

## 📖 Usage

### Send Job via RabbitMQ
```python
import pika
import json

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters('your-rabbitmq-host')
)
channel = connection.channel()

# Send job
message = {
    "JobId": "job-12345",
    "WorkspaceId": "workspace-abc",
    "FilePaths": [
        "https://arxiv.org/pdf/2101.00001.pdf",
        "https://example.com/research-paper.pdf"
    ]
}

channel.basic_publish(
    exchange='',
    routing_key='PDF_JOBS_QUEUE',
    body=json.dumps(message)
)

print("✅ Job sent!")
connection.close()
```

### Response (via Firebase)
```json
{
  "status": "completed",
  "workspaceId": "workspace-abc",
  "totalFiles": 2,
  "successful": 2,
  "failed": 0,
  "processingTimeMs": 68400,
  "results": [
    {
      "status": "success",
      "file_name": "2101.00001.pdf",
      "nodes_created": 12,
      "evidences_created": 18,
      "gaps_created": 8,
      "quality_metrics": {
        "llm_calls": 11,
        "llm_calls_breakdown": {
          "domain_extraction": 1,
          "recursive_expansion": 8,
          "gap_suggestions": 2
        }
      }
    },
    {
      "status": "success",
      "file_name": "research-paper.pdf",
      "nodes_created": 15,
      "gaps_created": 10,
      "quality_metrics": {
        "llm_calls": 13
      }
    }
  ]
}
```

---

## 🌳 Knowledge Graph Structure

```
Domain (Level 0)
└─ Category 1 (Level 1)
   ├─ Concept 1.1 (Level 2)
   │  ├─ Subconcept 1.1.1 (Level 3) ← Leaf node
   │  │  └─ Gap Suggestion: "Explore X in context Y"
   │  └─ Subconcept 1.1.2 (Level 3) ← Leaf node
   │     └─ Gap Suggestion: "Investigate Z approach"
   └─ Concept 1.2 (Level 2)
      └─ Subconcept 1.2.1 (Level 3) ← Leaf node
         └─ Gap Suggestion: "Compare A vs B methods"
```

**Depth**: 3-4 levels (domain → category → concept → subconcept)
**Width**: Max 3 children per node
**Evidence**: Every node has ≥1 evidence with position-based text

---

## 🎯 LLM Call Budget

### Typical 12-Call Breakdown
```
1. Domain Extraction:       1 call
2. Recursive Expansion:      8 calls
   ├─ Level 1 (categories):  1 call  → 3 nodes
   ├─ Level 2 (concepts):    3 calls → 9 nodes
   └─ Level 3 (subconcepts): 4 calls → 12 nodes
3. Gap Suggestions:          3 calls
   └─ 15 leaf nodes / 5 batch_size = 3 calls

Total: 12 calls ✅
```

### Budget Configuration
```python
# In run_recursive_expansion_pipeline()
MAX_DEPTH = 3          # 0=domain, 1=category, 2=concept, 3=subconcept
MAX_CHILDREN = 3       # Max 3 children per node
MIN_CONTENT = 800      # Min 800 chars to expand further

# In generate_gap_suggestions_batch()
BATCH_SIZE = 5         # Process 5 leaf nodes per LLM call
```

---

## 📝 Gap Suggestion Examples

### Input (5 leaf nodes)
```
[1] ID: subconcept-a1b2, Name: "Dueling DQN Architecture", Synthesis: "Value-advantage stream separation..."
[2] ID: subconcept-c3d4, Name: "Solar Storm Prediction", Synthesis: "Predictive models for energy management..."
[3] ID: subconcept-e5f6, Name: "Experience Replay", Synthesis: "Buffer optimization techniques..."
[4] ID: subconcept-g7h8, Name: "Communication Protocols", Synthesis: "Inter-satellite bandwidth efficiency..."
[5] ID: subconcept-i9j0, Name: "Battery Degradation", Synthesis: "Cycle life modeling under thermal stress..."
```

### Output (1 LLM call)
```json
{
  "suggestions": [
    {
      "node_id": "subconcept-a1b2",
      "suggestion_text": "Explore value-advantage decomposition impact in non-stationary multi-agent environments",
      "target_url": "https://arxiv.org/search/?query=dueling+dqn+non-stationary+multi-agent",
      "similarity_score": 0.87
    },
    {
      "node_id": "subconcept-c3d4",
      "suggestion_text": "Investigate adaptive algorithms for real-time solar storm prediction in LEO satellites",
      "target_url": "https://scholar.google.com/scholar?q=solar+storm+prediction+satellite+energy",
      "similarity_score": 0.82
    },
    ... (3 more suggestions)
  ]
}
```

---

## 🔍 Neo4j Queries

### View Knowledge Graph
```cypher
MATCH path = (domain:KnowledgeNode {workspace_id: 'your-workspace', level: 0})
             -[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL*1..3]->(child)
RETURN path
LIMIT 100
```

### View Gap Suggestions
```cypher
MATCH (n:KnowledgeNode {workspace_id: 'your-workspace'})-[:HAS_SUGGESTION]->(g:GapSuggestion)
RETURN n.name as LeafNode,
       g.suggestion_text as Suggestion,
       g.target_url as URL,
       g.similarity_score as Score
ORDER BY g.similarity_score DESC
```

### Stats
```cypher
MATCH (n:KnowledgeNode {workspace_id: 'your-workspace'})
WITH n.level as Level, count(n) as Count
RETURN Level, Count
ORDER BY Level
```

---

## 🧪 Testing

### Quick Test
```bash
# 1. Start worker
python worker.py

# 2. In another terminal, send test message
python -c "
import pika, json
conn = pika.BlockingConnection(pika.ConnectionParameters('your-rabbitmq-host'))
ch = conn.channel()
ch.basic_publish('', 'PDF_JOBS_QUEUE', json.dumps({
    'JobId': 'test-001',
    'WorkspaceId': 'test-ws',
    'FilePaths': ['https://arxiv.org/pdf/2101.00001.pdf']
}))
conn.close()
print('✅ Test message sent!')
"

# 3. Monitor logs
tail -f new_worker.log
```

### Verify Results
```cypher
// Neo4j
MATCH (n:KnowledgeNode {workspace_id: 'test-ws'})
RETURN count(n)
// Expected: 10-15 nodes

MATCH (:KnowledgeNode {workspace_id: 'test-ws'})-[:HAS_SUGGESTION]->(g)
RETURN count(g)
// Expected: 5-10 gap suggestions
```

See [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for comprehensive tests.

---

## 📚 Documentation

- **[PIPELINE_OPTIMIZATION_SUMMARY.md](../PIPELINE_OPTIMIZATION_SUMMARY.md)**: Detailed refactor summary
- **[EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)**: Sample processing results
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)**: Complete testing guide

---

## 🐛 Troubleshooting

### Issue: "LLM calls exceed budget (>15)"
**Solution**: Adjust recursive expansion limits in [worker.py:502-504](worker.py#L502-L504):
```python
MAX_DEPTH = 2         # Reduce depth (was 3)
MAX_CHILDREN = 2      # Reduce children (was 3)
```

### Issue: "Gap suggestions are generic"
**Check**:
1. LLM API key is valid
2. Prompt in [worker.py:240-276](worker.py#L240-L276) is correct
3. Review LLM response in logs

**Fallback**: If LLM fails, generic suggestions are used. Check logs for warnings.

### Issue: "Processing too slow (>60s)"
**Solutions**:
- Reduce `MAX_DEPTH` to 2
- Increase `MIN_CONTENT` to 1000
- Check Neo4j connection latency
- Review LLM API response times in logs

### Issue: "Memory leak after 100 PDFs"
**Solution**: Restart worker periodically or add explicit cleanup:
```python
import gc
gc.collect()  # After each batch
```

---

## 🚀 Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY RabbitMQ/ ./RabbitMQ/
COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
CMD ["python", "RabbitMQ/worker.py"]
```

```bash
docker build -t pdf-worker .
docker run -d \
  --name pdf-worker-1 \
  --env-file .env \
  pdf-worker
```

### Scaling
```bash
# Run multiple workers for parallel processing
docker-compose up --scale worker=5
```

---

## 📈 Monitoring

### Key Metrics to Track
- **LLM calls/PDF**: Should be 10-15
- **Processing time**: Should be <40s/PDF
- **Error rate**: Should be <1%
- **Gap suggestion quality**: Manual review weekly

### Logging
```bash
# View logs
tail -f new_worker.log

# Filter for important events
grep "Total LLM calls" new_worker.log
grep "ERROR" new_worker.log
grep "Gap suggestions" new_worker.log
```

---

## 🔐 Security

- **API Keys**: Store in environment variables, never in code
- **Neo4j**: Use SSL connection (`neo4j+s://`)
- **Firebase**: Restrict service account permissions
- **RabbitMQ**: Use SSL/TLS for production

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING](#-troubleshooting) section
2. Review logs: `new_worker.log`
3. Open GitHub issue with logs and error details

---

**Version**: RECURSIVE_EXPANSION_OPTIMIZED
**Last Updated**: 2025-11-22
**Status**: ✅ Production Ready
