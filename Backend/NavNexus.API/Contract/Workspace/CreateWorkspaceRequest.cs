namespace NavNexus.API.Contract.Workspace;

public class CreateWorkspaceRequest
{
    public required string Name { get; set; }
    public string? Description { get; set; }

    public List<string>? FileIds { get; set; }
}