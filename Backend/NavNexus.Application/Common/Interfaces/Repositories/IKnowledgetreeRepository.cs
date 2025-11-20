using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Repositories;

public interface IKnowledgetreeRepository
{
    Task<KnowledgeNode?> GetRootNodeByWorkspaceIdAsync(string workspaceId, CancellationToken cancellationToken = default);

    Task<KnowledgeNode?> GetNodeByIdAsync(string nodeId, CancellationToken cancellationToken = default);

    Task<List<KnowledgeNode>> GetAllRootNodesByWorkspaceIdAsync(string workspaceId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Copy nodes from other workspaces that have evidence with the same source_id (URL)
    /// Creates new nodes with new IDs and new workspace_id to avoid conflicts
    /// </summary>
    /// <param name="evidenceSourceId">The source_id (URL) to match in evidences</param>
    /// <param name="newWorkspaceId">The workspace ID to copy nodes to</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of newly created nodes</returns>
    Task<List<KnowledgeNode>> CopyNodesAsync(string evidenceSourceId, string newWorkspaceId, CancellationToken cancellationToken = default);
}