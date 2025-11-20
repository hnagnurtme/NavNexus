# New Worker - Complete Implementation Guide

## Overview

This is a **complete rewrite** of the RabbitMQ worker based on the requirements in the issue. The worker follows the `seed.py` logic exactly to ensure data structure matches `data2.json` and `data3.json`.

## ⭐ Key Differences from Old Worker

| Aspect | Old Worker (`worker.py`) | New Worker (`new_worker.py`) |
|--------|-------------------------|------------------------------|
| **Data Structure** | ❌ Missing many properties | ✅ Matches data2.json exactly |
| **Evidence Fields** | ❌ Missing Concepts, KeyClaims, QuestionsRaised | ✅ All fields included |
| **GapSuggestion** | ❌ Missing SimilarityScore | ✅ SimilarityScore included |
| **Relationships** | ❌ Incomplete (missing CONTAINS_CONCEPT, HAS_DETAIL) | ✅ All relationships correct |
| **Neo4j Logic** | ⚠️ Custom implementation | ✅ Exact copy from seed.py |
| **Firebase Integration** | ⚠️ Basic push | ✅ Real-time status updates with progress |

## 🎯 Data Structure (Matches data2.json)

### KnowledgeNode
```python
{
    "Id": "domain-sagin001",
    "Type": "domain",  # domain, category, concept, subconcept
    "Name": "Space-Air-Ground Integrated Networks",
    "Synthesis": "Comprehensive synthesis text...",
    "WorkspaceId": "Reinforcement-Learning",
    "Level": 0,  # 0: domain, 1: category, 2: concept, 3: subconcept
    "SourceCount": 2,
    "TotalConfidence": 0.92,
    "CreatedAt": "2025-01-15T08:30:00Z",
    "UpdatedAt": "2025-01-15T14:22:00Z",
    "ParentId": null  # or parent node ID
}
```

### Evidence
```python
{
    "Id": "evidence-domain-en001",
    "SourceId": "pdf-optimizing-sagin-ai",
    "SourceName": "Optimizing Space-Air-Ground...",
    "ChunkId": "chunk-005",
    "Text": "Full text of evidence...",
    "Page": 1,
    "Confidence": 0.92,
    "CreatedAt": "2025-01-15T08:30:00Z",
    "Language": "ENG",
    "SourceLanguage": "ENG",
    "HierarchyPath": "SAGIN",
    "Concepts": [
        "Network Architecture",
        "Heterogeneous Networks"
    ],
    "KeyClaims": [
        "SAGIN integrates satellite, aerial, and terrestrial networks",
        "Diverse propagation characteristics..."
    ],
    "QuestionsRaised": [
        "How to standardize protocols?",
        "What are optimal ratios?"
    ],
    "EvidenceStrength": 0.91,
    "StartPos": 1850,
    "EndPos": 3420,
    "ChunkIndex": 5,
    "HasMore": true,
    "OverlapLength": 120,
    "NodeId": "domain-sagin001"
}
```

### GapSuggestion
```python
{
    "Id": "gap-dqn-rainbow001",
    "SuggestionText": "Consider investigating Rainbow DQN...",
    "TargetNodeId": "https://arxiv.org/abs/1710.02298",
    "TargetFileId": "",
    "SimilarityScore": 0.87,
    "NodeId": "subconcept-dqn001"
}
```

## 🔗 Relationships

The worker creates the following Neo4j relationships:

```cypher
# Hierarchical relationships based on levels
(domain)-[:HAS_SUBCATEGORY]->(category)
(category)-[:CONTAINS_CONCEPT]->(concept)
(concept)-[:HAS_DETAIL]->(subconcept)

# Evidence relationships
(node)-[:HAS_EVIDENCE]->(evidence)

# Gap suggestion relationships
(node)-[:HAS_SUGGESTION]->(gapSuggestion)
```

## 🔥 Firebase Structure

The worker pushes job status to Firebase Realtime Database at `jobs/{jobId}`:

```json
{
  "status": "pending" | "completed" | "failed" | "partial",
  "workspaceId": "workspace-123",
  "totalFiles": 3,
  "successful": 2,
  "failed": 0,
  "currentFile": 2,
  "processingTimeMs": 45000,
  "timestamp": "2025-01-20T10:30:00Z",
  "results": [...]
}
```

## 🚀 Usage

### Running the Worker

```bash
cd RabbitMQ

# Set environment variables (optional - defaults are provided)
export NEO4J_URL="neo4j+s://your-instance.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"
export RABBITMQ_HOST="your-rabbitmq-host"
export RABBITMQ_USERNAME="your-username"
export RABBITMQ_PASSWORD="your-password"

# Run the new worker
python new_worker.py
```

### Message Format

Send messages to the RabbitMQ queue in this format:

```json
{
  "workspaceId": "workspace-123",
  "filePaths": [
    "https://storage.example.com/file1.pdf",
    "https://storage.example.com/file2.pdf"
  ],
  "jobId": "job-abc123"
}
```

## 📊 Processing Flow

```
1. Receive message from RabbitMQ
   ↓
2. Extract PDF content
   ↓
3. Create smart chunks (1500 chars, 150 overlap)
   ↓
4. LLM Analysis (generate Concepts, KeyClaims, QuestionsRaised)
   ↓
5. Build hierarchical structure (domain → category → concept → subconcept)
   ↓
6. Insert into Neo4j using seed.py logic
   ├─ Create KnowledgeNodes with MERGE
   ├─ Create Evidence nodes with MERGE
   ├─ Create GapSuggestion nodes with MERGE
   └─ Create relationships
   ↓
7. Push status to Firebase
   ↓
8. Store embeddings in Qdrant (optional)
```

## ⚙️ Configuration

All configuration is in environment variables with sensible defaults:

- **Neo4j**: NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD
- **RabbitMQ**: RABBITMQ_HOST, RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_VHOST
- **Qdrant**: QDRANT_URL, QDRANT_API_KEY
- **Firebase**: FIREBASE_SERVICE_ACCOUNT, FIREBASE_DATABASE_URL

## 🧪 Testing

### Manual Test

```python
# Test with a single PDF
test_message = {
    "workspaceId": "test-workspace",
    "filePaths": [
        "https://arxiv.org/pdf/2101.00001.pdf"
    ],
    "jobId": "test-job-001"
}

# Publish to RabbitMQ or call handler directly
handle_job_message(test_message, neo4j_driver, qdrant_client, firebase_client)
```

### Verify Output

1. **Check Neo4j**:
```cypher
MATCH (n:KnowledgeNode {workspace_id: "test-workspace"})
RETURN n

MATCH (e:Evidence)
RETURN e.concepts, e.key_claims, e.questions_raised

MATCH (g:GapSuggestion)
RETURN g.similarity_score
```

2. **Check Firebase**:
Visit: `https://navnexus-default-rtdb.firebaseio.com/jobs/test-job-001.json`

3. **Verify Relationships**:
```cypher
MATCH (parent)-[r]->(child)
WHERE parent.workspace_id = "test-workspace"
RETURN type(r), parent.type, child.type
```

## 🔍 Comparison with seed.py

The worker uses **EXACT COPIES** of these functions from `seed.py`:

- ✅ `create_knowledge_node()` - Line-by-line copy
- ✅ `create_evidence_node()` - Line-by-line copy
- ✅ `create_gap_suggestion_node()` - Line-by-line copy
- ✅ `create_parent_child_relationship()` - Line-by-line copy
- ✅ `determine_relationship_type()` - Line-by-line copy

This ensures **100% compatibility** with seeded data.

## 🐛 Troubleshooting

### Issue: No data in Neo4j
- Check Neo4j credentials
- Verify MERGE queries are executing
- Check Neo4j logs

### Issue: Firebase not updating
- Verify serviceAccountKey.json exists
- Check Firebase Realtime Database URL
- Ensure Firebase database rules allow writes

### Issue: Missing properties
- Compare output with `data2.json`
- Check LLM analysis is returning all required fields
- Verify Evidence model has all fields

## 📝 TODO / Improvements

- [ ] Replace mock LLM analysis with actual LLM calls
- [ ] Implement Qdrant embedding storage
- [ ] Add retry logic for LLM failures
- [ ] Add comprehensive logging
- [ ] Add metrics and monitoring
- [ ] Performance optimization for large PDFs
- [ ] Unit tests

## 🎯 Success Criteria

✅ Output matches `data2.json` structure exactly
✅ All KnowledgeNode properties present
✅ Evidence includes Concepts, KeyClaims, QuestionsRaised
✅ GapSuggestion includes SimilarityScore
✅ All relationships created correctly
✅ Firebase updates work in real-time
✅ Code is clean and maintainable

## 📚 References

- `seed.py` - Source of truth for Neo4j insertion
- `data2.json` - Target data structure
- `data3.json` - Additional example
- `swagger.json` - API structure reference
