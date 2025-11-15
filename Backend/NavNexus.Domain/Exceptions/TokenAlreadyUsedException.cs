namespace NavNexus.Domain.Exceptions;
using System.Net;
public class TokenAlreadyUsedException : DomainException
{

    public TokenAlreadyUsedException(string message = "Invalid credentials")
        : base(message, ExceptionCode.TOKEN_ALREADY_USED, HttpStatusCode.Unauthorized)
    {
    }
}