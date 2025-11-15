namespace NavNexus.Domain.Entities;

public class KnowledgeNode
    {
        public string Id { get; set; }                  // unique ID
        public string Type { get; set; }                // "category" hoặc "concept"
        public string Name { get; set; }                // tên node
        public string Synthesis { get; set; }           // tổng hợp nội dung (summary)
        public string WorkspaceId { get; set; }         // workspace
        public int Level { get; set; }                  // độ sâu trong cây
        public int SourceCount { get; set; }            // số lượng Evidence liên quan
        public float TotalConfidence { get; set; }      // độ tin cậy tổng thể
        public DateTime CreatedAt { get; set; }         // thời gian tạo node
        public DateTime UpdatedAt { get; set; }         // thời gian update cuối

        // Relationships
        public List<KnowledgeNode> Children { get; set; } = new List<KnowledgeNode>(); // node con
        public List<Evidence> Evidences { get; set; } = new List<Evidence>();

        public List<GapSuggestion> GapSuggestions { get; set; } = new List<GapSuggestion>();

        public bool IsLeafNode() => Children.Count == 0;
        
        public KnowledgeNode()
        {
            Id = Guid.NewGuid().ToString();
            Type = string.Empty;
            Name = string.Empty;
            Synthesis = string.Empty;
            WorkspaceId = string.Empty;
            Level = 0;
            SourceCount = 0;
            TotalConfidence = 0.0f;
            CreatedAt = DateTime.UtcNow;
            UpdatedAt = DateTime.UtcNow;
        }
    }