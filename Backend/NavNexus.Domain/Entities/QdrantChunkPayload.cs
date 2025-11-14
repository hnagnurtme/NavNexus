using System.Text.Json.Serialization;

namespace NavNexus.Domain.Entities;

/// <summary>
/// Payload của 1 vector point trong Qdrant
/// Used for semantic search and context retrieval
/// </summary>
public class QdrantChunkPayload
{
    [JsonPropertyName("chunk_id")]
    public string ChunkId { get; set; } = string.Empty; // "chunk-001"
    
    [JsonPropertyName("paper_id")]
    public string PaperId { get; set; } = string.Empty; // "file-uuid" or "PPO.pdf"
    
    [JsonPropertyName("page")]
    public int Page { get; set; }
    
    [JsonPropertyName("quote")]
    public string Quote { get; set; } = string.Empty; // Original text chunk
    
    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty; // LLM-generated summary
    
    [JsonPropertyName("concepts")]
    public List<string> Concepts { get; set; } = new(); // ["PPO", "actor-critic"]
    
    [JsonPropertyName("topic")]
    public string Topic { get; set; } = string.Empty; // Main topic
    
    [JsonPropertyName("workspace_id")]
    public string WorkspaceId { get; set; } = string.Empty;
    
    [JsonPropertyName("language")]
    public string Language { get; set; } = string.Empty; // "en" (after translation)
    
    [JsonPropertyName("source_language")]
    public string SourceLanguage { get; set; } = string.Empty; // "ko" (original)
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}
