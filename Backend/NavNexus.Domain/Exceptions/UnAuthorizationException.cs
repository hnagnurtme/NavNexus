namespace NavNexus.Domain.Exceptions;
using System.Net;
public class UnAuthorizationException : DomainException
{
    public UnAuthorizationException(string message = "Invalid credentials")
        : base(message, ExceptionCode.UN_AUTHORIZED, HttpStatusCode.Unauthorized)
    {
    }
}