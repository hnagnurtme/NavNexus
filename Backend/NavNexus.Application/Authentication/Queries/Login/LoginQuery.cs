using MediatR;
using ErrorOr;

namespace NavNexus.Application.Authentication;

public record LoginQuery(
    string Email,
    string Password,
    string IpAddress,
    string UserAgent,
    string DeviceFingerprint
) : IRequest<ErrorOr<AuthenticationResult>>;
