namespace NavNexus.Application.Chatbox.Result;

public class ChatbotQueryResult
{
    public required ChatbotMessageResult Message { get; set; }
    public required ChatbotUsageResult Usage { get; set; }
}

public class ChatbotMessageResult
{
    public required string Id { get; set; }
    public required string Role { get; set; }
    public required string Content { get; set; }

    public string? Source { get; set; }
    public string? NodeSnapshot { get; set; }
    public string? SourceSnapshot { get; set; }

    public List<ChatCitationResult>? Citations { get; set; }
    public List<ChatSuggestionResult>? Suggestions { get; set; }
}

public class ChatCitationResult
{
    public required string Id { get; set; }
    public required string Label { get; set; }
    public required string Type { get; set; }

    public string? Snippet { get; set; }
    public string? Confidence { get; set; }
}

public class ChatSuggestionResult
{
    public required string Id { get; set; }
    public required string Prompt { get; set; }
}

public class ChatbotUsageResult
{
    public required int PromptTokens { get; set; }
    public required int CompletionTokens { get; set; }
    public required int TotalTokens { get; set; }
}