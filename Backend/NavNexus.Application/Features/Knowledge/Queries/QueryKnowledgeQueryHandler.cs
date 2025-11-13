using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Common.Models;

namespace NavNexus.Application.Features.Knowledge.Queries;

/// <summary>
/// Handler for knowledge queries - implements Flow 3 from flow.md
/// STEP 1: Semantic Search (Qdrant)
/// STEP 2: Graph Traversal (Neo4j)
/// STEP 3: LLM Synthesis
/// </summary>
public class QueryKnowledgeQueryHandler : IRequestHandler<QueryKnowledgeQuery, Result<QueryKnowledgeResult>>
{
    private readonly IQdrantService _qdrantService;
    private readonly INeo4jService _neo4jService;
    private readonly ILlmService _llmService;
    private readonly ILogger<QueryKnowledgeQueryHandler> _logger;

    public QueryKnowledgeQueryHandler(
        IQdrantService qdrantService,
        INeo4jService neo4jService,
        ILlmService llmService,
        ILogger<QueryKnowledgeQueryHandler> logger)
    {
        _qdrantService = qdrantService;
        _neo4jService = neo4jService;
        _llmService = llmService;
        _logger = logger;
    }

    public async Task<Result<QueryKnowledgeResult>> Handle(QueryKnowledgeQuery request, CancellationToken cancellationToken)
    {
        try
        {
            _logger.LogInformation("Processing knowledge query for workspace {WorkspaceId}: {Query}", 
                request.WorkspaceId, request.Query);

            // STEP 1: Semantic Search (Qdrant)
            var collectionName = $"workspace_{request.WorkspaceId}";
            var queryVector = await _qdrantService.GenerateEmbeddingAsync(request.Query, cancellationToken);
            var semanticChunks = await _qdrantService.SearchSimilarChunksAsync(
                collectionName, 
                queryVector, 
                request.Limit, 
                cancellationToken);

            _logger.LogInformation("Found {Count} similar chunks from Qdrant", semanticChunks.Count);

            // STEP 2: Graph Traversal (Neo4j)
            var knowledgeGraph = await _neo4jService.GetKnowledgeGraphAsync(request.WorkspaceId, cancellationToken);
            
            _logger.LogInformation("Retrieved {Count} nodes from knowledge graph", knowledgeGraph.Count);

            // STEP 3: LLM Synthesis
            var answer = await _llmService.GenerateAnswerAsync(request.Query, semanticChunks, knowledgeGraph, cancellationToken);

            // Build response
            var result = new QueryKnowledgeResult
            {
                Answer = answer,
                Evidences = semanticChunks.Take(5).Select(chunk => new EvidenceDto
                {
                    Id = chunk.ChunkId,
                    Text = chunk.Quote,
                    Source = chunk.PaperId,
                    Url = $"https://nos.example.com/{request.WorkspaceId}/{chunk.PaperId}",
                    ConfidenceScore = 0.9 
                }).ToList(),
                RelatedTopics = knowledgeGraph.Take(5).Select(node => new TopicDto
                {
                    Id = node.Id,
                    Name = node.Name,
                    RelevanceScore = 0.85 
                }).ToList(),
                GraphPath = knowledgeGraph.Take(3).Select(n => n.Id).ToList()
            };

            return Result<QueryKnowledgeResult>.Success(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing knowledge query for workspace {WorkspaceId}", request.WorkspaceId);
            return Result<QueryKnowledgeResult>.Failure($"Query failed: {ex.Message}", "QUERY_FAILED");
        }
    }
}
