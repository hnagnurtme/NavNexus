namespace NavNexus.API.Contracts.Requests;

public class CreateNodeRequest
{
    public string Title { get; set; } = string.Empty;
    public string? Content { get; set; }
    public List<string> Tags { get; set; } = new();
    public string? ParentNodeId { get; set; }
}
