using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
namespace NavNexus.Application.Workspace.Queries;
public record GetUserWorkspaceQuery(
    string UserId
)  : IRequest<ErrorOr<GetUserWorkspaceResult>>;