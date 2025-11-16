using FluentValidation;

namespace NavNexus.Application.KnowledgeTree.Queries;

public class GetKnowledgeNodeByIdQueryValidator : AbstractValidator<GetKnowledgeNodeByIdQuery>
{
    public GetKnowledgeNodeByIdQueryValidator()
    {
        RuleFor(x => x.NodeId)
            .NotEmpty()
            .WithMessage("WorkspaceId is required");
    }
}