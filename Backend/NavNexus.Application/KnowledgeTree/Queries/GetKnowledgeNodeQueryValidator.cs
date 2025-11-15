using FluentValidation;

namespace NavNexus.Application.KnowledgeTree.Queries;

public class GetKnowledgeNodeQueryValidator : AbstractValidator<GetKnowledgeNodeQuery>
{
    public GetKnowledgeNodeQueryValidator()
    {
        RuleFor(x => x.WorkspaceId)
            .NotEmpty()
            .WithMessage("WorkspaceId is required");
    }
}