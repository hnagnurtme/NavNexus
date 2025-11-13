using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for Firestore operations (cache and metadata storage)
/// </summary>
public interface IFirestoreService
{
    /// <summary>
    /// Gets file metadata by file hash (for deduplication check)
    /// </summary>
    Task<FileMetadata?> GetFileByHashAsync(string workspaceId, string fileHash, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Gets file metadata by file ID
    /// </summary>
    Task<FileMetadata?> GetFileByIdAsync(string workspaceId, string fileId, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Saves or updates file metadata
    /// </summary>
    Task SaveFileMetadataAsync(FileMetadata fileMetadata, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Gets workspace by ID
    /// </summary>
    Task<Workspace?> GetWorkspaceAsync(string workspaceId, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Updates workspace statistics (file count, total size)
    /// </summary>
    Task UpdateWorkspaceStatsAsync(string workspaceId, int fileCountDelta, long sizeDelta, CancellationToken cancellationToken = default);
}
