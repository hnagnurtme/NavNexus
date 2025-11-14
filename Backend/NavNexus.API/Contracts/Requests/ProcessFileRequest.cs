namespace NavNexus.API.Contracts.Requests;

/// <summary>
/// Request to process a file upload
/// </summary>
public class ProcessFileRequest
{
    public string WorkspaceId { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string FileUrl { get; set; } = string.Empty;
    public string FileHash { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public string MimeType { get; set; } = string.Empty;
}
