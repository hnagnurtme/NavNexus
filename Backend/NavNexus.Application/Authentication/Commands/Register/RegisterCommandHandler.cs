using ErrorOr;
using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Exceptions;
using NavNexus.Application.Common.Interfaces.Events;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.Authentication.Commands.Register
{
    public class RegisterCommandHandler(
        IUserRepository userRepository,
        IHashService hashService,
        IDomainEventDispatcher domainEventDispatcher,
        ILogger<RegisterCommandHandler> logger
    )
        : IRequestHandler<RegisterCommand, ErrorOr<AuthenticationResult>>
    {
        private readonly IHashService _hashService = hashService;
        private readonly IDomainEventDispatcher _domainEventDispatcher = domainEventDispatcher;
        private readonly ILogger<RegisterCommandHandler> _logger = logger;

        public async Task<ErrorOr<AuthenticationResult>> Handle(RegisterCommand request, CancellationToken cancellationToken)
        {
            if (await userRepository.ExistsByEmailAsync(request.Email))
            {
                _logger.LogWarning("Email {Email} is already in use.", request.Email);
                throw new DuplicateEmailException("Email is already in use.");
            }

            var passwordHash = _hashService.Hash(request.Password);
            var user = new User(request.Email, passwordHash, request.FullName, request.PhoneNumber);

            await userRepository.AddAsync(user, cancellationToken);

            await _domainEventDispatcher.DispatchEventsAsync(user.DomainEvents);
            user.ClearDomainEvents();

            var userDto = new UserDTO(
                user.Id,
                user.Email,
                user.FullName ?? string.Empty,
                user.PhoneNumber ?? string.Empty,
                user.EmailVerified,
                user.CreatedAt,
                user.UpdatedAt
            );

            return new AuthenticationResult(null, null, userDto);
        }
    }
}
