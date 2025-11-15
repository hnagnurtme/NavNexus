namespace NavNexus.API.Contract.Workspace;

public class UserWorkspaceResponse
{
    public required int TotalWorkspaces { get; set; }
    public required List<WorkspaceDetailResponse> Workspaces { get; set; }
}