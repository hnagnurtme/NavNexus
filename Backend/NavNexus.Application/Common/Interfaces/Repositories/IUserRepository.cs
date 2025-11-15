using System;
using System.Threading;
using System.Threading.Tasks;
using Neo4j.Driver;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories
{
    public interface IUserRepository 
    {
        Task<User?> GetByEmailAsync(string email,  CancellationToken cancellationToken = default);

        Task<bool> ExistsByEmailAsync(string email,CancellationToken cancellationToken = default);

        Task<User?> GetWithTokensAsync(Guid userId, CancellationToken cancellationToken = default);
        
        Task AddAsync(User user, CancellationToken cancellationToken = default);
        
        Task UpdateAsync(User user, CancellationToken cancellationToken = default);
    }
}
