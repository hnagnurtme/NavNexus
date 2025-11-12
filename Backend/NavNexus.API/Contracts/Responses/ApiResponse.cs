namespace NavNexus.API.Contracts.Responses;

public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public ApiError? Error { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    public static ApiResponse<T> SuccessResponse(T data) => new()
    {
        Success = true,
        Data = data
    };

    public static ApiResponse<T> ErrorResponse(string message, string code) => new()
    {
        Success = false,
        Error = new ApiError
        {
            Message = message,
            Code = code
        }
    };
}

public class ApiResponse
{
    public bool Success { get; set; }
    public ApiError? Error { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    public static ApiResponse SuccessResponse() => new()
    {
        Success = true
    };

    public static ApiResponse ErrorResponse(string message, string code) => new()
    {
        Success = false,
        Error = new ApiError
        {
            Message = message,
            Code = code
        }
    };
}

public class ApiError
{
    public string Message { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
    public Dictionary<string, string[]>? ValidationErrors { get; set; }
}
