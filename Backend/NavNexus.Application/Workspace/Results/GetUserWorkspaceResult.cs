namespace NavNexus.Application.Workspace.Results;

public record GetUserWorkspaceResult(
    int TotalWorkspaces,
    List<GetWorkspaceDetailsResult> Workspaces
);