namespace NavNexus.Application.Workspace.Commands;

using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces;

public class CreateWorkspaceCommandHandler : IRequestHandler<CreateWorkspaceCommand, ErrorOr<GetWorkspaceDetailsResult>>
{
    private readonly IUserRepository _userRepository;

    private readonly ICurrentUserService _currentUserService;

    public CreateWorkspaceCommandHandler(IUserRepository userRepository, ICurrentUserService currentUserService)
    {
        _userRepository = userRepository;
        _currentUserService = currentUserService;
    }
    public async Task<ErrorOr<GetWorkspaceDetailsResult>> Handle(CreateWorkspaceCommand request, CancellationToken cancellationToken)
    { 
        // 1. Lấy user hiện tại
        var email = _currentUserService.Email;
        if (email == null)
        {
            return Error.Failure("Authentication.Required", "User must be authenticated to create a workspace.");
        }
        var user = await _userRepository.GetByEmailAsync(email, cancellationToken);

        if (user == null)
        {
            return Error.NotFound("User.NotFound", $"User with email {email} not found.");
        }
        // 2. Tạo workspace mới
        var workspace = new Domain.Entities.Workspace(
            request.Name,
            user.Id,
            request.Description ?? string.Empty,
            request.FileIds
        );

        // 3. Thêm workspace vào user
        user.Workspaces.Add(workspace);
        await _userRepository.UpdateAsync(user, cancellationToken);
        // 4. Tạo và trả về kết quả
        var result = new GetWorkspaceDetailsResult(
            workspace.Id,
            workspace.Name,
            workspace.Description ?? string.Empty,
            workspace.OwnerId,
            user.FullName ?? string.Empty,
            workspace.FileIds,
            workspace.CreatedAt,
            workspace.UpdatedAt
        );

        return result;
    }
}