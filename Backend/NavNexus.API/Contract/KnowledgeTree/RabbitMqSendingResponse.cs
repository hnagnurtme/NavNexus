namespace NavNexus.API.Contract.KnowledgeTree;

public class RabbitMqSendingResponse
{
    public required string MessageId { get; set; }
    public required DateTime SentAt { get; set; }

    public RabbitMqSendingResponse(string messageId, DateTime sentAt)
    {
        MessageId = messageId;
        SentAt = sentAt;
    }
}