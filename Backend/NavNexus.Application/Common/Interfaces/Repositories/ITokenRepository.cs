namespace NavNexus.Application.Common.Interfaces.Repositories
{
    public interface ITokenRepository
    {
        Task<RefreshToken?> GetByUserIdAsync(Guid userId,CancellationToken cancellationToken = default);
        Task<IEnumerable<RefreshToken>> GetActiveTokensByUserIdAsync(Guid userId, CancellationToken cancellationToken = default);
        Task<RefreshToken?> GetLatestActiveTokenByUserIdAsync(Guid userId, CancellationToken cancellationToken = default);
        Task RevokeAllForUserAsync(Guid userId, CancellationToken cancellationToken = default);
        Task<RefreshToken?> GetValidTokenAsync(Guid userId, string userAgent, string deviceFingerprint,CancellationToken cancellationToken = default);

        Task AddAsync(RefreshToken refreshToken, CancellationToken cancellationToken = default);

        Task UpdateAsync(RefreshToken refreshToken, CancellationToken cancellationToken = default);
    }
}
