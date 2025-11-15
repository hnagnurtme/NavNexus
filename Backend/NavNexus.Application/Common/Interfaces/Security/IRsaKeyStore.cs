using Microsoft.IdentityModel.Tokens;
namespace NavNexus.Application.Common.Interfaces.Security;

public interface IRsaKeyStore 
{
    string KeyId { get; } 
    RsaSecurityKey GetPrivateKey();
    RsaSecurityKey GetPublicKey();
}