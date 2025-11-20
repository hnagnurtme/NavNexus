using Google.Rpc;

namespace NavNexus.Application.KnowledgeTree.Results;

public class RabbitMqSendingResult
{
    public string MessageId { get; set; }

    public string WorkspaceId { get; set; } = string.Empty;

    public string Status { get; set; } = "PENDING"; // PENDING , SUCCESS

    public  DateTime SentAt { get; set; }

    public RabbitMqSendingResult(string messageId, string workspaceId, DateTime sentAt, string status = "PENDING")
    {
        MessageId = messageId;
        SentAt = sentAt;
        WorkspaceId = workspaceId;
        Status = status;
    }
}