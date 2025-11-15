namespace NavNexus.API.Contract.KnowledgeTree;


public class EvidenceResponse
{   
    public required string EvidenceId { get; set; }
    public required string Content { get; set; }
    public required string SourceFileId { get; set; }
    public required DateTime CreatedAt { get; set; }
    public required string Language { get; set; }
    public required string SourceLanguage { get; set; }
    public required string HierarchyPath { get; set; }
    public required List<string> Claims { get; set; }

    public required List<string> KeyClaims { get; set; }

    public required List<string> QuestionsRaised { get; set; }
    public required float EvidenceStrength { get; set; }
}