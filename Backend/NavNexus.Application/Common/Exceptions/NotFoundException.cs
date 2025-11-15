namespace NavNexus.Application.Common.Exceptions;

using System.Net;
public class NotFoundException : ApplicationExceptions
{
    public NotFoundException(string message = "Resource not found")
        : base(message, ExceptionCode.NOT_FOUND, HttpStatusCode.BadRequest)
    {
    }
}