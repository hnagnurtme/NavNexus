using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces.Security;

public interface IRefreshTokenGenerator
{
    RefreshToken Generate(
        Guid userId,
        string? ipAddress,
        string? userAgent,
        string? deviceFingerprint
    , out string plainToken);
}