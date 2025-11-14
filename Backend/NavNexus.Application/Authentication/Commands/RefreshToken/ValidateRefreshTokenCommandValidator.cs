using FluentValidation;
namespace NavNexus.Application.Authentication;

public class ValidateRefreshTokenCommandValidator : AbstractValidator<ValidateRefreshTokenCommand>
{
    public ValidateRefreshTokenCommandValidator()
    {
        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("UserId is required");
        RuleFor(x => x.RefreshToken)
            .NotEmpty()
            .WithMessage("RefreshToken is required");
        RuleFor(x => x.IpAddress)
            .NotEmpty()
            .WithMessage("IpAddress is required");
        RuleFor(x => x.UserAgent)
            .NotEmpty()
            .WithMessage("UserAgent is required");
        RuleFor(x => x.DeviceFingerprint)
            .NotEmpty()
            .WithMessage("DeviceFingerprint is required");
    }
}