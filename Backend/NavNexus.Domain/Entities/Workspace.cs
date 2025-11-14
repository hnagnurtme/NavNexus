using Google.Cloud.Firestore;
using NavNexus.Domain.Common.Events;
namespace NavNexus.Domain.Entities;


[FirestoreData]
public class Workspace
{
    [FirestoreProperty]
    public string Id { get;  set; }
    [FirestoreProperty]
    public string Name { get;  set; }

    [FirestoreProperty]
    public string? Description { get; set; }
    [FirestoreProperty]
    public string OwnerId { get;  set; }
    [FirestoreProperty]
    public User Owner { get;  set; } = null!;
    [FirestoreProperty]
    public ICollection<FileStorage> Files { get; set; } = new List<FileStorage>();

    [FirestoreProperty]
    public List<string> FileIds { get; set; } = new List<string>();

    public DateTime CreatedAt { get; private set; } = DateTime.UtcNow;

    public DateTime UpdatedAt { get; private set; } = DateTime.UtcNow;

    private Workspace()
    {
        Name = string.Empty;
        Id = Guid.NewGuid().ToString();
        OwnerId = string.Empty;
    }

    public Workspace(string name, string ownerId, string  description , List<string>? fileIds)
    {
        Id = Guid.NewGuid().ToString();
        Name = name;
        OwnerId = ownerId;
        Description = description;
        FileIds = fileIds ?? new List<string>();
        CreatedAt = DateTime.UtcNow;
        UpdatedAt = DateTime.UtcNow;
    }
}