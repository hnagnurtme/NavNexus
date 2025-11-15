using Microsoft.Extensions.Configuration;
using NavNexus.Application.Common.Interfaces.ExternalServices;

namespace NavNexus.Infrastructure.ExternalServices;

public class LlmService : ILlmService
{
    private readonly IConfiguration _configuration;
    private readonly HttpClient _httpClient;

    public LlmService(IConfiguration configuration, HttpClient httpClient)
    {
        _configuration = configuration;
        _httpClient = httpClient;
    }

    public async Task<string> CompareEvidenceAsync(string evidence1, string evidence2, string context, CancellationToken cancellationToken = default)
    {
        // TODO: Implement actual LLM API call (OpenAI, Anthropic, or Naver Hyperclova)
        await Task.Delay(1000, cancellationToken);
        
        return $"Comparison analysis:\n" +
               $"Evidence 1: {evidence1.Substring(0, Math.Min(50, evidence1.Length))}...\n" +
               $"Evidence 2: {evidence2.Substring(0, Math.Min(50, evidence2.Length))}...\n" +
               $"These pieces of evidence are related in the context of {context}.";
    }

    public async Task<List<string>> ExtractTopicsAsync(string text, CancellationToken cancellationToken = default)
    {
        // TODO: Implement actual topic extraction using LLM
        await Task.Delay(800, cancellationToken);
        
        return new List<string> { "Sample Topic 1", "Sample Topic 2" };
    }

    public async Task<string> SummarizeTextAsync(string text, int maxLength = 500, CancellationToken cancellationToken = default)
    {
        // TODO: Implement actual summarization using LLM
        await Task.Delay(600, cancellationToken);
        
        var summary = text.Length > maxLength 
            ? text.Substring(0, Math.Min(maxLength, text.Length)) + "..."
            : text;
        
        return summary;
    }
}
