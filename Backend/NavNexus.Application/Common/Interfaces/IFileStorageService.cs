namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for file storage operations (NOS/Cloud storage)
/// </summary>
public interface IFileStorageService
{
    /// <summary>
    /// Uploads a file to storage and returns the storage URL
    /// </summary>
    Task<string> UploadFileAsync(string fileName, Stream fileStream, string workspaceId, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Generates SHA256 hash for file deduplication
    /// </summary>
    Task<string> CalculateFileHashAsync(Stream fileStream, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Downloads file from storage
    /// </summary>
    Task<Stream> DownloadFileAsync(string fileUrl, CancellationToken cancellationToken = default);
}
