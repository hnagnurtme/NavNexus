# ENTITY.md - Data Models & Storage Schemas

## 📦 Backend C# Entities

### 1. **FileMetadata** (Firestore)
```csharp
using System;
using System.Collections.Generic;
using Newtonsoft.Json;

/// <summary>
/// Lưu trong Firestore: workspaces/{workspace_id}/files/{file_id}
/// Dùng để cache metadata và tránh reprocess file trùng
/// </summary>
public class FileMetadata
{
    [JsonProperty("file_id")]
    public string FileId { get; set; }
    
    [JsonProperty("file_hash")]
    public string FileHash { get; set; } // SHA256
    
    [JsonProperty("file_name")]
    public string FileName { get; set; }
    
    [JsonProperty("file_size")]
    public long FileSize { get; set; }
    
    [JsonProperty("mime_type")]
    public string MimeType { get; set; }
    
    [JsonProperty("workspace_id")]
    public string WorkspaceId { get; set; }
    
    [JsonProperty("upload_date")]
    public DateTime UploadDate { get; set; }
    
    [JsonProperty("nos_url")]
    public string NosUrl { get; set; }
    
    [JsonProperty("neo4j_node_ids")]
    public List<string> Neo4jNodeIds { get; set; }
    
    [JsonProperty("qdrant_point_ids")]
    public List<string> QdrantPointIds { get; set; }
    
    [JsonProperty("processing_status")]
    public ProcessingStatus Status { get; set; }
    
    [JsonProperty("error_message")]
    public string ErrorMessage { get; set; }
    
    [JsonProperty("language_detected")]
    public string LanguageDetected { get; set; } // "ko", "en", "ja", "vi"
    
    [JsonProperty("translation_target")]
    public string TranslationTarget { get; set; } // "en"
    
    [JsonProperty("processing_time_ms")]
    public long ProcessingTimeMs { get; set; }
}

public enum ProcessingStatus
{
    Pending,
    Processing,
    Completed,
    Failed
}
```

---

### 2. **User** (Firestore)
```csharp
/// <summary>
/// Lưu trong Firestore: users/{user_id}
/// </summary>
public class User
{
    [JsonProperty("user_id")]
    public string UserId { get; set; }
    
    [JsonProperty("email")]
    public string Email { get; set; }
    
    [JsonProperty("display_name")]
    public string DisplayName { get; set; }
    
    [JsonProperty("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonProperty("last_login")]
    public DateTime LastLogin { get; set; }
    
    [JsonProperty("workspace_ids")]
    public List<string> WorkspaceIds { get; set; }
    
    [JsonProperty("preferences")]
    public UserPreferences Preferences { get; set; }
}

public class UserPreferences
{
    [JsonProperty("default_target_language")]
    public string DefaultTargetLanguage { get; set; } // "en"
    
    [JsonProperty("theme")]
    public string Theme { get; set; } // "light", "dark"
    
    [JsonProperty("notification_enabled")]
    public bool NotificationEnabled { get; set; }
}
```

---

### 3. **Workspace** (Firestore)
```csharp
/// <summary>
/// Lưu trong Firestore: workspaces/{workspace_id}
/// </summary>
public class Workspace
{
    [JsonProperty("workspace_id")]
    public string WorkspaceId { get; set; }
    
    [JsonProperty("name")]
    public string Name { get; set; }
    
    [JsonProperty("description")]
    public string Description { get; set; }
    
    [JsonProperty("owner_id")]
    public string OwnerId { get; set; }
    
    [JsonProperty("member_ids")]
    public List<string> MemberIds { get; set; }
    
    [JsonProperty("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonProperty("updated_at")]
    public DateTime UpdatedAt { get; set; }
    
    [JsonProperty("qdrant_collection_name")]
    public string QdrantCollectionName { get; set; } // "workspace_{workspace_id}"
    
    [JsonProperty("file_count")]
    public int FileCount { get; set; }
    
    [JsonProperty("total_size_bytes")]
    public long TotalSizeBytes { get; set; }
}
```

---

### 4. **KnowledgeNodePoco** (Neo4j)
```csharp
using Neo4j.Driver.Mapping;

/// <summary>
/// Neo4j Node: (:KnowledgeNode)
/// </summary>
[Neo4jNode("KnowledgeNode")]
public class KnowledgeNodePoco
{
    [Neo4jProperty("id")]
    public string Id { get; set; } // "topic-ppo"
    
    [Neo4jProperty("name")]
    public string Name { get; set; } // "Proximal Policy Optimization"
    
    [Neo4jProperty("type")]
    public string Type { get; set; } // "topic", "concept", "algorithm", "problem"
    
    [Neo4jProperty("level")]
    public int Level { get; set; } // Hierarchy level: 0 (root), 1, 2, ...
    
    [Neo4jProperty("synthesis")]
    public string Synthesis { get; set; } // AI-generated summary
    
    [Neo4jProperty("concepts")]
    public List<string> Concepts { get; set; } // ["policy gradient", "clipping", "trust region"]
    
    [Neo4jProperty("qdrant_vector_id")]
    public string QdrantVectorId { get; set; } // Link to Qdrant point
    
    [Neo4jProperty("workspace_id")]
    public string WorkspaceId { get; set; }
    
    [Neo4jProperty("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [Neo4jProperty("is_gap")]
    public bool IsGap { get; set; } // Orphan node detected
    
    [Neo4jProperty("is_crossroads")]
    public bool IsCrossroads { get; set; } // Bridge between clusters
    
    // Relationships
    [Neo4jRelationship("HAS_CHILD")]
    public List<KnowledgeNodePoco> Children { get; set; }
    
    [Neo4jRelationship("HAS_EVIDENCE")]
    public List<EvidenceNodePoco> Evidences { get; set; }
}
```

---

### 5. **EvidenceNodePoco** (Neo4j)
```csharp
/// <summary>
/// Neo4j Node: (:Evidence)
/// </summary>
[Neo4jNode("Evidence")]
public class EvidenceNodePoco
{
    [Neo4jProperty("id")]
    public string Id { get; set; } // "evidence-001"
    
    [Neo4jProperty("text")]
    public string Text { get; set; } // Quote/snippet
    
    [Neo4jProperty("location")]
    public string Location { get; set; } // "Page 5, Paragraph 3"
    
    [Neo4jProperty("source_title")]
    public string SourceTitle { get; set; } // "PPO Paper"
    
    [Neo4jProperty("source_author")]
    public string SourceAuthor { get; set; } // "Schulman et al."
    
    [Neo4jProperty("source_year")]
    public int SourceYear { get; set; } // 2017
    
    [Neo4jProperty("source_url")]
    public string SourceUrl { get; set; } // NOS URL or external link
    
    [Neo4jProperty("confidence_score")]
    public double ConfidenceScore { get; set; } // 0.0 - 1.0
    
    [Neo4jProperty("workspace_id")]
    public string WorkspaceId { get; set; }
}
```

---

### 6. **QdrantChunkPayload** (Qdrant)
```csharp
using System.Text.Json.Serialization;

/// <summary>
/// Payload của 1 vector point trong Qdrant
/// </summary>
public class QdrantChunkPayload
{
    [JsonPropertyName("chunk_id")]
    public string ChunkId { get; set; } // "chunk-001"
    
    [JsonPropertyName("paper_id")]
    public string PaperId { get; set; } // "file-uuid" or "PPO.pdf"
    
    [JsonPropertyName("page")]
    public int Page { get; set; }
    
    [JsonPropertyName("quote")]
    public string Quote { get; set; } // Original text chunk
    
    [JsonPropertyName("summary")]
    public string Summary { get; set; } // LLM-generated summary
    
    [JsonPropertyName("concepts")]
    public List<string> Concepts { get; set; } // ["PPO", "actor-critic"]
    
    [JsonPropertyName("topic")]
    public string Topic { get; set; } // Main topic
    
    [JsonPropertyName("workspace_id")]
    public string WorkspaceId { get; set; }
    
    [JsonPropertyName("language")]
    public string Language { get; set; } // "en" (after translation)
    
    [JsonPropertyName("source_language")]
    public string SourceLanguage { get; set; } // "ko" (original)
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}
```

---

## 📄 JSON Sample Data

### Firestore: `users/{user_id}`
```json
{
  "user_id": "user_abc123",
  "email": "researcher@example.com",
  "display_name": "Dr. Nguyen",
  "created_at": "2025-01-15T08:30:00Z",
  "last_login": "2025-11-13T14:22:00Z",
  "workspace_ids": [
    "ws_reinforcement_learning",
    "ws_nlp_research"
  ],
  "preferences": {
    "default_target_language": "en",
    "theme": "dark",
    "notification_enabled": true
  }
}
```

---

### Firestore: `workspaces/{workspace_id}`
```json
{
  "workspace_id": "ws_reinforcement_learning",
  "name": "Reinforcement Learning Research",
  "description": "Papers on PPO, TRPO, Actor-Critic methods",
  "owner_id": "user_abc123",
  "member_ids": [
    "user_abc123",
    "user_def456"
  ],
  "created_at": "2025-10-01T10:00:00Z",
  "updated_at": "2025-11-13T12:00:00Z",
  "qdrant_collection_name": "workspace_ws_reinforcement_learning",
  "file_count": 12,
  "total_size_bytes": 45678901
}
```

---

### Firestore: `workspaces/{workspace_id}/files/{file_id}` (Cached File)
```json
{
  "file_id": "file_9a8b7c6d",
  "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_name": "PPO_Algorithm_Korean.pdf",
  "file_size": 2567890,
  "mime_type": "application/pdf",
  "workspace_id": "ws_reinforcement_learning",
  "upload_date": "2025-11-13T10:15:00Z",
  "nos_url": "https://nos.example.com/ws_reinforcement_learning/file_9a8b7c6d.pdf",
  "neo4j_node_ids": [
    "topic-ppo",
    "topic-policy-gradient",
    "concept-clipping"
  ],
  "qdrant_point_ids": [
    "chunk-001",
    "chunk-002",
    "chunk-003",
    "chunk-004"
  ],
  "processing_status": "completed",
  "error_message": null,
  "language_detected": "ko",
  "translation_target": "en",
  "processing_time_ms": 8432
}
```

---

### Neo4j: `(:KnowledgeNode)` (Cypher CREATE)
```cypher
CREATE (n:KnowledgeNode {
  id: 'topic-ppo',
  name: 'Proximal Policy Optimization',
  type: 'algorithm',
  level: 1,
  synthesis: 'PPO is a policy gradient method that uses a clipped surrogate objective to prevent large policy updates, improving training stability.',
  concepts: ['policy gradient', 'trust region', 'clipping', 'importance sampling'],
  qdrant_vector_id: 'topic-ppo-vector',
  workspace_id: 'ws_reinforcement_learning',
  created_at: datetime('2025-11-13T10:20:00Z'),
  is_gap: false,
  is_crossroads: true
})
```

**JSON Representation (for API response):**
```json
{
  "id": "topic-ppo",
  "name": "Proximal Policy Optimization",
  "type": "algorithm",
  "level": 1,
  "synthesis": "PPO is a policy gradient method that uses a clipped surrogate objective to prevent large policy updates, improving training stability.",
  "concepts": [
    "policy gradient",
    "trust region",
    "clipping",
    "importance sampling"
  ],
  "qdrant_vector_id": "topic-ppo-vector",
  "workspace_id": "ws_reinforcement_learning",
  "created_at": "2025-11-13T10:20:00Z",
  "is_gap": false,
  "is_crossroads": true,
  "children": [
    {
      "id": "concept-clipping",
      "name": "Clipped Surrogate Objective",
      "type": "concept"
    }
  ],
  "evidences": [
    {
      "id": "evidence-001",
      "text": "We propose a novel objective function that enables multiple epochs of minibatch updates...",
      "source_title": "Proximal Policy Optimization Algorithms"
    }
  ]
}
```

---

### Neo4j: `(:Evidence)` (Cypher CREATE)
```cypher
CREATE (e:Evidence {
  id: 'evidence-001',
  text: 'We propose a novel objective function that enables multiple epochs of minibatch updates without causing destructively large policy updates.',
  location: 'Abstract, Page 1',
  source_title: 'Proximal Policy Optimization Algorithms',
  source_author: 'Schulman, Wolski, Dhariwal, Radford, Klimov',
  source_year: 2017,
  source_url: 'https://nos.example.com/ws_rl/ppo_paper.pdf',
  confidence_score: 0.95,
  workspace_id: 'ws_reinforcement_learning'
})
```

**JSON Representation:**
```json
{
  "id": "evidence-001",
  "text": "We propose a novel objective function that enables multiple epochs of minibatch updates without causing destructively large policy updates.",
  "location": "Abstract, Page 1",
  "source_title": "Proximal Policy Optimization Algorithms",
  "source_author": "Schulman, Wolski, Dhariwal, Radford, Klimov",
  "source_year": 2017,
  "source_url": "https://nos.example.com/ws_rl/ppo_paper.pdf",
  "confidence_score": 0.95,
  "workspace_id": "ws_reinforcement_learning"
}
```

---

### Neo4j: Relationships
```cypher
// Cha-con: PPO có khái niệm Clipping
MATCH (parent:KnowledgeNode {id: 'topic-ppo'})
MATCH (child:KnowledgeNode {id: 'concept-clipping'})
CREATE (parent)-[:HAS_CHILD]->(child)

// Bằng chứng: PPO có evidence từ paper
MATCH (topic:KnowledgeNode {id: 'topic-ppo'})
MATCH (evidence:Evidence {id: 'evidence-001'})
CREATE (topic)-[:HAS_EVIDENCE]->(evidence)
```

---

### Qdrant: Point with Payload
```json
{
  "id": "chunk-001",
  "vector": [0.123, -0.456, 0.789, ...],
  "payload": {
    "chunk_id": "chunk-001",
    "paper_id": "file_9a8b7c6d",
    "page": 3,
    "quote": "The clipped surrogate objective function prevents the policy from changing too much in a single update step. This is achieved by clipping the probability ratio between the new and old policies.",
    "summary": "PPO uses a clipped objective to limit policy updates and maintain training stability.",
    "concepts": [
      "PPO",
      "clipping",
      "policy gradient",
      "stability"
    ],
    "topic": "Proximal Policy Optimization",
    "workspace_id": "ws_reinforcement_learning",
    "language": "en",
    "source_language": "ko",
    "created_at": "2025-11-13T10:18:00Z"
  }
}
```

---

### Qdrant: Search Request
```json
{
  "collection_name": "workspace_ws_reinforcement_learning",
  "vector": [0.111, -0.222, 0.333, ...],
  "limit": 5,
  "with_payload": true,
  "filter": {
    "must": [
      {
        "key": "workspace_id",
        "match": {
          "value": "ws_reinforcement_learning"
        }
      }
    ]
  }
}
```

---

### Qdrant: Search Response
```json
{
  "result": [
    {
      "id": "chunk-001",
      "score": 0.92,
      "payload": {
        "chunk_id": "chunk-001",
        "summary": "PPO uses a clipped objective to limit policy updates...",
        "concepts": ["PPO", "clipping"],
        "topic": "Proximal Policy Optimization"
      }
    },
    {
      "id": "chunk-015",
      "score": 0.87,
      "payload": {
        "chunk_id": "chunk-015",
        "summary": "Actor-Critic methods combine value-based and policy-based approaches...",
        "concepts": ["actor-critic", "value function"],
        "topic": "Actor-Critic Methods"
      }
    }
  ]
}
```

---

## 🔗 Cross-Reference Links

### KnowledgeNode ↔ Qdrant
```
Neo4j KnowledgeNode:
  qdrant_vector_id: "topic-ppo-vector"
  
Qdrant Point:
  id: "topic-ppo-vector"
  payload.topic: "Proximal Policy Optimization"
```

### Evidence ↔ FileMetadata
```
Neo4j Evidence:
  source_url: "https://nos.example.com/ws_rl/file_9a8b7c6d.pdf"
  
Firestore FileMetadata:
  nos_url: "https://nos.example.com/ws_rl/file_9a8b7c6d.pdf"
  file_id: "file_9a8b7c6d"
```

### Workspace Isolation
```
All entities have workspace_id:
  - Firestore: workspaces/{workspace_id}/files/{file_id}
  - Neo4j: node.workspace_id = "ws_xxx"
  - Qdrant: collection_name = "workspace_{workspace_id}"
```

---

## 📊 Index Strategies

### Firestore
```
Collection: workspaces/{workspace_id}/files
Indexes:
  - file_hash (ASC) - for duplicate detection
  - processing_status (ASC) + upload_date (DESC) - for admin dashboard
  - workspace_id (ASC) + upload_date (DESC) - for workspace file list
```

### Neo4j
```cypher
// Node indexes
CREATE INDEX knowledge_node_id FOR (n:KnowledgeNode) ON (n.id);
CREATE INDEX knowledge_node_workspace FOR (n:KnowledgeNode) ON (n.workspace_id);
CREATE INDEX evidence_id FOR (e:Evidence) ON (e.id);

// Full-text search
CREATE FULLTEXT INDEX knowledge_synthesis FOR (n:KnowledgeNode) ON EACH [n.synthesis, n.name];
```

### Qdrant
```
Collection config:
  - Distance: Cosine
  - Vector size: 1024 (or based on embedding model)
  - Index: HNSW (fast approximate search)
  - Payload index: workspace_id, concepts, topic
```

---

## 🎯 API Response DTOs

### Upload Response
```json
{
  "success": true,
  "file_id": "file_9a8b7c6d",
  "status": "completed",
  "message": "File processed successfully",
  "data": {
    "neo4j_nodes_created": 5,
    "qdrant_chunks_created": 12,
    "evidences_extracted": 8,
    "processing_time_ms": 8432,
    "language_detected": "ko",
    "translation_performed": true
  }
}
```

### Query Response
```json
{
  "query": "Explain PPO algorithm advantages",
  "answer": "PPO offers several key advantages: 1) Stable training through clipped objectives...",
  "evidences": [
    {
      "id": "evidence-001",
      "text": "We propose a novel objective function...",
      "source": "Schulman et al. 2017",
      "url": "https://nos.example.com/..."
    }
  ],
  "related_topics": [
    {
      "id": "topic-trpo",
      "name": "Trust Region Policy Optimization",
      "relevance_score": 0.85
    }
  ],
  "graph_path": [
    "topic-policy-gradient",
    "topic-ppo",
    "concept-clipping"
  ]
}
```