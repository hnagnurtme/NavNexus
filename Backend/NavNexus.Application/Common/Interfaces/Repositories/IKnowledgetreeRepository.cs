using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories;

public interface IKnowledgetreeRepository
{
    Task<KnowledgeNode?> GetRootNodeByWorkspaceIdAsync(string workspaceId,CancellationToken cancellationToken = default);

    Task<KnowledgeNode?> GetNodeByIdAsync(string nodeId, CancellationToken cancellationToken = default);
}