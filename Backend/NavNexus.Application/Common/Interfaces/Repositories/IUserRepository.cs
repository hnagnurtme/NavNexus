using System;
using System.Threading;
using System.Threading.Tasks;
using Neo4j.Driver;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories
{
    public interface IUserRepository 
    {
        Task<User?> GetByEmailAsync(string email, IAsyncTransaction tx, CancellationToken cancellationToken = default);

        Task<bool> ExistsByEmailAsync(string email, IAsyncTransaction tx, CancellationToken cancellationToken = default);

        Task<User?> GetWithTokensAsync(Guid userId, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        
        Task AddAsync(User user, IAsyncTransaction tx, CancellationToken cancellationToken = default);
        
        Task UpdateAsync(User user, IAsyncTransaction tx, CancellationToken cancellationToken = default);
    }
}
