using MediatR;
using NavNexus.Application.Common.Models;

namespace NavNexus.Application.Features.Documents.Commands;

/// <summary>
/// Command to process a file upload and extract knowledge
/// This triggers the async background processing flow
/// </summary>
public record ProcessFileCommand(
    string WorkspaceId,
    string FileId,
    string FileName,
    string FileUrl,
    string FileHash,
    long FileSize,
    string MimeType,
    string UserId) : IRequest<Result<string>>;
