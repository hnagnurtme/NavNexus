using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.ExternalServices;

namespace NavNexus.Infrastructure.HealthChecks
{
    public class RabbitMqHealthCheck : IHealthCheck
    {
        private readonly IRabbitMQService _rabbitMqService;
        private readonly ILogger<RabbitMqHealthCheck> _logger;

        public RabbitMqHealthCheck(
            IRabbitMQService rabbitMqService,
            ILogger<RabbitMqHealthCheck> logger)
        {
            _rabbitMqService = rabbitMqService ?? throw new ArgumentNullException(nameof(rabbitMqService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        public async Task<HealthCheckResult> CheckHealthAsync(
            HealthCheckContext context,
            CancellationToken cancellationToken = default)
        {
            try
            {
                _logger.LogDebug("Performing RabbitMQ health check...");

                // Try to send a test message to a health check queue
                var testMessage = new { Type = "HealthCheck", Timestamp = DateTime.UtcNow };
                var jobId = await _rabbitMqService.SendMessageWithJobIdAsync(
                    "health_check_queue",
                    testMessage,
                    cancellationToken);

                _logger.LogDebug("RabbitMQ health check passed - JobId: {JobId}", jobId);

                return HealthCheckResult.Healthy(
                    "RabbitMQ connection is healthy",
                    new Dictionary<string, object>
                    {
                        { "jobId", jobId },
                        { "timestamp", DateTime.UtcNow }
                    });
            }
            catch (ObjectDisposedException ex)
            {
                _logger.LogError(ex, "RabbitMQ service has been disposed");
                return HealthCheckResult.Unhealthy(
                    "RabbitMQ service is disposed",
                    ex,
                    new Dictionary<string, object>
                    {
                        { "error", "Service disposed" },
                        { "timestamp", DateTime.UtcNow }
                    });
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogError(ex, "RabbitMQ connection is not open");
                return HealthCheckResult.Unhealthy(
                    "RabbitMQ connection is not available",
                    ex,
                    new Dictionary<string, object>
                    {
                        { "error", "Connection not open" },
                        { "timestamp", DateTime.UtcNow }
                    });
            }
            catch (TimeoutException ex)
            {
                _logger.LogError(ex, "RabbitMQ health check timeout");
                return HealthCheckResult.Degraded(
                    "RabbitMQ is responding slowly",
                    ex,
                    new Dictionary<string, object>
                    {
                        { "error", "Timeout" },
                        { "timestamp", DateTime.UtcNow }
                    });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "RabbitMQ health check failed");
                return HealthCheckResult.Unhealthy(
                    "RabbitMQ health check failed",
                    ex,
                    new Dictionary<string, object>
                    {
                        { "error", ex.Message },
                        { "timestamp", DateTime.UtcNow }
                    });
            }
        }
    }
}