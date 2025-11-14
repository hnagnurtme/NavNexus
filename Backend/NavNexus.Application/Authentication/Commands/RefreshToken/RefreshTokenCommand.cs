using ErrorOr;
using MediatR;

namespace NavNexus.Application.Authentication;

public record GenerateRefreshTokenCommand(Guid UserId, string IpAddress, string UserAgent, string? DeviceFingerprint) 
    : IRequest<ErrorOr<RefreshTokenResult>>;
