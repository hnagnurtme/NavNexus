using FluentValidation;

namespace NavNexus.Application.Workspace.Queries;

public class GetUserWorkspaceQueryValidator : AbstractValidator<GetUserWorkspaceQuery>
{
    public GetUserWorkspaceQueryValidator()
    {
        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("UserId is required");
    }
}