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
    private readonly IKnowledgetreeRepository _knowledgetreeRepository;

    public CreateWorkspaceCommandHandler(
        IUserRepository userRepository, 
        ICurrentUserService currentUserService,
        IKnowledgetreeRepository knowledgetreeRepository)
    {
        _userRepository = userRepository;
        _currentUserService = currentUserService;
        _knowledgetreeRepository = knowledgetreeRepository;
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

        // 4. Nếu có fileIds, sao chép các nodes từ workspaces khác có evidence với source_id trùng
        if (request.FileIds != null && request.FileIds.Count > 0)
        {
            try
            {
                foreach (var fileId in request.FileIds)
                {
                    // Sao chép tất cả nodes từ workspaces khác có evidence với source_id này
                    await _knowledgetreeRepository.CopyNodesAsync(fileId, workspace.Id, cancellationToken);
                }
            }
            catch (Exception ex)
            {
                // Log lỗi nhưng vẫn tiếp tục tạo workspace
                // Workspace đã được tạo, chỉ việc copy nodes bị lỗi
                // Có thể log hoặc thêm warning vào response nếu cần
                // Hiện tại chúng ta vẫn trả về workspace đã tạo thành công
                Console.WriteLine($"Warning: Failed to copy nodes for fileIds: {ex.Message}");
            }
        }

        // 5. Tạo và trả về kết quả
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