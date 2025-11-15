namespace NavNexus.Application.Common.Exceptions;

using System.Net;

public class TicketNotOnSaleException : ApplicationExceptions
{
    public TicketNotOnSaleException(string message = "Ticket is not on sale")
        : base(message, ExceptionCode.TICKET_NOT_ON_SALE, HttpStatusCode.BadRequest)
    {
    }
}