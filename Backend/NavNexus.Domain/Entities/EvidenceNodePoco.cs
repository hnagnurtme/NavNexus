namespace NavNexus.Domain.Entities;

/// <summary>
/// Neo4j Node: (:Evidence)
/// Represents a quote, snippet, or citation supporting knowledge nodes
/// </summary>
public class EvidenceNodePoco
{
    public string Id { get; set; } = string.Empty; // "evidence-001"
    
    public string Text { get; set; } = string.Empty; // Quote/snippet
    
    public string Location { get; set; } = string.Empty; // "Page 5, Paragraph 3"
    
    public string SourceTitle { get; set; } = string.Empty; // "PPO Paper"
    
    public string SourceAuthor { get; set; } = string.Empty; // "Schulman et al."
    
    public int SourceYear { get; set; } // 2017
    
    public string SourceUrl { get; set; } = string.Empty; // NOS URL or external link
    
    public double ConfidenceScore { get; set; } // 0.0 - 1.0
    
    public string WorkspaceId { get; set; } = string.Empty;
}
