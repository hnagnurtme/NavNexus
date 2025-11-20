namespace NavNexus.API.Contract.Chatbox
{
    public class ChatbotQueryRequest
    {
        public required string Prompt { get; set; }
        public string? WorkspaceId { get; set; }
        public string? TopicId { get; set; }

        public List<ChatContextItem> Contexts { get; set; } = new();
        public List<ChatHistoryItem> History { get; set; } = new();
    }

    public class ChatContextItem
    {
        public required string Id { get; set; }
        public string? EntityId { get; set; }
        public required string Type { get; set; }
        public required string Label { get; set; }
    }

    public class ChatHistoryItem
    {
        public required string Role { get; set; }
        public required string Content { get; set; }
        public required long Timestamp { get; set; }

        public string? NodeSnapshot { get; set; }
        public string? SourceSnapshot { get; set; }
        public string? Source { get; set; }
    }
}
