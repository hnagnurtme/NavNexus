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

    /// <summary>
    /// Get all leaf nodes (nodes without children) in a workspace
    /// </summary>
    /// <param name="workspaceId">The workspace ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of leaf nodes</returns>
    Task<List<KnowledgeNode>> GetLeafNodesAsync(string workspaceId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a node has gap suggestions
    /// </summary>
    /// <param name="nodeId">The node ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>True if node has gap suggestions, false otherwise</returns>
    Task<bool> HasGapSuggestionsAsync(string nodeId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Save gap suggestions for a node
    /// </summary>
    /// <param name="nodeId">The node ID</param>
    /// <param name="suggestions">List of gap suggestions to save</param>
    /// <param name="cancellationToken">Cancellation token</param>
    Task SaveGapSuggestionsAsync(string nodeId, List<GapSuggestion> suggestions, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all nodes in a workspace (includes evidences)
    /// </summary>
    /// <param name="workspaceId">The workspace ID</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of all nodes in workspace</returns>
    Task<List<KnowledgeNode>> GetAllNodesInWorkspaceAsync(string workspaceId, CancellationToken cancellationToken = default);
}