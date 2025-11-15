using System;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using RabbitMQ.Client;
using RabbitMQ.Client.Exceptions;

namespace NavNexus.Infrastructure.ExternalServices
{
    public class RabbitMqService : IRabbitMQService, IDisposable
    {
        private readonly ILogger<RabbitMqService> _logger;
        private IConnection _connection;
        private IModel _channel;
        private bool _disposed = false;

        public RabbitMqService(IConfiguration configuration, ILogger<RabbitMqService> logger)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            
            try
            {
                InitializeConnection(configuration);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to initialize RabbitMQ connection");
                throw;
            }
        }

        private void InitializeConnection(IConfiguration configuration)
        {
            _logger.LogInformation("Initializing RabbitMQ connection...");

            // Đọc cấu hình
            var host = configuration["RabbitMQ:Host"];
            var username = configuration["RabbitMQ:Username"];
            var password = configuration["RabbitMQ:Password"];
            var vhost = configuration["RabbitMQ:VirtualHost"]; // Thêm vhost config

            // Validate configuration
            if (string.IsNullOrWhiteSpace(host))
            {
                _logger.LogError("RabbitMQ:Host is not configured");
                throw new InvalidOperationException("RabbitMQ host not configured");
            }

            if (string.IsNullOrWhiteSpace(username))
            {
                _logger.LogError("RabbitMQ:Username is not configured");
                throw new InvalidOperationException("RabbitMQ username not configured");
            }

            if (string.IsNullOrWhiteSpace(password))
            {
                _logger.LogError("RabbitMQ:Password is not configured");
                throw new InvalidOperationException("RabbitMQ password not configured");
            }

            // CloudAMQP: VirtualHost = first part of username (before colon)
            // Example: "odgfvgev:odgfvgev" -> vhost = "odgfvgev"
            var actualVHost = vhost ?? username.Split(':')[0];

            _logger.LogInformation("RabbitMQ Configuration - Host: {Host}, Username: {Username}, VirtualHost: {VHost}", 
                host, username, actualVHost);

            // CloudAMQP format: 
            // - Host: chameleon-01.lmq.cloudamqp.com
            // - Username: odgfvgev (NOT odgfvgev:odgfvgev)
            // - VirtualHost: odgfvgev
            var factory = new ConnectionFactory
            {
                HostName = host,
                UserName = username.Split(':')[0], // Use only the first part
                Password = password,
                VirtualHost = actualVHost,
                Port = 5672,
                RequestedHeartbeat = TimeSpan.FromSeconds(60),
                AutomaticRecoveryEnabled = true,
                NetworkRecoveryInterval = TimeSpan.FromSeconds(10),
                DispatchConsumersAsync = false,
                // Timeout settings
                RequestedConnectionTimeout = TimeSpan.FromSeconds(30),
                SocketReadTimeout = TimeSpan.FromSeconds(30),
                SocketWriteTimeout = TimeSpan.FromSeconds(30)
            };

            _logger.LogInformation("Connection factory configured - UserName: {UserName}, VirtualHost: {VHost}, Port: {Port}", 
                factory.UserName, factory.VirtualHost, factory.Port);

            try
            {
                _logger.LogInformation("Creating connection to RabbitMQ...");
                _connection = factory.CreateConnection();
                
                _logger.LogInformation("RabbitMQ connection established successfully");
                _logger.LogInformation("Connection details - IsOpen: {IsOpen}, Endpoint: {Endpoint}", 
                    _connection.IsOpen, _connection.Endpoint);

                _logger.LogInformation("Creating channel...");
                _channel = _connection.CreateModel();
                
                _logger.LogInformation("Channel created successfully - ChannelNumber: {ChannelNumber}, IsOpen: {IsOpen}", 
                    _channel.ChannelNumber, _channel.IsOpen);

                // Subscribe to connection events
                _connection.ConnectionShutdown += (sender, args) =>
                {
                    _logger.LogWarning("RabbitMQ connection shutdown - ReplyCode: {ReplyCode}, ReplyText: {ReplyText}", 
                        args.ReplyCode, args.ReplyText);
                };

                _connection.CallbackException += (sender, args) =>
                {
                    _logger.LogError(args.Exception, "RabbitMQ callback exception occurred");
                };

                _connection.ConnectionBlocked += (sender, args) =>
                {
                    _logger.LogWarning("RabbitMQ connection blocked - Reason: {Reason}", args.Reason);
                };

                _connection.ConnectionUnblocked += (sender, args) =>
                {
                    _logger.LogInformation("RabbitMQ connection unblocked");
                };
            }
            catch (BrokerUnreachableException ex)
            {
                _logger.LogError(ex, "Cannot reach RabbitMQ broker at {Host}. Please check: 1) Host address is correct, 2) Port 5672 is accessible, 3) Firewall settings", host);
                throw;
            }
            catch (AuthenticationFailureException ex)
            {
                _logger.LogError(ex, "Authentication failed. Please check username and password");
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error while connecting to RabbitMQ");
                throw;
            }
        }

        public Task<string> SendMessageWithJobIdAsync<T>(string queueName, T message, CancellationToken cancellationToken = default)
        {
            if (_disposed)
            {
                _logger.LogError("Cannot send message - service is disposed");
                throw new ObjectDisposedException(nameof(RabbitMqService));
            }

            if (string.IsNullOrWhiteSpace(queueName))
            {
                _logger.LogError("Queue name is required");
                throw new ArgumentException("Queue name is required", nameof(queueName));
            }

            if (!_connection.IsOpen)
            {
                _logger.LogError("RabbitMQ connection is closed");
                throw new InvalidOperationException("RabbitMQ connection is not open");
            }

            if (!_channel.IsOpen)
            {
                _logger.LogError("RabbitMQ channel is closed");
                throw new InvalidOperationException("RabbitMQ channel is not open");
            }

            try
            {
                // 1. Generate a unique JobId
                var jobId = Guid.NewGuid().ToString();
                _logger.LogDebug("Generated JobId: {JobId} for queue: {QueueName}", jobId, queueName);

                // 2. Build payload
                var payload = new
                {
                    JobId = jobId,
                    Data = message,
                    Timestamp = DateTime.UtcNow
                };
                
                var jsonOptions = new JsonSerializerOptions
                {
                    WriteIndented = false
                };
                var json = JsonSerializer.Serialize(payload, jsonOptions);
                var body = Encoding.UTF8.GetBytes(json);

                _logger.LogDebug("Message payload size: {Size} bytes", body.Length);

                // 3. Declare queue (durable)
                _logger.LogDebug("Declaring queue: {QueueName}", queueName);
                var queueDeclareOk = _channel.QueueDeclare(
                    queue: queueName,
                    durable: true,
                    exclusive: false,
                    autoDelete: false,
                    arguments: null
                );
                
                _logger.LogDebug("Queue declared - Name: {QueueName}, MessageCount: {MessageCount}, ConsumerCount: {ConsumerCount}", 
                    queueDeclareOk.QueueName, queueDeclareOk.MessageCount, queueDeclareOk.ConsumerCount);

                // 4. Set message properties
                var properties = _channel.CreateBasicProperties();
                properties.Persistent = true;
                properties.MessageId = jobId;
                properties.ContentType = "application/json";
                properties.DeliveryMode = 2; // Persistent
                properties.Timestamp = new AmqpTimestamp(DateTimeOffset.UtcNow.ToUnixTimeSeconds());

                // 5. Publish message
                _logger.LogInformation("Publishing message to queue '{QueueName}' with JobId: {JobId}", queueName, jobId);
                
                _channel.BasicPublish(
                    exchange: "",
                    routingKey: queueName,
                    basicProperties: properties,
                    body: body
                );

                _logger.LogInformation("Message successfully sent to queue '{QueueName}', JobId: {JobId}", queueName, jobId);

                return Task.FromResult(jobId);
            }
            catch (AlreadyClosedException ex)
            {
                _logger.LogError(ex, "Channel or connection is already closed");
                throw;
            }
            catch (OperationInterruptedException ex)
            {
                _logger.LogError(ex, "Operation was interrupted - ReplyCode: {ReplyCode}, ReplyText: {ReplyText}", 
                    ex.ShutdownReason?.ReplyCode, ex.ShutdownReason?.ReplyText);
                throw;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending message to queue '{QueueName}'", queueName);
                throw;
            }
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _logger.LogInformation("Disposing RabbitMQ service...");

            try
            {
                if (_channel != null && _channel.IsOpen)
                {
                    _logger.LogDebug("Closing channel...");
                    _channel.Close();
                    _logger.LogDebug("Channel closed successfully");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error closing RabbitMQ channel");
            }

            try
            {
                if (_connection != null && _connection.IsOpen)
                {
                    _logger.LogDebug("Closing connection...");
                    _connection.Close();
                    _logger.LogDebug("Connection closed successfully");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error closing RabbitMQ connection");
            }

            _channel?.Dispose();
            _connection?.Dispose();

            _disposed = true;
            _logger.LogInformation("RabbitMQ service disposed");
        }
    }
}