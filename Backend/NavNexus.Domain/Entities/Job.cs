namespace NavNexus.Domain.Entities;

public class Job
{
    public string Id { get; set; }
    public string WorkspaceId { get; set; }
    public string FilePath { get; set; }
    public string Status { get; set; } = "PENDING"; 
    public DateTime CreatedAt { get; set; }
    public DateTime? CompletedAt { get; set; }

    public Job()
    {
        Id = Guid.NewGuid().ToString();
        WorkspaceId = string.Empty;
        FilePath = string.Empty;
        Status = "PENDING";
        CreatedAt = DateTime.UtcNow;
        CompletedAt = null;
    }

    public void MarkAsCompleted()
    {
        Status = "COMPLETED";
        CompletedAt = DateTime.UtcNow;
    }

    public Job (string workspaceId, string filePath , string status)
    {
        Id = Guid.NewGuid().ToString();
        WorkspaceId = workspaceId;
        FilePath = filePath;
        Status = status;
        CreatedAt = DateTime.UtcNow;
        CompletedAt = null;
    }
}