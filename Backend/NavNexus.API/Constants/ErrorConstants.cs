namespace NavNexus.API.Constants;

public static class ErrorConstants
{
    // Authentication errors
    public const string UNAUTHORIZED = "UNAUTHORIZED";
    public const string INVALID_TOKEN = "INVALID_TOKEN";
    public const string TOKEN_EXPIRED = "TOKEN_EXPIRED";
    public const string MISSING_AUTH_HEADER = "MISSING_AUTH_HEADER";
    
    // Validation errors
    public const string VALIDATION_ERROR = "VALIDATION_ERROR";
    public const string INVALID_INPUT = "INVALID_INPUT";
    
    // Business errors
    public const string NOT_FOUND = "NOT_FOUND";
    public const string ALREADY_EXISTS = "ALREADY_EXISTS";
    public const string OPERATION_FAILED = "OPERATION_FAILED";
    
    // Server errors
    public const string INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR";
    public const string SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE";
}
