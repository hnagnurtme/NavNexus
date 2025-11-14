using System.Net;
using FluentValidation;
using NavNexus.API.Constants;
using NavNexus.API.Contracts.Responses;
using NavNexus.Application.Exceptions;
using NavNexus.Domain.Exceptions;

namespace NavNexus.API.Middlewares;

public class GlobalExceptionHandler
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionHandler> _logger;

    public GlobalExceptionHandler(RequestDelegate next, ILogger<GlobalExceptionHandler> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An unhandled exception occurred");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        context.Response.ContentType = "application/json";

        var response = exception switch
        {
            ValidationException validationEx => new
            {
                StatusCode = (int)HttpStatusCode.BadRequest,
                Response = new ApiResponse
                {
                    Success = false,
                    Error = new ApiError
                    {
                        Message = "Validation failed",
                        Code = ErrorConstants.VALIDATION_ERROR,
                        ValidationErrors = validationEx.Errors
                            .GroupBy(e => e.PropertyName)
                            .ToDictionary(
                                g => g.Key,
                                g => g.Select(e => e.ErrorMessage).ToArray()
                            )
                    },
                    Timestamp = DateTime.UtcNow
                }
            },
            BusinessException businessEx => new
            {
                StatusCode = (int)HttpStatusCode.BadRequest,
                Response = ApiResponse.ErrorResponse(businessEx.Message, businessEx.ErrorCode)
            },
            DomainException domainEx => new
            {
                StatusCode = (int)HttpStatusCode.BadRequest,
                Response = ApiResponse.ErrorResponse(domainEx.Message, ErrorConstants.OPERATION_FAILED)
            },
            _ => new
            {
                StatusCode = (int)HttpStatusCode.InternalServerError,
                Response = ApiResponse.ErrorResponse(
                    "An internal server error occurred",
                    ErrorConstants.INTERNAL_SERVER_ERROR
                )
            }
        };

        context.Response.StatusCode = response.StatusCode;
        return context.Response.WriteAsJsonAsync(response.Response);
    }
}
