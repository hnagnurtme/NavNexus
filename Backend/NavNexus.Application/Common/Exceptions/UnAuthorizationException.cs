namespace NavNexus.Application.Common.Exceptions;

using System.Net;

public class UnAuthorizationException : ApplicationExceptions
{
    public UnAuthorizationException(string message = "Invalid credentials")
        : base(message, ExceptionCode.UN_AUTHORIZED, HttpStatusCode.Unauthorized)
    {
    }
}