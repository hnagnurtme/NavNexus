using System.Security.Claims;
using Hangfire;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NavNexus.API.Contracts.Requests;
using NavNexus.API.Contracts.Responses;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Features.Documents.Commands;
using Swashbuckle.AspNetCore.Annotations;

namespace NavNexus.API.Controllers;

/// <summary>
/// Controller for file upload and processing operations
/// Implements async flow: Cache check → Enqueue job → Return 202
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class FilesController : ControllerBase
{
    private readonly IFirestoreService _firestoreService;
    private readonly IBackgroundJobClient _backgroundJobClient;
    private readonly ILogger<FilesController> _logger;

    public FilesController(
        IFirestoreService firestoreService,
        IBackgroundJobClient backgroundJobClient,
        ILogger<FilesController> logger)
    {
        _firestoreService = firestoreService;
        _backgroundJobClient = backgroundJobClient;
        _logger = logger;
    }

    /// <summary>
    /// Processes a file upload asynchronously
    /// Returns 202 Accepted immediately and processes in background
    /// </summary>
    /// <param name="request">File processing request</param>
    /// <returns>202 Accepted with job ID</returns>
    [HttpPost("process")]
    [SwaggerOperation(
        Summary = "Process file upload (async)",
        Description = "Enqueues file for background processing. Returns immediately with 202 Accepted."
    )]
    [SwaggerResponse(202, "File accepted for processing", typeof(ApiResponse<ProcessFileResponse>))]
    [SwaggerResponse(400, "Invalid request", typeof(ApiResponse))]
    [SwaggerResponse(409, "File already processed (cached)", typeof(ApiResponse<ProcessFileResponse>))]
    public async Task<IActionResult> ProcessFile([FromBody] ProcessFileRequest request)
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "anonymous";
        // Sanitize user input for logging to prevent log forging
        var sanitizedWorkspaceId = request.WorkspaceId?.Replace("\n", "").Replace("\r", "") ?? "";
        var sanitizedFileName = request.FileName?.Replace("\n", "").Replace("\r", "") ?? "";
        _logger.LogInformation("Processing file request for workspace {WorkspaceId}, file {FileName}", 
            sanitizedWorkspaceId, sanitizedFileName);

        // STEP 1: Cache check (Firestore)
        var existingFile = await _firestoreService.GetFileByHashAsync(request.WorkspaceId, request.FileHash);
        if (existingFile != null && existingFile.Status == Domain.Entities.ProcessingStatus.Completed)
        {
            _logger.LogInformation("File already processed (cache hit): {FileId}", existingFile.FileId);
            return Conflict(ApiResponse<ProcessFileResponse>.SuccessResponse(new ProcessFileResponse
            {
                FileId = existingFile.FileId,
                Status = "cached",
                Message = "File already processed (duplicate detected)"
            }));
        }

        // Generate unique file ID
        var fileId = Guid.NewGuid().ToString();

        // STEP 2: Enqueue background job (Hangfire)
        var command = new ProcessFileCommand(
            request.WorkspaceId,
            fileId,
            request.FileName,
            request.FileUrl,
            request.FileHash,
            request.FileSize,
            request.MimeType,
            userId
        );

        var jobId = _backgroundJobClient.Enqueue<IMediator>(mediator => 
            mediator.Send(command, CancellationToken.None));

        _logger.LogInformation("File {FileId} enqueued for processing with job ID {JobId}", fileId, jobId);

        // STEP 3: Return 202 Accepted
        return Accepted(ApiResponse<ProcessFileResponse>.SuccessResponse(new ProcessFileResponse
        {
            FileId = fileId,
            Status = "processing",
            Message = "File accepted for processing",
            JobId = jobId
        }));
    }

    /// <summary>
    /// Gets the status of a file processing job
    /// </summary>
    /// <param name="workspaceId">Workspace ID</param>
    /// <param name="fileId">File ID</param>
    /// <returns>File processing status</returns>
    [HttpGet("{workspaceId}/files/{fileId}/status")]
    [SwaggerOperation(
        Summary = "Get file processing status",
        Description = "Returns the current status of a file processing job."
    )]
    [SwaggerResponse(200, "Status retrieved successfully", typeof(ApiResponse<ProcessFileResponse>))]
    [SwaggerResponse(404, "File not found", typeof(ApiResponse))]
    public async Task<IActionResult> GetFileStatus(string workspaceId, string fileId)
    {
        var fileMetadata = await _firestoreService.GetFileByIdAsync(workspaceId, fileId);
        if (fileMetadata == null)
        {
            return NotFound(ApiResponse.ErrorResponse("File not found", "FILE_NOT_FOUND"));
        }

        return Ok(ApiResponse<ProcessFileResponse>.SuccessResponse(new ProcessFileResponse
        {
            FileId = fileMetadata.FileId,
            Status = fileMetadata.Status.ToString().ToLowerInvariant(),
            Message = fileMetadata.ErrorMessage ?? $"File is {fileMetadata.Status}"
        }));
    }
}
