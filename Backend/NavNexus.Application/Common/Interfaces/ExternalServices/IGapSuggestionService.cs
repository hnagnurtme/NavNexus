using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface IGapSuggestionService
{
    /// <summary>
    /// Generate gap suggestions for a leaf node using LLM
    /// </summary>
    /// <param name="leafNode">The leaf node to generate suggestions for</param>
    /// <param name="allNodesInWorkspace">All nodes in the workspace for context</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of generated gap suggestions</returns>
    Task<List<GapSuggestion>> GenerateGapSuggestionsAsync(
        KnowledgeNode leafNode,
        List<KnowledgeNode> allNodesInWorkspace,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a node has gap suggestions
    /// </summary>
    /// <param name="nodeId">The node ID to check</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>True if node has gap suggestions, false otherwise</returns>
    Task<bool> HasGapSuggestionsAsync(string nodeId, CancellationToken cancellationToken = default);
}
