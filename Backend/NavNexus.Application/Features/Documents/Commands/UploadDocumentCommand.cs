using MediatR;
using NavNexus.Application.Common.Models;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Features.Documents.Commands;

public record UploadDocumentCommand(
    string UserId,
    string FileName,
    string ContentType,
    long FileSize,
    string StoragePath) : IRequest<Result<Document>>;

public class UploadDocumentCommandHandler : IRequestHandler<UploadDocumentCommand, Result<Document>>
{
    public Task<Result<Document>> Handle(UploadDocumentCommand request, CancellationToken cancellationToken)
    {
        // This is a placeholder implementation
        var document = new Document
        {
            Id = Guid.NewGuid().ToString(),
            UserId = request.UserId,
            FileName = request.FileName,
            ContentType = request.ContentType,
            FileSize = request.FileSize,
            StoragePath = request.StoragePath,
            UploadedAt = DateTime.UtcNow,
            Status = DocumentStatus.Pending
        };

        return Task.FromResult(Result<Document>.Success(document));
    }
}
