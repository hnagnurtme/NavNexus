using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Neo4j.Driver;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories
{
    public interface ITokenRepository
    {
        Task<RefreshToken?> GetByUserIdAsync(Guid userId, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        Task<IEnumerable<RefreshToken>> GetActiveTokensByUserIdAsync(Guid userId, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        Task<RefreshToken?> GetLatestActiveTokenByUserIdAsync(Guid userId, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        Task RevokeAllForUserAsync(Guid userId, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        Task<RefreshToken?> GetValidTokenAsync(Guid userId, string userAgent, string deviceFingerprint, IAsyncTransaction tx, CancellationToken cancellationToken = default);
    }
}
