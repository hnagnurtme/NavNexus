using ErrorOr;
using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.KnowledgeTree.Commands;
using NavNexus.Application.KnowledgeTree.Results;

namespace NavNexus.Application.KnowledgeTree.Handlers
{
    public class CreateKnowledgeTreeCommandHandler : IRequestHandler<CreateKnowledgeNodeCommand, ErrorOr<RabbitMqSendingResult>>
    {
        private readonly IRabbitMQService _rabbitMQService;
        private readonly ILogger<CreateKnowledgeTreeCommandHandler> _logger;
        private const string PDF_JOBS_QUEUE = "pdf_jobs_queue";

        public CreateKnowledgeTreeCommandHandler(
            IRabbitMQService rabbitMQService,
            ILogger<CreateKnowledgeTreeCommandHandler> logger)
        {
            _rabbitMQService = rabbitMQService ?? throw new ArgumentNullException(nameof(rabbitMQService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        public async Task<ErrorOr<RabbitMqSendingResult>> Handle(
            CreateKnowledgeNodeCommand request, 
            CancellationToken cancellationToken)
        {
            _logger.LogInformation(
                "Processing CreateKnowledgeNodeCommand - WorkspaceId: {WorkspaceId}, FilePaths count: {FileCount}",
                request.WorkspaceId,
                request.FilePaths?.Count ?? 0);

            try
            {
                // Validation
                if (string.IsNullOrWhiteSpace(request.WorkspaceId))
                {
                    _logger.LogWarning("WorkspaceId is null or empty");
                    return Error.Validation(
                        code: "KnowledgeTree.InvalidWorkspaceId",
                        description: "WorkspaceId is required");
                }

                if (request.FilePaths == null || !request.FilePaths.Any())
                {
                    _logger.LogWarning("FilePaths is null or empty for WorkspaceId: {WorkspaceId}", request.WorkspaceId);
                    return Error.Validation(
                        code: "KnowledgeTree.InvalidFilePaths",
                        description: "At least one file path is required");
                }

                // Validate file paths
                var invalidPaths = request.FilePaths.Where(string.IsNullOrWhiteSpace).ToList();
                if (invalidPaths.Any())
                {
                    _logger.LogWarning("Found {Count} invalid file paths", invalidPaths.Count);
                    return Error.Validation(
                        code: "KnowledgeTree.InvalidFilePath",
                        description: "One or more file paths are invalid");
                }

                // Tạo payload message
                var messagePayload = new
                {
                    WorkspaceId = request.WorkspaceId,
                    FilePaths = request.FilePaths,
                    CreatedAt = DateTime.UtcNow,
                    RequestId = Guid.NewGuid().ToString() // For tracing
                };

                _logger.LogDebug(
                    "Sending message to queue '{QueueName}' for WorkspaceId: {WorkspaceId}",
                    PDF_JOBS_QUEUE,
                    request.WorkspaceId);

                // Gửi message lên RabbitMQ
                var jobId = await _rabbitMQService.SendMessageWithJobIdAsync(
                    PDF_JOBS_QUEUE, 
                    messagePayload, 
                    cancellationToken);

                var result = new RabbitMqSendingResult(jobId, DateTime.UtcNow);

                _logger.LogInformation(
                    "Successfully sent message to RabbitMQ - JobId: {JobId}, WorkspaceId: {WorkspaceId}",
                    jobId,
                    request.WorkspaceId);

                return result;
            }
            catch (ArgumentException ex)
            {
                _logger.LogError(ex, "Invalid argument when sending message to RabbitMQ");
                return Error.Validation(
                    code: "KnowledgeTree.InvalidArgument",
                    description: $"Invalid argument: {ex.Message}");
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogError(ex, "RabbitMQ connection error");
                return Error.Failure(
                    code: "KnowledgeTree.ConnectionError",
                    description: $"RabbitMQ connection error: {ex.Message}");
            }
            catch (TimeoutException ex)
            {
                _logger.LogError(ex, "Timeout sending message to RabbitMQ");
                return Error.Failure(
                    code: "KnowledgeTree.Timeout",
                    description: "Request timeout while sending message to queue");
            }
            catch (OperationCanceledException ex)
            {
                _logger.LogWarning(ex, "Operation was cancelled");
                return Error.Failure(
                    code: "KnowledgeTree.Cancelled",
                    description: "Operation was cancelled");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, 
                    "Unexpected error sending message to RabbitMQ for WorkspaceId: {WorkspaceId}", 
                    request.WorkspaceId);
                
                return Error.Failure(
                    code: "KnowledgeTree.UnexpectedError",
                    description: $"Failed to send message to RabbitMQ: {ex.Message}");
            }
        }
    }
}