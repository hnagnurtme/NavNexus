namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface INaverObjectStorageService
{
    Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType, CancellationToken cancellationToken = default);
    Task<Stream> DownloadFileAsync(string fileUrl, CancellationToken cancellationToken = default);
    Task<bool> DeleteFileAsync(string fileUrl, CancellationToken cancellationToken = default);
    Task<string> GetPresignedUrlAsync(string fileUrl, int expirationMinutes = 60, CancellationToken cancellationToken = default);
}
