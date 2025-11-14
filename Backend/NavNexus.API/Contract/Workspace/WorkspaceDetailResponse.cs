namespace NavNexus.API.Contract.Workspace;

public class WorkspaceDetailResponse
{
    public required string WorkspaceId { get; set; }
    public required string Name { get; set; }
    public required string Description { get; set; }

    public required string OwnerId { get; set; }
    public required string OwnerName { get; set; }

    public required List<string> FileIds { get; set; }

    public required DateTime CreatedAt { get; set; }
    public required DateTime UpdatedAt { get; set; }
}