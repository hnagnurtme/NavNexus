using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for Neo4j knowledge graph operations
/// </summary>
public interface INeo4jService
{
    /// <summary>
    /// Creates or updates knowledge nodes in the graph
    /// </summary>
    Task<List<string>> UpsertKnowledgeNodesAsync(List<KnowledgeNodePoco> nodes, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Creates evidence nodes and links them to knowledge nodes
    /// </summary>
    Task<List<string>> CreateEvidenceNodesAsync(List<EvidenceNodePoco> evidences, List<string> knowledgeNodeIds, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Creates relationships between knowledge nodes (HAS_CHILD)
    /// </summary>
    Task CreateRelationshipsAsync(List<(string parentId, string childId)> relationships, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Gets knowledge graph for a workspace
    /// </summary>
    Task<List<KnowledgeNodePoco>> GetKnowledgeGraphAsync(string workspaceId, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Finds orphan nodes (gap detection)
    /// </summary>
    Task<List<KnowledgeNodePoco>> FindOrphanNodesAsync(string workspaceId, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Finds weak connections (nodes with few evidences)
    /// </summary>
    Task<List<KnowledgeNodePoco>> FindWeakConnectionsAsync(string workspaceId, int minEvidenceCount, CancellationToken cancellationToken = default);
}
