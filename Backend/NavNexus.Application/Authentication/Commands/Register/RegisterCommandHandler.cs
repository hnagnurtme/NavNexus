using MediatR;
using ErrorOr;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Events;
using NavNexus.Domain.Entities;
using NavNexus.Application.Common.Exceptions;
using System.Threading;
using System.Threading.Tasks;
using NavNexus.Application.Common.Interfaces;
using Neo4j.Driver;

namespace NavNexus.Application.Authentication
{
    public class RegisterCommandHandler : IRequestHandler<RegisterCommand, ErrorOr<AuthenticationResult>>
    {
        private readonly IHashService _hashService;
        private readonly IDomainEventDispatcher _domainEventDispatcher;
        private readonly ILogger<RegisterCommandHandler> _logger;

        public RegisterCommandHandler(
            IHashService hashService,
            IDomainEventDispatcher domainEventDispatcher,
            ILogger<RegisterCommandHandler> logger)
        {
            _hashService = hashService;
            _domainEventDispatcher = domainEventDispatcher;
            _logger = logger;
        }

        public async Task<ErrorOr<AuthenticationResult>> Handle(RegisterCommand request, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
