namespace NavNexus.Application.Common.Exceptions;

using System.Net;

public class DuplicateEmailException : ApplicationExceptions
{
    public DuplicateEmailException(string message = "Email already in use")
        : base(message, ExceptionCode.DUPLICATE_EMAIL, HttpStatusCode.Conflict)
    {
    }
}