namespace NavNexus.Application.Workspace.Commands;

using System.Text.RegularExpressions;
using FluentValidation;
public class CreateWorkspaceCommandValidator : AbstractValidator<CreateWorkspaceCommand>
{
    public CreateWorkspaceCommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .WithMessage("Workspace name is required.")
            .MaximumLength(100)
            .WithMessage("Workspace name must not exceed 100 characters.");

        RuleFor(x => x.Description)
            .MaximumLength(500)
            .WithMessage("Description must not exceed 500 characters.");
        RuleFor(x => x.FileIds)
            .Must(fileIds => fileIds == null || fileIds.All(id =>
                !string.IsNullOrWhiteSpace(id) &&
                Regex.IsMatch(id, @"^[a-zA-Z0-9_-]+$") // chỉ cho phép chữ, số, dấu gạch ngang và dấu gạch dưới
            ))
            .WithMessage("File IDs must be alphanumeric and may contain only '-' or '_'. No empty or whitespace strings allowed.");
    }
}