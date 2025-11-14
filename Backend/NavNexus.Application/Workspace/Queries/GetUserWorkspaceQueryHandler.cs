namespace NavNexus.Application.Workspace.Queries;

using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Exceptions;

public class GetUserWorkspaceQueryHandler : IRequestHandler<GetUserWorkspaceQuery, ErrorOr<GetUserWorkspaceResult>>
{
    private readonly IUserRepository _userRepository;

    public GetUserWorkspaceQueryHandler(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<ErrorOr<GetUserWorkspaceResult>> Handle(GetUserWorkspaceQuery request, CancellationToken cancellationToken)
    {
        if (!Guid.TryParse(request.UserId, out var userGuid))
            return Error.Validation("User.Id", "Invalid user ID format.");

        var user = await _userRepository.GetWithTokensAsync(userGuid, cancellationToken);
        if (user == null)
            return Error.NotFound("User.NotFound", $"User with ID {request.UserId} not found.");

        var workspaceResults = user.Workspaces.Select(workspace => new GetWorkspaceDetailsResult(
            workspace.Id,
            workspace.Name,
            workspace.Description ?? string.Empty,
            workspace.OwnerId,
            user.FullName ?? string.Empty,
            workspace.Files.Select(f => f.Id).ToList(),
            workspace.CreatedAt,
            workspace.UpdatedAt
        )).ToList();

        var result = new GetUserWorkspaceResult(
            workspaceResults.Count,
            workspaceResults
        );

        return result;
    }
}
