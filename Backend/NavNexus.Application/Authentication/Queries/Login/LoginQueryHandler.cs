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
        private readonly IMediator _mediator;

        public LoginQueryHandler(
            IJwtService jwtService,
            IHashService hashService,
            IMediator mediator)
        {
            _jwtService = jwtService;
            _hashService = hashService;
            _mediator = mediator;
        }

        public async Task<ErrorOr<AuthenticationResult>> Handle(
            LoginQuery request, 
            CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
