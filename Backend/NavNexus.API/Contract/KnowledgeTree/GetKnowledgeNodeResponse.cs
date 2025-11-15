namespace NavNexus.API.Contract.KnowledgeTree;


public class GetKnowledgeNodeResponse
{
    public required string NodeId { get; set; }
    public required string NodeName { get; set; }
    public required string Description { get; set; }
    public required List<string> Tags { get; set; }

    public required int Level { get; set; }
    public required int SourceCount { get; set; }
    public required List<EvidenceResponse> Evidences { get; set; }
    public required DateTime CreatedAt { get; set; }
    public required DateTime UpdatedAt { get; set; }
    public required List<GetKnowledgeNodeResponse> ChildNodes{ get; set; }
}