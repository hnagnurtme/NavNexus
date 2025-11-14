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
using Microsoft.AspNetCore.Authorization;
using NavNexus.Application.Workspace.Commands;
using System.Security.Claims;

namespace NavNexus.API.Controller;

[ApiController]
[Route("api/workspace")]
[Authorize]
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


    [HttpPost]
    [SwaggerOperation(Summary = "Create a new workspace", Description = "Create a new workspace with the provided details.")]
    [ProducesResponseType(typeof(ApiResponse<WorkspaceDetailResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> CreateWorkspace([FromBody] CreateWorkspaceRequest request)
    {
        var command = _mapper.Map<CreateWorkspaceCommand>(request);
        var result = await _mediator.Send(command);
        var response = result.MapTo<GetWorkspaceDetailsResult, WorkspaceDetailResponse>(_mapper);
        return CREATE.HandleResult(response, "Workspace created successfully");
    }

    [HttpGet("")]
    [SwaggerOperation(Summary = "Get workspace details by user ID", Description = "Retrieve details of a specific workspace by its ID.")]
    [ProducesResponseType(typeof(ApiResponse<WorkspaceDetailResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetWorkspaceByUserId()
    {   
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier); 
        if (string.IsNullOrEmpty(userIdString))
        {
            return Unauthorized("Invalid user ID");
        }
        var query = new GetUserWorkspaceQuery(userIdString);
        var result = await _mediator.Send(query);
        var response = result.MapTo<GetUserWorkspaceResult,UserWorkspaceResponse>(_mapper);
        return OK.HandleResult(response, "Workspace details retrieved successfully");
    }
}