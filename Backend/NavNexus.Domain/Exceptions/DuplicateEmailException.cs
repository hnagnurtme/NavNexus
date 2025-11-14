namespace NavNexus.Domain.Exceptions;
using System.Net;


public class DuplicateEmailException : DomainException
{
    public DuplicateEmailException(string message = "Email already in use")
        : base(message, ExceptionCode.DUPLICATE_EMAIL, HttpStatusCode.Conflict)
    {
    }
}