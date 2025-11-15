using System.Security.Claims;
namespace NavNexus.Application.Common.Interfaces.Security;

public interface IJwtService
{
    string GenerateToken(IEnumerable<Claim> claims, TimeSpan? lifetime = null);

    ClaimsPrincipal? ValidateToken(string token);
}