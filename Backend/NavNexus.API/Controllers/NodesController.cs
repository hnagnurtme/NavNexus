using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NavNexus.API.Contracts.Requests;
using NavNexus.API.Contracts.Responses;
using NavNexus.Domain.Entities;

namespace NavNexus.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class NodesController : ControllerBase
{
    private readonly ILogger<NodesController> _logger;

    public NodesController(ILogger<NodesController> logger)
    {
        _logger = logger;
    }

    [HttpGet]
    public IActionResult GetNodes()
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        _logger.LogInformation("Getting nodes for user: {UserId}", userId);

        // Mock response for demonstration
        var nodes = new List<NodeResponse>
        {
            new()
            {
                Id = Guid.NewGuid().ToString(),
                Title = "Sample Node",
                Content = "This is a sample node",
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                Tags = new List<string> { "sample", "test" }
            }
        };

        return Ok(ApiResponse<List<NodeResponse>>.SuccessResponse(nodes));
    }

    [HttpGet("{id}")]
    public IActionResult GetNode(string id)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        _logger.LogInformation("Getting node {NodeId} for user: {UserId}", id, userId);

        // Mock response for demonstration
        var node = new NodeResponse
        {
            Id = id,
            Title = "Sample Node",
            Content = "This is a sample node",
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow,
            Tags = new List<string> { "sample", "test" }
        };

        return Ok(ApiResponse<NodeResponse>.SuccessResponse(node));
    }

    [HttpPost]
    public IActionResult CreateNode([FromBody] CreateNodeRequest request)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        _logger.LogInformation("Creating node for user: {UserId}", userId);

        // Mock response for demonstration
        var node = new NodeResponse
        {
            Id = Guid.NewGuid().ToString(),
            Title = request.Title,
            Content = request.Content,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow,
            Tags = request.Tags,
            ParentNodeId = request.ParentNodeId
        };

        return CreatedAtAction(nameof(GetNode), new { id = node.Id }, 
            ApiResponse<NodeResponse>.SuccessResponse(node));
    }
}
