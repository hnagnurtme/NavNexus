
using Microsoft.IdentityModel.Tokens;
using NavNexus.Application.Common.Interfaces.Security;

namespace NavNexus.Infrastructure.Security;

public class JwksProvider : IJwksProvider
{
    private readonly IRsaKeyStore _rsaKeyStore;

    public JwksProvider(IRsaKeyStore rsaKeyStore)
    {
        _rsaKeyStore = rsaKeyStore;
    }

    public object GetJwks()
    {
        var _parameters = _rsaKeyStore.GetPublicKey().Rsa.ExportParameters(false);

        return new
        {
            keys = new object[]
            {
                new {
                    kty = "RSA",
                    use = "sig",
                    kid = _rsaKeyStore.KeyId,
                    e = Base64UrlEncoder.Encode(_parameters.Exponent),
                    n = Base64UrlEncoder.Encode(_parameters.Modulus)
                }

            }
        };
    }
    
}