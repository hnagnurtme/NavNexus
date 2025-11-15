namespace NavNexus.API.Contract.KnowledgeTree;

public class CreatedKnowledgetreeRequest
{
    public required string WorkspaceId { get; set; }

    public required List<string> FilePaths { get; set; }
}