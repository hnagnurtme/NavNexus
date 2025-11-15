using ErrorOr;

namespace NavNexus.Application.Common.Interfaces.ExternalServices;


public interface IRabbitMQService
{
    Task<string> SendMessageWithJobIdAsync<T>(string queueName, T message, CancellationToken cancellationToken = default);
}