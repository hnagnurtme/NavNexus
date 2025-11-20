namespace NavNexus.API.Contract.Chatbox
{
    public class ChatbotQueryResponseData
    {
        public required ChatbotMessageResponse Message { get; set; }
        public required ChatbotUsage Usage { get; set; }
    }

    public class ChatbotMessageResponse
    {
        public required string Id { get; set; }
        public required string Role { get; set; }
        public required string Content { get; set; }

        public string? Source { get; set; }
        public string? NodeSnapshot { get; set; }
        public string? SourceSnapshot { get; set; }

        public List<ChatCitationItem>? Citations { get; set; }
        public List<ChatSuggestionItem>? Suggestions { get; set; }
    }

    public class ChatCitationItem
    {
        public required string Id { get; set; }
        public required string Label { get; set; }
        public required string Type { get; set; }

        public string? Snippet { get; set; }
        public string? Confidence { get; set; }
    }

    public class ChatSuggestionItem
    {
        public required string Id { get; set; }
        public required string Prompt { get; set; }
    }

    public class ChatbotUsage
    {
        public required int PromptTokens { get; set; }
        public required int CompletionTokens { get; set; }
        public required int TotalTokens { get; set; }
    }
}
