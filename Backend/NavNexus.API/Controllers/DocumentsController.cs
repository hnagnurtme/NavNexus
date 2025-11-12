using System.Security.Claims;
using AutoMapper;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NavNexus.API.Contracts.Requests;
using NavNexus.API.Contracts.Responses;
using NavNexus.Application.Features.Documents.Commands;
using NavNexus.Application.Features.Documents.Queries;

namespace NavNexus.API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class DocumentsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IMapper _mapper;
    private readonly ILogger<DocumentsController> _logger;

    public DocumentsController(IMediator mediator, IMapper mapper, ILogger<DocumentsController> logger)
    {
        _mediator = mediator;
        _mapper = mapper;
        _logger = logger;
    }

    [HttpPost("upload")]
    public async Task<IActionResult> UploadDocument([FromBody] UploadDocumentRequest request)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "";
        _logger.LogInformation("Uploading document for user: {UserId}", userId);

        var command = new UploadDocumentCommand(
            userId,
            request.FileName,
            request.ContentType,
            request.FileSize,
            request.StoragePath);

        var result = await _mediator.Send(command);

        if (!result.IsSuccess)
        {
            return BadRequest(ApiResponse.ErrorResponse(result.Error ?? "Upload failed", result.ErrorCode ?? "UPLOAD_FAILED"));
        }

        var response = _mapper.Map<DocumentResponse>(result.Data);
        return Ok(ApiResponse<DocumentResponse>.SuccessResponse(response));
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetDocument(string id)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "";
        _logger.LogInformation("Getting document {DocumentId} for user: {UserId}", id, userId);

        var query = new GetDocumentQuery(id, userId);
        var result = await _mediator.Send(query);

        if (!result.IsSuccess)
        {
            return NotFound(ApiResponse.ErrorResponse(result.Error ?? "Document not found", result.ErrorCode ?? "NOT_FOUND"));
        }

        var response = _mapper.Map<DocumentResponse>(result.Data);
        return Ok(ApiResponse<DocumentResponse>.SuccessResponse(response));
    }
}
