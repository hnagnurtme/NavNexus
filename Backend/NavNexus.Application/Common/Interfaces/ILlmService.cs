using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for LLM operations (HyperCLOVA X)
/// </summary>
public interface ILlmService
{
    /// <summary>
    /// Processes document text and extracts knowledge structure
    /// </summary>
    /// <param name="text">Document text (translated if needed)</param>
    /// <param name="context">Context from previous documents (from Qdrant)</param>
    /// <returns>Extracted knowledge nodes, evidence, and chunks</returns>
    Task<LlmExtractionResult> ExtractKnowledgeAsync(string text, List<QdrantChunkPayload>? context = null, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Generates answer for user query using retrieved context
    /// </summary>
    Task<string> GenerateAnswerAsync(string query, List<QdrantChunkPayload> qdrantContext, List<KnowledgeNodePoco> graphContext, CancellationToken cancellationToken = default);
}

/// <summary>
/// Result of LLM knowledge extraction
/// </summary>
public class LlmExtractionResult
{
    public List<KnowledgeNodePoco> KnowledgeNodes { get; set; } = new();
    public List<EvidenceNodePoco> Evidences { get; set; } = new();
    public List<(QdrantChunkPayload Payload, string Text)> Chunks { get; set; } = new();
    public List<(string ParentId, string ChildId)> Relationships { get; set; } = new();
}
