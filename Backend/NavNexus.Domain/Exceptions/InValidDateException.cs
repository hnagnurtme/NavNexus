namespace NavNexus.Domain.Exceptions;
using System.Net;


public class InValidDateException : DomainException
{

    public InValidDateException(string message = "Invalid date provided")
        : base(message, ExceptionCode.INVALID_DATE, HttpStatusCode.BadRequest)
    {
    }
}