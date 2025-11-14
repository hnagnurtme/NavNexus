using FluentValidation;

namespace NavNexus.Application.Workspace.Queries;

public class GetWorkspaceDetailsQueryValidators : AbstractValidator<GetWorkspaceDetailsQuery>
{
    public GetWorkspaceDetailsQueryValidators()
    {
        RuleFor(x => x.WorkspaceId)
            .NotEmpty()
            .WithMessage("WorkspaceId is required");
        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("UserId is required");
    }
}