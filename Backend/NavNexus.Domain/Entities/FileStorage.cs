using Google.Cloud.Firestore;
using NavNexus.Domain.Common.Events;
namespace NavNexus.Domain.Entities;

[FirestoreData]
public class FileStorage
{
    [FirestoreProperty]
    public string Id { get; private set; }
    [FirestoreProperty]
    public string FileName { get; private set; }
    [FirestoreProperty]
    public string FilePath { get; private set; }
    [FirestoreProperty]
    public long FileSize { get; private set; }
    [FirestoreProperty]
    public Guid UploadedByUserId { get; private set; }
    [FirestoreProperty]
    public DateTime UploadedAt { get; private set; } = DateTime.UtcNow;

    [FirestoreProperty]
    public String fileHash { get; private set; } = string.Empty;

    private FileStorage()
    {
        FileName = string.Empty;
        FilePath = string.Empty;
        FileSize = 0;
        UploadedByUserId = Guid.Empty;
        UploadedAt = DateTime.UtcNow;
        fileHash = string.Empty;
        Id = Guid.NewGuid().ToString();
    }

    public FileStorage(string fileName, string filePath, long fileSize,  Guid uploadedByUserId , String fileHash)
    {
        Id = Guid.NewGuid().ToString();
        FileName = fileName;
        FilePath = filePath;
        FileSize = fileSize;
        UploadedByUserId = uploadedByUserId;
        UploadedAt = DateTime.UtcNow;
        this.fileHash = fileHash;
    }
}