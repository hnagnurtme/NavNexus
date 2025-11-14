using MediatR;
using ErrorOr;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using Neo4j.Driver;

namespace NavNexus.Application.Authentication.Commands.RefreshToken
{
    public class GenerateRefreshTokenCommandHandler
        : IRequestHandler<GenerateRefreshTokenCommand, ErrorOr<RefreshTokenResult>>
    {
        private readonly IRefreshTokenGenerator _refreshTokenGenerator;
        private readonly ITokenRepository _tokenRepository;

        public GenerateRefreshTokenCommandHandler(
            IRefreshTokenGenerator refreshTokenGenerator , ITokenRepository tokenRepository)
        {
            _refreshTokenGenerator = refreshTokenGenerator;
            _tokenRepository = tokenRepository;
        }

        public async Task<ErrorOr<RefreshTokenResult>> Handle(
        GenerateRefreshTokenCommand request,
        CancellationToken cancellationToken)
        {
            var refreshToken = _refreshTokenGenerator.Generate(
            request.UserId,
            request.IpAddress,
            request.UserAgent,
            request.DeviceFingerprint,
            out var plainToken);

        await _tokenRepository.AddAsync(refreshToken, cancellationToken);
        
        return new RefreshTokenResult(plainToken, refreshToken.ExpiresAt);
        }
    }
}
