namespace NavNexus.Application.Workspace.Results;

public record GetWorkspaceDetailsResult(
    string WorkspaceId,
    string Name,
    string Description,
    string OwnerId,
    string OwnerName,
    List<string> FileIds,
    DateTime CreatedAt,
    DateTime UpdatedAt
);