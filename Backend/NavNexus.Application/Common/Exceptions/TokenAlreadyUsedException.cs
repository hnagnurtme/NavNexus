namespace NavNexus.Application.Common.Exceptions;

using System.Net;
public class TokenAlreadyUsedException : ApplicationExceptions
{

    public TokenAlreadyUsedException(string message = "Invalid credentials")
        : base(message, ExceptionCode.TOKEN_ALREADY_USED, HttpStatusCode.Unauthorized)
    {
    }
}