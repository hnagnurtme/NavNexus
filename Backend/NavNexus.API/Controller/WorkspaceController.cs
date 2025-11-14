using AutoMapper;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using ErrorOr;
using Swashbuckle.AspNetCore.Annotations;
using NavNexus.API.Common;
using NavNexus.API.Contract.Authentication;
using NavNexus.Application.Authentication;
using NavNexus.API.Contract.Workspace;
using NavNexus.Application.Workspace.Queries;
using NavNexus.Application.Workspace.Results;

namespace NavNexus.API.Controller;

[ApiController]
[Route("api/workspace")]
public class WorkspaceController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IMapper _mapper;

    public WorkspaceController(IMediator mediator, IMapper mapper)
    {
        _mediator = mediator;
        _mapper = mapper;
    }
    [HttpGet("{userId}")]
    [SwaggerOperation(Summary = "Get workspace details", Description = "Retrieve details of a specific workspace by its ID.")]
    [ProducesResponseType(typeof(ApiResponse<WorkspaceDetailResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetWorkspaceDetails(
        [FromRoute] string userId,
        [FromQuery] string workspaceId)
    {
        var query = new GetWorkspaceDetailsQuery(workspaceId, userId);
        var result = await _mediator.Send(query);
        var response = result.MapTo<GetWorkspaceDetailsResult, WorkspaceDetailResponse>(_mapper);
        return OK.HandleResult(response, "Workspace details retrieved successfully");
    }
}