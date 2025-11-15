using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;
using Neo4j.Driver;

namespace NavNexus.Infrastructure.Persistence.Repositories;

public class KnowLedgeTreeRepository : IKnowledgetreeRepository
{
    private readonly Neo4jConnection _neo4jConnection;

    public KnowLedgeTreeRepository(Neo4jConnection neo4jConnection)
    {
        _neo4jConnection = neo4jConnection;
    }

    public async Task<KnowledgeNode?> GetNodeByIdAsync(string id, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {id: $id})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:CONTAINS_CONCEPT]->(c:KnowledgeNode)
                RETURN n, collect(e) AS evidences, collect(c) AS children
            ", new { id });

            var record = await result.SingleOrDefaultAsync(cancellationToken);
            if (record == null) return null;

            var node = record["n"].As<INode>();
            var evidences = record["evidences"].As<List<INode>>();
            var childrenNodes = record["children"].As<List<INode>>();

            var knowledgeNode = MapKnowledgeNode(node, evidences, childrenNodes);
            return knowledgeNode;
        }
        catch (Exception ex)
        {
            // Có thể log ex.Message, ex.StackTrace
            throw new Exception($"Error while fetching KnowledgeNode by Id '{id}': {ex.Message}", ex);
        }
    }

    public async Task<KnowledgeNode?> GetRootNodeByWorkspaceIdAsync(string workspaceId, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId, level: 0})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:CONTAINS_CONCEPT]->(c:KnowledgeNode)
                RETURN n, collect(e) AS evidences, collect(c) AS children
            ", new { workspaceId });

            var record = await result.SingleOrDefaultAsync(cancellationToken);
            if (record == null) return null;

            var node = record["n"].As<INode>();
            var evidences = record["evidences"].As<List<INode>>();
            var childrenNodes = record["children"].As<List<INode>>();

            var knowledgeNode = MapKnowledgeNode(node, evidences, childrenNodes);
            return knowledgeNode;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching root KnowledgeNode for workspace '{workspaceId}': {ex.Message}", ex);
        }
    }

    private KnowledgeNode MapKnowledgeNode(INode node, List<INode> evidences, List<INode> childrenNodes)
    {
        var knowledgeNode = new KnowledgeNode
        {
            Id = node.Properties["id"].As<string>(),
            Type = node.Properties["type"].As<string>(),
            Name = node.Properties["name"].As<string>(),
            Synthesis = node.Properties["synthesis"].As<string>(),
            WorkspaceId = node.Properties["workspace_id"].As<string>(),
            Level = (int)node.Properties["level"].As<long>(),
            SourceCount = (int)node.Properties["sourceCount"].As<long>(),
            TotalConfidence = (float)node.Properties["totalConfidence"].As<double>(),
            CreatedAt = DateTime.Parse(node.Properties["createdAt"].As<string>()),
            UpdatedAt = DateTime.Parse(node.Properties["updatedAt"].As<string>())
        };

        foreach (var e in evidences)
        {
            knowledgeNode.Evidences.Add(new Evidence
            {
                Id = e.Properties["id"].As<string>(),
                Text = e.Properties["text"].As<string>(),
                Page = (int)e.Properties["page"].As<long>(),
                // map các field khác nếu cần
            });
        }

        foreach (var c in childrenNodes)
        {
            knowledgeNode.Children.Add(new KnowledgeNode
            {
                Id = c.Properties["id"].As<string>(),
                Name = c.Properties["name"].As<string>(),
                Type = c.Properties["type"].As<string>(),
                Synthesis = c.Properties["synthesis"].As<string>(),
                WorkspaceId = c.Properties["workspaceId"].As<string>(),
                Level = (int)c.Properties["level"].As<long>(),
                SourceCount = (int)c.Properties["sourceCount"].As<long>(),
                TotalConfidence = (float)c.Properties["totalConfidence"].As<double>(),
                CreatedAt = DateTime.Parse(c.Properties["createdAt"].As<string>()),
                UpdatedAt = DateTime.Parse(c.Properties["updatedAt"].As<string>())
            });
        }

        return knowledgeNode;
    }
}
