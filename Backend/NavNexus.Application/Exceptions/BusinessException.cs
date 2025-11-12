namespace NavNexus.Application.Exceptions;

public class BusinessException : Exception
{
    public string ErrorCode { get; }

    public BusinessException(string message, string errorCode = "BUSINESS_ERROR") 
        : base(message)
    {
        ErrorCode = errorCode;
    }

    public BusinessException(string message, string errorCode, Exception innerException) 
        : base(message, innerException)
    {
        ErrorCode = errorCode;
    }
}
