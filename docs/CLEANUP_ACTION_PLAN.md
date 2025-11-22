# Code Cleanup - Action Plan
**Quick Reference Guide**

---

## 🚨 CRITICAL: Fix worker.py Import Errors

### Problem
`worker.py` has **5 broken imports** that will cause runtime errors:

```python
# Line 28: ❌ BROKEN
from src.pipeline.pdf_extraction import extract_pdf_fast

# Lines 35-37: ❌ BROKEN - Files don't exist!
from src.pipeline.llm_analysis_optimized import extract_hierarchical_structure_compact, process_chunks_ultra_compact
from src.pipeline.neo4j_graph_optimized import create_hierarchical_graph_with_cascading_dedup
from src.pipeline.qdrant_storage_optimized import store_chunks_in_qdrant
```

### Solution Options

#### Option A: Fix worker.py (Recommended if you need both workers)

**Step 1:** Update imports (Lines 28, 35-37, 41)
```python
# Line 28 - CHANGE:
from src.pipeline.pdf_extraction import extract_pdf_enhanced

# Line 35 - CHANGE:
from src.pipeline.llm_analysis import extract_merge_optimized_structure, analyze_chunks_for_merging

# Line 36 - CHANGE:
from src.pipeline.neo4j_graph import create_hierarchical_knowledge_graph, now_iso

# Line 37 - CHANGE:
from src.pipeline.qdrant_storage import store_chunks_in_qdrant

# Line 41 - REMOVE unused imports:
# DELETE: find_or_merge_node, add_evidence_to_node (keep now_iso)
```

**Step 2:** Update function calls

Find and replace these function names:
```python
# Around line 149:
extract_pdf_fast → extract_pdf_enhanced

# Around line 155:
extract_hierarchical_structure_compact → extract_merge_optimized_structure

# Around line 195:
create_hierarchical_graph_with_cascading_dedup → create_hierarchical_knowledge_graph

# Around line 216:
process_chunks_ultra_compact → analyze_chunks_for_merging
```

**Step 3:** Adjust function parameters if needed
```python
# extract_pdf_enhanced returns (text, language, metadata)
# Instead of (text, language)
# Update line ~149:
full_text, lang, pdf_metadata = extract_pdf_enhanced(pdf_url, max_pages=25)

# analyze_chunks_for_merging returns different format
# Check return structure and adapt lines ~216-234
```

#### Option B: Use worker_enhanced.py instead (Recommended for simplicity)

```bash
# Rename files
mv worker.py worker_legacy.py  # Archive old worker
mv worker_enhanced.py worker.py  # Use working version

# Update any deployment scripts that reference worker_enhanced.py
# Update documentation
```

---

## 🗑️ Step-by-Step File Deletion

### 1. Test/Example Files to Delete (Safe)

```bash
# Execute these commands:
cd /Users/anhnon/NavNexus/RabbitMQ

# Delete test files
rm test_worker.py                          # 233 lines
rm test_enhanced_pipeline.py               # 275 lines
rm test_chunking_positions.py              # 44 lines
rm example_evidence_with_positions.py      # 137 lines

# Delete temporary test
rm papago_test.py                          # 32 lines

# Delete analysis scripts (after reviewing reports)
rm analyze_imports.py                      # ~150 lines
rm analyze_code_usage.py                   # ~150 lines

# Total removed: ~1,021 lines
```

### 2. Enhanced Pipeline Files (Decision Required)

**If keeping as experimental:**
```bash
mkdir -p experimental
mv src/pipeline/enhanced_evidence_pipeline.py experimental/
mv src/pipeline/evidence_optimizer.py experimental/
```

**If archiving:**
```bash
mkdir -p archive/$(date +%Y%m%d)
mv src/pipeline/enhanced_evidence_pipeline.py archive/$(date +%Y%m%d)/
mv src/pipeline/evidence_optimizer.py archive/$(date +%Y%m%d)/
```

**If deleting:**
```bash
rm src/pipeline/enhanced_evidence_pipeline.py
rm src/pipeline/evidence_optimizer.py
```

### 3. Clean Python Cache

```bash
# Remove all cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

---

## 🔧 Fix Duplicate Function

### Problem
`create_gap_suggestion_node` defined twice with different signatures:
- `src/pipeline/neo4j_graph.py:128`
- `src/pipeline/resource_discovery.py:14`

### Solution
Rename the one in resource_discovery.py:

**File:** `src/pipeline/resource_discovery.py`

```python
# Line 14 - CHANGE function name:
# BEFORE:
def create_gap_suggestion_node(session, gap: GapSuggestion, target_node_id: str) -> str:

# AFTER:
def create_resource_gap_node(session, gap: GapSuggestion, target_node_id: str) -> str:
```

Then update all calls to this function in the same file:
```bash
# In resource_discovery.py, find and replace:
create_gap_suggestion_node → create_resource_gap_node
# (Only within the same file)
```

---

## 📋 Checklist

### Pre-Cleanup

- [ ] Review both analysis reports:
  - [ ] `CODE_CLEANUP_REPORT.md`
  - [ ] `DETAILED_IMPORT_ANALYSIS.md`
- [ ] Backup current code:
  ```bash
  git add -A
  git commit -m "Pre-cleanup backup"
  # OR
  git stash save "Backup before cleanup $(date)"
  ```
- [ ] Decide: Fix worker.py OR use worker_enhanced.py?
- [ ] Decide: Keep/Archive/Delete enhanced pipeline?

### Cleanup Actions

#### Priority 1: Fix Imports (Critical)
- [ ] Option A: Fix worker.py imports (5 changes)
  - [ ] Update import statements
  - [ ] Update function calls
  - [ ] Test: `python3 worker.py` (should not crash)
- [ ] OR Option B: Switch to worker_enhanced.py
  - [ ] Rename files
  - [ ] Update deployment scripts

#### Priority 2: Delete Files
- [ ] Delete test files (7 files)
- [ ] Decide on enhanced pipeline (2 files)
- [ ] Clean Python cache

#### Priority 3: Fix Duplicates
- [ ] Rename `create_gap_suggestion_node` in resource_discovery.py
- [ ] Update function calls in same file
- [ ] Test: Check resource discovery still works

#### Priority 4: Remove Unused Imports
- [ ] worker.py: Remove `translate_batch`
- [ ] worker.py: Remove `find_or_merge_node`, `add_evidence_to_node`
- [ ] worker.py: Remove `Evidence` import (if not used)

### Post-Cleanup

- [ ] Run tests:
  ```bash
  python3 -m pytest __tests__/
  ```
- [ ] Test worker:
  ```bash
  # Terminal 1: Start worker
  python3 worker.py

  # Terminal 2: Send test message
  python3 test_publisher.py
  ```
- [ ] Verify processing:
  - [ ] Check worker logs for errors
  - [ ] Check Neo4j for created nodes
  - [ ] Check Qdrant for vectors
  - [ ] Check Firebase for results
- [ ] Commit changes:
  ```bash
  git add -A
  git commit -m "Code cleanup: fix imports, remove test files, resolve duplicates"
  git push
  ```
- [ ] Update documentation:
  - [ ] README.md
  - [ ] Deployment guides
  - [ ] API documentation (if any)

---

## 🧪 Testing Commands

### Test Import Fixes
```bash
# Test that worker starts without errors
python3 worker.py &
WORKER_PID=$!
sleep 2
kill $WORKER_PID

# Should see:
# ✓ Connected to Qdrant, Neo4j & Firebase
# ✓ Worker ready and listening to queue: pdf_jobs_queue
```

### Test End-to-End
```bash
# 1. Start worker
python3 worker.py

# 2. In another terminal, publish test message
python3 test_publisher.py

# 3. Watch worker logs for processing
# Should complete without ImportError or ModuleNotFoundError
```

### Test Specific Functions
```python
# Test imports in Python shell
python3 << 'EOF'
from src.pipeline.llm_analysis import extract_merge_optimized_structure, analyze_chunks_for_merging
from src.pipeline.neo4j_graph import create_hierarchical_knowledge_graph
from src.pipeline.qdrant_storage import store_chunks_in_qdrant
from src.pipeline.pdf_extraction import extract_pdf_enhanced
print("✅ All imports successful!")
EOF
```

---

## 📊 Expected Impact

### Before Cleanup
- **Total Python files:** 37
- **Root test files:** 9
- **Import errors:** 5 (worker.py)
- **Duplicate functions:** 1 (create_gap_suggestion_node)
- **Unused imports:** ~4
- **Cache files:** Many

### After Cleanup
- **Total Python files:** 28 (-9 test files)
- **Root test files:** 1 (test_publisher.py)
- **Import errors:** 0 ✅
- **Duplicate functions:** 0 ✅
- **Unused imports:** 0 ✅
- **Cache files:** 0 ✅

### Code Reduction
- **Lines removed:** ~1,021 (test files)
- **Files removed:** 7-9 (depending on enhanced pipeline decision)
- **Disk space saved:** ~50 KB (test files + cache)

---

## 🚀 Quick Start (After Cleanup)

### For developers:

```bash
# 1. Clone repo
git clone <repo-url>
cd RabbitMQ

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Start worker
python3 worker.py

# 5. Test with sample PDF
python3 test_publisher.py
```

### For deployment:

```bash
# Use clean, working worker
python3 worker.py

# OR use worker_enhanced.py if you prefer
python3 worker_enhanced.py
```

---

## 📝 Git Commit Messages

Use these commit messages for each step:

```bash
# After fixing worker.py imports
git commit -m "fix(worker): correct import paths for pipeline modules

- Change llm_analysis_optimized to llm_analysis
- Change neo4j_graph_optimized to neo4j_graph
- Change qdrant_storage_optimized to qdrant_storage
- Update extract_pdf_fast to extract_pdf_enhanced
- Update function calls to match new imports"

# After deleting test files
git commit -m "chore: remove test and example files

- Remove test_worker.py, test_enhanced_pipeline.py
- Remove example_evidence_with_positions.py
- Remove test_chunking_positions.py
- Remove papago_test.py
- Remove analysis scripts

Total: 1,021 lines removed"

# After fixing duplicates
git commit -m "refactor(resource_discovery): rename duplicate function

- Rename create_gap_suggestion_node to create_resource_gap_node
- Resolves naming conflict with neo4j_graph.py
- Update all references in resource_discovery.py"

# After removing unused imports
git commit -m "chore: remove unused imports

- Remove unused translate_batch from worker.py
- Remove unused neo4j_graph functions
- Remove unused Evidence import"

# After cleanup
git commit -m "chore: clean Python cache files

- Remove __pycache__ directories
- Remove .pyc and .pyo files"
```

---

## 🔍 Validation Script

Save as `validate_cleanup.sh`:

```bash
#!/bin/bash
# Validate that cleanup was successful

echo "🔍 Validating cleanup..."
echo ""

# Check 1: Test files removed
echo "✓ Checking test files removed..."
test_files=(
    "test_worker.py"
    "test_enhanced_pipeline.py"
    "test_chunking_positions.py"
    "example_evidence_with_positions.py"
    "papago_test.py"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ $file still exists"
    else
        echo "  ✅ $file removed"
    fi
done

# Check 2: Worker imports
echo ""
echo "✓ Checking worker.py imports..."
if grep -q "llm_analysis_optimized" worker.py 2>/dev/null; then
    echo "  ❌ worker.py still has broken imports"
else
    echo "  ✅ worker.py imports fixed"
fi

# Check 3: Python cache
echo ""
echo "✓ Checking Python cache..."
cache_count=$(find . -type d -name "__pycache__" | wc -l)
if [ "$cache_count" -gt 0 ]; then
    echo "  ⚠️  Found $cache_count __pycache__ directories"
else
    echo "  ✅ No Python cache found"
fi

# Check 4: Can import modules
echo ""
echo "✓ Testing imports..."
python3 << 'EOF'
try:
    from src.pipeline.llm_analysis import extract_merge_optimized_structure
    from src.pipeline.neo4j_graph import create_hierarchical_knowledge_graph
    from src.pipeline.qdrant_storage import store_chunks_in_qdrant
    print("  ✅ All critical imports work")
except ImportError as e:
    print(f"  ❌ Import error: {e}")
EOF

echo ""
echo "✅ Validation complete!"
```

Run with: `bash validate_cleanup.sh`

---

## 🆘 Rollback Plan

If something goes wrong:

### Quick Rollback
```bash
# If you used git stash:
git stash pop

# If you made a backup commit:
git log  # Find the backup commit hash
git reset --hard <commit-hash>
```

### Selective Rollback
```bash
# Restore specific files
git checkout HEAD~1 -- worker.py
git checkout HEAD~1 -- test_worker.py

# Restore directory
git checkout HEAD~1 -- src/pipeline/
```

---

## 📞 Support

If you encounter issues after cleanup:

1. Check validation script output
2. Review error logs
3. Compare with backup (git diff)
4. Check this action plan for missed steps
5. Review detailed analysis reports

---

**Action Plan Created:** 2025-11-19
**Last Updated:** 2025-11-19
