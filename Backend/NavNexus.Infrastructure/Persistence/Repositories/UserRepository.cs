using Google.Cloud.Firestore;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;
using NavNexus.Infrastructure.Persistence;

namespace NavNexus.Infrastructure.Persistence.Repositories;

public class UserRepository : IUserRepository
{
    private readonly CollectionReference _users;

    public UserRepository(FirebaseConnection firebase)
    {
        var db = firebase.GetFirestore();
        _users = db.Collection("Users"); 
    }

    public async Task<User?> GetByEmailAsync(string email, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(email))
            return null;

        try
        {
            var query = await _users
                .WhereEqualTo("Email", email.Trim().ToLowerInvariant())
                .Limit(1)
                .GetSnapshotAsync(cancellationToken);

            var doc = query.Documents.FirstOrDefault();
            return doc?.ConvertTo<User>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[GetByEmailAsync] Firestore error: {ex}");
            throw new InvalidOperationException("Failed to get user by email.", ex);
        }
    }

    public async Task<bool> ExistsByEmailAsync(string email, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(email))
            return false;

        try
        {
            var querySnapshot = await _users
                .WhereEqualTo("Email", email.Trim().ToLowerInvariant())
                .Limit(1)
                .GetSnapshotAsync(cancellationToken);

            return querySnapshot.Documents.Count > 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[ExistsByEmailAsync] Firestore error: {ex}");
            throw new InvalidOperationException("Failed to query Firestore users.", ex);
        }
    }

    public async Task<User?> GetWithTokensAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        try
        {
            var doc = await _users
                .Document(userId.ToString())
                .GetSnapshotAsync(cancellationToken);

            return doc.Exists ? doc.ConvertTo<User>() : null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[GetWithTokensAsync] Firestore error: {ex}");
            throw new InvalidOperationException($"Failed to get user {userId}.", ex);
        }
    }

    public async Task AddAsync(User user, CancellationToken cancellationToken = default)
    {
        try
        {
            await _users
                .Document(user.Id.ToString())
                .SetAsync(user, cancellationToken: cancellationToken);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[AddAsync] Firestore error: {ex}");
            throw new InvalidOperationException($"Failed to add user {user.Id}.", ex);
        }
    }

    public async Task UpdateAsync(User user, CancellationToken cancellationToken = default)
    {
        try
        {
            await _users
                .Document(user.Id.ToString())
                .SetAsync(user, SetOptions.MergeAll, cancellationToken);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[UpdateAsync] Firestore error: {ex}");
            throw new InvalidOperationException($"Failed to update user {user.Id}.", ex);
        }
    }
}
