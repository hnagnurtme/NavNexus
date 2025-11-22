namespace NavNexus.Application.Workspace.Commands;

using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;
using NavNexus.Application.KnowledgeTree.Commands;

public class CreateWorkspaceCommandHandler : IRequestHandler<CreateWorkspaceCommand, ErrorOr<GetWorkspaceDetailsResult>>
{
    private readonly IUserRepository _userRepository;
    private readonly ICurrentUserService _currentUserService;
    private readonly IMediator _mediator;
    private readonly ILogger<CreateWorkspaceCommandHandler> _logger;

    public CreateWorkspaceCommandHandler(
        IUserRepository userRepository,
        ICurrentUserService currentUserService,
        IMediator mediator,
        ILogger<CreateWorkspaceCommandHandler> logger)
    {
        _userRepository = userRepository;
        _currentUserService = currentUserService;
        _mediator = mediator;
        _logger = logger;
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

        // 4. Nếu có fileIds, delegate sang CreateKnowledgeNodeCommand để xử lý
        if (request.FileIds != null && request.FileIds.Count > 0)
        {
            try
            {
                _logger.LogInformation(
                    "Detected {Count} FileIds for workspace {WorkspaceId}. Delegating to CreateKnowledgeNodeCommand.",
                    request.FileIds.Count,
                    workspace.Id);

                var createKnowledgeNodeCommand = new CreateKnowledgeNodeCommand(
                    WorkspaceId: workspace.Id,
                    FilePaths: request.FileIds
                );

                var knowledgeNodeResult = await _mediator.Send(createKnowledgeNodeCommand, cancellationToken);

                if (knowledgeNodeResult.IsError)
                {
                    _logger.LogWarning(
                        "Failed to process FileIds for workspace {WorkspaceId}. Errors: {Errors}",
                        workspace.Id,
                        string.Join(", ", knowledgeNodeResult.Errors.Select(e => e.Description)));
                }
                else
                {
                    _logger.LogInformation(
                        "Successfully delegated FileIds processing to CreateKnowledgeNodeCommand for workspace {WorkspaceId}. Status: {Status}",
                        workspace.Id,
                        knowledgeNodeResult.Value.Status);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to delegate FileIds processing for workspace {WorkspaceId} with fileIds: {FileIds}",
                    workspace.Id,
                    string.Join(", ", request.FileIds));
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