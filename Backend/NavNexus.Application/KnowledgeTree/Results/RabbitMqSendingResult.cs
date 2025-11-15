namespace NavNexus.Application.KnowledgeTree.Results;

public class RabbitMqSendingResult
{
    public string MessageId { get; set; }

    public  DateTime SentAt { get; set; }

    public RabbitMqSendingResult(string messageId, DateTime sentAt)
    {
        MessageId = messageId;
        SentAt = sentAt;
    }
}