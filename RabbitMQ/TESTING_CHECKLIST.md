# Testing Checklist - Optimized Pipeline

## 🧪 Pre-Deployment Testing

### 1. Environment Setup
- [ ] Neo4j database is running and accessible
- [ ] Firebase credentials are configured (`serviceAccountKey.json`)
- [ ] RabbitMQ connection is working
- [ ] HyperClovaX API key is valid (`CLOVA_API_KEY`)
- [ ] Python dependencies installed:
  ```bash
  pip install neo4j firebase-admin pika requests
  ```

---

### 2. Unit Tests

#### Test Gap Suggestion Batch Function
```python
# Test file: test_gap_suggestions.py
import asyncio
from worker import generate_gap_suggestions_batch

async def test_gap_batch():
    leaf_nodes = [
        {"id": "node-1", "name": "Reinforcement Learning", "synthesis": "ML technique for agents", "parent_name": "AI"},
        {"id": "node-2", "name": "Energy Management", "synthesis": "Optimizing power usage", "parent_name": "Systems"},
        {"id": "node-3", "name": "Satellite Coordination", "synthesis": "Multi-agent coordination", "parent_name": "Space"},
    ]

    result = await generate_gap_suggestions_batch(
        leaf_nodes=leaf_nodes,
        file_name="test.pdf",
        domain_name="AI Research",
        language="en",
        batch_size=3
    )

    # Assertions
    assert len(result) == 3, f"Expected 3 suggestions, got {len(result)}"
    for node_id, gap_data in result.items():
        assert 'suggestion_text' in gap_data
        assert 'target_url' in gap_data
        assert 'similarity_score' in gap_data
        assert len(gap_data['suggestion_text']) > 20, "Suggestion too short"
        assert gap_data['target_url'].startswith('http'), "Invalid URL"
        assert 0.0 <= gap_data['similarity_score'] <= 1.0, "Score out of range"

    print("✅ Gap batch test passed!")

# Run
asyncio.run(test_gap_batch())
```

**Expected Output**:
```
  🤖 Generating gap suggestions for 3 leaf nodes (batch_size=3)...
    Processing batch 1/1 (3 nodes)...
      ✓ LLM generated 3 gap suggestions
  ✓ Generated 3 gap suggestions across 1 batches
✅ Gap batch test passed!
```

**Checklist**:
- [ ] Function completes without errors
- [ ] Returns exactly 3 suggestions
- [ ] All suggestions have valid text, URL, and score
- [ ] LLM call count = 1 (logged in console)

---

#### Test LLM Call Counting
```python
# Test that total calls stay within budget
async def test_llm_budget():
    from worker import run_recursive_expansion_pipeline
    from neo4j import GraphDatabase

    # Setup
    neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))

    result = await run_recursive_expansion_pipeline(
        workspace_id="test-workspace",
        pdf_url="https://arxiv.org/pdf/sample.pdf",
        file_name="sample.pdf",
        neo4j_driver=neo4j_driver,
        job_id="test-job-123"
    )

    # Assertions
    total_calls = result['quality_metrics']['llm_calls']
    assert total_calls <= 15, f"Too many LLM calls: {total_calls} > 15"

    breakdown = result['quality_metrics']['llm_calls_breakdown']
    assert breakdown['domain_extraction'] == 1
    assert 5 <= breakdown['recursive_expansion'] <= 8
    assert 2 <= breakdown['gap_suggestions'] <= 5

    print(f"✅ LLM budget test passed! Total calls: {total_calls}")

# Run
asyncio.run(test_llm_budget())
```

**Checklist**:
- [ ] Total LLM calls ≤ 15
- [ ] Domain extraction = 1 call
- [ ] Recursive expansion = 5-8 calls
- [ ] Gap suggestions = 2-5 calls (depends on leaf nodes)

---

### 3. Integration Tests

#### Test Single PDF Processing
```bash
# Send test message to RabbitMQ
python -c "
import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('chameleon-01.lmq.cloudamqp.com'))
channel = connection.channel()

message = {
    'JobId': 'test-job-001',
    'WorkspaceId': 'test-workspace',
    'FilePaths': ['https://arxiv.org/pdf/2101.00001.pdf']
}

channel.basic_publish(
    exchange='',
    routing_key='PDF_JOBS_QUEUE',
    body=json.dumps(message)
)
print('✅ Test message sent!')
connection.close()
"
```

**Monitor Logs**:
```bash
tail -f new_worker.log | grep -E "Processing complete|Total LLM calls|Gap suggestions"
```

**Expected**:
```
  📊 Total LLM calls: 12 (domain=1, recursive=8, gap_batches=3)
  ✓ Created 15 LLM-powered gap suggestions (batch mode).
  ✅ Processing complete in 34.2s
```

**Checklist**:
- [ ] Worker processes message without crashes
- [ ] LLM calls logged correctly
- [ ] Gap suggestions created successfully
- [ ] Neo4j nodes inserted (verify with query below)
- [ ] Firebase status updated

---

#### Verify Neo4j Data
```cypher
// 1. Count nodes created
MATCH (n:KnowledgeNode {workspace_id: 'test-workspace'})
RETURN count(n) as TotalNodes

// Expected: 10-15 nodes

// 2. Check gap suggestions
MATCH (n:KnowledgeNode {workspace_id: 'test-workspace'})-[:HAS_SUGGESTION]->(g:GapSuggestion)
RETURN n.name as LeafNode,
       g.suggestion_text as Suggestion,
       g.target_url as URL,
       g.similarity_score as Score
ORDER BY g.similarity_score DESC
LIMIT 5

// Expected: 5+ gap suggestions with specific text and valid URLs

// 3. Verify hierarchy
MATCH path = (domain:KnowledgeNode {workspace_id: 'test-workspace', level: 0})
             -[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL*1..3]->(leaf)
WHERE NOT (leaf)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
RETURN domain.name, length(path) as Depth, count(leaf) as LeafNodes

// Expected: Depth = 3 or 4, LeafNodes = 5-10
```

**Checklist**:
- [ ] Nodes created: 10-15
- [ ] Gap suggestions: 5-10 with valid text/URLs
- [ ] Max hierarchy depth: 3-4 levels
- [ ] All leaf nodes have ≥1 gap suggestion

---

### 4. Quality Validation

#### Check Gap Suggestion Quality
```cypher
MATCH (g:GapSuggestion)
WHERE g.target_file_id CONTAINS 'test-workspace'
RETURN g.suggestion_text as Text,
       length(g.suggestion_text) as Length,
       g.target_url as URL
ORDER BY Length DESC
LIMIT 10
```

**Quality Criteria**:
- [ ] ✅ Text length: 50-150 chars (SPECIFIC, not generic)
- [ ] ✅ No generic phrases like "learn more about X"
- [ ] ✅ URLs are realistic (arxiv.org, scholar.google.com, etc.)
- [ ] ✅ URLs contain relevant search terms
- [ ] ❌ No broken suggestions like "Explore {node_name}"

**Bad Examples** (should NOT appear):
```
❌ "Consider exploring related research areas"
❌ "https://arxiv.org/search" (no query)
❌ "Learn more about this topic"
```

**Good Examples** (should appear):
```
✅ "Explore value-advantage decomposition in non-stationary multi-agent environments"
✅ "https://arxiv.org/search/?query=dueling+dqn+non-stationary"
✅ "Investigate adaptive solar storm prediction for satellite energy management"
```

---

### 5. Performance Benchmarks

#### Test Processing Speed
```python
import time
import asyncio
from worker import run_recursive_expansion_pipeline

async def benchmark():
    start = time.time()

    result = await run_recursive_expansion_pipeline(
        workspace_id="benchmark-ws",
        pdf_url="https://arxiv.org/pdf/2101.00001.pdf",
        file_name="benchmark.pdf",
        neo4j_driver=neo4j_driver,
        job_id="benchmark-001"
    )

    elapsed = time.time() - start
    llm_calls = result['quality_metrics']['llm_calls']

    print(f"⏱️  Processing time: {elapsed:.1f}s")
    print(f"📊 LLM calls: {llm_calls}")
    print(f"📈 Nodes/second: {result['nodes_created'] / elapsed:.2f}")
    print(f"⚡ Seconds/LLM call: {elapsed / llm_calls:.2f}")

asyncio.run(benchmark())
```

**Target Performance**:
- [ ] Processing time: <40s for ~50KB PDF
- [ ] LLM calls: 10-15
- [ ] Nodes created: 10-15
- [ ] Seconds per LLM call: 2-4s

---

### 6. Batch Processing Test

#### Test Multiple PDFs
```python
async def test_batch():
    from worker import process_files_batch

    result = await process_files_batch_async(
        workspace_id="batch-test",
        file_paths=[
            "https://arxiv.org/pdf/2101.00001.pdf",
            "https://arxiv.org/pdf/2102.00002.pdf",
            "https://arxiv.org/pdf/2103.00003.pdf"
        ],
        job_id="batch-job-001",
        neo4j_driver=neo4j_driver,
        firebase_client=firebase_client
    )

    assert result['successful'] == 3
    assert result['failed'] == 0
    assert result['status'] == 'completed'

    print(f"✅ Batch test passed: {result['successful']}/3 files processed")

asyncio.run(test_batch())
```

**Checklist**:
- [ ] All 3 PDFs processed successfully
- [ ] Total LLM calls: 30-45 (10-15 per PDF)
- [ ] Firebase updated 3 times (once per PDF)
- [ ] No memory leaks (check with `htop`)

---

### 7. Error Handling Tests

#### Test LLM Failure Gracefully
```python
# Temporarily set invalid API key
os.environ['CLOVA_API_KEY'] = 'invalid-key'

result = await run_recursive_expansion_pipeline(...)

# Should use fallback gap suggestions
assert result['status'] == 'success' or result['status'] == 'failed'
# If failed, check that error message is clear
```

**Checklist**:
- [ ] Pipeline fails gracefully with clear error message
- [ ] Fallback gap suggestions used if LLM fails
- [ ] No crashes or unhandled exceptions

---

### 8. Edge Cases

#### Test Very Short PDF
```python
# PDF with <1000 chars (should trigger validation error)
result = await run_recursive_expansion_pipeline(
    pdf_url="https://example.com/very-short.pdf",
    ...
)
assert result['status'] == 'failed'
assert 'too short' in result['error'].lower()
```

#### Test PDF with No Leaf Nodes
```python
# Shallow document (only domain + 1 category)
# Should create 0 gap suggestions
result = await run_recursive_expansion_pipeline(...)
assert result['gaps_created'] == 0
```

**Checklist**:
- [ ] Short PDFs rejected with clear error
- [ ] Shallow documents handled (0 gaps OK)
- [ ] Large PDFs (>100 pages) limited to 25 pages

---

## ✅ Final Deployment Checklist

### Before Deploying to Production
- [ ] All unit tests pass
- [ ] Integration tests pass (single + batch)
- [ ] Neo4j data verified (nodes + gaps)
- [ ] Gap suggestion quality validated
- [ ] Performance benchmarks met (<40s/PDF, <15 LLM calls)
- [ ] Error handling tested
- [ ] Edge cases handled
- [ ] Logs reviewed (no warnings/errors)
- [ ] Memory usage acceptable (<1GB per worker)
- [ ] Firebase updates working
- [ ] RabbitMQ message acknowledgment working

### Production Smoke Test
```bash
# 1. Deploy worker
python RabbitMQ/worker.py &

# 2. Send real job
curl -X POST http://your-backend/api/upload-pdf \
  -H "Content-Type: application/json" \
  -d '{"workspaceId": "prod-test", "pdfUrl": "https://arxiv.org/pdf/2101.00001.pdf"}'

# 3. Monitor
tail -f new_worker.log

# 4. Verify in Neo4j
# (Run queries from section 3 above)

# 5. Check Firebase
# Verify job status updated to "completed"
```

**Checklist**:
- [ ] Worker starts without errors
- [ ] Job processed successfully
- [ ] Logs show correct LLM call count
- [ ] Neo4j contains new nodes + gaps
- [ ] Firebase shows "completed" status

---

## 🎯 Success Criteria Summary

| Criteria | Target | Status |
|----------|--------|--------|
| LLM Calls/PDF | ≤15 | ⬜ |
| Processing Time | <40s | ⬜ |
| Gap Suggestion Quality | 100% LLM-powered, SPECIFIC | ⬜ |
| Node Quality Filter | >85% pass rate | ⬜ |
| Error Rate | <1% | ⬜ |
| Memory Usage | <1GB/worker | ⬜ |

---

**Last Updated**: 2025-11-22
**Version**: RECURSIVE_EXPANSION_OPTIMIZED
