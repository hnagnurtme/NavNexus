using System.Security.Claims;
using FirebaseAdmin.Auth;
using NavNexus.API.Constants;

namespace NavNexus.API.Middlewares;

public class FirebaseAuthMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<FirebaseAuthMiddleware> _logger;

    public FirebaseAuthMiddleware(RequestDelegate next, ILogger<FirebaseAuthMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var authHeader = context.Request.Headers["Authorization"].FirstOrDefault();

        if (authHeader != null && authHeader.StartsWith("Bearer "))
        {
            var token = authHeader.Substring("Bearer ".Length).Trim();

            try
            {
                var decodedToken = await FirebaseAuth.DefaultInstance.VerifyIdTokenAsync(token);
                
                // Set user claims
                var claims = new List<Claim>
                {
                    new Claim(ClaimTypes.NameIdentifier, decodedToken.Uid),
                    new Claim(ClaimTypes.Email, decodedToken.Claims.ContainsKey("email") 
                        ? decodedToken.Claims["email"].ToString() ?? "" 
                        : "")
                };

                var identity = new ClaimsIdentity(claims, "Firebase");
                context.User = new ClaimsPrincipal(identity);

                _logger.LogInformation("User authenticated: {UserId}", decodedToken.Uid);
            }
            catch (FirebaseAuthException ex)
            {
                _logger.LogWarning("Firebase token verification failed: {Message}", ex.Message);
                context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsJsonAsync(new
                {
                    Success = false,
                    Error = new
                    {
                        Message = "Invalid or expired token",
                        Code = ErrorConstants.INVALID_TOKEN
                    },
                    Timestamp = DateTime.UtcNow
                });
                return;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error verifying Firebase token");
                context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsJsonAsync(new
                {
                    Success = false,
                    Error = new
                    {
                        Message = "Authentication failed",
                        Code = ErrorConstants.UNAUTHORIZED
                    },
                    Timestamp = DateTime.UtcNow
                });
                return;
            }
        }

        await _next(context);
    }
}
