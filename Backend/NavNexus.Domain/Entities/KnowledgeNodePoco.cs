namespace NavNexus.Domain.Entities;

/// <summary>
/// Neo4j Node: (:KnowledgeNode)
/// Represents a topic, concept, algorithm, or problem in the knowledge graph
/// </summary>
public class KnowledgeNodePoco
{
    public string Id { get; set; } = string.Empty; // "topic-ppo"
    
    public string Name { get; set; } = string.Empty; // "Proximal Policy Optimization"
    
    public string Type { get; set; } = string.Empty; // "topic", "concept", "algorithm", "problem"
    
    public int Level { get; set; } // Hierarchy level: 0 (root), 1, 2, ...
    
    public string Synthesis { get; set; } = string.Empty; // AI-generated summary
    
    public List<string> Concepts { get; set; } = new(); // ["policy gradient", "clipping", "trust region"]
    
    public string? QdrantVectorId { get; set; } // Link to Qdrant point
    
    public string WorkspaceId { get; set; } = string.Empty;
    
    public DateTime CreatedAt { get; set; }
    
    public bool IsGap { get; set; } // Orphan node detected
    
    public bool IsCrossroads { get; set; } // Bridge between clusters
    
    // Relationships (populated via graph traversal)
    public List<KnowledgeNodePoco> Children { get; set; } = new();
    
    public List<EvidenceNodePoco> Evidences { get; set; } = new();
}
