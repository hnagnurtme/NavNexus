namespace NavNexus.Application.Common.Exceptions;

using System.Net;

public class InvalidFormatException : ApplicationExceptions
{
    public InvalidFormatException(string message = "Invalid format")
        : base(message, ExceptionCode.INVALID_FORMAT, HttpStatusCode.BadRequest)
    {
    }
}