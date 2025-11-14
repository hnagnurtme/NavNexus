namespace NavNexus.Application.Common.Exceptions;

using System.Net;
public class TokenAlreadyRevokedException : ApplicationExceptions
{

    public TokenAlreadyRevokedException(string message = "Invalid credentials")
        : base(message, ExceptionCode.TOKEN_ALREADY_REVOKED, HttpStatusCode.Unauthorized)
    {
    }
}