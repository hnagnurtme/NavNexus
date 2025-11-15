using FluentValidation;

namespace NavNexus.Application.KnowledgeTree.Commands;

public class CreateKnowledgeNodeCommandValidator : AbstractValidator<CreateKnowledgeNodeCommand>
{
    public CreateKnowledgeNodeCommandValidator()
    {
        RuleFor(x => x.WorkspaceId)
            .NotEmpty()
            .WithMessage("WorkspaceId is required");

        RuleFor(x => x.FilePaths)
            .NotEmpty()
            .WithMessage("At least one file path is required");
    }
}