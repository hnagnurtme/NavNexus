using ErrorOr;
using MediatR;
using Microsoft.Extensions.Logging;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.KnowledgeTree.Commands;
using NavNexus.Application.KnowledgeTree.Results;

namespace NavNexus.Application.KnowledgeTree.Handlers
{
    public class CreateKnowledgeTreeCommandHandler : IRequestHandler<CreateKnowledgeNodeCommand, ErrorOr<RabbitMqSendingResult>>
    {
        private readonly IRabbitMQService _rabbitMQService;
        private readonly IKnowledgetreeRepository _knowledgeTreeRepository;
        private readonly ILogger<CreateKnowledgeTreeCommandHandler> _logger;
        private const string PDF_JOBS_QUEUE = "pdf_jobs_queue";

        public CreateKnowledgeTreeCommandHandler(
            IRabbitMQService rabbitMQService,
            IKnowledgetreeRepository knowledgeTreeRepository,
            ILogger<CreateKnowledgeTreeCommandHandler> logger)
        {
            _rabbitMQService = rabbitMQService ?? throw new ArgumentNullException(nameof(rabbitMQService));
            _knowledgeTreeRepository = knowledgeTreeRepository ?? throw new ArgumentNullException(nameof(knowledgeTreeRepository));
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

                // Bước 1: Copy nodes từ workspace khác nếu URL đã tồn tại
                var totalCopiedNodes = 0;
                var successfullyCopiedFiles = new List<string>();

                foreach (var filePath in request.FilePaths)
                {
                    try
                    {
                        _logger.LogInformation(
                            "Checking if nodes exist for source URL: {FilePath} in other workspaces",
                            filePath);

                        var copiedNodes = await _knowledgeTreeRepository.CopyNodesAsync(
                            evidenceSourceId: filePath,
                            newWorkspaceId: request.WorkspaceId,
                            cancellationToken);

                        if (copiedNodes.Count > 0)
                        {
                            totalCopiedNodes += copiedNodes.Count;
                            successfullyCopiedFiles.Add(filePath);

                            _logger.LogInformation(
                                "Successfully copied {Count} nodes from other workspaces for URL: {FilePath}",
                                copiedNodes.Count,
                                filePath);
                        }
                        else
                        {
                            _logger.LogDebug(
                                "No existing nodes found for URL: {FilePath}, will process as new",
                                filePath);
                        }
                    }
                    catch (Exception ex)
                    {
                        // Log error but continue - copying is optional optimization
                        _logger.LogWarning(ex,
                            "Failed to copy existing nodes for URL: {FilePath}, will process as new. Error: {Error}",
                            filePath,
                            ex.Message);
                    }
                }

                // Lọc ra các files chưa được copy thành công
                var filesToProcess = request.FilePaths
                    .Except(successfullyCopiedFiles)
                    .ToList();

                // Nếu TẤT CẢ files đều đã copy thành công → SUCCESS, không cần RabbitMQ
                if (filesToProcess.Count == 0)
                {
                    _logger.LogInformation(
                        "All {Count} files already exist in other workspaces. " +
                        "Total {NodeCount} nodes copied to workspace {WorkspaceId}. " +
                        "No need to process files via RabbitMQ.",
                        successfullyCopiedFiles.Count,
                        totalCopiedNodes,
                        request.WorkspaceId);

                    var successResult = new RabbitMqSendingResult(
                        messageId: Guid.NewGuid().ToString(), // Generate ID for tracking
                        workspaceId: request.WorkspaceId,
                        sentAt: DateTime.UtcNow,
                        status: "SUCCESS"); // ✅ SUCCESS vì đã copy xong

                    return successResult;
                }

                // Có files cần xử lý → Chỉ gửi files chưa có lên RabbitMQ
                if (totalCopiedNodes > 0)
                {
                    _logger.LogInformation(
                        "Copied {NodeCount} nodes from {CopiedFileCount}/{TotalFileCount} files. " +
                        "Sending {RemainingFileCount} remaining files to RabbitMQ for processing.",
                        totalCopiedNodes,
                        successfullyCopiedFiles.Count,
                        request.FilePaths.Count,
                        filesToProcess.Count);
                }
                else
                {
                    _logger.LogInformation(
                        "No files were copied. Sending all {FileCount} files to RabbitMQ for processing.",
                        filesToProcess.Count);
                }

                // Bước 2: Tạo payload message - CHỈ gửi files chưa có
                var messagePayload = new
                {
                    WorkspaceId = request.WorkspaceId,
                    FilePaths = filesToProcess, // ✅ CHỈ gửi files chưa copy
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

                var result = new RabbitMqSendingResult(
                    messageId: jobId,
                    workspaceId: request.WorkspaceId,
                    sentAt: DateTime.UtcNow,
                    status: "PENDING");

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