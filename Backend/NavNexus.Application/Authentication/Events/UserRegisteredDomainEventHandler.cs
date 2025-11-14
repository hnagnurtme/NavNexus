using System.Security.Claims;
using MediatR;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using NavNexus.Domain.Common.Events;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Common.Interfaces.Security;

public class UserRegisteredDomainEventHandler
    : INotificationHandler<UserRegisteredDomainEvent>
{
    private readonly ILogger<UserRegisteredDomainEventHandler> _logger;

    private readonly IEmailSender _emailSender;

    private readonly IConfiguration _configuration;

    private readonly IJwtService _jwtService;

    public UserRegisteredDomainEventHandler(
        ILogger<UserRegisteredDomainEventHandler> logger,
        IConfiguration configuration,
        IJwtService jwtService,
        IEmailSender emailSender)
    {
        _logger = logger;
        _jwtService = jwtService;
        _configuration = configuration;
        _emailSender = emailSender;
    }
    public Task Handle(UserRegisteredDomainEvent notification, CancellationToken cancellationToken)
    {
        _logger.LogInformation("User registered with ID: {UserId} and Email: {Email}",
            notification.UserId, notification.Email);

        // Generate email verification token
        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.Email, notification.Email)
        };
        var token = _jwtService.GenerateToken(claims, TimeSpan.FromDays(1));
        // xác định path cho link verification láy từ env

        var baseUrl = _configuration["App:BaseUrl"]
              ?? throw new InvalidOperationException("BaseUrl is not configured.");

        var verificationLink = $"{baseUrl}/api/auth/verify-email?Email={notification.Email}&Token={token}";
        var subject = "Welcome to NavNexus!";
        var message = $"Thank you for registering, please verify your email: {notification.Email} by clicking the link: {verificationLink}";
        _emailSender.SendEmailAsync(notification.Email, subject, message);

        return Task.CompletedTask;
    }
}
