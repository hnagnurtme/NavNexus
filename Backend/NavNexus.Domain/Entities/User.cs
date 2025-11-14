using NavNexus.Domain.Common.Events;
namespace NavNexus.Domain.Entities;
using Google.Cloud.Firestore;
[FirestoreData]
public class User
{
    [FirestoreProperty]
    public String Id { get; private set; }
    [FirestoreProperty]
    public string Email { get; private set; }
    [FirestoreProperty]
    public string PasswordHash { get; private set; }
    [FirestoreProperty]
    public string FullName { get; private set; }
    [FirestoreProperty]
    public string? PhoneNumber { get; private set; }
    [FirestoreProperty]
    public UserRole Roles { get; private set; } = UserRole.USER;
    [FirestoreProperty]
    public bool EmailVerified { get; private set; } = true;
    [FirestoreProperty]
    public bool IsActive { get; private set; } = true;
    [FirestoreProperty]
    public DateTime? LastLoginAt { get; private set; }
    [FirestoreProperty]
    public int LoginAttempts { get; private set; } = 0;
    [FirestoreProperty]
    public DateTime? LockedUntil { get; private set; }
    [FirestoreProperty]
    public DateTime CreatedAt { get; private set; } = DateTime.UtcNow;
    [FirestoreProperty]
    public DateTime UpdatedAt { get; private set; } = DateTime.UtcNow;
    [FirestoreProperty]
    public ICollection<Workspace> Workspaces { get; set; } = new List<Workspace>();
    public ICollection<RefreshToken> RefreshTokens { get; set; } = new List<RefreshToken>();

    private User()
    {
        Email = string.Empty;
        PasswordHash = string.Empty;
        FullName = string.Empty;
        Id = Guid.NewGuid().ToString();
    }
    public User? Organizer { get; private set; }

    public User(string email, string passwordHash, string fullName, string? phoneNumber, UserRole roles = UserRole.USER )
    {
        Id = Guid.NewGuid().ToString();
        Email = email.Trim().ToLowerInvariant();
        PasswordHash = passwordHash;
        FullName = fullName;
        PhoneNumber = phoneNumber;
        Roles = roles;
        AddDomainEvent(new UserRegisteredDomainEvent(Id, email));
    }
    
    public void UpdateLogin(DateTime loginTime)
    {
        LastLoginAt = loginTime;
        LoginAttempts = 0;
        LockedUntil = null;
        Touch();

    }

    public void IncrementLoginAttempts()
    {
        LoginAttempts++;
        Touch();
    }

    public void LockAccount(DateTime until)
    {
        LockedUntil = until;
        Touch();
    }

    public void UpdateProfile(string fullName, string? phoneNumber)
    {
        FullName = fullName;
        PhoneNumber = phoneNumber;
        Touch();
    }
    public void MarkEmailAsVerified()
    {
        EmailVerified = true;
        Touch();
    }

    public bool IsLocked => LockedUntil.HasValue && LockedUntil > DateTime.UtcNow;

    private void Touch() => UpdatedAt = DateTime.UtcNow;

    public void AddRole(UserRole role)
    {
        Roles |= role; 
        Touch();
    }

    public void RemoveRole(UserRole role)
    {
        Roles &= ~role; 
        Touch();
    }

    public bool HasRole(UserRole role) => Roles.HasFlag(role);

    private readonly List<IDomainEvent> _domainEvents = new();

    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    private void AddDomainEvent(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);

    public void ClearDomainEvents() => _domainEvents.Clear();
}

[Flags]
public enum UserRole
{
    NONE  = 0,
    USER = 1 << 0,
    ADMIN = 1 << 1,

}

