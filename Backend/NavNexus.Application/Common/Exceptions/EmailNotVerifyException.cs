namespace NavNexus.Application.Common.Exceptions;

using System.Net;
public class EmailNotVerifyException : ApplicationExceptions
{
    public EmailNotVerifyException(string message = "Email not verified")
        : base(message, ExceptionCode.EMAIL_NOT_VERIFIED, HttpStatusCode.Unauthorized)
    {
    }
}