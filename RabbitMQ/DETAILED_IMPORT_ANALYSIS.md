# Detailed Import Analysis
**RabbitMQ Python Codebase**

---

## worker.py - Complete Import Breakdown

### Line-by-Line Import Analysis

```python
# ✅ STANDARD LIBRARY (Lines 12-19)
import os              # Used: ✓ (config, paths)
import sys             # Used: ✓ (path manipulation)
import json            # Used: ✓ (message parsing)
import uuid            # Used: ✓ (ID generation)
import gc              # Used: ✓ (garbage collection)
import traceback       # Used: ✓ (error handling)
from datetime import datetime   # Used: ✓ (timestamps)
from typing import Dict, Any    # Used: ✓ (type hints)

# ✅ EXTERNAL LIBRARIES (Lines 47-48)
from neo4j import GraphDatabase   # Used: ✓ (Neo4j connection)
from qdrant_client import QdrantClient  # Used: ✓ (Qdrant connection)

# ✅ INTERNAL - CLIENTS (Lines 24-25)
from src.rabbitmq_client import RabbitMQClient    # Used: ✓
from src.handler.firebase import FirebaseClient   # Used: ✓

# ✅ INTERNAL - PIPELINE (Lines 28-31)
from src.pipeline.pdf_extraction import extract_pdf_fast   # Used: ✓ (Line 149)
from src.pipeline.chunking import create_smart_chunks      # Used: ✓ (Line 213)
from src.pipeline.embedding import create_embedding_via_clova, calculate_similarity  # Used: ✓
from src.pipeline.translation import translate_batch, translate_structure, translate_chunk_analysis  # Used: Partial

# ⚠️ TRANSLATION FUNCTIONS USAGE
translate_batch          # Used: ❌ NOT USED
translate_structure      # Used: ✓ (Line 173)
translate_chunk_analysis # Used: ✓ (Line 230)

# ✅ INTERNAL - EMBEDDING CACHE (Line 34)
from src.pipeline.embedding_cache import extract_all_concept_names, batch_create_embeddings
# Both used: ✓

# ❌ CRITICAL: NON-EXISTENT MODULES (Lines 35-37)
from src.pipeline.llm_analysis_optimized import extract_hierarchical_structure_compact, process_chunks_ultra_compact
# FILE DOES NOT EXIST!
# Should be: from src.pipeline.llm_analysis import extract_merge_optimized_structure, analyze_chunks_for_merging

from src.pipeline.neo4j_graph_optimized import create_hierarchical_graph_with_cascading_dedup
# FILE DOES NOT EXIST!
# Should be: from src.pipeline.neo4j_graph import create_hierarchical_knowledge_graph

from src.pipeline.qdrant_storage_optimized import store_chunks_in_qdrant
# FILE DOES NOT EXIST!
# Should be: from src.pipeline.qdrant_storage import store_chunks_in_qdrant

# ⚠️ LEGACY IMPORTS (Line 41)
from src.pipeline.neo4j_graph import find_or_merge_node, add_evidence_to_node, now_iso
# find_or_merge_node: Used: ❌ NOT USED
# add_evidence_to_node: Used: ❌ NOT USED
# now_iso: Used: ✓ (Line 297)

# ✅ INTERNAL - RESOURCE DISCOVERY (Line 38)
from src.pipeline.resource_discovery import discover_resources_with_hyperclova
# Used: ✓ (Line 327)

# ✅ INTERNAL - MODELS (Lines 43-44)
from src.model.Evidence import Evidence         # Used: ❌ NOT USED (imported but never instantiated)
from src.model.QdrantChunk import QdrantChunk  # Used: ✓ (Line 286)
```

### Summary for worker.py

| Category | Count | Status |
|----------|-------|--------|
| Total imports | 23 | - |
| Working imports | 19 | ✅ |
| Broken imports | 4 | ❌ CRITICAL |
| Unused imports | 4 | ⚠️ Can remove |

**Unused but harmless:**
- `translate_batch` (from translation)
- `find_or_merge_node` (from neo4j_graph)
- `add_evidence_to_node` (from neo4j_graph)
- `Evidence` (from model)

---

## worker_enhanced.py - Import Analysis

```python
# ✅ ALL IMPORTS WORKING
from src.rabbitmq_client import RabbitMQClient              # Used: ✓
from src.handler.firebase import FirebaseClient             # Used: ✓
from src.pipeline.main_pipeline import process_pdf_to_knowledge_graph  # Used: ✓
from neo4j import GraphDatabase                             # Used: ✓
from qdrant_client import QdrantClient                      # Used: ✓
```

### Summary for worker_enhanced.py

| Category | Count | Status |
|----------|-------|--------|
| Total imports | 16 | - |
| Working imports | 16 | ✅ ALL GOOD |
| Broken imports | 0 | ✅ |
| Unused imports | 0 | ✅ |

**Analysis:** `worker_enhanced.py` has clean imports! 🎉

---

## src/pipeline/main_pipeline.py - Import Analysis

```python
# ✅ INTERNAL IMPORTS (Lines 10-33)
from config import (
    CLOVA_API_KEY, CLOVA_API_URL, CLOVA_EMBEDDING_URL,
    PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET,
    # ... many more config imports
)

# ⚠️ POTENTIAL ISSUE: Relative import 'config' instead of 'src.config'
# Should be: from src.config import ...
# This works if main_pipeline.py is run from project root, but breaks otherwise

# ✅ PIPELINE IMPORTS (Lines 37-62)
from .pdf_extraction import extract_pdf_enhanced           # Used: ✓
from .chunking import create_smart_chunks, calculate_chunk_stats  # Used: ✓
from .llm_analysis import (
    extract_merge_optimized_structure,   # Used: ✓
    analyze_chunks_for_merging,          # Used: ✓
)
from .embedding_cache import batch_create_embeddings, extract_all_concept_names  # Used: ✓
from .embedding import create_embedding_via_clova, calculate_similarity  # Used: ✓
from .neo4j_graph import create_hierarchical_knowledge_graph  # Used: ✓
from .qdrant_storage import (
    store_chunks_in_qdrant,              # Used: ✓
    search_similar_chunks,               # Used: ❌ NOT USED
    get_collection_stats                 # Used: ❌ NOT USED (but used in get_pipeline_status)
)
from .translation import (
    translate_structure_enhanced,        # Used: ✓
    translate_chunk_analysis_enhanced,   # Used: ✓
    validate_language_codes              # Used: ✓
)
from .resource_discovery import (
    discover_resources_via_knowledge_analysis,  # Used: ✓
    get_resource_discovery_stats         # Used: ✓
)

# ✅ MODEL IMPORTS (Line 64)
from ..model.QdrantChunk import QdrantChunk  # Used: ✓
```

### Summary for main_pipeline.py

| Category | Count | Status |
|----------|-------|--------|
| Config imports | ~34 | ✅ |
| Pipeline imports | ~20 | ✅ |
| Unused imports | 1 | ⚠️ Minor |

**Note:** `search_similar_chunks` is imported but not used in main_pipeline.py itself.

---

## Unused Import Summary Across All Files

### worker.py
```python
# Can be removed:
from src.pipeline.translation import translate_batch  # NOT USED
from src.pipeline.neo4j_graph import find_or_merge_node, add_evidence_to_node  # NOT USED
from src.model.Evidence import Evidence  # NOT USED
```

### main_pipeline.py
```python
# Can be removed (but kept for completeness):
from .qdrant_storage import search_similar_chunks  # NOT USED in main file
```

---

## Function Availability Matrix

### llm_analysis.py Functions

| Function Name (worker.py expects) | Actual Name (llm_analysis.py) | Status |
|-----------------------------------|-------------------------------|--------|
| `extract_hierarchical_structure_compact` | `extract_merge_optimized_structure` ✅ | RENAME NEEDED |
| - | `extract_deep_merge_structure` ✅ | ACTUAL FUNCTION |
| `process_chunks_ultra_compact` | `analyze_chunks_for_merging` ✅ | RENAME NEEDED |

**Note:** Line 1077 in llm_analysis.py:
```python
extract_merge_optimized_structure = extract_deep_merge_structure
```
This is an alias! So both names work.

### neo4j_graph.py Functions

| Function Name (worker.py expects) | Actual Name (neo4j_graph.py) | Status |
|-----------------------------------|------------------------------|--------|
| `create_hierarchical_graph_with_cascading_dedup` | `create_hierarchical_knowledge_graph` ✅ | RENAME NEEDED |

### qdrant_storage.py Functions

| Function Name (worker.py expects) | Actual Name (qdrant_storage.py) | Status |
|-----------------------------------|--------------------------------|--------|
| `store_chunks_in_qdrant` | `store_chunks_in_qdrant` ✅ | ✅ EXACT MATCH |

**Note:** `store_chunks_in_qdrant` is the ONE function that exists with the correct name!

---

## Enhanced Evidence Pipeline - Import Chain

```
test_enhanced_pipeline.py
├── from src.pipeline.chunking import create_smart_chunks
├── from src.model.Evidence import Evidence
└── from src.pipeline.evidence_optimizer import EvidenceOptimizer
    └── import anthropic  # EXTERNAL: Requires anthropic package

src/pipeline/enhanced_evidence_pipeline.py
├── from src.pipeline.chunking import create_smart_chunks
├── from src.pipeline.evidence_optimizer import EvidenceOptimizer
├── from src.model.Evidence import Evidence
└── from qdrant_client import QdrantClient, PointStruct

src/pipeline/evidence_optimizer.py
├── import anthropic  # REQUIRES: pip install anthropic
├── import json
└── import os
```

**Dependency:** Enhanced pipeline requires `anthropic` package (Claude API).

---

## Translation Module Usage Analysis

### translation.py Exports

```python
# Available functions:
- translate_batch(texts, source, target, client_id, secret)
- translate_structure(structure, source, target, client_id, secret)
- translate_chunk_analysis(chunk, source, target, client_id, secret)
- translate_structure_enhanced(structure, source, target, client_id, secret)
- translate_chunk_analysis_enhanced(chunk, source, target, client_id, secret)
- validate_language_codes(source, target)
```

### Usage Across Files

| Function | worker.py | main_pipeline.py | Used? |
|----------|-----------|------------------|-------|
| `translate_batch` | Imported | ❌ | ❌ UNUSED |
| `translate_structure` | ✅ Used | ❌ | ✅ |
| `translate_chunk_analysis` | ✅ Used | ❌ | ✅ |
| `translate_structure_enhanced` | ❌ | ✅ Used | ✅ |
| `translate_chunk_analysis_enhanced` | ❌ | ✅ Used | ✅ |
| `validate_language_codes` | ❌ | ✅ Used | ✅ |

**Observation:**
- `worker.py` uses non-enhanced versions
- `main_pipeline.py` uses enhanced versions
- Different APIs but similar functionality

---

## Resource Discovery - Duplicate Function Issue

### The Duplicate: `create_gap_suggestion_node`

**Location 1:** `src/pipeline/neo4j_graph.py:128`
```python
def create_gap_suggestion_node(session, gap_suggestion: GapSuggestion, knowledge_node_id: str):
    """Create a gap suggestion node and link to knowledge node"""
    # Implementation...
```

**Location 2:** `src/pipeline/resource_discovery.py:14`
```python
def create_gap_suggestion_node(session, gap: GapSuggestion, target_node_id: str) -> str:
    """Create gap suggestion node in Neo4j"""
    # Different implementation!
```

### Which is Used?

```python
# neo4j_graph.py version:
# - Called by: add_gap_suggestions_to_node() in same file
# - Parameters: gap_suggestion, knowledge_node_id
# - Returns: None

# resource_discovery.py version:
# - Called by: discover_resources_via_knowledge_analysis()
# - Parameters: gap, target_node_id
# - Returns: str (node ID)
```

**Impact:** Both are used! They're different functions with the same name.

**Solution:** Rename one:
```python
# In resource_discovery.py:
def create_resource_gap_node(session, gap: GapSuggestion, target_node_id: str) -> str:
    """Create resource discovery gap suggestion node"""
```

---

## Embedding Functions - Complete List

### embedding.py
```python
create_embedding_via_clova(text, api_key, url) -> List[float]  # Production
create_hash_embedding(text, dim=384) -> List[float]             # Fallback
calculate_similarity(vec1, vec2) -> float                       # Utility
```

### embedding_cache.py
```python
extract_all_concept_names(structure) -> List[str]              # Extract names
batch_create_embeddings(names, api_key, url, batch_size) -> Dict  # Batch processing
```

### enhanced_evidence_pipeline.py
```python
create_mock_embedding(text) -> List[float]                      # Mock/testing only
```

**Usage:**
- Production: `create_embedding_via_clova` (all files)
- Testing: `create_mock_embedding` (test files only)
- Unused: `create_hash_embedding` (fallback, never called)

---

## PDF Extraction Analysis

### Available Functions

```python
# pdf_extraction.py:
extract_pdf_enhanced(url, max_pages, timeout) -> Tuple[str, str, Dict]  # Main
extract_text_from_pdf(pdf_bytes, max_pages) -> Dict                      # Helper
get_pdf_metadata(pdf_bytes) -> Dict                                      # UNUSED
```

### Usage

| Function | worker.py | main_pipeline.py | Status |
|----------|-----------|------------------|--------|
| `extract_pdf_fast` | ✅ Used | ❌ | ❌ DOES NOT EXIST |
| `extract_pdf_enhanced` | ❌ | ✅ Used | ✅ CORRECT |
| `get_pdf_metadata` | ❌ | ❌ | ❌ DEAD CODE |

**Issue:** `worker.py` imports non-existent `extract_pdf_fast`!

**Fix:**
```python
# worker.py line 28:
# BEFORE:
from src.pipeline.pdf_extraction import extract_pdf_fast

# AFTER:
from src.pipeline.pdf_extraction import extract_pdf_enhanced
# Then rename usage: extract_pdf_fast() -> extract_pdf_enhanced()
```

---

## Correct Import Statements for worker.py

### Complete Fixed Imports Block

```python
"""
RabbitMQ Worker for processing PDF jobs - FIXED VERSION
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

# Pipeline modules - CORRECTED
from src.pipeline.pdf_extraction import extract_pdf_enhanced  # FIXED: was extract_pdf_fast
from src.pipeline.chunking import create_smart_chunks
from src.pipeline.embedding import create_embedding_via_clova, calculate_similarity
from src.pipeline.translation import translate_structure, translate_chunk_analysis  # REMOVED: translate_batch

# CORRECTED MODULES - Use actual function names
from src.pipeline.embedding_cache import extract_all_concept_names, batch_create_embeddings
from src.pipeline.llm_analysis import extract_merge_optimized_structure, analyze_chunks_for_merging  # FIXED
from src.pipeline.neo4j_graph import create_hierarchical_knowledge_graph, now_iso  # FIXED, REMOVED: unused functions
from src.pipeline.qdrant_storage import store_chunks_in_qdrant  # FIXED: was qdrant_storage_optimized
from src.pipeline.resource_discovery import discover_resources_via_knowledge_analysis  # Consider renaming

from src.model.QdrantChunk import QdrantChunk  # REMOVED: Evidence (not used)

# External dependencies
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
```

### Function Call Replacements Needed

```python
# Line ~155: Structure extraction
# BEFORE:
structure = extract_hierarchical_structure_compact(
    full_text, file_name, lang,
    CLOVA_API_KEY, CLOVA_API_URL
)

# AFTER:
structure = extract_merge_optimized_structure(
    full_text[:20000], file_name, lang,
    CLOVA_API_KEY, CLOVA_API_URL
)

# Line ~215: Chunk processing
# BEFORE:
chunk_analyses = process_chunks_ultra_compact(
    chunks, structure,
    CLOVA_API_KEY, CLOVA_API_URL,
    lang
)

# AFTER:
chunk_analyses_result = analyze_chunks_for_merging(
    chunks, structure,
    CLOVA_API_KEY, CLOVA_API_URL
)
# Note: May need to adjust format - check return type

# Line ~195: Graph creation
# BEFORE:
dedup_stats = create_hierarchical_graph_with_cascading_dedup(
    session, workspace_id, structure, file_id, file_name,
    embeddings_cache
)

# AFTER:
graph_stats = create_hierarchical_knowledge_graph(
    session, workspace_id, structure, file_id, file_name, embeddings_cache
)
```

---

## Import Best Practices Violations

### Issue 1: Relative vs Absolute Imports

**main_pipeline.py Line 10:**
```python
# CURRENT (problematic):
from config import CLOVA_API_KEY, ...

# SHOULD BE:
from src.config import CLOVA_API_KEY, ...
```

**Impact:** Works when run from project root, fails otherwise.

### Issue 2: Wildcard Imports

**None found** ✅ - Good!

### Issue 3: Circular Imports

**None detected** ✅ - Good!

### Issue 4: Import Order

Most files follow PEP 8:
1. Standard library
2. Third-party packages
3. Local imports

✅ Generally good!

---

## Dependencies Analysis

### Required External Packages

```python
# From imports:
neo4j>=5.0.0           # GraphDatabase
qdrant-client>=1.0.0   # QdrantClient
anthropic>=0.8.0       # For evidence_optimizer (optional)
firebase-admin>=6.0.0  # For FirebaseClient
pika>=1.0.0            # For RabbitMQ (in rabbitmq_client)
requests>=2.0.0        # For HTTP requests (PDF download, Papago)
pypdf>=3.0.0           # For PDF extraction
```

### Optional Packages

```python
anthropic  # Only needed for enhanced_evidence_pipeline.py
```

---

## Recommendations Summary

### 🔴 Critical Fixes

1. **worker.py - Fix 5 broken imports:**
   - `llm_analysis_optimized` → `llm_analysis`
   - `neo4j_graph_optimized` → `neo4j_graph`
   - `qdrant_storage_optimized` → `qdrant_storage`
   - `extract_pdf_fast` → `extract_pdf_enhanced`
   - Update all function calls

### 🟡 Cleanup

2. **Remove unused imports:**
   - `translate_batch` from worker.py
   - `find_or_merge_node`, `add_evidence_to_node` from worker.py
   - `Evidence` model from worker.py (not instantiated)

3. **Fix config import in main_pipeline.py:**
   - Change `from config import` to `from src.config import`

### 🟢 Enhancements

4. **Rename duplicate function:**
   - `create_gap_suggestion_node` in resource_discovery.py → `create_resource_gap_node`

5. **Document function aliases:**
   - Add comment in llm_analysis.py explaining why `extract_merge_optimized_structure` exists

---

## Testing Checklist

After fixing imports, test:

- [ ] `python3 worker.py` - Should start without ImportError
- [ ] `python3 worker_enhanced.py` - Should still work
- [ ] `python3 test_publisher.py` - Should publish test message
- [ ] Process one test PDF - End-to-end test
- [ ] Check Neo4j - Verify nodes created
- [ ] Check Qdrant - Verify vectors stored
- [ ] Check Firebase - Verify results pushed

---

**Analysis Complete**
