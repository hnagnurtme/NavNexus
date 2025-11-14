namespace NavNexus.Domain.Exceptions;
using System.Net;

public class InValidOperationException : DomainException
{

    public InValidOperationException(string message = "Invalid operation")
        : base(message, ExceptionCode.INVALID_OPERATION, HttpStatusCode.BadRequest)
    {
    }
}