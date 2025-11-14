using MediatR;
using ErrorOr;
using Microsoft.Extensions.Logging;
using System.Security.Claims;
using Neo4j.Driver;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Application.Authentication;
using NavNexus.Application.Common.Exceptions;

namespace NavNexus.Application.Authentication
{
    public class VerifyEmailQueryHandler : IRequestHandler<VerifyEmailQuery, ErrorOr<AuthenticationResult>>
    {
        private readonly ILogger<VerifyEmailQueryHandler> _logger;
        private readonly IJwtService _jwtService;

        public VerifyEmailQueryHandler(

            ILogger<VerifyEmailQueryHandler> logger,
            IJwtService jwtService)
        {
            _logger = logger;
            _jwtService = jwtService;
        }

        public async Task<ErrorOr<AuthenticationResult>> Handle(
            VerifyEmailQuery request, 
            CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
