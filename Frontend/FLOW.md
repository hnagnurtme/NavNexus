```
User Opens Page 3 (Workspace)
         │
         ▼
    ┌─────────────────────────────┐
    │  API 1: GET Root Node       │ ◄── Chỉ gọi 1 lần duy nhất
    │  Load node 'root' với       │     (Tree root từ mockKnowledgeTree)
    │  5 children IDs             │
    └─────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │  UI renders:                │
    │  • 1 root node (collapsed)  │
    │  • 5 children nodes         │
    │    (topic-sagsins,          │
    │     topic-rl-ppo, ...)      │
    └─────────────────────────────┘
         │
         │ User clicks [+] expand
         ▼
    ┌─────────────────────────────────────────┐
    │  Promise.all([
    │    API 2: GET Children (fast ~100ms)   │ ◄── Parallel
    │    API 3: GET Details (slow ~500ms)    │ ◄── Parallel  
    │  ])                                     │
    └─────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    API 2 Done    API 3 Done    React Updates
    Add children  Show sidebar   • Children appear
    to tree       Show synthesis • Indent level++
                  Show evidence  • Sidebar fills
```
### API Endpoints Chi tiết
### API 1: Load Forest (Initial Load)
**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/document-trees
```
**Params**:

- `workspaceId` (path): ID của workspace hiện tại

**Response Time**: ~50-100ms

**Backend Logic**:
```typescript
// Pseudo-code
function getDocumentTrees(workspaceId: string): TreeNodeShallow[] {
  const analysis = getAnalysisByWorkspace(workspaceId); // mockAnalysis
  const tree = analysis.tree; // mockKnowledgeTree
  
  // Chỉ lấy các node con trực tiếp của root (level 1 - documents)
  return tree.children.map(docNode => ({
    id: docNode.id,
    name: docNode.name,
    type: docNode.type,
    isGap: docNode.isGap || false,
    isCrossroads: docNode.children.some(child => 
      child.children && child.children.length > 1
    ),
    hasChildren: docNode.children.length > 0
  }));
}
```
**Interface**:
```typescript
export type NodeType = 
  | 'topic' 
  | 'document' 
  | 'problem-domain' 
  | 'algorithm' 
  | 'challenge' 
  | 'feature' 
  | 'concept';

/**
 * TreeNode "Siêu nhẹ" - Chỉ chứa metadata để render
 * KHÔNG bao gồm synthesis, evidence (tiết kiệm bandwidth)
 */
export interface TreeNodeShallow {
  id: string;              // Unique identifier
  name: string;            // Display text (max 100 chars)
  type: NodeType;          // Loại node
  isGap: boolean;          // true = Node "mồ côi" (thiếu tài liệu)
  isCrossroads: boolean;   // true = Node có ≥2 approaches khác nhau
  hasChildren: boolean;    // true = Hiển thị nút [+] expand
}

export type DocumentTreesResponse = TreeNodeShallow[];
```
**JSON Response (từ mockKnowledgeTree)**:
```json
[
  {
    "id": "topic-sagsins",
    "name": "Vấn đề: Tối ưu Mạng SAGSINs",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true
  },
  {
    "id": "topic-rl-ppo",
    "name": "Lĩnh vực: Reinforcement Learning",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true
  },
  {
    "id": "topic-cv",
    "name": "Lĩnh vực: Computer Vision",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true
  },
  {
    "id": "topic-nlp",
    "name": "Lĩnh vực: Natural Language Processing",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true
  },
  {
    "id": "topic-network-infra",
    "name": "Lĩnh vực: Network Infrastructure",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true
  }
]
```

---

### **API 2: Load Children (On Click)**

**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/nodes/{nodeId}/children
```
**Params**:

- `workspaceId` (path): ID workspace
- `nodeId` (path): ID của node được click

**Query Params (optional)**:
```typescript
{
  depth?: number;  // Default: 1 (chỉ load 1 cấp con)
}
```
**Response Time**: ~100-200ms

**Backend Logic**:
```typescript
function getNodeChildren(
  workspaceId: string, 
  nodeId: string, 
  depth: number = 1
): NodeChildrenResponse {
  const node = findNodeInTree(mockKnowledgeTree, nodeId);
  if (!node || !node.children) {
    return { nodes: [], edges: [] };
  }
  
  // Flatten children (chỉ lấy 1 cấp)
  const childNodes: TreeNodeShallow[] = node.children.map(child => ({
    id: child.id,
    name: child.name,
    type: child.type,
    isGap: child.isGap || (child.evidence.length === 0 && !child.children.length),
    isCrossroads: child.children && child.children.length >= 2,
    hasChildren: child.children && child.children.length > 0
  }));
  
  // Tạo edges (parent → children)
  const edges: EdgeData[] = childNodes.map(child => ({
    id: `e-${nodeId}-${child.id}`,
    source: nodeId,
    target: child.id,
    type: 'default' // hoặc 'smoothstep', 'step', etc.
  }));
  
  return { nodes: childNodes, edges };
}
```
**Interface**:
```typescript
export interface EdgeData {
  id: string;          // Unique edge ID
  source: string;      // Parent node ID
  target: string;      // Child node ID
  type?: 'default' | 'smoothstep' | 'step'; // React Flow edge types
}

export interface NodeChildrenResponse {
  nodes: TreeNodeShallow[];  // Mảng các node con mới
  edges: EdgeData[];         // Mảng các cạnh nối cha-con
}
```
**JSON Response (khi click topic-sagsins)**:
```json
{
  "nodes": [
    {
      "id": "topic-latency",
      "name": "Tối ưu Độ trễ (Latency)",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true
    },
    {
      "id": "topic-resource",
      "name": "Tối ưu Tài nguyên (Resource)",
      "type": "topic",
      "isGap": false,
      "isCrossroads": false,
      "hasChildren": true
    }
  ],
  "edges": [
    {
      "id": "e-topic-sagsins-topic-latency",
      "source": "topic-sagsins",
      "target": "topic-latency",
      "type": "smoothstep"
    },
    {
      "id": "e-topic-sagsins-topic-resource",
      "source": "topic-sagsins",
      "target": "topic-resource",
      "type": "smoothstep"
    }
  ]
}
```
**JSON Response (khi click topic-latency - CROSSROADS scenario)**:
```json
{
  "nodes": [
    {
      "id": "sol-A",
      "name": "Giải pháp: Phương pháp A (Lập lịch)",
      "type": "algorithm",
      "isGap": false,
      "isCrossroads": false,
      "hasChildren": true
    },
    {
      "id": "sol-DQN",
      "name": "Giải pháp: DQN (Học Tăng Cường)",
      "type": "algorithm",
      "isGap": false,
      "isCrossroads": false,
      "hasChildren": true
    }
  ],
  "edges": [
    {
      "id": "e-topic-latency-sol-A",
      "source": "topic-latency",
      "target": "sol-A",
      "type": "smoothstep"
    },
    {
      "id": "e-topic-latency-sol-DQN",
      "source": "topic-latency",
      "target": "sol-DQN",
      "type": "smoothstep"
    }
  ]
}
```

---

### **API 3: Load Details (On Click - Parallel)**

**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/nodes/{nodeId}/details
```
**Params**:

- `workspaceId` (path): ID workspace
- `nodeId` (path): ID của node được click

**Response Time**: ~300-800ms (tùy Qdrant query complexity)

**Backend Logic**:
```typescript
async function getNodeDetails(
  workspaceId: string, 
  nodeId: string
): Promise<NodeDetailsResponse> {
  const node = findNodeInTree(mockKnowledgeTree, nodeId);
  if (!node) throw new Error('Node not found');
  
  // 1. Lấy synthesis (từ cache hoặc generate bằng Claude)
  const synthesis = node.synthesis;
  
  // 2. Lấy evidence (từ Qdrant vector DB)
  const evidence = node.evidence; // mockEvidenceSnippets
  
  // 3. Generate AI Suggestion (Recommendation Engine)
  const aiSuggestion = await generateAiSuggestion(node);
  
  return {
    id: node.id,
    name: node.name,
    type: node.type,
    synthesis,
    evidence,
    aiSuggestion
  };
}

async function generateAiSuggestion(node: TreeNode): Promise<AiSuggestion> {
  const isGap = node.isGap || (node.evidence.length === 0 && node.children.length === 0);
  const isCrossroads = node.children && node.children.length >= 2;
  
  let reason = '';
  let suggestedDocuments = [];
  
  if (isGap) {
    reason = `Node "${node.name}" chưa có bằng chứng từ tài liệu. Đây là một "khoảng trống tri thức" cần bổ sung.`;
    // Query Recommendation Engine cho suggested docs
    suggestedDocuments = await querySimilarDocuments(node.name);
  } else if (isCrossroads) {
    reason = `Node "${node.name}" có ${node.children.length} approaches khác nhau. Hãy khám phá để so sánh.`;
  } else {
    reason = `Node "${node.name}" có ${node.evidence.length} bằng chứng từ ${new Set(node.evidence.map(e => e.sourceTitle)).size} tài liệu.`;
  }
  
  return { isGap, isCrossroads, reason, suggestedDocuments };
}
```
**Interface**:
```typescript
export interface Evidence {
  id: string;           // Unique snippet ID
  text: string;         // Trích dẫn văn bản (max 500 chars)
  location: string;     // Vị trí trong tài liệu gốc
  sourceTitle: string;  // Tiêu đề PDF/document
  sourceAuthor: string; // Tác giả
  sourceYear: number;   // Năm xuất bản
  sourceUrl: string;    // Link tới tài liệu gốc
}

export interface SuggestedDocument {
  title: string;        // Tiêu đề tài liệu được gợi ý
  reason: string;       // Lý do gợi ý (similarity score, topic match...)
  uploadUrl: string;    // API endpoint để upload file này
  previewUrl?: string;  // (Optional) Link preview nếu có
}

export interface AiSuggestion {
  isGap: boolean;              // true = Node thiếu evidence
  isCrossroads: boolean;        // true = Node có ≥2 approaches
  reason: string;               // Giải thích chi tiết
  suggestedDocuments?: SuggestedDocument[]; // Gợi ý tài liệu để lấp lỗ hổng
}

export interface NodeDetailsResponse {
  id: string;
  name: string;
  type: NodeType;
  synthesis: string;          // Tóm tắt AI-generated (markdown supported)
  evidence: Evidence[];       // Mảng bằng chứng từ Qdrant
  aiSuggestion: AiSuggestion; // Gợi ý từ Recommendation Engine
}
```
**JSON Response (khi click topic-sagsins)**:
```json
{
  "id": "topic-sagsins",
  "name": "Vấn đề: Tối ưu Mạng SAGSINs",
  "type": "topic",
  "synthesis": "AI Tổng hợp: Chủ đề này được trích xuất từ 2 nguồn: [Nguyen, 2023] (Việt Nam) và [Kim, 2024] (Hàn Quốc). Cả hai đều tập trung vào việc tối ưu hiệu năng mạng SAGSINs. (MERGE scenario)",
  "evidence": [
    {
      "id": "snip-001",
      "text": "...để giải quyết vấn đề độ trễ cao (high latency), chúng tôi đề xuất \"Phương pháp A\", một cơ chế lập lịch ưu tiên (priority scheduling) dựa trên hàng đợi...",
      "location": "Trang 4, Đoạn 2",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-002",
      "text": "...vấn đề tối ưu tài nguyên (resource optimization) được giải quyết bằng \"Phương pháp B\", một thuật toán phân bổ động (dynamic allocation)...",
      "location": "Trang 5, Đoạn 1",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-006",
      "text": "본 연구는 SAGSIN 네트워크의 높은 지연 시간(high latency) 문제를 해결하기 위해 심층 Q-네트워크(DQN)를 사용한 동적 라우팅 기법을 제안합니다...",
      "location": "Trang 2, Đoạn 1",
      "sourceTitle": "Deep Q-Networks for Latency-Aware Routing in 6G SAGSINs (Báo cáo Hàn Quốc)",
      "sourceAuthor": "Kim, J. & Park, S.",
      "sourceYear": 2024,
      "sourceUrl": "https://www.koreascience.or.kr/DQN-SAGSINs"
    }
  ],
  "aiSuggestion": {
    "isGap": false,
    "isCrossroads": true,
    "reason": "Node này có 2 chủ đề con với các approaches khác nhau (Latency optimization vs Resource optimization). Hãy expand để khám phá chi tiết.",
    "suggestedDocuments": []
  }
}
```
**JSON Response (khi click sol-A-impl - GAP scenario)**:
```json
{
  "id": "sol-A-impl",
  "name": "Triển khai: Heap Data Structure",
  "type": "concept",
  "synthesis": "Chi tiết triển khai về cấu trúc heap chưa được tìm thấy trong tài liệu.",
  "evidence": [],
  "aiSuggestion": {
    "isGap": true,
    "isCrossroads": false,
    "reason": "Node này là một \"khoảng trống tri thức\". Không có bằng chứng từ tài liệu đã nạp. Hãy nạp thêm tài liệu liên quan để lấp lỗ hổng này.",
    "suggestedDocuments": [
      {
        "title": "Introduction to Algorithms (CLRS) - Chapter 6: Heapsort",
        "reason": "Giải thích chi tiết về cấu trúc heap và priority queue (similarity: 0.87)",
        "uploadUrl": "/api/workspaces/ws-123/documents/upload",
        "previewUrl": "https://mitpress.mit.edu/books/introduction-algorithms"
      },
      {
        "title": "Data Structures and Algorithm Analysis in C++",
        "reason": "Implementation chi tiết về heap data structure với code examples (similarity: 0.82)",
        "uploadUrl": "/api/workspaces/ws-123/documents/upload",
        "previewUrl": "https://www.pearson.com/..."
      }
    ]
  }
}
```
**JSON Response (khi click topic-latency - COMPARE scenario)**:
```json
{
  "id": "topic-latency",
  "name": "Tối ưu Độ trễ (Latency)",
  "type": "topic",
  "synthesis": "AI Tổng hợp: \"Tối ưu Độ trễ\" là một thách thức chung. Các tài liệu đã nạp tiếp cận vấn đề này bằng 2 cách khác nhau:\n1. [Nguyen, 2023] sử dụng \"Phương pháp A\" (Lập lịch truyền thống).\n2. [Kim, 2024] sử dụng \"DQN\" (Học Tăng Cường). (COMPARE scenario)",
  "evidence": [
    {
      "id": "snip-001",
      "text": "...để giải quyết vấn đề độ trễ cao (high latency), chúng tôi đề xuất \"Phương pháp A\"...",
      "location": "Trang 4, Đoạn 2",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-006",
      "text": "본 연구는 SAGSIN 네트워크의 높은 지연 시간(high latency) 문제를 해결하기 위해 심층 Q-네트워크(DQN)를 사용한 동적 라우팅 기법을 제안합니다...",
      "location": "Trang 2, Đoạn 1",
      "sourceTitle": "Deep Q-Networks for Latency-Aware Routing in 6G SAGSINs",
      "sourceAuthor": "Kim, J. & Park, S.",
      "sourceYear": 2024,
      "sourceUrl": "https://www.koreascience.or.kr/DQN-SAGSINs"
    }
  ],
  "aiSuggestion": {
    "isGap": false,
    "isCrossroads": true,
    "reason": "Node này là một \"ngã rẽ\" (crossroads) với 2 approaches khác nhau: Traditional Scheduling (Nguyen, 2023) vs Reinforcement Learning (Kim, 2024). Expand để so sánh chi tiết.",
    "suggestedDocuments": []
  }
}
```

### 🎨 Frontend Implementation (React)
**Component Structure**
```typescript
// WorkspacePage.tsx
import { useEffect, useState } from 'react';
import ReactFlow, { Node, Edge } from 'reactflow';

function WorkspacePage({ workspaceId }: { workspaceId: string }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeDetailsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // 1. Initial Load: API 1
  useEffect(() => {
    loadForest();
  }, [workspaceId]);

  async function loadForest() {
    const response = await fetch(`/api/workspaces/${workspaceId}/document-trees`);
    const data: DocumentTreesResponse = await response.json();
    
    // Convert to React Flow nodes
    const flowNodes: Node[] = data.map(node => ({
      id: node.id,
      type: 'custom', // Custom node component
      data: { ...node },
      position: calculatePosition(node) // Auto-layout
    }));
    
    setNodes(flowNodes);
  }

  // 2. On Node Click: API 2 + 3 (Parallel)
  async function handleNodeClick(nodeId: string) {
    setLoading(true);
    
    try {
      const [childrenData, detailsData] = await Promise.all([
        fetch(`/api/workspaces/${workspaceId}/nodes/${nodeId}/children`).then(r => r.json()),
        fetch(`/api/workspaces/${workspaceId}/nodes/${nodeId}/details`).then(r => r.json())
      ]);

      // Update nodes & edges (from API 2)
      const newNodes: Node[] = childrenData.nodes.map(node => ({
        id: node.id,
        type: 'custom',
        data: { ...node },
        position: calculateChildPosition(nodeId, node)
      }));
      
      setNodes(prev => [...prev, ...newNodes]);
      setEdges(prev => [...prev, ...childrenData.edges]);

      // Update sidebar (from API 3)
      setSelectedNode(detailsData);
    } catch (error) {
      console.error('Failed to load node data:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workspace-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => handleNodeClick(node.id)}
      />
      
      {selectedNode && (
        <Sidebar
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
      
      {loading && <LoadingSpinner />}
    </div>
  );
}
```

### 📈 Performance Metrics
| Metric              | Target  | Notes                               |
|---------------------|---------|-------------------------------------|
| API 1 (Forest)      | < 100ms | Cached, minimal data                |
| API 2 (Children)    | < 200ms | Tree traversal only                 |
| API 3 (Details)     | < 800ms | Qdrant query + LLM                  |
| Total click latency | < 1s    | Parallel loading                    |
| Bandwidth/click     | < 25KB  | Compressed JSON                     |

### 🔮 Future Enhancements

- **Prefetching**: Predict next click & preload children
- **WebSocket**: Real-time updates khi có document mới
- **Caching**: Redis cho frequently accessed nodes
- **Pagination**: Evidence list pagination nếu > 10 items
- **Batch API**: Load multiple nodes in 1 request (cho breadth-first exploration)

---
## Tài liệu Tối ưu: Lazy Loading Architecture cho Knowledge Tree (Hierarchical Structure)
### 🎯 Tổng quan Architecture
Hệ thống sử dụng 3-tier lazy loading để render cây tri thức phân cấp (hierarchical tree) với 7 cấp độ và 100+ nodes:

- **Tier 1**: Load "Root" (1 node gốc duy nhất) - ~0.5KB
- **Tier 2**: Load "Children" khi click expand - ~2-5KB/click
- **Tier 3**: Load "Details" song song - ~10-20KB/click

**Lưu ý**: Không có "edges" - đây là cấu trúc cây thuần túy (parent-children hierarchy)

### 📊 Flow Diagram
```
User Opens Page 3 (Workspace)
         │
         ▼
    ┌─────────────────────────────┐
    │  API 1: GET Root Node       │ ◄── Chỉ gọi 1 lần duy nhất
    │  Load node 'root' với       │     (Tree root từ mockKnowledgeTree)
    │  5 children IDs             │
    └─────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────┐
    │  UI renders:                │
    │  • 1 root node (collapsed)  │
    │  • 5 children nodes         │
    │    (topic-sagsins,          │
    │     topic-rl-ppo, ...)      │
    └─────────────────────────────┘
         │
         │ User clicks [+] expand
         ▼
    ┌─────────────────────────────────────────┐
    │  Promise.all([
    │    API 2: GET Children (fast ~100ms)   │ ◄── Parallel
    │    API 3: GET Details (slow ~500ms)    │ ◄── Parallel  
    │  ])                                     │
    └─────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    API 2 Done    API 3 Done    React Updates
    Add children  Show sidebar   • Children appear
    to tree       Show synthesis • Indent level++
                  Show evidence  • Sidebar fills
```

### 🔌 API Endpoints Chi tiết
#### API 1: Load Root & First Level (Initial Load)
**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/tree/root
```
**Params**:

- `workspaceId` (path): ID của workspace hiện tại

**Response Time**: ~50-100ms

**Backend Logic**:
```typescript
function getTreeRoot(workspaceId: string): TreeRootResponse {
  const analysis = getAnalysisByWorkspace(workspaceId); // mockAnalysis
  const rootNode = analysis.tree; // mockKnowledgeTree
  
  // Node gốc
  const root: TreeNodeShallow = {
    id: rootNode.id,
    name: rootNode.name,
    type: rootNode.type,
    isGap: false, // Root không bao giờ là gap
    isCrossroads: false,
    hasChildren: rootNode.children.length > 0,
    parentId: null, // Root không có parent
    level: 0 // Root ở level 0
  };
  
  // Children level 1 (5 topic nodes)
  const children: TreeNodeShallow[] = rootNode.children.map(child => ({
    id: child.id,
    name: child.name,
    type: child.type,
    isGap: child.isGap || false,
    isCrossroads: child.children && child.children.length >= 2,
    hasChildren: child.children && child.children.length > 0,
    parentId: rootNode.id,
    level: 1
  }));
  
  return { root, children };
}
```
**Interface**:
```typescript
export type NodeType = 
  | 'topic' 
  | 'document' 
  | 'problem-domain' 
  | 'algorithm' 
  | 'challenge' 
  | 'feature' 
  | 'concept';

/**
 * TreeNode "Siêu nhẹ" - Chỉ chứa metadata để render
 * KHÔNG bao gồm synthesis, evidence (tiết kiệm bandwidth)
 */
export interface TreeNodeShallow {
  id: string;              // Unique identifier
  name: string;            // Display text
  type: NodeType;          // Loại node
  isGap: boolean;          // true = Node "mồ côi" (thiếu tài liệu)
  isCrossroads: boolean;   // true = Node có ≥2 approaches khác nhau
  hasChildren: boolean;    // true = Hiển thị nút [+] expand
  parentId: string | null; // ID của node cha (null nếu là root)
  level: number;           // Độ sâu trong cây (0 = root, 1 = children của root, ...)
}

export interface TreeRootResponse {
  root: TreeNodeShallow;      // Node gốc
  children: TreeNodeShallow[]; // 5 children level 1
}
```
**JSON Response (từ mockKnowledgeTree)**:
```json
{
  "root": {
    "id": "root",
    "name": "Phân tích Tài liệu Đa lĩnh vực",
    "type": "topic",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": null,
    "level": 0
  },
  "children": [
    {
      "id": "topic-sagsins",
      "name": "Vấn đề: Tối ưu Mạng SAGSINs",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true,
      "parentId": "root",
      "level": 1
    },
    {
      "id": "topic-rl-ppo",
      "name": "Lĩnh vực: Reinforcement Learning",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true,
      "parentId": "root",
      "level": 1
    },
    {
      "id": "topic-cv",
      "name": "Lĩnh vực: Computer Vision",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true,
      "parentId": "root",
      "level": 1
    },
    {
      "id": "topic-nlp",
      "name": "Lĩnh vực: Natural Language Processing",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true,
      "parentId": "root",
      "level": 1
    },
    {
      "id": "topic-network-infra",
      "name": "Lĩnh vực: Network Infrastructure",
      "type": "topic",
      "isGap": false,
      "isCrossroads": true,
      "hasChildren": true,
      "parentId": "root",
      "level": 1
    }
  ]
}
```

---

### **API 2: Load Children (On Expand)**

**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/tree/nodes/{nodeId}/children
```
**Params**:

- `workspaceId` (path): ID workspace
- `nodeId` (path): ID của node được expand (click vào nút [+])

**Response Time**: ~100-200ms

**Backend Logic**:
```typescript
function getNodeChildren(
  workspaceId: string, 
  nodeId: string
): TreeNodeShallow[] {
  const node = findNodeInTree(mockKnowledgeTree, nodeId);
  if (!node || !node.children) {
    return [];
  }
  
  const parentLevel = calculateNodeLevel(mockKnowledgeTree, nodeId);
  
  // Chỉ lấy children trực tiếp (không lấy grandchildren)
  const children: TreeNodeShallow[] = node.children.map(child => {
    // Tính isGap: node không có evidence và không có children
    const isGap = (child.evidence.length === 0 && child.children.length === 0);
    
    // Tính isCrossroads: có >= 2 children (compare/alternatives scenario)
    const isCrossroads = child.children && child.children.length >= 2;
    
    return {
      id: child.id,
      name: child.name,
      type: child.type,
      isGap,
      isCrossroads,
      hasChildren: child.children && child.children.length > 0,
      parentId: nodeId,
      level: parentLevel + 1
    };
  });
  
  return children;
}
```
**Interface**:
```typescript
// Sử dụng lại TreeNodeShallow từ API 1
export type NodeChildrenResponse = TreeNodeShallow[];
```
**JSON Response - Scenario 1: Khi expand topic-sagsins (Level 1 → Level 2)**:
```json
[
  {
    "id": "topic-latency",
    "name": "Tối ưu Độ trễ (Latency)",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true,
    "parentId": "topic-sagsins",
    "level": 2
  },
  {
    "id": "topic-resource",
    "name": "Tối ưu Tài nguyên (Resource)",
    "type": "topic",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "topic-sagsins",
    "level": 2
  }
]
```
**JSON Response - Scenario 2: Khi expand topic-latency (Level 2 → Level 3 - CROSSROADS)**:
```json
[
  {
    "id": "sol-A",
    "name": "Giải pháp: Phương pháp A (Lập lịch)",
    "type": "algorithm",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "topic-latency",
    "level": 3
  },
  {
    "id": "sol-DQN",
    "name": "Giải pháp: DQN (Học Tăng Cường)",
    "type": "algorithm",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "topic-latency",
    "level": 3
  }
]
```
**JSON Response - Scenario 3: Khi expand sol-A (Level 3 → Level 4)**:
```json
[
  {
    "id": "sol-A-queue",
    "name": "Chi tiết: Priority Queue Mechanism",
    "type": "concept",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "sol-A",
    "level": 4
  }
]
```
**JSON Response - Scenario 4: Khi expand sol-A-queue (Level 4 → Level 5 - GAP)**:
```json
[
  {
    "id": "sol-A-impl",
    "name": "Triển khai: Heap Data Structure",
    "type": "concept",
    "isGap": true,
    "isCrossroads": false,
    "hasChildren": false,
    "parentId": "sol-A-queue",
    "level": 5
  }
]
```
**JSON Response - Scenario 5: Khi expand topic-rl-ppo (Level 1 → Level 2 - Complex)**:
```json
[
  {
    "id": "rl-value-based",
    "name": "Phân loại: Value-Based Methods",
    "type": "topic",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "topic-rl-ppo",
    "level": 2
  },
  {
    "id": "rl-policy",
    "name": "Phân loại: Policy-Based Methods",
    "type": "topic",
    "isGap": false,
    "isCrossroads": true,
    "hasChildren": true,
    "parentId": "topic-rl-ppo",
    "level": 2
  }
]
```
**JSON Response - Scenario 6: Khi expand rl-policy (Level 2 → Level 3 - Multiple children)**:
```json
[
  {
    "id": "sol-PPO",
    "name": "Thuật toán: PPO (Proximal Policy Optimization)",
    "type": "algorithm",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "rl-policy",
    "level": 3
  },
  {
    "id": "sol-A3C",
    "name": "Thuật toán: A3C (Asynchronous Actor-Critic)",
    "type": "algorithm",
    "isGap": false,
    "isCrossroads": false,
    "hasChildren": true,
    "parentId": "rl-policy",
    "level": 3
  }
]
```
**JSON Response - Scenario 7: Deep nesting - expand đến Level 7 (Deepest)**:
```json
// Level 6 → Level 7 (từ node 'gpt-prompting')
[
  {
    "id": "gpt-alignment",
    "name": "Thách thức: Model Alignment",
    "type": "challenge",
    "isGap": true,
    "isCrossroads": false,
    "hasChildren": false,
    "parentId": "gpt-prompting",
    "level": 7
  }
]
```

---

### **API 3: Load Details (On Click - Parallel)**

**Endpoint**:  
```
GET /api/workspaces/{workspaceId}/tree/nodes/{nodeId}/details
```
**Params**:

- `workspaceId` (path): ID workspace
- `nodeId` (path): ID của node được click (để hiển thị sidebar)

**Response Time**: ~300-800ms

**Backend Logic**:
```typescript
async function getNodeDetails(
  workspaceId: string, 
  nodeId: string
): Promise<NodeDetailsResponse> {
  const node = findNodeInTree(mockKnowledgeTree, nodeId);
  if (!node) throw new Error('Node not found');
  
  // 1. Lấy synthesis từ node
  const synthesis = node.synthesis;
  
  // 2. Lấy evidence từ node (đã được trích xuất sẵn)
  const evidence = node.evidence; // Tham chiếu đến mockEvidenceSnippets
  
  // 3. Generate AI Suggestion
  const aiSuggestion = await generateAiSuggestion(node);
  
  return {
    id: node.id,
    name: node.name,
    type: node.type,
    synthesis,
    evidence,
    aiSuggestion
  };
}

async function generateAiSuggestion(node: TreeNode): Promise<AiSuggestion> {
  const isGap = node.evidence.length === 0 && node.children.length === 0;
  const isCrossroads = node.children && node.children.length >= 2;
  
  let reason = '';
  let suggestedDocuments: SuggestedDocument[] = [];
  
  if (isGap) {
    reason = `Node "${node.name}" chưa có bằng chứng từ tài liệu. Đây là một "khoảng trống tri thức" (research gap) cần bổ sung.`;
    // Query Recommendation Engine
    suggestedDocuments = await querySimilarDocuments(node.name);
  } else if (isCrossroads) {
    const approachCount = node.children.length;
    reason = `Node "${node.name}" có ${approachCount} approaches khác nhau (COMPARE scenario). Hãy expand để khám phá từng phương pháp.`;
  } else if (node.evidence.length > 0) {
    const uniqueSources = new Set(node.evidence.map(e => e.sourceTitle)).size;
    reason = `Node "${node.name}" có ${node.evidence.length} bằng chứng từ ${uniqueSources} tài liệu (MERGED scenario).`;
  } else {
    reason = `Node "${node.name}" là một chủ đề trung gian. Expand để khám phá chi tiết.`;
  }
  
  return { isGap, isCrossroads, reason, suggestedDocuments };
}
```
**Interface**:
```typescript
// === Evidence Interface (từ mock-analysis.ts) ===
export interface Evidence {
  id: string;           // ID duy nhất của snippet
  text: string;         // Đoạn trích văn bản thực tế
  location: string;     // Vị trí trong tài liệu
  sourceTitle: string;  // Tiêu đề của PDF/Tài liệu
  sourceAuthor: string; // Tác giả
  sourceYear: number;   // Năm xuất bản
  sourceUrl: string;    // Link tới tài liệu gốc
}

export interface SuggestedDocument {
  title: string;        // Tiêu đề tài liệu được gợi ý
  reason: string;       // Lý do gợi ý
  uploadUrl: string;    // API endpoint để upload file này
  previewUrl?: string;  // (Optional) Link preview
}

export interface AiSuggestion {
  isGap: boolean;              // true = Node thiếu evidence (GAP)
  isCrossroads: boolean;        // true = Node có ≥2 approaches (COMPARE)
  reason: string;               // Giải thích chi tiết
  suggestedDocuments?: SuggestedDocument[]; // Gợi ý tài liệu để lấp lỗ hổng
}

export interface NodeDetailsResponse {
  id: string;
  name: string;
  type: NodeType;
  synthesis: string;          // Tóm tắt AI-generated (từ node.synthesis)
  evidence: Evidence[];       // Mảng bằng chứng (từ node.evidence)
  aiSuggestion: AiSuggestion; // Gợi ý AI
}
```
**JSON Response - Scenario 1: Click topic-sagsins (MERGE scenario)**:
```json
{
  "id": "topic-sagsins",
  "name": "Vấn đề: Tối ưu Mạng SAGSINs",
  "type": "topic",
  "synthesis": "AI Tổng hợp: Chủ đề này được trích xuất từ 2 nguồn: [Nguyen, 2023] (Việt Nam) và [Kim, 2024] (Hàn Quốc). Cả hai đều tập trung vào việc tối ưu hiệu năng mạng SAGSINs. (MERGE scenario)",
  "evidence": [
    {
      "id": "snip-001",
      "text": "...để giải quyết vấn đề độ trễ cao (high latency), chúng tôi đề xuất \"Phương pháp A\", một cơ chế lập lịch ưu tiên (priority scheduling) dựa trên hàng đợi...",
      "location": "Trang 4, Đoạn 2",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-002",
      "text": "...vấn đề tối ưu tài nguyên (resource optimization) được giải quyết bằng \"Phương pháp B\", một thuật toán phân bổ động (dynamic allocation)...",
      "location": "Trang 5, Đoạn 1",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-006",
      "text": "본 연구는 SAGSIN 네트워크의 높은 지연 시간(high latency) 문제를 해결하기 위해 심층 Q-네트워크(DQN)를 사용한 동적 라우팅 기법을 제안합니다...",
      "location": "Trang 2, Đoạn 1",
      "sourceTitle": "Deep Q-Networks for Latency-Aware Routing in 6G SAGSINs (Báo cáo Hàn Quốc)",
      "sourceAuthor": "Kim, J. & Park, S.",
      "sourceYear": 2024,
      "sourceUrl": "https://www.koreascience.or.kr/DQN-SAGSINs"
    }
  ],
  "aiSuggestion": {
    "isGap": false,
    "isCrossroads": true,
    "reason": "Node này có 2 chủ đề con với các approaches khác nhau (CROSSROADS scenario). Hãy expand để khám phá chi tiết.",
    "suggestedDocuments": []
  }
}
```
**JSON Response - Scenario 2: Click topic-latency (COMPARE scenario)**:
```json
{
  "id": "topic-latency",
  "name": "Tối ưu Độ trễ (Latency)",
  "type": "topic",
  "synthesis": "AI Tổng hợp: \"Tối ưu Độ trễ\" là một thách thức chung. Các tài liệu đã nạp tiếp cận vấn đề này bằng 2 cách khác nhau:\n1. [Nguyen, 2023] sử dụng \"Phương pháp A\" (Lập lịch truyền thống).\n2. [Kim, 2024] sử dụng \"DQN\" (Học Tăng Cường). (COMPARE scenario)",
  "evidence": [
    {
      "id": "snip-001",
      "text": "...để giải quyết vấn đề độ trễ cao (high latency), chúng tôi đề xuất \"Phương pháp A\", một cơ chế lập lịch ưu tiên (priority scheduling) dựa trên hàng đợi...",
      "location": "Trang 4, Đoạn 2",
      "sourceTitle": "Tối ưu Hiệu năng trong Mạng SAGSINs: So sánh Phương pháp A và B",
      "sourceAuthor": "Nguyen, Van Hung & Tran, Thi An",
      "sourceYear": 2023,
      "sourceUrl": "https://vjst.vn/vi/sagsins-performance-2023"
    },
    {
      "id": "snip-006",
      "text": "본 연구는 SAGSIN 네트워크의 높은 지연 시간(high latency) 문제를 해결하기 위해 심층 Q-네트워크(DQN)를 사용한 동적 라우팅 기법을 제안합니다...",
      "location": "Trang 2, Đoạn 1",
      "sourceTitle": "Deep Q-Networks for Latency-Aware Routing in 6G SAGSINs (Báo cáo Hàn Quốc)",
      "sourceAuthor": "Kim, J. & Park, S.",
      "sourceYear": 2024,
      "sourceUrl": "https://www.koreascience.or.kr/DQN-SAGSINs"
    }
  ],
  "aiSuggestion": {
    "isGap": false,
    "isCrossroads": true,
    "reason": "Node này là một \"ngã rẽ\" (crossroads) với 2 approaches khác nhau: Traditional Scheduling (Nguyen, 2023) vs Reinforcement Learning (Kim, 2024). Expand để so sánh chi tiết.",
    "suggestedDocuments": []
  }
}
```