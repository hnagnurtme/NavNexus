using System.Text.Json.Serialization;

namespace NavNexus.Domain.Entities;

/// <summary>
/// Lưu trong Firestore: workspaces/{workspace_id}
/// </summary>
public class Workspace
{
    [JsonPropertyName("workspace_id")]
    public string WorkspaceId { get; set; } = string.Empty;
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
    
    [JsonPropertyName("owner_id")]
    public string OwnerId { get; set; } = string.Empty;
    
    [JsonPropertyName("member_ids")]
    public List<string> MemberIds { get; set; } = new();
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }
    
    [JsonPropertyName("qdrant_collection_name")]
    public string QdrantCollectionName { get; set; } = string.Empty; // "workspace_{workspace_id}"
    
    [JsonPropertyName("file_count")]
    public int FileCount { get; set; }
    
    [JsonPropertyName("total_size_bytes")]
    public long TotalSizeBytes { get; set; }
}
