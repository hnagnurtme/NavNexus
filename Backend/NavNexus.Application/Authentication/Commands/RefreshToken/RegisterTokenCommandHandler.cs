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

        public GenerateRefreshTokenCommandHandler(
            IRefreshTokenGenerator refreshTokenGenerator)
        {
            _refreshTokenGenerator = refreshTokenGenerator;
        }

        public async Task<ErrorOr<RefreshTokenResult>> Handle(
        GenerateRefreshTokenCommand request,
        CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
