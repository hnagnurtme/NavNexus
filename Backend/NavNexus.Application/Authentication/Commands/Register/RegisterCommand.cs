using ErrorOr;
using MediatR;

namespace NavNexus.Application.Authentication;

public record RegisterCommand (string Email, string Password, string FullName, string PhoneNumber) : IRequest<ErrorOr<AuthenticationResult>>;