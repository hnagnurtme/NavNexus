using FirebaseAdmin;
using Google.Apis.Auth.OAuth2;
using Google.Cloud.Firestore;
using Microsoft.Extensions.Configuration;

namespace NavNexus.Infrastructure.Services;

public interface IFirebaseService
{
    FirestoreDb GetFirestoreDb();
}

public class FirebaseService : IFirebaseService
{
    private readonly FirestoreDb _firestoreDb;

    public FirebaseService(IConfiguration configuration)
    {
        var projectId = configuration["Firebase:ProjectId"] ?? "navnexus-demo";
        
        // Initialize Firebase if not already initialized
        if (FirebaseApp.DefaultInstance == null)
        {
            // For development, you can use application default credentials
            // In production, use service account key file
            FirebaseApp.Create(new AppOptions
            {
                Credential = GoogleCredential.GetApplicationDefault()
            });
        }

        _firestoreDb = FirestoreDb.Create(projectId);
    }

    public FirestoreDb GetFirestoreDb() => _firestoreDb;
}
