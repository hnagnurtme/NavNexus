using MediatR;
using ErrorOr;
using System.Security.Claims;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using Neo4j.Driver;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Authentication.Commands.RefreshToken;

public class ValidateRefreshTokenCommandHandler
    : IRequestHandler<ValidateRefreshTokenCommand, ErrorOr<AuthenticationResult>>
{
    private readonly IJwtService _jwtService;
    private readonly IHashService _hashService;
    private readonly IRefreshTokenGenerator _refreshTokenGenerator;
    private readonly ILogger<ValidateRefreshTokenCommandHandler> _logger;

    public ValidateRefreshTokenCommandHandler(
        IJwtService jwtService,
        IHashService hashService,
        IRefreshTokenGenerator refreshTokenGenerator,
        ILogger<ValidateRefreshTokenCommandHandler> logger)
    {
        _jwtService = jwtService;
        _hashService = hashService;
        _refreshTokenGenerator = refreshTokenGenerator;
        _logger = logger;
    }

    public async Task<ErrorOr<AuthenticationResult>> Handle(
    ValidateRefreshTokenCommand request,
    CancellationToken cancellationToken)
{
        throw new NotImplementedException();
}

}
