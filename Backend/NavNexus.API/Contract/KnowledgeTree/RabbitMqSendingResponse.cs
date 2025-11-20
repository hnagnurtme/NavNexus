namespace NavNexus.API.Contract.KnowledgeTree;

public class RabbitMqSendingResponse
{
    public required string MessageId { get; set; }

    public required string WorkspaceId { get; set; } = string.Empty;

    public required string Status { get; set; } = "PENDING"; // PENDING , SUCCESS

    public required DateTime SentAt { get; set; }

    public RabbitMqSendingResponse(string messageId, string workspaceId, DateTime sentAt, string status = "PENDING")
    {
        MessageId = messageId;
        SentAt = sentAt;
        WorkspaceId = workspaceId;
        Status = status;
    }
}