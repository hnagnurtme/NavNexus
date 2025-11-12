using MediatR;
using NavNexus.Application.Common.Models;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Features.Documents.Queries;

public record GetDocumentQuery(string DocumentId, string UserId) : IRequest<Result<Document>>;

public class GetDocumentQueryHandler : IRequestHandler<GetDocumentQuery, Result<Document>>
{
    public Task<Result<Document>> Handle(GetDocumentQuery request, CancellationToken cancellationToken)
    {
        // This is a placeholder implementation
        return Task.FromResult(Result<Document>.Failure("Document not found", "NOT_FOUND"));
    }
}
