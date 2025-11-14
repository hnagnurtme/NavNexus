using MediatR;
using System.Security.Claims;
using ErrorOr;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Application.Common.Exceptions;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Authentication
{
    public class LoginQueryHandler : IRequestHandler<LoginQuery, ErrorOr<AuthenticationResult>>
    {
        private readonly IJwtService _jwtService;
        private readonly IHashService _hashService;

        private readonly IUserRepository _userRepository;
        private readonly IMediator _mediator;

        public LoginQueryHandler(
            IJwtService jwtService,
            IHashService hashService,
            IUserRepository userRepository,
            IMediator mediator)
        {
            _jwtService = jwtService;
            _hashService = hashService;
            _userRepository = userRepository;
            _mediator = mediator;
        }

        public async Task<ErrorOr<AuthenticationResult>> Handle(
            LoginQuery request, 
            CancellationToken cancellationToken)
        {
            var user = await _userRepository.GetByEmailAsync(request.Email, cancellationToken);
        if (user == null)
        {
            throw new UnAuthorizationException("Invalid credentials.");
        }
        // Check if email is verified
        if (!user.EmailVerified)
        {
            throw new EmailNotVerifyException("Email is not verified. Please verify your email before logging in.");
        }

        if (!VerifyPassword(request.Password, user.PasswordHash))
        {
            throw new UnAuthorizationException("Invalid credentials.");
        }
        user.UpdateLogin(DateTime.UtcNow);
        await _userRepository.UpdateAsync(user, cancellationToken);

        var claims = new List<Claim>
            {
                new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
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

        var refreshTokenCommand = new GenerateRefreshTokenCommand(
            Guid.Parse(user.Id),
            request.IpAddress,
            request.UserAgent,
            request.DeviceFingerprint
        );

        var refreshTokenResult = Guid.NewGuid();

        var userDto = new UserDTO(
            user.Id,
            user.Email,
            user.FullName ?? string.Empty,
            user.PhoneNumber ?? string.Empty,
            user.EmailVerified,
            user.CreatedAt,
            user.UpdatedAt
        );


        return new AuthenticationResult(accessToken, null, userDto);
        }

        private bool VerifyPassword(string password, string passwordHash)
        => _hashService.Verify(password, passwordHash);
    }
}
