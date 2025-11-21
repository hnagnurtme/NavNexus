using System.Net.Http.Json;
using System.Text.Json;
using Google.Apis.Auth.OAuth2;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Domain.Entities;

namespace NavNexus.Infrastructure.Persistence.Repositories;

public class JobRepository : IJobRepository
{
    private readonly string _databaseUrl;
    private readonly GoogleCredential _credential;
    private readonly HttpClient _httpClient;

    public JobRepository(string databaseUrl, string credentialPath)
    {
        _databaseUrl = databaseUrl?.TrimEnd('/') ?? throw new ArgumentNullException(nameof(databaseUrl));

        // Use CredentialFactory to avoid obsolete warning
        #pragma warning disable CS0618
        _credential = GoogleCredential.FromFile(credentialPath);
        #pragma warning restore CS0618

        _httpClient = new HttpClient();
    }

    public async Task<Job> CreateJobAsync(Job job, CancellationToken cancellationToken = default)
    {
        if (job == null)
            throw new ArgumentNullException(nameof(job));

        // Get access token
        var accessToken = await GetAccessTokenAsync();

        // Create job path: jobs/{workspaceId}/{jobId}
        var url = $"{_databaseUrl}/jobs/{job.WorkspaceId}/{job.Id}.json?access_token={accessToken}";

        var jobData = new Dictionary<string, object>
        {
            { "id", job.Id },
            { "workspaceId", job.WorkspaceId },
            { "filePath", job.FilePath },
            { "status", job.Status },
            { "createdAt", job.CreatedAt.ToString("o") }, // ISO 8601 format
            { "completedAt", job.CompletedAt?.ToString("o") ?? "" }
        };

        var response = await _httpClient.PutAsJsonAsync(url, jobData, cancellationToken);
        response.EnsureSuccessStatusCode();

        return job;
    }

    public async Task<Job?> GetJobByFilePathAsync(string workspaceId, string filePath, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(workspaceId))
            throw new ArgumentException("WorkspaceId cannot be empty", nameof(workspaceId));

        if (string.IsNullOrWhiteSpace(filePath))
            throw new ArgumentException("FilePath cannot be empty", nameof(filePath));

        // Get access token
        var accessToken = await GetAccessTokenAsync();

        // Query jobs by workspace and filePath
        // orderBy="filePath"&equalTo="{filePath}"
        var encodedFilePath = Uri.EscapeDataString($"\"{filePath}\"");
        var url = $"{_databaseUrl}/jobs/{workspaceId}.json?orderBy=\"filePath\"&equalTo={encodedFilePath}&access_token={accessToken}";

        var response = await _httpClient.GetAsync(url, cancellationToken);
        response.EnsureSuccessStatusCode();

        var content = await response.Content.ReadAsStringAsync(cancellationToken);

        if (string.IsNullOrWhiteSpace(content) || content == "null")
            return null;

        var jobs = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(content);
        if (jobs == null || jobs.Count == 0)
            return null;

        // Get first matching job
        var firstJob = jobs.First().Value;
        return MapToJob(firstJob);
    }

    private Job MapToJob(JsonElement jobElement)
    {
        var job = new Job
        {
            Id = GetStringProperty(jobElement, "id"),
            WorkspaceId = GetStringProperty(jobElement, "workspaceId"),
            FilePath = GetStringProperty(jobElement, "filePath"),
            Status = GetStringProperty(jobElement, "status"),
            CreatedAt = DateTime.Parse(GetStringProperty(jobElement, "createdAt")),
        };

        var completedAtStr = GetStringProperty(jobElement, "completedAt");
        if (!string.IsNullOrEmpty(completedAtStr))
        {
            job.CompletedAt = DateTime.Parse(completedAtStr);
        }

        return job;
    }

    private static string GetStringProperty(JsonElement element, string propertyName)
    {
        if (element.TryGetProperty(propertyName, out var property))
        {
            return property.GetString() ?? string.Empty;
        }
        return string.Empty;
    }

    private async Task<string> GetAccessTokenAsync()
    {
        var scopedCredential = _credential.CreateScoped(
            "https://www.googleapis.com/auth/firebase.database",
            "https://www.googleapis.com/auth/userinfo.email"
        );

        var token = await ((ITokenAccess)scopedCredential).GetAccessTokenForRequestAsync();
        return token ?? throw new InvalidOperationException("Failed to get access token");
    }
}
