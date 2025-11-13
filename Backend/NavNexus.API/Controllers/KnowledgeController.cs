using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NavNexus.API.Contracts.Responses;
using NavNexus.Application.Features.Knowledge.Queries;
using Swashbuckle.AspNetCore.Annotations;

namespace NavNexus.API.Controllers;

/// <summary>
/// Controller for knowledge base queries and recommendations
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class KnowledgeController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<KnowledgeController> _logger;

    public KnowledgeController(IMediator mediator, ILogger<KnowledgeController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Query the knowledge base using semantic + graph search
    /// </summary>
    /// <param name="workspaceId">Workspace ID</param>
    /// <param name="query">User query</param>
    /// <param name="limit">Maximum number of results</param>
    /// <returns>Query result with answer, evidences, and related topics</returns>
    [HttpGet("{workspaceId}/query")]
    [SwaggerOperation(
        Summary = "Query knowledge base",
        Description = "Performs semantic search + graph traversal + LLM synthesis to answer user queries."
    )]
    [SwaggerResponse(200, "Query successful", typeof(ApiResponse<QueryKnowledgeResult>))]
    [SwaggerResponse(400, "Invalid query", typeof(ApiResponse))]
    [SwaggerResponse(404, "Workspace not found", typeof(ApiResponse))]
    public async Task<IActionResult> QueryKnowledge(
        [FromRoute] string workspaceId,
        [FromQuery] string query,
        [FromQuery] int limit = 10)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            return BadRequest(ApiResponse.ErrorResponse("Query cannot be empty", "INVALID_QUERY"));
        }

        // Sanitize user input for logging to prevent log forging
        var sanitizedWorkspaceId = workspaceId?.Replace("\n", "").Replace("\r", "") ?? "";
        var sanitizedQuery = query?.Replace("\n", "").Replace("\r", "") ?? "";
        _logger.LogInformation("Querying knowledge base for workspace {WorkspaceId}: {Query}", sanitizedWorkspaceId, sanitizedQuery);

        var queryCommand = new QueryKnowledgeQuery(workspaceId, query, limit);
        var result = await _mediator.Send(queryCommand);

        if (!result.IsSuccess)
        {
            return BadRequest(ApiResponse.ErrorResponse(result.Error ?? "Query failed", result.ErrorCode ?? "QUERY_FAILED"));
        }

        return Ok(ApiResponse<QueryKnowledgeResult>.SuccessResponse(result.Data!));
    }

    /// <summary>
    /// Get gap analysis and recommendations for a workspace
    /// </summary>
    /// <param name="workspaceId">Workspace ID</param>
    /// <returns>Gap analysis with recommendations</returns>
    [HttpGet("{workspaceId}/gaps")]
    [SwaggerOperation(
        Summary = "Get gap analysis",
        Description = "Analyzes knowledge graph to find gaps, orphan nodes, and weak connections."
    )]
    [SwaggerResponse(200, "Gap analysis retrieved", typeof(ApiResponse<GapAnalysisResult>))]
    [SwaggerResponse(404, "Workspace not found", typeof(ApiResponse))]
    public async Task<IActionResult> GetGapAnalysis([FromRoute] string workspaceId)
    {
        // Sanitize user input for logging to prevent log forging
        var sanitizedWorkspaceId = workspaceId?.Replace("\n", "").Replace("\r", "") ?? "";
        _logger.LogInformation("Getting gap analysis for workspace {WorkspaceId}", sanitizedWorkspaceId);

        // TODO: Implement gap analysis query
        var result = new GapAnalysisResult
        {
            OrphanNodes = new List<string>(),
            WeakConnections = new List<string>(),
            Recommendations = new List<string>
            {
                "Upload papers about: Actor-Critic + PPO connection",
                "Missing evidence for: Policy Gradient Theorem"
            }
        };

        return Ok(ApiResponse<GapAnalysisResult>.SuccessResponse(result));
    }
}

public class GapAnalysisResult
{
    public List<string> OrphanNodes { get; set; } = new();
    public List<string> WeakConnections { get; set; } = new();
    public List<string> Recommendations { get; set; } = new();
}
