namespace NavNexus.Application.Common.Exceptions;

using System.Net;

public class InsufficientInventoryException : ApplicationExceptions
{
    public InsufficientInventoryException(string message = "Insufficient inventory for the requested ticket.")
            : base(message, ExceptionCode.INSUFFICIENT_INVENTORY, HttpStatusCode.BadRequest)
    {
    }
}