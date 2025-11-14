namespace NavNexus.Application.Workspace.Queries;

using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Exceptions;

public class GetWorkspaceDetailsQueryHandler : IRequestHandler<GetWorkspaceDetailsQuery, ErrorOr<GetWorkspaceDetailsResult>>
{
    private readonly IUserRepository _userRepository;

    public GetWorkspaceDetailsQueryHandler(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<ErrorOr<GetWorkspaceDetailsResult>> Handle(GetWorkspaceDetailsQuery request, CancellationToken cancellationToken)
    {
        // 1. Lấy user
        var user = await _userRepository.GetWithTokensAsync(Guid.Parse(request.UserId), cancellationToken);
        if (user == null)
            return Error.NotFound("User.NotFound", $"User with ID {request.UserId} not found.");

        // 2. Tìm workspace trong user
        var workspace = user.Workspaces.FirstOrDefault(w => w.Id.ToString() == request.WorkspaceId);
        if (workspace == null)
            return Error.NotFound("Workspace.NotFound", $"Workspace with ID {request.WorkspaceId} not found for this user.");

        // 3. Tạo và trả về kết quả
        var result = new GetWorkspaceDetailsResult(
            workspace.Id,
            workspace.Name,
            workspace.Description ?? string.Empty,
            workspace.OwnerId,
            user.FullName ?? string.Empty,
            workspace.Files.Select(f => f.Id).ToList(),
            workspace.CreatedAt,
            workspace.UpdatedAt
        );

        return result;
    }
}