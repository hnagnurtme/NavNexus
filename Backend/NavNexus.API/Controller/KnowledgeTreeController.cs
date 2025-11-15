using AutoMapper;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using ErrorOr;
using Swashbuckle.AspNetCore.Annotations;
using NavNexus.API.Common;
using NavNexus.API.Contract.Authentication;
using NavNexus.Application.Authentication;
using NavNexus.API.Contract.KnowledgeTree;
using Microsoft.AspNetCore.Authorization;
using NavNexus.Application.KnowledgeTree.Queries;
using NavNexus.Application.KnowledgeTree.Results;
using NavNexus.Application.KnowledgeTree.Commands;

namespace NavNexus.API.Controller;

[ApiController]
[Authorize]
[Route("api/knowledge-tree")]
public class KnowledgeNodeController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IMapper _mapper;

    public KnowledgeNodeController(IMediator mediator, IMapper mapper)
    {
        _mediator = mediator;
        _mapper = mapper;
    }

    [HttpGet("{workspaceId}")]
    [SwaggerOperation(Summary = "Get Knowledge Node", Description = "Retrieve a knowledge node by its ID within a specified workspace.")]
    [ProducesResponseType(typeof(ApiResponse<GetKnowledgeNodeResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetKnowledgeNode([FromQuery] string nodeId, [FromRoute] string workspaceId)
    {
        var query = new GetKnowledgeNodeQuery(workspaceId, nodeId);
        var result = await _mediator.Send(query);
        var response = result.MapTo<GetKnowledgeNodeResult, GetKnowledgeNodeResponse>(_mapper);
        return OK.HandleResult(response, "Knowledge node retrieved successfully");
    }



    [HttpPost("")]
    [SwaggerOperation(Summary = "Create Knowledge Tree", Description = "Create a knowledge tree for a specified workspace using provided file paths.")]
    [ProducesResponseType(typeof(ApiResponse<RabbitMqSendingResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> CreateKnowledgeTree([FromBody] CreatedKnowledgetreeRequest request)
    {
        var command = _mapper.Map<CreatedKnowledgetreeRequest, CreateKnowledgeNodeCommand>(request);
        var result = await _mediator.Send(command);
        var response = result.MapTo<RabbitMqSendingResult, RabbitMqSendingResponse>(_mapper);
        return OK.HandleResult(response, "Knowledge tree creation initiated successfully");
    }
}