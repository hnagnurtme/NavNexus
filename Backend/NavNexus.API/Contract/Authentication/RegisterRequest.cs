using Swashbuckle.AspNetCore.Annotations;

namespace NavNexus.API.Contract.Authentication;



public class RegisterRequest
{
    [SwaggerSchema(Description = "User's email address")]
    public required string Email { get; set; }
    [SwaggerSchema(Description = "User's password")]
    public required string Password { get; set; }
    [SwaggerSchema(Description = "User's full name")]
    public required string FullName { get; set; }
    [SwaggerSchema(Description = "User's phone number")]
    public required string PhoneNumber { get; set; }
}