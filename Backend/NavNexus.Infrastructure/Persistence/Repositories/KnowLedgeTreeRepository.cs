using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;
using Neo4j.Driver;

namespace NavNexus.Infrastructure.Persistence.Repositories;

public class KnowledgeTreeRepository : IKnowledgetreeRepository
{
    private readonly Neo4jConnection _neo4jConnection;

    public KnowledgeTreeRepository(Neo4jConnection neo4jConnection)
    {
        _neo4jConnection = neo4jConnection;
    }

    public async Task<KnowledgeNode?> GetNodeByIdAsync(string id, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            
            // Query với đúng relationship names và GapSuggestion
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {id: $id})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->(c:KnowledgeNode)
                OPTIONAL MATCH (n)-[:HAS_SUGGESTION]->(g:GapSuggestion)
                RETURN n, 
                       collect(DISTINCT e) AS evidences, 
                       collect(DISTINCT c) AS children,
                       collect(DISTINCT g) AS suggestions
            ", new { id });

            var record = await result.SingleOrDefaultAsync(cancellationToken);
            if (record == null) return null;

            var node = record["n"].As<INode>();
            var evidences = record["evidences"].As<List<INode>>();
            var childrenNodes = record["children"].As<List<INode>>();
            var suggestions = record["suggestions"].As<List<INode>>();

            var knowledgeNode = MapKnowledgeNode(node, evidences, childrenNodes, suggestions);
            return knowledgeNode;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching KnowledgeNode by Id '{id}': {ex.Message}", ex);
        }
    }

    public async Task<KnowledgeNode?> GetRootNodeByWorkspaceIdAsync(string workspaceId, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            
            // Root node có level = 0, type = "domain"
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId, level: 0, type: 'domain'})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY]->(c:KnowledgeNode)
                RETURN n, 
                       collect(DISTINCT e) AS evidences, 
                       collect(DISTINCT c) AS children
                LIMIT 1
            ", new { workspaceId });

            var record = await result.SingleOrDefaultAsync(cancellationToken);
            if (record == null) return null;

            var node = record["n"].As<INode>();
            var evidences = record["evidences"].As<List<INode>>();
            var childrenNodes = record["children"].As<List<INode>>();

            var knowledgeNode = MapKnowledgeNode(node, evidences, childrenNodes, new List<INode>());
            return knowledgeNode;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching root KnowledgeNode for workspace '{workspaceId}': {ex.Message}", ex);
        }
    }

    public async Task<List<KnowledgeNode>> GetAllNodesInWorkspaceAsync(string workspaceId, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                RETURN n, collect(DISTINCT e) AS evidences
                ORDER BY n.level, n.name
            ", new { workspaceId });

            var nodes = new List<KnowledgeNode>();
            await foreach (var record in result)
            {
                var node = record["n"].As<INode>();
                var evidences = record["evidences"].As<List<INode>>();
                
                var knowledgeNode = MapKnowledgeNodeSimple(node, evidences);
                nodes.Add(knowledgeNode);
            }

            return nodes;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching all nodes for workspace '{workspaceId}': {ex.Message}", ex);
        }
    }

    public async Task<List<KnowledgeNode>> GetMergedNodesAsync(string workspaceId, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            
            // Lấy nodes có nhiều hơn 1 source (merged from multiple documents)
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId})
                MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                WITH n, 
                     count(DISTINCT e.source_id) as source_count,
                     collect(DISTINCT e.source_name) as sources,
                     collect(DISTINCT e) as evidences
                WHERE source_count > 1
                RETURN n, evidences, sources, source_count
                ORDER BY source_count DESC
            ", new { workspaceId });

            var nodes = new List<KnowledgeNode>();
            await foreach (var record in result)
            {
                var node = record["n"].As<INode>();
                var evidences = record["evidences"].As<List<INode>>();
                
                var knowledgeNode = MapKnowledgeNodeSimple(node, evidences);
                nodes.Add(knowledgeNode);
            }

            return nodes;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching merged nodes for workspace '{workspaceId}': {ex.Message}", ex);
        }
    }

    private KnowledgeNode MapKnowledgeNode(INode node, List<INode> evidences, List<INode> childrenNodes, List<INode> suggestions)
    {
        var knowledgeNode = new KnowledgeNode
        {
            Id = GetStringProperty(node, "id"),
            Type = GetStringProperty(node, "type"),
            Name = GetStringProperty(node, "name"),
            Synthesis = GetStringProperty(node, "synthesis"),
            WorkspaceId = GetStringProperty(node, "workspace_id"),
            Level = GetIntProperty(node, "level"),
            SourceCount = GetIntProperty(node, "source_count"),
            TotalConfidence = GetFloatProperty(node, "total_confidence"),
            CreatedAt = GetDateTimeProperty(node, "created_at"),
            UpdatedAt = GetDateTimeProperty(node, "updated_at")
        };

        // Map Evidences với đầy đủ fields
        foreach (var e in evidences)
        {
            if (e.Properties.Count == 0) continue; // Skip empty nodes
            
            knowledgeNode.Evidences.Add(new Evidence
            {
                Id = GetStringProperty(e, "id"),
                SourceId = GetStringProperty(e, "source_id"),
                SourceName = GetStringProperty(e, "source_name"),
                ChunkId = GetStringProperty(e, "chunk_id"),
                Text = GetStringProperty(e, "text"),
                Page = GetIntProperty(e, "page"),
                Confidence = GetFloatProperty(e, "confidence"),
                CreatedAt = GetDateTimeProperty(e, "created_at"),
                Language = GetStringProperty(e, "language"),
                SourceLanguage = GetStringProperty(e, "source_language"),
                HierarchyPath = GetStringProperty(e, "hierarchy_path"),
                Concepts = GetStringListProperty(e, "concepts"),
                KeyClaims = GetStringListProperty(e, "key_claims"),
                QuestionsRaised = GetStringListProperty(e, "questions_raised"),
                EvidenceStrength = GetFloatProperty(e, "evidence_strength")
            });
        }

        // Map Children
        foreach (var c in childrenNodes)
        {
            if (c.Properties.Count == 0) continue;
            
            knowledgeNode.Children.Add(new KnowledgeNode
            {
                Id = GetStringProperty(c, "id"),
                Name = GetStringProperty(c, "name"),
                Type = GetStringProperty(c, "type"),
                Synthesis = GetStringProperty(c, "synthesis"),
                WorkspaceId = GetStringProperty(c, "workspace_id"),
                Level = GetIntProperty(c, "level"),
                SourceCount = GetIntProperty(c, "source_count"),
                TotalConfidence = GetFloatProperty(c, "total_confidence"),
                CreatedAt = GetDateTimeProperty(c, "created_at"),
                UpdatedAt = GetDateTimeProperty(c, "updated_at")
            });
        }

        // Map Gap Suggestions
        foreach (var g in suggestions)
        {
            if (g.Properties.Count == 0) continue;
            
            knowledgeNode.GapSuggestions.Add(new GapSuggestion
            {
                Id = GetStringProperty(g, "id"),
                SuggestionText = GetStringProperty(g, "suggestion_text"),
                TargetNodeId = GetStringProperty(g, "target_node_id"),
                TargetFileId = GetStringProperty(g, "target_file_id"),
                SimilarityScore = GetFloatProperty(g, "similarity_score")
            });
        }

        return knowledgeNode;
    }

    private KnowledgeNode MapKnowledgeNodeSimple(INode node, List<INode> evidences)
    {
        return MapKnowledgeNode(node, evidences, new List<INode>(), new List<INode>());
    }

    // Helper methods để safely get properties
    private string GetStringProperty(INode node, string key)
    {
        return node.Properties.ContainsKey(key) ? node.Properties[key].As<string>() : string.Empty;
    }

    private int GetIntProperty(INode node, string key)
    {
        if (!node.Properties.ContainsKey(key)) return 0;
        var value = node.Properties[key];
        return value is long longValue ? (int)longValue : 0;
    }

    private float GetFloatProperty(INode node, string key)
    {
        if (!node.Properties.ContainsKey(key)) return 0f;
        var value = node.Properties[key];
        return value is double doubleValue ? (float)doubleValue : 0f;
    }

    private DateTime GetDateTimeProperty(INode node, string key)
    {
        if (!node.Properties.ContainsKey(key)) return DateTime.UtcNow;
        
        try
        {
            var value = node.Properties[key].As<string>();
            return DateTime.Parse(value);
        }
        catch
        {
            return DateTime.UtcNow;
        }
    }

    private List<string> GetStringListProperty(INode node, string key)
    {
        if (!node.Properties.ContainsKey(key)) return new List<string>();
        
        try
        {
            return node.Properties[key].As<List<string>>();
        }
        catch
        {
            return new List<string>();
        }
    }
}