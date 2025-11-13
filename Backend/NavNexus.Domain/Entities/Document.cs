namespace NavNexus.Domain.Entities;

public class Document
{
    public string Id { get; set; } = string.Empty;
    public string UserId { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string StoragePath { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public string ContentType { get; set; } = string.Empty;
    public DateTime UploadedAt { get; set; }
    public string? NodeId { get; set; }
    public DocumentStatus Status { get; set; } = DocumentStatus.Pending;
}

public enum DocumentStatus
{
    Pending,
    Processing,
    Completed,
    Failed
}
