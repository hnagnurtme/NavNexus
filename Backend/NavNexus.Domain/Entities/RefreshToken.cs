using Google.Cloud.Firestore;

[FirestoreData]
public class RefreshToken
{
    [FirestoreProperty] public String Id { get; private set; }
    [FirestoreProperty] public Guid UserId { get; private set; }

    [FirestoreProperty] public string TokenHash { get; private set; } = string.Empty;
    [FirestoreProperty] public DateTime ExpiresAt { get; private set; }

    [FirestoreProperty] public DateTime CreatedAt { get; private set; } = DateTime.UtcNow;
    [FirestoreProperty] public DateTime? RevokedAt { get; private set; }
    [FirestoreProperty] public bool Used { get; private set; } = false;

    [FirestoreProperty] public Guid? ReplacedByTokenId { get; private set; }

    [FirestoreProperty] public string? IpAddress { get; private set; }
    [FirestoreProperty] public string? UserAgent { get; private set; }
    [FirestoreProperty] public string? DeviceFingerprint { get; private set; }

    private RefreshToken() { }

    public RefreshToken(
        Guid userId,
        string tokenHash,
        DateTime expiresAt,
        string? ip = null,
        string? userAgent = null,
        string? deviceFingerprint = null)
    {
        Id = Guid.NewGuid().ToString();
        UserId = userId;
        TokenHash = tokenHash ?? throw new ArgumentNullException(nameof(tokenHash));
        ExpiresAt = expiresAt;
        IpAddress = ip;
        UserAgent = userAgent;
        DeviceFingerprint = deviceFingerprint;
    }

    public bool IsActive => RevokedAt == null && !Used && ExpiresAt > DateTime.UtcNow;

    public void MarkAsUsed()
    {
        if (Used) throw new InvalidOperationException("Token is already used.");
        Used = true;
    }

    public void Revoke()
    {
        if (RevokedAt != null) throw new InvalidOperationException("Token already revoked.");
        RevokedAt = DateTime.UtcNow;
    }

    public void Replace(Guid newTokenId)
    {
        Revoke();
        ReplacedByTokenId = newTokenId;
    }
}
