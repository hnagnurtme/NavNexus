using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using NavNexus.API.Constants;
using NavNexus.API.Contracts.Responses;
using System.Security.Claims;

namespace NavNexus.API.Filters;

public class AuthorizationFilter : IAuthorizationFilter
{
    public void OnAuthorization(AuthorizationFilterContext context)
    {
        var user = context.HttpContext.User;

        if (user?.Identity?.IsAuthenticated != true)
        {
            var response = ApiResponse.ErrorResponse(
                "Authentication required",
                ErrorConstants.UNAUTHORIZED
            );

            context.Result = new UnauthorizedObjectResult(response);
            return;
        }

        // Additional authorization logic can be added here
        var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (string.IsNullOrEmpty(userId))
        {
            var response = ApiResponse.ErrorResponse(
                "Invalid user identity",
                ErrorConstants.INVALID_TOKEN
            );

            context.Result = new UnauthorizedObjectResult(response);
        }
    }
}
