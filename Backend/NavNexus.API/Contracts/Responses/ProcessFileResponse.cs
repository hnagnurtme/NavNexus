namespace NavNexus.API.Contracts.Responses;

/// <summary>
/// Response for file processing request
/// </summary>
public class ProcessFileResponse
{
    public string FileId { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string? JobId { get; set; }
}
