using MediatR;
using ErrorOr;

namespace NavNexus.Application.Authentication;

public record VerifyEmailQuery(string Email, string Token) : IRequest<ErrorOr<AuthenticationResult>>;