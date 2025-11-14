using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
namespace NavNexus.Application.Workspace.Queries;

public record GetWorkspaceDetailsQuery(
    string WorkspaceId,
    string UserId

)  : IRequest<ErrorOr<GetWorkspaceDetailsResult>>;