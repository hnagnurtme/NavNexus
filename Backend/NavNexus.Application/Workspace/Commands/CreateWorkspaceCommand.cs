namespace NavNexus.Application.Workspace.Commands;

using MediatR;
using ErrorOr;
using NavNexus.Application.Workspace.Results;

public record CreateWorkspaceCommand(
    string Name,
    string? Description,
    List<string>? FileIds
) : IRequest<ErrorOr<GetWorkspaceDetailsResult>>;