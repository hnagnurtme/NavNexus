using Google.Cloud.Firestore;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace NavNexus.Infrastructure.Persistence.Repositories;

public class TokenRepository : ITokenRepository
{
    private readonly FirestoreDb _db;
    private const string CollectionName = "refreshTokens";

    public TokenRepository(FirestoreDb db)
    {
        _db = db;
    }

    public async Task<RefreshToken?> GetByUserIdAsync(Guid userId, CancellationToken cancellationToken)
    {
        var query = _db.Collection(CollectionName)
                       .WhereEqualTo("UserId", userId)
                       .Limit(1);
        var snapshot = await query.GetSnapshotAsync(cancellationToken);
        return snapshot.Documents.FirstOrDefault()?.ConvertTo<RefreshToken>();
    }

    public async Task<IEnumerable<RefreshToken>> GetActiveTokensByUserIdAsync(Guid userId, CancellationToken cancellationToken)
    {
        var query = _db.Collection(CollectionName)
                       .WhereEqualTo("UserId", userId)
                       .WhereEqualTo("Used", false)
                       .WhereEqualTo("RevokedAt", null)
                       .WhereGreaterThan("ExpiresAt", DateTime.UtcNow);

        var snapshot = await query.GetSnapshotAsync(cancellationToken);
        return snapshot.Documents.Select(d => d.ConvertTo<RefreshToken>());
    }

    public async Task<RefreshToken?> GetLatestActiveTokenByUserIdAsync(Guid userId, CancellationToken cancellationToken)
    {
        var query = _db.Collection(CollectionName)
                       .WhereEqualTo("UserId", userId)
                       .WhereEqualTo("Used", false)
                       .WhereEqualTo("RevokedAt", null)
                       .WhereGreaterThan("ExpiresAt", DateTime.UtcNow)
                       .OrderByDescending("CreatedAt")
                       .Limit(1);

        var snapshot = await query.GetSnapshotAsync(cancellationToken);
        return snapshot.Documents.FirstOrDefault()?.ConvertTo<RefreshToken>();
    }

    public async Task RevokeAllForUserAsync(Guid userId, CancellationToken cancellationToken)
    {
        var query = _db.Collection(CollectionName)
                       .WhereEqualTo("UserId", userId)
                       .WhereEqualTo("Used", false)
                       .WhereEqualTo("RevokedAt", null)
                       .WhereGreaterThan("ExpiresAt", DateTime.UtcNow);

        var snapshot = await query.GetSnapshotAsync(cancellationToken);

        foreach (var doc in snapshot.Documents)
        {
            await doc.Reference.UpdateAsync(new Dictionary<string, object>
            {
                { "RevokedAt", DateTime.UtcNow }
            }, cancellationToken: cancellationToken);
        }
    }

    public async Task<RefreshToken?> GetValidTokenAsync(
    Guid userId,
    string tokenValue,
    string tokenType,   
    CancellationToken cancellationToken)
    {
        var query = _db.Collection(CollectionName)
                       .WhereEqualTo("UserId", userId)
                       .WhereEqualTo("TokenHash", tokenValue) 
                       .WhereEqualTo("Used", false)
                       .WhereEqualTo("RevokedAt", null)
                       .WhereGreaterThan("ExpiresAt", DateTime.UtcNow)
                       .Limit(1);

        var snapshot = await query.GetSnapshotAsync(cancellationToken);
        return snapshot.Documents.FirstOrDefault()?.ConvertTo<RefreshToken>();
    }

    public async Task AddAsync(RefreshToken token, CancellationToken cancellationToken)
    {
        await _db.Collection(CollectionName)
                 .Document(token.Id.ToString())
                 .SetAsync(token, cancellationToken: cancellationToken);
    }

    public async Task UpdateAsync(RefreshToken token, CancellationToken cancellationToken)
    {
        await _db.Collection(CollectionName)
                 .Document(token.Id.ToString())
                 .SetAsync(token, SetOptions.Overwrite, cancellationToken);
    }

    
}
