using Google.Cloud.Firestore;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Domain.Entities;

namespace NavNexus.Infrastructure.Services;

/// <summary>
/// Firestore service implementation for metadata caching
/// </summary>
public class FirestoreMetadataService : IFirestoreService
{
    private readonly FirestoreDb? _firestoreDb;

    public FirestoreMetadataService()
    {
        try
        {
            // Try to initialize Firestore, but don't fail if not configured
            _firestoreDb = FirestoreDb.Create("navnexus-project");
        }
        catch
        {
            _firestoreDb = null;
        }
    }

    public async Task<FileMetadata?> GetFileByHashAsync(string workspaceId, string fileHash, CancellationToken cancellationToken = default)
    {
        if (_firestoreDb == null) return null;
        
        var query = _firestoreDb
            .Collection("workspaces").Document(workspaceId)
            .Collection("files")
            .WhereEqualTo("file_hash", fileHash)
            .Limit(1);
            
        var snapshot = await query.GetSnapshotAsync(cancellationToken);
        return snapshot.Documents.FirstOrDefault()?.ConvertTo<FileMetadata>();
    }

    public async Task<FileMetadata?> GetFileByIdAsync(string workspaceId, string fileId, CancellationToken cancellationToken = default)
    {
        if (_firestoreDb == null) return null;
        
        var docRef = _firestoreDb
            .Collection("workspaces").Document(workspaceId)
            .Collection("files").Document(fileId);
            
        var snapshot = await docRef.GetSnapshotAsync(cancellationToken);
        return snapshot.Exists ? snapshot.ConvertTo<FileMetadata>() : null;
    }

    public async Task SaveFileMetadataAsync(FileMetadata fileMetadata, CancellationToken cancellationToken = default)
    {
        if (_firestoreDb == null) return;
        
        var docRef = _firestoreDb
            .Collection("workspaces").Document(fileMetadata.WorkspaceId)
            .Collection("files").Document(fileMetadata.FileId);
            
        await docRef.SetAsync(fileMetadata, cancellationToken: cancellationToken);
    }

    public async Task<Workspace?> GetWorkspaceAsync(string workspaceId, CancellationToken cancellationToken = default)
    {
        if (_firestoreDb == null) return null;
        
        var docRef = _firestoreDb.Collection("workspaces").Document(workspaceId);
        var snapshot = await docRef.GetSnapshotAsync(cancellationToken);
        return snapshot.Exists ? snapshot.ConvertTo<Workspace>() : null;
    }

    public async Task UpdateWorkspaceStatsAsync(string workspaceId, int fileCountDelta, long sizeDelta, CancellationToken cancellationToken = default)
    {
        if (_firestoreDb == null) return;
        
        var docRef = _firestoreDb.Collection("workspaces").Document(workspaceId);
        await docRef.UpdateAsync(new Dictionary<string, object>
        {
            { "file_count", FieldValue.Increment(fileCountDelta) },
            { "total_size_bytes", FieldValue.Increment(sizeDelta) },
            { "updated_at", FieldValue.ServerTimestamp }
        }, cancellationToken: cancellationToken);
    }
}
