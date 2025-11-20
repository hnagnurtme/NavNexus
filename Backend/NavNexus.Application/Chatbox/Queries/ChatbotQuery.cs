namespace NavNexus.Application.Chatbox.Queries;

using MediatR;
using NavNexus.Application.Chatbox.Result;
using ErrorOr;

public record ChatContext(
    string Id,
    string? EntityId,
    string Type,
    string Label
);

public record ChatHistory(
    string Role,
    string Content,
    long Timestamp,
    string? NodeSnapshot = null,
    string? SourceSnapshot = null,
    string? Source = null
);

public record ChatbotQuery(
    string Prompt,
    string? WorkspaceId = null,
    string? TopicId = null,
    List<ChatContext> Contexts = null!,
    List<ChatHistory> History = null!
) : IRequest<ErrorOr<ChatbotQueryResult>>;
