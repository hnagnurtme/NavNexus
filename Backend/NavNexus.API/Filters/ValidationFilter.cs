using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using NavNexus.API.Constants;
using NavNexus.API.Contracts.Responses;

namespace NavNexus.API.Filters;

public class ValidationFilter : IActionFilter
{
    public void OnActionExecuting(ActionExecutingContext context)
    {
        if (!context.ModelState.IsValid)
        {
            var errors = context.ModelState
                .Where(x => x.Value?.Errors.Count > 0)
                .ToDictionary(
                    kvp => kvp.Key,
                    kvp => kvp.Value?.Errors.Select(e => e.ErrorMessage).ToArray() ?? Array.Empty<string>()
                );

            var response = new ApiResponse
            {
                Success = false,
                Error = new ApiError
                {
                    Message = "Validation failed",
                    Code = ErrorConstants.VALIDATION_ERROR,
                    ValidationErrors = errors
                },
                Timestamp = DateTime.UtcNow
            };

            context.Result = new BadRequestObjectResult(response);
        }
    }

    public void OnActionExecuted(ActionExecutedContext context)
    {
        // No operation needed after action execution
    }
}
