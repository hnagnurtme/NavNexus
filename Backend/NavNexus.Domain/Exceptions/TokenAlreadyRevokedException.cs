namespace NavNexus.Domain.Exceptions;
using System.Net;

public class TokenAlreadyRevokedException : DomainException
{

    public TokenAlreadyRevokedException(string message = "Invalid credentials")
        : base(message, ExceptionCode.TOKEN_ALREADY_REVOKED, HttpStatusCode.Unauthorized)
    {
    }
}