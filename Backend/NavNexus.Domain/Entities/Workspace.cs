using Google.Cloud.Firestore;
using NavNexus.Domain.Common.Events;
namespace NavNexus.Domain.Entities;


[FirestoreData]
public class Workspace
{
    [FirestoreProperty]
    public String Id { get; private set; }
    [FirestoreProperty]
    public string Name { get; private set; }
    [FirestoreProperty]
    public Guid OwnerId { get; private set; }
    [FirestoreProperty]
    public User Owner { get; private set; } = null!;
    [FirestoreProperty]
    public ICollection<FileStorage> Files { get; set; } = new List<FileStorage>();

    private Workspace()
    {
        Name = string.Empty;
        Id = Guid.NewGuid().ToString();
    }

    public Workspace(string name, Guid ownerId)
    {
        Id = Guid.NewGuid().ToString();
        Name = name;
        OwnerId = ownerId;
    }
}