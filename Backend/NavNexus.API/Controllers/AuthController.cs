using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Microsoft.IdentityModel.Tokens;
using NavNexus.API.Contracts.Responses;

namespace NavNexus.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<AuthController> _logger;

    public AuthController(IConfiguration configuration, ILogger<AuthController> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    [HttpPost("token")]
    public IActionResult GenerateToken([FromBody] TokenRequest request)
    {
        // This is a simplified demo endpoint for JWT generation
        // In production, validate Firebase token or credentials first
        
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.UTF8.GetBytes(_configuration["Jwt:Key"] ?? "your-super-secret-key-that-is-at-least-32-characters-long");
        
        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(new[]
            {
                new Claim(ClaimTypes.NameIdentifier, request.UserId),
                new Claim(ClaimTypes.Email, request.Email ?? "")
            }),
            Expires = DateTime.UtcNow.AddHours(24),
            Issuer = _configuration["Jwt:Issuer"],
            Audience = _configuration["Jwt:Audience"],
            SigningCredentials = new SigningCredentials(
                new SymmetricSecurityKey(key),
                SecurityAlgorithms.HmacSha256Signature)
        };

        var token = tokenHandler.CreateToken(tokenDescriptor);
        var tokenString = tokenHandler.WriteToken(token);

        _logger.LogInformation("Token generated for user: {UserId}", request.UserId);

        return Ok(ApiResponse<TokenResponse>.SuccessResponse(new TokenResponse
        {
            Token = tokenString,
            ExpiresAt = tokenDescriptor.Expires.Value
        }));
    }

    [HttpGet("verify")]
    public IActionResult VerifyToken()
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        var email = User.FindFirst(ClaimTypes.Email)?.Value;

        if (string.IsNullOrEmpty(userId))
        {
            return Unauthorized(ApiResponse.ErrorResponse("Not authenticated", "UNAUTHORIZED"));
        }

        return Ok(ApiResponse<UserInfo>.SuccessResponse(new UserInfo
        {
            UserId = userId,
            Email = email ?? "",
            IsAuthenticated = true
        }));
    }
}

public class TokenRequest
{
    public string UserId { get; set; } = string.Empty;
    public string? Email { get; set; }
}

public class TokenResponse
{
    public string Token { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
}

public class UserInfo
{
    public string UserId { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public bool IsAuthenticated { get; set; }
}
