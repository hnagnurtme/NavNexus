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
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId, level:0})
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:HAS_SUBCATEGORY]->(c:KnowledgeNode)
                RETURN n, 
                    collect(DISTINCT e) AS evidences, 
                    collect(DISTINCT c) AS children
                ORDER BY n.created_at DESC
                LIMIT 100  
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

        // Bước 1: Tìm tất cả nodes có evidence từ source_id này, bao gồm cả cây con
        var result = await session.RunAsync(@"
            // Tìm tất cả nodes có evidence từ source_id
            MATCH (originalNode:KnowledgeNode)-[:HAS_EVIDENCE]->(originalEvidence:Evidence {source_id: $evidenceSourceId})
            WHERE originalNode.workspace_id <> $newWorkspaceId
            
            // Tìm toàn bộ cây con của các nodes này
            OPTIONAL MATCH (originalNode)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL*0..10]->(childNode:KnowledgeNode)
            
            WITH COLLECT(DISTINCT originalNode) + COLLECT(DISTINCT childNode) AS allNodes
            UNWIND allNodes AS nodeToCopy
            WITH DISTINCT nodeToCopy
            
            // Bước 2: Tạo hoặc cập nhật node trong workspace mới
            MERGE (newNode:KnowledgeNode {
                id: nodeToCopy.id + '-copy-' + $newWorkspaceId,
                workspace_id: $newWorkspaceId
            })
            ON CREATE SET
                newNode.name = nodeToCopy.name,
                newNode.type = nodeToCopy.type,
                newNode.synthesis = nodeToCopy.synthesis,
                newNode.level = nodeToCopy.level,
                newNode.created_at = datetime(),
                newNode.updated_at = datetime(),
                newNode.source_count = 0, // Sẽ tính lại sau
                newNode.total_confidence = 0.0 // Sẽ tính lại sau
            ON MATCH SET
                newNode.updated_at = datetime()
            
            // Bước 3: Copy evidences từ source_id này
            WITH newNode, nodeToCopy
            MATCH (nodeToCopy)-[:HAS_EVIDENCE]->(originalEvidence:Evidence {source_id: $evidenceSourceId})
            
            // Tạo evidence mới với ID duy nhất
            CREATE (newEvidence:Evidence {
                id: 'evidence-' + randomUUID(),
                source_id: originalEvidence.source_id,
                source_name: originalEvidence.source_name,
                chunk_id: originalEvidence.chunk_id,
                text: originalEvidence.text,
                page: originalEvidence.page,
                confidence: originalEvidence.confidence,
                created_at: datetime(),
                language: originalEvidence.language,
                source_language: originalEvidence.source_language,
                hierarchy_path: originalEvidence.hierarchy_path,
                concepts: originalEvidence.concepts,
                key_claims: originalEvidence.key_claims,
                questions_raised: originalEvidence.questions_raised,
                evidence_strength: originalEvidence.evidence_strength
            })
            
            // Tạo relationship
            MERGE (newNode)-[:HAS_EVIDENCE]->(newEvidence)
            
            RETURN newNode.id AS newNodeId, nodeToCopy.id AS originalNodeId
        ", new { evidenceSourceId, newWorkspaceId });

        var oldToNewIdMap = new Dictionary<string, string>();
        await foreach (var record in result.WithCancellation(cancellationToken))
        {
            var originalNodeId = record["originalNodeId"].As<string>();
            var newNodeId = record["newNodeId"].As<string>();
            oldToNewIdMap[originalNodeId] = newNodeId;
        }

        // Bước 4: Copy relationships giữa các nodes
        if (oldToNewIdMap.Count > 0)
        {
            await CopyRelationshipsAsync(session, oldToNewIdMap, "HAS_SUBCATEGORY");
            await CopyRelationshipsAsync(session, oldToNewIdMap, "CONTAINS_CONCEPT");
            await CopyRelationshipsAsync(session, oldToNewIdMap, "HAS_DETAIL");
        }

        // Bước 5: Tính toán lại source_count và total_confidence
        await RecalculateNodeStatisticsAsync(session, newWorkspaceId);

        // Bước 6: Lấy kết quả cuối cùng
        return await GetCopiedNodesWithEvidencesAsync(session, oldToNewIdMap.Values.ToList(), evidenceSourceId, cancellationToken);
    }
    catch (Exception ex)
    {
        throw new Exception($"Error while copying nodes with source_id '{evidenceSourceId}' to workspace '{newWorkspaceId}': {ex.Message}", ex);
    }
}

private async Task CopyRelationshipsAsync(IAsyncSession session, Dictionary<string, string> idMap, string relationshipType)
{
    var relationships = await session.RunAsync(@"
        UNWIND $mappings AS mapping
        MATCH (oldParent:KnowledgeNode {id: mapping.oldId})-[r:" + relationshipType + @"]->(oldChild:KnowledgeNode)
        WHERE oldChild.id IN $oldIds
        RETURN mapping.oldId as oldParentId, mapping.newId as newParentId, oldChild.id as oldChildId
    ", new
    {
        mappings = idMap.Select(kvp => new { oldId = kvp.Key, newId = kvp.Value }).ToList(),
        oldIds = idMap.Keys.ToList()
    });

    var relationshipsToCreate = new List<object>();
    await foreach (var record in relationships)
    {
        var oldParentId = record["oldParentId"].As<string>();
        var newParentId = record["newParentId"].As<string>();
        var oldChildId = record["oldChildId"].As<string>();

        if (idMap.TryGetValue(oldChildId, out var newChildId))
        {
            relationshipsToCreate.Add(new
            {
                parentId = newParentId,
                childId = newChildId,
                relationshipType = relationshipType
            });
        }
    }

    // Tạo relationships mới
    if (relationshipsToCreate.Count > 0)
    {
        await session.RunAsync(@"
            UNWIND $relationships AS rel
            MATCH (parent:KnowledgeNode {id: rel.parentId})
            MATCH (child:KnowledgeNode {id: rel.childId})
            MERGE (parent)-[r:" + relationshipType + @"]->(child)
        ", new { relationships = relationshipsToCreate });
    }
}

private async Task RecalculateNodeStatisticsAsync(IAsyncSession session, string workspaceId)
{
    // Tính toán lại source_count dựa trên số lượng source_id distinct
    await session.RunAsync(@"
        MATCH (n:KnowledgeNode {workspace_id: $workspaceId})-[:HAS_EVIDENCE]->(e:Evidence)
        WITH n, COUNT(DISTINCT e.source_id) as distinctSourceCount, AVG(e.confidence) as avgConfidence
        SET n.source_count = distinctSourceCount,
            n.total_confidence = avgConfidence
    ", new { workspaceId });
}

private async Task<List<KnowledgeNode>> GetCopiedNodesWithEvidencesAsync(
    IAsyncSession session, 
    List<string> nodeIds, 
    string evidenceSourceId, 
    CancellationToken cancellationToken)
{
    var result = await session.RunAsync(@"
        MATCH (n:KnowledgeNode)
        WHERE n.id IN $nodeIds
        OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
        RETURN n, collect(DISTINCT e) as evidences
        ORDER BY n.level, n.name
    ", new { nodeIds, evidenceSourceId });

    var nodes = new List<KnowledgeNode>();
    await foreach (var record in result.WithCancellation(cancellationToken))
    {
        var node = record["n"].As<INode>();
        var evidences = record["evidences"].As<List<INode>>();
        var knowledgeNode = MapKnowledgeNodeSimple(node, evidences);
        nodes.Add(knowledgeNode);
    }

    return nodes;
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

            var rawSuggestionText = GetStringProperty(g, "suggestion_text");
            var cleanedText = CleanGapSuggestionText(rawSuggestionText);

            if (!string.IsNullOrWhiteSpace(cleanedText))
            {
                knowledgeNode.GapSuggestions.Add(new GapSuggestion
                {
                    Id = GetStringProperty(g, "id"),
                    SuggestionText = cleanedText,
                    TargetNodeId = GetStringProperty(g, "target_node_id"),
                    TargetFileId = GetStringProperty(g, "target_file_id"),
                    SimilarityScore = GetFloatProperty(g, "similarity_score")
                });
            }
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

    private static string CleanGapSuggestionText(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return string.Empty;
        }

        var trimmed = text.Trim();

        // Check if the text accidentally contains JSON (starts with [ or {)
        // This handles cases where old data was saved incorrectly
        if (trimmed.StartsWith('[') || trimmed.StartsWith('{'))
        {
            try
            {
                // Try to extract from array format: [{"suggestion_text":"..."}]
                if (trimmed.StartsWith('['))
                {
                    var arrayStart = trimmed.IndexOf('[');
                    var arrayEnd = trimmed.LastIndexOf(']');
                    if (arrayStart >= 0 && arrayEnd > arrayStart)
                    {
                        var jsonArray = trimmed.Substring(arrayStart, arrayEnd - arrayStart + 1);
                        var suggestions = System.Text.Json.JsonSerializer.Deserialize<List<System.Collections.Generic.Dictionary<string, string>>>(
                            jsonArray,
                            new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                        if (suggestions?.Count > 0 && suggestions[0].TryGetValue("suggestion_text", out var suggestionText))
                        {
                            return suggestionText.Trim();
                        }
                    }
                }
                // Try to extract from object format: {"suggestion_text":"..."}
                else if (trimmed.StartsWith('{'))
                {
                    var suggestion = System.Text.Json.JsonSerializer.Deserialize<System.Collections.Generic.Dictionary<string, string>>(
                        trimmed,
                        new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                    if (suggestion != null && suggestion.TryGetValue("suggestion_text", out var suggestionText))
                    {
                        return suggestionText.Trim();
                    }
                }
            }
            catch
            {
                // If JSON parsing fails, just return the original text
                return trimmed;
            }
        }

        return trimmed;
    }

    public async Task<List<KnowledgeNode>> GetLeafNodesAsync(string workspaceId, CancellationToken cancellationToken = default)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();

            // Find nodes with no outgoing relationships (leaf nodes)
            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {workspace_id: $workspaceId})
                WHERE NOT (n)-[:HAS_SUBCATEGORY|CONTAINS_CONCEPT|HAS_DETAIL]->()
                OPTIONAL MATCH (n)-[:HAS_EVIDENCE]->(e:Evidence)
                OPTIONAL MATCH (n)-[:HAS_SUGGESTION]->(g:GapSuggestion)
                RETURN n,
                       collect(DISTINCT e) AS evidences,
                       collect(DISTINCT g) AS suggestions
                ORDER BY n.level DESC
            ", new { workspaceId });

            var nodes = new List<KnowledgeNode>();
            await foreach (var record in result.WithCancellation(cancellationToken))
            {
                var node = record["n"].As<INode>();
                var evidences = record["evidences"].As<List<INode>>();
                var suggestions = record["suggestions"].As<List<INode>>();

                var knowledgeNode = MapKnowledgeNode(node, evidences, new List<INode>(), suggestions);
                nodes.Add(knowledgeNode);
            }

            return nodes;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error while fetching leaf nodes for workspace '{workspaceId}': {ex.Message}", ex);
        }
    }

    public async Task<bool> HasGapSuggestionsAsync(string nodeId, CancellationToken cancellationToken = default)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();

            var result = await session.RunAsync(@"
                MATCH (n:KnowledgeNode {id: $nodeId})-[:HAS_SUGGESTION]->(g:GapSuggestion)
                RETURN COUNT(g) as suggestionCount
            ", new { nodeId });

            var record = await result.SingleOrDefaultAsync(cancellationToken);
            if (record == null) return false;

            var count = record["suggestionCount"].As<long>();
            return count > 0;
        }
        catch (Exception ex)
        {
            throw new Exception($"Error checking gap suggestions for node '{nodeId}': {ex.Message}", ex);
        }
    }

    public async Task SaveGapSuggestionsAsync(string nodeId, List<GapSuggestion> suggestions, CancellationToken cancellationToken = default)
    {
        try
        {
            await using var session = _neo4jConnection.GetAsyncSession();

            foreach (var suggestion in suggestions)
            {
                await session.RunAsync(@"
                    MATCH (n:KnowledgeNode {id: $nodeId})
                    MERGE (g:GapSuggestion {id: $suggestionId})
                    SET g.suggestion_text = $suggestionText,
                        g.target_node_id = $targetNodeId,
                        g.target_file_id = $targetFileId,
                        g.similarity_score = $similarityScore
                    MERGE (n)-[:HAS_SUGGESTION]->(g)
                ", new
                {
                    nodeId,
                    suggestionId = suggestion.Id,
                    suggestionText = suggestion.SuggestionText,
                    targetNodeId = suggestion.TargetNodeId,
                    targetFileId = suggestion.TargetFileId,
                    similarityScore = suggestion.SimilarityScore
                });
            }
        }
        catch (Exception ex)
        {
            throw new Exception($"Error saving gap suggestions for node '{nodeId}': {ex.Message}", ex);
        }
    }

}