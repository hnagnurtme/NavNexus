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

    public async Task<List<KnowledgeNode>> GetAllRootNodesByWorkspaceIdAsync(string workspaceId, CancellationToken cancellationToken)
    {
        // Validate input
        if (string.IsNullOrWhiteSpace(workspaceId))
            throw new ArgumentException("Workspace ID cannot be empty", nameof(workspaceId));

        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();
            
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId, leve:0})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY]->(c:KnowledgeNode)
                RETURN n, 
                    collect(DISTINCT e) AS evidences, 
                    collect(DISTINCT c) AS children
                ORDER BY n.created_at DESC
                LIMIT 100  // Thêm giới hạn để tránh overload
            ", new { workspaceId });

            var nodes = new List<KnowledgeNode>();
            await foreach (var record in result.WithCancellation(cancellationToken))
            {
                var node = record["n"].As<INode>();
                var evidences = record["evidences"].As<List<INode>>();
                var childrenNodes = record["children"].As<List<INode>>();
    
                var knowledgeNode = MapKnowledgeNode(node, evidences, childrenNodes, new List<INode>());
                nodes.Add(knowledgeNode);
            }

            return nodes;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching root KnowledgeNodes for workspace '{workspaceId}': {ex.Message}", ex);
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

    // Copy nodes from other workspaces when source_id in evidences is the same
    // Creates new nodes with new IDs and new workspace_id to avoid conflicts
    public async Task<List<KnowledgeNode>> CopyNodesAsync(string evidenceSourceId, string newWorkspaceId, CancellationToken cancellationToken)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();

            // Sao chép nodes từ workspace khác có cùng source_id sang workspace mới
            // Dùng MERGE để tránh duplicate khi node có nhiều evidences từ các files khác nhau
            var result = await session.RunAsync(@"
                // Bước 1: Tìm tất cả nodes từ workspace khác có evidence với source_id này
                MATCH (originalNode:KnowledgeNode)
                WHERE originalNode.workspace_id <> $newWorkspaceId
                MATCH (originalNode)-[:HAS_EVIDENCE]->(originalEvidence:Evidence {source_id: $evidenceSourceId})

                // Bước 2: MERGE node - tạo mới hoặc sử dụng node đã có (dựa trên name + type + workspace_id)
                WITH originalNode,
                     collect(DISTINCT originalEvidence) as originalEvidences
                MERGE (newNode:KnowledgeNode {
                    name: originalNode.name,
                    type: originalNode.type,
                    workspace_id: $newWorkspaceId
                })
                ON CREATE SET
                    newNode.id = originalNode.type + '-' + substring(randomUUID(), 0, 8),
                    newNode.synthesis = originalNode.synthesis,
                    newNode.level = originalNode.level,
                    newNode.source_count = 1,
                    newNode.total_confidence = originalNode.total_confidence,
                    newNode.created_at = datetime(),
                    newNode.updated_at = datetime()
                ON MATCH SET
                    newNode.source_count = newNode.source_count + 1,
                    newNode.synthesis = CASE
                        WHEN newNode.synthesis <> originalNode.synthesis
                        THEN newNode.synthesis 
                        ELSE newNode.synthesis
                    END,
                    newNode.updated_at = datetime()

                // Bước 3: Clone evidences cho node (luôn tạo evidences mới cho mỗi source_id)
                WITH newNode, originalNode, originalEvidences
                UNWIND originalEvidences as originalEvidence

                // Kiểm tra xem evidence từ source_id này đã tồn tại chưa
                MERGE (newEvidence:Evidence {
                    source_id: originalEvidence.source_id,
                    chunk_id: originalEvidence.chunk_id
                })
                ON CREATE SET
                    newEvidence.id = randomUUID(),
                    newEvidence.source_name = originalEvidence.source_name,
                    newEvidence.text = originalEvidence.text,
                    newEvidence.page = originalEvidence.page,
                    newEvidence.confidence = originalEvidence.confidence,
                    newEvidence.created_at = datetime(),
                    newEvidence.language = originalEvidence.language,
                    newEvidence.source_language = originalEvidence.source_language,
                    newEvidence.hierarchy_path = originalEvidence.hierarchy_path,
                    newEvidence.concepts = originalEvidence.concepts,
                    newEvidence.key_claims = originalEvidence.key_claims,
                    newEvidence.questions_raised = originalEvidence.questions_raised,
                    newEvidence.evidence_strength = originalEvidence.evidence_strength

                // Tạo relationship giữa node và evidence (nếu chưa có)
                MERGE (newNode)-[:HAS_EVIDENCE]->(newEvidence)

                // Bước 4: Return node với evidences
                WITH newNode, originalNode, collect(DISTINCT newEvidence) as newEvidences
                RETURN newNode, newEvidences, originalNode.id as originalNodeId
                ORDER BY newNode.level, newNode.created_at
            ", new { evidenceSourceId, newWorkspaceId });

            var processedNodeIds = new HashSet<string>(); // Track nodes đã được process
            var oldToNewIdMap = new Dictionary<string, string>(); // Map từ old ID -> new ID để tạo relationships sau

            // Collect tất cả nodes đã được tạo/updated
            await foreach (var record in result.WithCancellation(cancellationToken))
            {
                var newNode = record["newNode"].As<INode>();
                var originalNodeId = record["originalNodeId"].As<string>();
                var newNodeId = GetStringProperty(newNode, "id");

                // Track mapping từ old ID sang new ID
                oldToNewIdMap[originalNodeId] = newNodeId;
                processedNodeIds.Add(newNodeId);
            }

            // Sau khi MERGE xong, query lại để lấy nodes với evidences từ source_id này
            var copiedNodes = new List<KnowledgeNode>();
            if (processedNodeIds.Count > 0)
            {
                var nodesResult = await session.RunAsync(@"
                    MATCH (n:KnowledgeNode)
                    WHERE n.id IN $nodeIds
                    OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                    WHERE e.source_id = $evidenceSourceId
                    RETURN n, collect(e) as evidences
                ", new { nodeIds = processedNodeIds.ToList(), evidenceSourceId });

                await foreach (var record in nodesResult.WithCancellation(cancellationToken))
                {
                    var node = record["n"].As<INode>();
                    var evidences = record["evidences"].As<List<INode>>();

                    var knowledgeNode = MapKnowledgeNodeSimple(node, evidences);
                    copiedNodes.Add(knowledgeNode);
                }
            }

            // Bước 5: Clone relationships giữa các nodes
            // Tìm relationships giữa các original nodes và tạo lại cho new nodes
            if (oldToNewIdMap.Count > 0)
            {
                // Clone HAS_SUBCATEGORY relationships
                await session.RunAsync(@"
                    UNWIND $idMappings as mapping
                    MATCH (oldParent:KnowledgeNode {id: mapping.oldId})-[:HAS_SUBCATEGORY]->(oldChild:KnowledgeNode)
                    WHERE oldChild.id IN $oldNodeIds
                    WITH mapping.newId as newParentId, oldChild.id as oldChildId
                    UNWIND $idMappings as childMapping
                    WITH newParentId, oldChildId, childMapping
                    WHERE childMapping.oldId = oldChildId
                    MATCH (newParent:KnowledgeNode {id: newParentId})
                    MATCH (newChild:KnowledgeNode {id: childMapping.newId})
                    MERGE (newParent)-[:HAS_SUBCATEGORY]->(newChild)
                ", new
                {
                    oldNodeIds = oldToNewIdMap.Keys.ToList(),
                    idMappings = oldToNewIdMap.Select(kvp => new { oldId = kvp.Key, newId = kvp.Value }).ToList()
                });

                // Clone CONTAINS_CONCEPT relationships
                await session.RunAsync(@"
                    UNWIND $idMappings as mapping
                    MATCH (oldParent:KnowledgeNode {id: mapping.oldId})-[:CONTAINS_CONCEPT]->(oldChild:KnowledgeNode)
                    WHERE oldChild.id IN $oldNodeIds
                    WITH mapping.newId as newParentId, oldChild.id as oldChildId
                    UNWIND $idMappings as childMapping
                    WITH newParentId, oldChildId, childMapping
                    WHERE childMapping.oldId = oldChildId
                    MATCH (newParent:KnowledgeNode {id: newParentId})
                    MATCH (newChild:KnowledgeNode {id: childMapping.newId})
                    MERGE (newParent)-[:CONTAINS_CONCEPT]->(newChild)
                ", new
                {
                    oldNodeIds = oldToNewIdMap.Keys.ToList(),
                    idMappings = oldToNewIdMap.Select(kvp => new { oldId = kvp.Key, newId = kvp.Value }).ToList()
                });

                // Clone HAS_DETAIL relationships
                await session.RunAsync(@"
                    UNWIND $idMappings as mapping
                    MATCH (oldParent:KnowledgeNode {id: mapping.oldId})-[:HAS_DETAIL]->(oldChild:KnowledgeNode)
                    WHERE oldChild.id IN $oldNodeIds
                    WITH mapping.newId as newParentId, oldChild.id as oldChildId
                    UNWIND $idMappings as childMapping
                    WITH newParentId, oldChildId, childMapping
                    WHERE childMapping.oldId = oldChildId
                    MATCH (newParent:KnowledgeNode {id: newParentId})
                    MATCH (newChild:KnowledgeNode {id: childMapping.newId})
                    MERGE (newParent)-[:HAS_DETAIL]->(newChild)
                ", new
                {
                    oldNodeIds = oldToNewIdMap.Keys.ToList(),
                    idMappings = oldToNewIdMap.Select(kvp => new { oldId = kvp.Key, newId = kvp.Value }).ToList()
                });
            }

            return copiedNodes;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while copying nodes with source_id '{evidenceSourceId}' to workspace '{newWorkspaceId}': {ex.Message}", ex);
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