# Critical Issues: Frontend Evidence/Upload & Worker Algorithm Updates

## Problem Summary

This issue tracks two critical problems that need to be addressed:

---

## 1. Frontend Issues

### 1.1 Question Raise Display in Evidence
**Current behavior:** Questions raised in evidence are not properly separated and displayed on the node level.

**Expected behavior:** Questions should be extracted from evidence and displayed at the node level for better visibility and organization.

**Impact:** Users cannot easily see which questions are associated with specific nodes, reducing usability.

---

### 1.2 File Upload in Workspace
**Current behavior:** File upload functionality in workspace is not fully implemented.

**Required implementation:**
1. **Upload to Cloudinary:** Files should be uploaded to Cloudinary first
2. **Convert to URL:** Get the Cloudinary URL for the uploaded file
3. **Send to Backend:** Send the Cloudinary URL to Backend, treating it the same as when a user provides a link directly

**Flow:**
```
User selects file → Upload to Cloudinary → Get URL → Send to Backend (same as link upload)
```

**Impact:** Users cannot upload local files, only links, limiting workspace functionality.

---

## 2. Worker.py Algorithm Issues

### 2.1 Still Using Old Chunk-based Logic
**Current behavior:** `worker.py` is still stuck in the old logic that processes documents using chunking approach.

**Expected behavior:** Should use the **top-down approach** instead:
- Start with high-level document structure
- Break down hierarchically into sections, subsections, etc.
- Create a proper knowledge tree structure

**Impact:**
- Inefficient processing
- Poor knowledge tree structure
- Does not align with the current backend architecture

**References:**
- The backend expects a hierarchical tree structure from worker
- Current chunking approach creates flat, disconnected nodes

---

### 2.2 Missing Gap Suggestion for Leaf Nodes
**Current behavior:** `worker.py` does not call gap suggestion generation for leaf nodes after processing.

**Expected behavior:** After creating the knowledge tree, `worker.py` should:
1. Identify all leaf nodes
2. Call gap suggestion service for each leaf node
3. Store the generated suggestions

**Reference Implementation:** The Backend already handles this in `CreateKnowledgeNodeCommandHandler.cs` lines 274-388, specifically the `ProcessGapSuggestionsForCopiedNodesAsync` method.

**Code Reference:**
```csharp
private async Task ProcessGapSuggestionsForCopiedNodesAsync(
    List<Domain.Entities.KnowledgeNode> copiedNodes,
    string workspaceId,
    CancellationToken cancellationToken)
{
    // Get all leaf nodes from copied nodes
    var leafNodes = copiedNodes.Where(n => n.IsLeafNode()).ToList();

    // Check which leaf nodes don't have gap suggestions
    foreach (var leafNode in leafNodes)
    {
        var hasSuggestions = await _knowledgeTreeRepository.HasGapSuggestionsAsync(
            leafNode.Id,
            cancellationToken);

        if (!hasSuggestions)
        {
            nodesNeedingSuggestions.Add(leafNode);
        }
    }

    // Generate gap suggestions for ALL nodes in parallel
    var gapSuggestionTasks = nodesNeedingSuggestions.Select(async leafNode =>
    {
        var suggestions = await _gapSuggestionService.GenerateGapSuggestionsAsync(
            leafNode,
            allNodesInWorkspace,
            cancellationToken);

        if (suggestions.Count > 0)
        {
            await _knowledgeTreeRepository.SaveGapSuggestionsAsync(
                leafNode.Id,
                suggestions,
                cancellationToken);
        }
    }).ToList();

    await Task.WhenAll(gapSuggestionTasks);
}
```

**Impact:**
- Leaf nodes processed by worker don't have gap suggestions
- Only nodes that are copied have gap suggestions
- Inconsistent user experience between copied and newly processed nodes

---

## Action Items

### Frontend Team
- [ ] **Task 1.1:** Implement question extraction from evidence and display on node level
  - Extract questions from evidence data structure
  - Add UI component to display questions on node cards/views
  - Ensure proper linking between questions and their source evidence

- [ ] **Task 1.2:** Implement Cloudinary upload flow for workspace file uploads
  - Add file picker component in workspace
  - Implement Cloudinary upload integration
  - Convert uploaded file to Cloudinary URL
  - Send URL to Backend (reuse existing link upload logic)
  - Add loading states and error handling

### Backend/Worker Team
- [ ] **Task 2.1:** Refactor `worker.py` to use top-down processing approach
  - Remove chunking-based logic
  - Implement hierarchical document parsing (top-down)
  - Create proper parent-child relationships in knowledge tree
  - Test with various document types (PDF, etc.)

- [ ] **Task 2.2:** Add gap suggestion generation for leaf nodes in `worker.py`
  - Identify leaf nodes after tree creation
  - Implement gap suggestion service call
  - Handle parallel processing for efficiency
  - Add proper error handling and logging
  - Follow the pattern from `CreateKnowledgeNodeCommandHandler.cs:274-388`

---

## Related Code References

**Backend:**
- [`Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs:274-388`](Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs#L274-L388) - Gap suggestion logic reference implementation
- [`Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs:73-117`](Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs#L73-L117) - Node copying logic
- [`Backend/NavNexus.Application/Workspace/Commands/CreateWorkspaceCommandHandler.cs:55-94`](Backend/NavNexus.Application/Workspace/Commands/CreateWorkspaceCommandHandler.cs#L55-L94) - Workspace creation with file handling

**Worker:**
- `worker.py` - Needs refactoring for top-down approach and gap suggestions

**Frontend:**
- Cloudinary integration components
- Evidence/Node display components

---

## Technical Details

### Worker Top-Down Approach Algorithm
```python
# Pseudocode for top-down approach
def process_document_topdown(document_url, workspace_id):
    # 1. Parse document structure
    document = parse_document(document_url)

    # 2. Create root node (document level)
    root_node = create_node(
        name=document.title,
        level=0,
        workspace_id=workspace_id
    )

    # 3. Recursively create child nodes
    for section in document.sections:
        section_node = create_node(
            name=section.title,
            parent_id=root_node.id,
            level=1,
            workspace_id=workspace_id
        )

        # Continue recursively for subsections
        process_section(section, section_node, level=2)

    # 4. Identify leaf nodes
    leaf_nodes = get_leaf_nodes(root_node)

    # 5. Generate gap suggestions for leaf nodes
    for leaf_node in leaf_nodes:
        generate_gap_suggestions(leaf_node, workspace_id)
```

### Gap Suggestion Service Call
```python
# Pseudocode for gap suggestion in worker
async def generate_gap_suggestions_for_leaf_nodes(workspace_id, leaf_nodes):
    # Get all nodes in workspace for context
    all_nodes = get_all_nodes_in_workspace(workspace_id)

    # Process in parallel
    tasks = []
    for leaf_node in leaf_nodes:
        # Check if already has suggestions
        has_suggestions = await check_gap_suggestions_exist(leaf_node.id)

        if not has_suggestions:
            task = generate_and_save_gap_suggestions(
                leaf_node=leaf_node,
                all_nodes=all_nodes,
                workspace_id=workspace_id
            )
            tasks.append(task)

    # Wait for all to complete
    await asyncio.gather(*tasks)
```

---

## Priority
🔴 **High Priority** - These issues affect core functionality and user experience.

## Estimated Effort
- **Frontend Tasks:** 3-5 days
  - Task 1.1: 1-2 days
  - Task 1.2: 2-3 days
- **Worker Tasks:** 5-7 days
  - Task 2.1: 3-4 days (major refactoring)
  - Task 2.2: 2-3 days

## Dependencies
- Worker tasks should be done together as they're related
- Frontend tasks are independent and can be done in parallel
- Task 2.2 requires gap suggestion service to be accessible from worker

## Suggested Labels
`enhancement`, `bug`, `frontend`, `backend`, `worker`, `high-priority`, `knowledge-tree`

---

## Testing Checklist

### Frontend Testing
- [ ] Questions display correctly on nodes
- [ ] File upload to Cloudinary succeeds
- [ ] Uploaded files trigger backend processing
- [ ] Error handling works for failed uploads
- [ ] Loading states are clear to users

### Worker Testing
- [ ] Top-down processing creates correct tree structure
- [ ] Parent-child relationships are correct
- [ ] Leaf nodes are properly identified
- [ ] Gap suggestions are generated for all leaf nodes
- [ ] Processing handles various document types
- [ ] Error handling and logging work correctly
