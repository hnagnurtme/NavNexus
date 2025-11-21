using FirebaseAdmin;
using Google.Apis.Auth.OAuth2;
using Google.Cloud.Firestore;

namespace NavNexus.Infrastructure.Persistence;

public class FirebaseConnection
{
    private readonly FirestoreDb _db;
    private readonly FirebaseApp _app;
    private readonly string _databaseUrl;

    public FirebaseConnection(string projectId, string credentialPath, string databaseUrl)
    {
        _databaseUrl = databaseUrl;

        // 1. Tải credential từ file
        var credential = GoogleCredential.FromFile(credentialPath);

        // 2. Initialize FirebaseApp for Realtime Database
        _app = FirebaseApp.Create(new AppOptions
        {
            Credential = credential,
            ProjectId = projectId
        });

        // 3. Sử dụng FirestoreDbBuilder để tạo FirestoreDb
        _db = new FirestoreDbBuilder
        {
            ProjectId = projectId,
            Credential = credential
        }.Build();
    }

    public FirestoreDb GetFirestore() => _db;

    public string GetDatabaseUrl() => _databaseUrl;

    public FirebaseApp GetFirebaseApp() => _app;
}
