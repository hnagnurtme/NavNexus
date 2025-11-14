namespace NavNexus.Application.Authentication;

public record AuthenticationResult(string? AccessToken , RefreshTokenDTO? RefreshToken ,UserDTO User);

public record UserDTO
(
    String Id,
    string Email,
    string FullName,
    string PhoneNumber,
    bool EmailVerified,
    DateTime CreatedAt ,
    DateTime UpdatedAt
);

public record RefreshTokenDTO
(
    string RefreshToken,
    DateTime RefreshTokenExpiresAt
);
