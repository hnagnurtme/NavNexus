# Issue: Tối ưu hóa RabbitMQ Worker và Frontend UX cho Knowledge Graph Build

## 📋 Tóm tắt

Hiện tại logic backend khi tạo workspace hoặc upload link mới đã hoàn thiện với 2 trường hợp:
- **Status = SUCCESS**: Tất cả files đã tồn tại trong workspace khác, đã copy xong → không cần xử lý thêm
- **Status = PENDING**: Có files mới cần xử lý → gửi lên RabbitMQ queue

**Vấn đề:**
1. ⚠️ Folder `RabbitMQ/` hiện tại quá lộn xộn, không tuân theo chuẩn của `seed.py`
2. ⚠️ Frontend chưa xử lý đúng 2 trường hợp trên với UX phù hợp
3. ⚠️ Worker cần xử lý data theo đúng format như `data2.json` (nodes, evidences, gapSuggestions)

> **🚨 QUAN TRỌNG:**
> - **Worker hiện tại đang hoạt động SAI HOÀN TOÀN** - cần viết lại từ đầu
> - **KHÔNG SỬA worker.py hiện tại** - chỉ tham khảo để hiểu flow
> - **CHỈ TẬP TRUNG VÀO**: `seed.py`, `data2.json`, `data3.json` làm nguồn chân lý duy nhất
> - **Backend API structure**: Tham khảo [`docs/swagger.json`](../docs/swagger.json) để biết cấu trúc endpoints và response format

---

## 🎯 Mục tiêu

### 1. Backend Worker (RabbitMQ folder)

#### Yêu cầu:
Worker cần xử lý PDF và tạo data theo đúng chuẩn như khi dùng `seed.py`:
- ✅ Tạo **KnowledgeNode** với đầy đủ properties (Id, Type, Name, Synthesis, WorkspaceId, Level, SourceCount, TotalConfidence, CreatedAt, UpdatedAt, ParentId)
- ✅ Tạo **Evidence** với đầy đủ properties (Id, NodeId, SourceId, SourceName, ChunkId, Text, Page, Confidence, Language, HierarchyPath, Concepts, KeyClaims, QuestionsRaised, EvidenceStrength)
- ✅ Tạo **GapSuggestion** (Id, NodeId, SuggestionText, TargetNodeId, SimilarityScore)
- ✅ Tạo relationships đúng chuẩn: HAS_SUBCATEGORY, CONTAINS_CONCEPT, HAS_DETAIL, HAS_EVIDENCE, HAS_SUGGESTION

#### ⭐ File tham khảo (NGUỒN CHÂN LÝ):
- **Data structure**:
  - [`RabbitMQ/mock/data2.json`](../RabbitMQ/mock/data2.json) - ⭐⭐⭐ **CHUẨN chính** - Cấu trúc data mục tiêu
  - [`RabbitMQ/mock/data3.json`](../RabbitMQ/mock/data3.json) - ⭐⭐⭐ **CHUẨN chính** - Ví dụ thêm
- **Seed logic**: [`RabbitMQ/seed.py`](../RabbitMQ/seed.py) - ⭐⭐⭐ **CHUẨN chính** - Logic insert vào Neo4j đúng chuẩn
- **Backend API**: [`docs/swagger.json`](../docs/swagger.json) - API structure và response format
- **Current worker**: [`RabbitMQ/worker.py`](../RabbitMQ/worker.py) - ⚠️ **ĐANG SAI** - CHỈ tham khảo flow, KHÔNG copy code

#### ⚠️ Vấn đề hiện tại trong folder RabbitMQ:
```
RabbitMQ/
├── src/pipeline/          ❌❌❌ ĐANG SAI - Logic xử lý không đúng chuẩn
│   ├── main_pipeline.py   ❌ Output không match data2.json
│   ├── pdf_extraction.py
│   ├── chunking.py
│   ├── llm_analysis.py    ❌ Thiếu Concepts, KeyClaims, QuestionsRaised
│   ├── neo4j_graph.py     ❌ Relationships không đúng chuẩn
│   ├── qdrant_storage.py
│   └── ...nhiều file khác
├── src/model/            ⚠️ Models chưa đầy đủ properties như data2.json
│   ├── KnowledgeNode.py  ⚠️ Thiếu TotalConfidence, SourceCount, etc.
│   ├── Evidence.py       ⚠️ Thiếu Concepts, KeyClaims, QuestionsRaised
│   └── GapSuggestion.py  ⚠️ Thiếu SimilarityScore
└── worker.py             ❌❌❌ ĐANG SAI HOÀN TOÀN - Cần viết lại
```

> **🔴 CẢNH BÁO QUAN TRỌNG:**
> Worker hiện tại (`worker.py` và `src/pipeline/`) đang tạo data **SAI HOÀN TOÀN**:
> - ❌ Thiếu nhiều properties quan trọng (Concepts, KeyClaims, QuestionsRaised, etc.)
> - ❌ Relationships không đúng chuẩn (thiếu HAS_DETAIL, CONTAINS_CONCEPT)
> - ❌ Không có GapSuggestion generation
> - ❌ Structure không match với `data2.json` / `data3.json`
>
> **✅ GIẢI PHÁP:**
> - Viết lại worker hoàn toàn mới
> - Chỉ copy logic từ `seed.py` (cách insert vào Neo4j)
> - Đảm bảo output 100% giống `data2.json` / `data3.json`

#### 🎯 Action items (THEO THỨ TỰ):

**BƯỚC 1: Phân tích nguồn chân lý**
1. 📖 **Đọc và hiểu `data2.json` + `data3.json`**:
   - Map ra tất cả properties của KnowledgeNode
   - Map ra tất cả properties của Evidence (đặc biệt: Concepts, KeyClaims, QuestionsRaised)
   - Map ra tất cả properties của GapSuggestion
   - Ghi chú các relationships cần tạo

2. 📖 **Đọc và hiểu `seed.py`**:
   - Logic tạo KnowledgeNode với MERGE (tránh duplicate)
   - Logic tạo Evidence và link với node (`HAS_EVIDENCE` relationship)
   - Logic tạo GapSuggestion và link với node (`HAS_SUGGESTION` relationship)
   - Logic tạo hierarchical relationships (HAS_SUBCATEGORY, CONTAINS_CONCEPT, HAS_DETAIL)

3. 📖 **Đọc `swagger.json`**:
   - Hiểu cấu trúc API endpoints
   - Hiểu response format backend trả về
   - Hiểu cấu trúc data frontend cần fetch

**BƯỚC 2: Viết lại worker hoàn toàn mới**
1. 🆕 **Tạo `new_worker.py`** (KHÔNG sửa worker.py cũ):
   - Copy CHÍNH XÁC logic insert từ `seed.py`:
     - `create_knowledge_node()` - MERGE với đầy đủ properties
     - `create_evidence_node()` - MERGE với Concepts, KeyClaims, QuestionsRaised
     - `create_gap_suggestion_node()` - MERGE với SimilarityScore
     - `create_parent_child_relationship()` - Tạo đúng relationship types

2. 🔧 **Pipeline xử lý PDF**:
   - Extract text từ PDF
   - **LLM analysis** để tạo:
     - Concepts (list of concepts found in chunk)
     - KeyClaims (key claims/statements)
     - QuestionsRaised (questions raised by the evidence)
     - EvidenceStrength (confidence score)
   - Tạo KnowledgeNode hierarchy (domain → category → concept → subconcept)
   - Generate GapSuggestion với SimilarityScore

3. ✅ **Verify output 100% match**:
   - Chạy worker với 1 PDF mẫu
   - Export data từ Neo4j
   - So sánh với `data2.json` - PHẢI GIỐNG HỆT

**BƯỚC 3: Firebase integration**
1. Push job result với đúng structure:
   ```json
   {
     "status": "completed",
     "workspaceId": "...",
     "totalFiles": N,
     "successful": M,
     "results": [...]
   }
   ```

**BƯỚC 4: Testing**
1. Test với PDF đơn giản
2. Test với multiple PDFs
3. Verify tất cả properties được tạo
4. Verify tất cả relationships đúng chuẩn

---

### 2. Frontend (UI/UX)

#### Flow mong muốn:

```
User upload PDF/link và bấm "Build Knowledge Graph"
                    ↓
        POST /api/knowledge-tree
                    ↓
        Backend check duplicate
                    ↓
        ┌──────────────────────────────┐
        │                              │
    ✅ SUCCESS                    ⏳ PENDING
(All files existed)        (New files to process)
        │                              │
        ↓                              ↓
  Fetch API ngay               Show loading animation
  GET /knowledge-tree          Register Firebase listener
        │                              │
        ↓                              ↓
  Display graph                Wait for job completion
                                       │
                                       ↓
                              Firebase event: status=SUCCESS
                                       │
                                       ↓
                               Fetch API & display graph
```

#### Yêu cầu Frontend:

**File cần sửa**: [`Frontend/src/pages/workspace/components/control/ControlPanel.tsx`](../Frontend/src/pages/workspace/components/control/ControlPanel.tsx)

**1. Khi bấm "Build Knowledge Graph" button:**
```typescript
async function handleBuildKnowledgeGraph() {
  // Call API
  const response = await POST('/api/knowledge-tree', {
    workspaceId: currentWorkspaceId,
    filePaths: uploadedItems.map(item => item.url)
  });

  if (response.status === "SUCCESS") {
    // ✅ Case 1: All files already exist
    // → Fetch graph data immediately
    await fetchKnowledgeGraph(workspaceId);
    showSuccessToast("Knowledge graph ready!");
  }
  else if (response.status === "PENDING") {
    // ⏳ Case 2: Processing new files
    // → Show loading animation
    setIsBuilding(true);

    // → Register Firebase Realtime Database listener
    const jobId = response.messageId;
    listenToJobStatus(jobId, (status) => {
      if (status === "completed") {
        setIsBuilding(false);
        fetchKnowledgeGraph(workspaceId);
        showSuccessToast("Knowledge graph built successfully!");
      } else if (status === "failed") {
        setIsBuilding(false);
        showErrorToast("Failed to build knowledge graph");
      }
    });
  }
}
```

**2. Loading Animation khi PENDING:**
```tsx
{isBuilding && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
    <div className="bg-slate-900 rounded-2xl p-8 text-center">
      <Loader className="animate-spin w-16 h-16 mx-auto mb-4 text-emerald-400" />
      <h3 className="text-xl font-semibold text-white mb-2">
        Building Knowledge Graph...
      </h3>
      <p className="text-white/60">
        Processing your documents. This may take a few minutes.
      </p>
    </div>
  </div>
)}
```

**3. Firebase Realtime Database Integration:**
```typescript
// utils/firebase-listener.ts
import { getDatabase, ref, onValue, off } from 'firebase/database';

export function listenToJobStatus(
  jobId: string,
  onStatusChange: (status: string, data?: any) => void
) {
  const db = getDatabase();
  const jobRef = ref(db, `jobs/${jobId}`);

  const unsubscribe = onValue(jobRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
      onStatusChange(data.status, data);

      // Cleanup listener if job completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        off(jobRef);
      }
    }
  });

  return unsubscribe;
}
```

#### Firebase Realtime Database Structure:
```json
{
  "jobs": {
    "{jobId}": {
      "status": "pending" | "completed" | "failed",
      "workspaceId": "workspace-123",
      "totalFiles": 3,
      "successful": 2,
      "failed": 1,
      "processingTimeMs": 45000,
      "timestamp": "2025-01-20T10:30:00Z",
      "results": [...]
    }
  }
}
```

---

## 📝 Implementation Checklist

### Backend (RabbitMQ Worker)
- [ ] Refactor `worker.py` để output đúng format `data2.json`
- [ ] Verify tất cả KnowledgeNode properties được tạo đầy đủ
- [ ] Verify Evidence được tạo với đủ metadata (Concepts, KeyClaims, QuestionsRaised)
- [ ] Verify GapSuggestion được tạo và link đúng
- [ ] Verify relationships (HAS_SUBCATEGORY, CONTAINS_CONCEPT, etc.) được tạo đúng
- [ ] Push job result lên Firebase Realtime Database với cấu trúc rõ ràng
- [ ] Cleanup folder `RabbitMQ/src/pipeline/` - loại bỏ code không dùng
- [ ] Test end-to-end với file PDF thật

### Frontend (UI/UX)
- [ ] Thêm state `isBuilding` vào ControlPanel
- [ ] Xử lý response.status === "SUCCESS" → fetch API ngay
- [ ] Xử lý response.status === "PENDING" → show loading
- [ ] Implement Firebase listener cho job status
- [ ] Design loading animation UX
- [ ] Handle job completion → fetch graph data
- [ ] Handle job failure → show error message
- [ ] Test với cả 2 scenarios (SUCCESS và PENDING)

---

## 🔗 Related Files

### Backend
- [`Backend/NavNexus.API/Controller/KnowledgeTreeController.cs`](../Backend/NavNexus.API/Controller/KnowledgeTreeController.cs) - API endpoint
- [`Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs`](../Backend/NavNexus.Application/KnowledgeTree/Commands/CreateKnowledgeNodeCommandHandler.cs) - Business logic (✅ đã hoàn thiện)

### RabbitMQ Worker - ⭐ NGUỒN CHÂN LÝ
- [`RabbitMQ/seed.py`](../RabbitMQ/seed.py) - ⭐⭐⭐ **CHUẨN CHÍNH** - Logic insert vào Neo4j
- [`RabbitMQ/mock/data2.json`](../RabbitMQ/mock/data2.json) - ⭐⭐⭐ **CHUẨN CHÍNH** - Target data structure
- [`RabbitMQ/mock/data3.json`](../RabbitMQ/mock/data3.json) - ⭐⭐⭐ **CHUẨN CHÍNH** - Ví dụ thêm
- [`docs/swagger.json`](../docs/swagger.json) - ⭐⭐ Backend API structure

### RabbitMQ Worker - ⚠️ HIỆN TẠI (SAI - CHỈ THAM KHẢO)
- [`RabbitMQ/worker.py`](../RabbitMQ/worker.py) - ❌ ĐANG SAI - chỉ tham khảo flow
- [`RabbitMQ/src/pipeline/main_pipeline.py`](../RabbitMQ/src/pipeline/main_pipeline.py) - ❌ Output không đúng
- [`RabbitMQ/src/model/KnowledgeNode.py`](../RabbitMQ/src/model/KnowledgeNode.py) - ⚠️ Thiếu properties
- [`RabbitMQ/src/model/Evidence.py`](../RabbitMQ/src/model/Evidence.py) - ⚠️ Thiếu Concepts, KeyClaims
- [`RabbitMQ/src/model/GapSuggestion.py`](../RabbitMQ/src/model/GapSuggestion.py) - ⚠️ Thiếu SimilarityScore

### Frontend
- [`Frontend/src/pages/workspace/components/control/ControlPanel.tsx`](../Frontend/src/pages/workspace/components/control/ControlPanel.tsx) - Upload UI
- [`Frontend/src/contexts/WorkSpaceContext.tsx`](../Frontend/src/contexts/WorkSpaceContext.tsx) - Workspace state management

---

## 📊 Success Criteria

### Backend Worker:
✅ Worker tạo data đúng format `data2.json`
✅ Tất cả nodes có đầy đủ properties và metadata
✅ Relationships được tạo đúng chuẩn
✅ Job status được push lên Firebase realtime
✅ Code trong folder RabbitMQ gọn gàng, dễ maintain

### Frontend:
✅ Status SUCCESS → fetch API ngay, không có delay
✅ Status PENDING → loading animation mượt mà
✅ Firebase listener hoạt động ổn định
✅ Job completion → graph hiển thị ngay lập tức
✅ Error handling rõ ràng, user-friendly

---

## 🚀 Priority

**HIGH** - Ảnh hưởng trực tiếp đến UX khi user upload documents

## 💡 Notes

### 🚨 Cực kỳ quan trọng:
1. **Worker hiện tại ĐANG SAI HOÀN TOÀN** - output không match `data2.json`
2. **KHÔNG sửa code cũ** - viết lại hoàn toàn theo `seed.py` + `data2.json`
3. **Nguồn chân lý duy nhất**: `seed.py`, `data2.json`, `data3.json`
4. **Backend API reference**: `docs/swagger.json` - để hiểu structure endpoints

### Technical notes:
- Firebase Realtime Database URL: `https://navnexus-default-rtdb.firebaseio.com/`
- Worker hiện tại đã có `firebase_client.push_job_result()` - cần verify structure
- Cần test với volume lớn (10+ PDFs) để đảm bảo performance
- Consider adding progress tracking (% completion) trong Firebase cho better UX

### Checklist trước khi implement:
- [ ] Đọc kỹ và hiểu `data2.json` + `data3.json` - note lại TẤT CẢ properties
- [ ] Đọc kỹ `seed.py` - hiểu CHÍNH XÁC logic insert vào Neo4j
- [ ] Đọc `swagger.json` - hiểu API structure
- [ ] KHÔNG copy code từ `worker.py` cũ (chỉ tham khảo flow message handling)

---

## 👥 Stakeholders

- **Backend Team**: Refactor RabbitMQ worker
- **Frontend Team**: Implement loading UX và Firebase listener
- **DevOps**: Monitor Firebase usage và RabbitMQ queue health
