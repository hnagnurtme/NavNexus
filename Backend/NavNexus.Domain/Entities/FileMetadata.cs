using System.Text.Json.Serialization;

namespace NavNexus.Domain.Entities;

/// <summary>
/// Lưu trong Firestore: workspaces/{workspace_id}/files/{file_id}
/// Dùng để cache metadata và tránh reprocess file trùng
/// </summary>
public class FileMetadata
{
    [JsonPropertyName("file_id")]
    public string FileId { get; set; } = string.Empty;
    
    [JsonPropertyName("file_hash")]
    public string FileHash { get; set; } = string.Empty; // SHA256
    
    [JsonPropertyName("file_name")]
    public string FileName { get; set; } = string.Empty;
    
    [JsonPropertyName("file_size")]
    public long FileSize { get; set; }
    
    [JsonPropertyName("mime_type")]
    public string MimeType { get; set; } = string.Empty;
    
    [JsonPropertyName("workspace_id")]
    public string WorkspaceId { get; set; } = string.Empty;
    
    [JsonPropertyName("upload_date")]
    public DateTime UploadDate { get; set; }
    
    [JsonPropertyName("nos_url")]
    public string NosUrl { get; set; } = string.Empty;
    
    [JsonPropertyName("neo4j_node_ids")]
    public List<string> Neo4jNodeIds { get; set; } = new();
    
    [JsonPropertyName("qdrant_point_ids")]
    public List<string> QdrantPointIds { get; set; } = new();
    
    [JsonPropertyName("processing_status")]
    public ProcessingStatus Status { get; set; }
    
    [JsonPropertyName("error_message")]
    public string? ErrorMessage { get; set; }
    
    [JsonPropertyName("language_detected")]
    public string? LanguageDetected { get; set; } // "ko", "en", "ja", "vi"
    
    [JsonPropertyName("translation_target")]
    public string? TranslationTarget { get; set; } // "en"
    
    [JsonPropertyName("processing_time_ms")]
    public long ProcessingTimeMs { get; set; }
}

public enum ProcessingStatus
{
    Pending,
    Processing,
    Completed,
    Failed
}
