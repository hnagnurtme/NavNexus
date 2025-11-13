using System.Text.Json.Serialization;

namespace NavNexus.Domain.Entities;

/// <summary>
/// Lưu trong Firestore: users/{user_id}
/// </summary>
public class User
{
    [JsonPropertyName("user_id")]
    public string UserId { get; set; } = string.Empty;
    
    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;
    
    [JsonPropertyName("display_name")]
    public string DisplayName { get; set; } = string.Empty;
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonPropertyName("last_login")]
    public DateTime LastLogin { get; set; }
    
    [JsonPropertyName("workspace_ids")]
    public List<string> WorkspaceIds { get; set; } = new();
    
    [JsonPropertyName("preferences")]
    public UserPreferences Preferences { get; set; } = new();
}

public class UserPreferences
{
    [JsonPropertyName("default_target_language")]
    public string DefaultTargetLanguage { get; set; } = "en";
    
    [JsonPropertyName("theme")]
    public string Theme { get; set; } = "light"; // "light", "dark"
    
    [JsonPropertyName("notification_enabled")]
    public bool NotificationEnabled { get; set; } = true;
}
