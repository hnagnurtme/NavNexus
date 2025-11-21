using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories;

public interface IJobRepository
{
    Task<Job> CreateJobAsync(Job job, CancellationToken cancellationToken = default);

    // Find by path
    Task<Job?> GetJobByFilePathAsync(string workspaceId, string filePath,  CancellationToken cancellationToken = default);
}