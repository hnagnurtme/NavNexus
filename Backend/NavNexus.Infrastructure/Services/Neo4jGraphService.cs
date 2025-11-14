using Neo4j.Driver;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Domain.Entities;

namespace NavNexus.Infrastructure.Services;

/// <summary>
/// Neo4j service implementation for knowledge graph operations
/// </summary>
public class Neo4jGraphService : INeo4jService
{
    private readonly IDriver? _driver;

    public Neo4jGraphService()
    {
        // TODO: Initialize from configuration
        // For now, create a placeholder that won't fail
        try
        {
            _driver = GraphDatabase.Driver("bolt://localhost:7687", AuthTokens.Basic("neo4j", "password"));
        }
        catch
        {
            _driver = null;
        }
    }

    public async Task<List<string>> UpsertKnowledgeNodesAsync(List<KnowledgeNodePoco> nodes, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return nodes.Select(n => n.Id).ToList();
        
        var session = _driver.AsyncSession();
        try
        {
            var nodeIds = new List<string>();
            foreach (var node in nodes)
            {
                var result = await session.ExecuteWriteAsync(async tx =>
                {
                    var query = @"
                        MERGE (n:KnowledgeNode {id: $id})
                        SET n.name = $name,
                            n.type = $type,
                            n.level = $level,
                            n.synthesis = $synthesis,
                            n.concepts = $concepts,
                            n.qdrant_vector_id = $qdrantVectorId,
                            n.workspace_id = $workspaceId,
                            n.created_at = $createdAt,
                            n.is_gap = $isGap,
                            n.is_crossroads = $isCrossroads
                        RETURN n.id as id";
                    
                    var cursor = await tx.RunAsync(query, new
                    {
                        id = node.Id,
                        name = node.Name,
                        type = node.Type,
                        level = node.Level,
                        synthesis = node.Synthesis,
                        concepts = node.Concepts,
                        qdrantVectorId = node.QdrantVectorId,
                        workspaceId = node.WorkspaceId,
                        createdAt = node.CreatedAt,
                        isGap = node.IsGap,
                        isCrossroads = node.IsCrossroads
                    });
                    
                    var record = await cursor.SingleAsync();
                    return record["id"].As<string>();
                });
                nodeIds.Add(result);
            }
            return nodeIds;
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    public async Task<List<string>> CreateEvidenceNodesAsync(List<EvidenceNodePoco> evidences, List<string> knowledgeNodeIds, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return evidences.Select(e => e.Id).ToList();
        
        var session = _driver.AsyncSession();
        try
        {
            var evidenceIds = new List<string>();
            for (int i = 0; i < evidences.Count; i++)
            {
                var evidence = evidences[i];
                var knowledgeNodeId = knowledgeNodeIds[Math.Min(i, knowledgeNodeIds.Count - 1)];
                
                await session.ExecuteWriteAsync(async tx =>
                {
                    var query = @"
                        CREATE (e:Evidence {
                            id: $id,
                            text: $text,
                            location: $location,
                            source_title: $sourceTitle,
                            source_author: $sourceAuthor,
                            source_year: $sourceYear,
                            source_url: $sourceUrl,
                            confidence_score: $confidenceScore,
                            workspace_id: $workspaceId
                        })
                        WITH e
                        MATCH (k:KnowledgeNode {id: $knowledgeNodeId})
                        CREATE (k)-[:HAS_EVIDENCE]->(e)
                        RETURN e.id as id";
                    
                    var cursor = await tx.RunAsync(query, new
                    {
                        id = evidence.Id,
                        text = evidence.Text,
                        location = evidence.Location,
                        sourceTitle = evidence.SourceTitle,
                        sourceAuthor = evidence.SourceAuthor,
                        sourceYear = evidence.SourceYear,
                        sourceUrl = evidence.SourceUrl,
                        confidenceScore = evidence.ConfidenceScore,
                        workspaceId = evidence.WorkspaceId,
                        knowledgeNodeId
                    });
                    
                    var record = await cursor.SingleAsync();
                    return record["id"].As<string>();
                });
                evidenceIds.Add(evidence.Id);
            }
            return evidenceIds;
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    public async Task CreateRelationshipsAsync(List<(string parentId, string childId)> relationships, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return;
        
        var session = _driver.AsyncSession();
        try
        {
            foreach (var (parentId, childId) in relationships)
            {
                await session.ExecuteWriteAsync(async tx =>
                {
                    var query = @"
                        MATCH (parent:KnowledgeNode {id: $parentId})
                        MATCH (child:KnowledgeNode {id: $childId})
                        MERGE (parent)-[:HAS_CHILD]->(child)";
                    
                    await tx.RunAsync(query, new { parentId, childId });
                });
            }
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    public async Task<List<KnowledgeNodePoco>> GetKnowledgeGraphAsync(string workspaceId, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return new List<KnowledgeNodePoco>();
        
        var session = _driver.AsyncSession();
        try
        {
            return await session.ExecuteReadAsync(async tx =>
            {
                var query = @"
                    MATCH (n:KnowledgeNode {workspace_id: $workspaceId})
                    RETURN n";
                
                var cursor = await tx.RunAsync(query, new { workspaceId });
                var nodes = new List<KnowledgeNodePoco>();
                
                await cursor.ForEachAsync(record =>
                {
                    var node = record["n"].As<INode>();
                    nodes.Add(MapToKnowledgeNode(node));
                });
                
                return nodes;
            });
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    public async Task<List<KnowledgeNodePoco>> FindOrphanNodesAsync(string workspaceId, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return new List<KnowledgeNodePoco>();
        
        var session = _driver.AsyncSession();
        try
        {
            return await session.ExecuteReadAsync(async tx =>
            {
                var query = @"
                    MATCH (n:KnowledgeNode {workspace_id: $workspaceId})
                    WHERE NOT (n)-[:HAS_CHILD|HAS_EVIDENCE]-()
                    RETURN n";
                
                var cursor = await tx.RunAsync(query, new { workspaceId });
                var nodes = new List<KnowledgeNodePoco>();
                
                await cursor.ForEachAsync(record =>
                {
                    var node = record["n"].As<INode>();
                    nodes.Add(MapToKnowledgeNode(node));
                });
                
                return nodes;
            });
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    public async Task<List<KnowledgeNodePoco>> FindWeakConnectionsAsync(string workspaceId, int minEvidenceCount, CancellationToken cancellationToken = default)
    {
        if (_driver == null) return new List<KnowledgeNodePoco>();
        
        var session = _driver.AsyncSession();
        try
        {
            return await session.ExecuteReadAsync(async tx =>
            {
                var query = @"
                    MATCH (n:KnowledgeNode {workspace_id: $workspaceId})-[r:HAS_EVIDENCE]-(e)
                    WITH n, COUNT(e) as evidence_count
                    WHERE evidence_count < $minEvidenceCount
                    RETURN n";
                
                var cursor = await tx.RunAsync(query, new { workspaceId, minEvidenceCount });
                var nodes = new List<KnowledgeNodePoco>();
                
                await cursor.ForEachAsync(record =>
                {
                    var node = record["n"].As<INode>();
                    nodes.Add(MapToKnowledgeNode(node));
                });
                
                return nodes;
            });
        }
        finally
        {
            await session.CloseAsync();
        }
    }

    private KnowledgeNodePoco MapToKnowledgeNode(INode node)
    {
        return new KnowledgeNodePoco
        {
            Id = node.Properties["id"].As<string>(),
            Name = node.Properties["name"].As<string>(),
            Type = node.Properties["type"].As<string>(),
            Level = node.Properties["level"].As<int>(),
            Synthesis = node.Properties["synthesis"].As<string>(),
            Concepts = node.Properties.ContainsKey("concepts") ? node.Properties["concepts"].As<List<string>>() : new List<string>(),
            QdrantVectorId = node.Properties.ContainsKey("qdrant_vector_id") ? node.Properties["qdrant_vector_id"].As<string>() : null,
            WorkspaceId = node.Properties["workspace_id"].As<string>(),
            CreatedAt = node.Properties["created_at"].As<DateTime>(),
            IsGap = node.Properties.ContainsKey("is_gap") && node.Properties["is_gap"].As<bool>(),
            IsCrossroads = node.Properties.ContainsKey("is_crossroads") && node.Properties["is_crossroads"].As<bool>()
        };
    }
}
