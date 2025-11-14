using FirebaseAdmin;
using Google.Apis.Auth.OAuth2;
using Google.Cloud.Firestore;

namespace NavNexus.Infrastructure.Persistence;

public class FirebaseConnection
{
    private readonly FirestoreDb _db;

    public FirebaseConnection(string projectId, string credentialPath)
{
    // 1. Tải credential từ file
    var credential = GoogleCredential.FromFile(credentialPath);

    // 2. Sử dụng FirestoreDbBuilder để tạo FirestoreDb
    //    và chỉ định rõ ProjectId VÀ Credential
    _db = new FirestoreDbBuilder
    {
        ProjectId = projectId,
        Credential = credential
    }.Build();

    // Bạn không cần khởi tạo FirebaseApp.Create()
    // trừ khi bạn dùng các dịch vụ Firebase Admin khác
    // (như Firebase Auth hoặc Messaging).
    // Nếu bạn CHỈ dùng Firestore, code ở trên là đủ.
}

    public FirestoreDb GetFirestore() => _db;
}
