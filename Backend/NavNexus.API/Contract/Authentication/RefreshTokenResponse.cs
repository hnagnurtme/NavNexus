namespace NavNexus.API.Contract.Authentication;


public class RefreshTokenResponse
{
    public required string Token { get; set; }
    public required DateTime ExpiresAt { get; set; }
}