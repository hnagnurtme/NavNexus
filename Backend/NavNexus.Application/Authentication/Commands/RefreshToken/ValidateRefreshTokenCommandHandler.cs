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
    private readonly ITokenRepository _tokenRepository;

    private readonly IUserRepository _userRepository;
    private readonly IMediator _mediator;
    private readonly IRefreshTokenGenerator _refreshTokenGenerator;
    private readonly ILogger<ValidateRefreshTokenCommandHandler> _logger;

    public ValidateRefreshTokenCommandHandler(
        IJwtService jwtService,
        IHashService hashService,
        IRefreshTokenGenerator refreshTokenGenerator,
        ITokenRepository tokenRepo,
        IMediator mediator,
        IUserRepository userRepository,
        ILogger<ValidateRefreshTokenCommandHandler> logger)
    {
        _jwtService = jwtService;
        _hashService = hashService;
        _refreshTokenGenerator = refreshTokenGenerator;
        _logger = logger;
        _tokenRepository = tokenRepo;
        _userRepository = userRepository;
        _mediator = mediator;
    }

    public async Task<ErrorOr<AuthenticationResult>> Handle(
    ValidateRefreshTokenCommand request,
    CancellationToken cancellationToken)
    {
        var token = await _tokenRepository.GetValidTokenAsync(
            request.UserId,
            request.UserAgent,
            request.DeviceFingerprint,
            cancellationToken);

        if (token == null || !_hashService.Verify(request.RefreshToken, token.TokenHash) || !token.IsActive)
        {
            return Error.Unauthorized(description: "Invalid or expired refresh token.");
        }
        if (!string.IsNullOrEmpty(token.IpAddress) &&
            !string.Equals(token.IpAddress, request.IpAddress, StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogWarning("IP mismatch for refresh token. Expected {Expected}, got {Actual}",
                token.IpAddress, request.IpAddress);
        }

        token.MarkAsUsed();
        token.Revoke();
        User user = await _userRepository.GetWithTokensAsync(token.UserId, cancellationToken);

        if (user == null)
        {
            return Error.Unauthorized(description: "User not found.");
        }

        user.UpdateLogin(DateTime.UtcNow);
        await _userRepository.UpdateAsync(user, cancellationToken);



        token.Replace(Guid.Parse(token.Id));

        await _tokenRepository.UpdateAsync(token, cancellationToken);


        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.NameIdentifier,user.Id.ToString()),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Name, user.FullName ?? string.Empty),
            new Claim(ClaimTypes.MobilePhone, user.PhoneNumber ?? string.Empty),
        };
        foreach (UserRole role in Enum.GetValues(typeof(UserRole)))
        {
            if (role != UserRole.NONE && user.Roles.HasFlag(role))
            {
                claims.Add(new Claim(ClaimTypes.Role, role.ToString()));
            }
        }
        var accessToken = _jwtService.GenerateToken(claims);

        var refreshCommand = new GenerateRefreshTokenCommand(
            token.UserId,
            request.IpAddress,
            request.UserAgent,
            request.DeviceFingerprint
        );
        var newRefreshResult = await _mediator.Send(refreshCommand, cancellationToken);

        var userDto = new UserDTO(
            user.Id,
            user.Email,
            user.FullName ?? string.Empty,
            user.PhoneNumber ?? string.Empty,
            user.EmailVerified,
            user.CreatedAt,
            user.UpdatedAt
        );

        var refreshDto = new RefreshTokenDTO(
            newRefreshResult.Value.Token,
            newRefreshResult.Value.ExpiresAt
        );

        return new AuthenticationResult(accessToken, refreshDto, userDto);
    }

}
