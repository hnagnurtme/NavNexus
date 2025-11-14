using MediatR;
using ErrorOr;

namespace NavNexus.Application.Authentication;

public record ValidateRefreshTokenCommand( Guid UserId , string RefreshToken , string IpAddress , string UserAgent , string DeviceFingerprint)
    : IRequest<ErrorOr<AuthenticationResult>>;
