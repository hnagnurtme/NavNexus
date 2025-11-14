using MediatR;
using NavNexus.Application.Common.Models;

namespace NavNexus.Application.Features.Knowledge.Queries;

/// <summary>
/// Query to search knowledge base using semantic + graph search
/// </summary>
public record QueryKnowledgeQuery(
    string WorkspaceId,
    string Query,
    int Limit = 10) : IRequest<Result<QueryKnowledgeResult>>;

public class QueryKnowledgeResult
{
    public string Answer { get; set; } = string.Empty;
    public List<EvidenceDto> Evidences { get; set; } = new();
    public List<TopicDto> RelatedTopics { get; set; } = new();
    public List<string> GraphPath { get; set; } = new();
}

public class EvidenceDto
{
    public string Id { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public double ConfidenceScore { get; set; }
}

public class TopicDto
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public double RelevanceScore { get; set; }
}
