namespace NavNexus.Application.Common.Exceptions;

using System.Net;
public class InvalidPermissionException : ApplicationExceptions
{
    public InvalidPermissionException(string message = "You do not have permission to perform this action.")
        : base(message, ExceptionCode.INVALID_PERMISSION, HttpStatusCode.Forbidden)
    {
    }
}