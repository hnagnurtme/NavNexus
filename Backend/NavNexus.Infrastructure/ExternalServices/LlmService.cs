using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using NavNexus.Application.Chatbox.Result;

namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public class HyperClovaService : ILlmService
{
    private readonly HttpClient _httpClient;
    private readonly HyperClovaSettings _settings;
    private readonly ILogger<HyperClovaService> _logger;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public HyperClovaService(
        HttpClient httpClient,
        IOptions<HyperClovaSettings> settings,
        ILogger<HyperClovaService> logger)
    {
        _httpClient = httpClient;
        _settings = settings.Value;
        _logger = logger;
    }

    public async Task<ChatbotQueryResult> GetChatbotResponseAsync(string prompt, CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Sending request to HyperClova API. Prompt length: {PromptLength}", prompt.Length);

            var requestBody = new
            {
                messages = new[]
                {
                    new
                    {
                        role = "user",
                        content = prompt
                    }
                },
                topP = 0.85,             // Balanced diversity
                topK = 0,
                maxTokens = 800,         // Concise but comprehensive responses
                temperature = 0.6,       // Focused and accurate responses
                repeatPenalty = 1.3,     // Moderate repetition control
                stopBefore = Array.Empty<string>(),
                includeAiFilters = true
            };

            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var request = new HttpRequestMessage(HttpMethod.Post, _settings.ApiUrl)
            {
                Content = content
            };

            AddHeaders(request);

            var response = await _httpClient.SendAsync(request, cancellationToken);
            
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogError("HyperClova API request failed with status {StatusCode}: {ErrorContent}", 
                    response.StatusCode, errorContent);
                
                return CreateErrorResponse($"API request failed with status {response.StatusCode}");
            }

            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            _logger.LogDebug("Raw HyperClova response: {Response}", responseContent);

            var hyperClovaResponse = JsonSerializer.Deserialize<HyperClovaApiResponse>(responseContent, JsonOptions);

            if (hyperClovaResponse == null)
            {
                _logger.LogError("Failed to deserialize HyperClova response");
                return CreateErrorResponse("Failed to deserialize API response");
            }

            // Check if the API call was successful
            if (hyperClovaResponse.Status?.Code != "20000")
            {
                _logger.LogError("HyperClova API returned error: {Code} - {Message}", 
                    hyperClovaResponse.Status?.Code, hyperClovaResponse.Status?.Message);
                return CreateErrorResponse($"HyperClova API error: {hyperClovaResponse.Status?.Message}");
            }

            _logger.LogInformation("Successfully received response from HyperClova API. Token usage: {TotalTokens}", 
                hyperClovaResponse.Result?.Usage?.TotalTokens ?? 0);

            return MapToChatbotQueryResult(hyperClovaResponse);
        }
        catch (OperationCanceledException)
        {
            _logger.LogWarning("HyperClova API request was cancelled");
            return CreateErrorResponse("Request was cancelled");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling HyperClova API");
            return CreateErrorResponse($"Failed to communicate with LLM service: {ex.Message}");
        }
    }

    private void AddHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("Authorization", $"Bearer {_settings.ApiKey}");
        request.Headers.Add("X-NCP-CLOVASTUDIO-REQUEST-ID", Guid.NewGuid().ToString());
    }

    private ChatbotQueryResult MapToChatbotQueryResult(HyperClovaApiResponse hyperClovaResponse)
    {
        var result = hyperClovaResponse.Result;
        var message = result?.Message;
        
        var messageResult = new ChatbotMessageResult
        {
            Id = Guid.NewGuid().ToString(),
            Role = message?.Role ?? "assistant",
            Content = message?.Content ?? string.Empty,
            Source = null, // Will be populated by handler if node context exists
            NodeSnapshot = null, // Will be populated by handler if node context exists
            SourceSnapshot = null, // Will be populated by handler if node context exists
            Citations = [], // Initialize empty, will be populated by handler
            Suggestions = [] // Initialize empty, will be populated by handler
        };

        var usageResult = new ChatbotUsageResult
        {
            PromptTokens = result?.Usage?.PromptTokens ?? 0,
            CompletionTokens = result?.Usage?.CompletionTokens ?? 0,
            TotalTokens = result?.Usage?.TotalTokens ?? 0
        };

        return new ChatbotQueryResult
        {
            Message = messageResult,
            Usage = usageResult
        };
    }

    private ChatbotQueryResult CreateErrorResponse(string errorMessage)
    {
        return new ChatbotQueryResult
        {
            Message = new ChatbotMessageResult
            {
                Id = Guid.NewGuid().ToString(),
                Role = "assistant",
                Content = $"Sorry, I encountered an error: {errorMessage}",
                Source = null,
                NodeSnapshot = null,
                SourceSnapshot = null,
                Citations = [],
                Suggestions = []
            },
            Usage = new ChatbotUsageResult
            {
                PromptTokens = 0,
                CompletionTokens = 0,
                TotalTokens = 0
            }
        };
    }
}

// Updated HyperClova API Response Models to match actual response structure
internal class HyperClovaApiResponse
{
    public HyperClovaStatus? Status { get; set; }
    public HyperClovaResult? Result { get; set; }
}

internal class HyperClovaStatus
{
    public string? Code { get; set; }
    public string? Message { get; set; }
}

internal class HyperClovaResult
{
    public HyperClovaMessage? Message { get; set; }
    public string? FinishReason { get; set; }
    public long Created { get; set; }
    public long Seed { get; set; }
    public HyperClovaUsage? Usage { get; set; }
    public List<HyperClovaAiFilter>? AiFilter { get; set; }
}

internal class HyperClovaMessage
{
    public string? Role { get; set; }
    public string? Content { get; set; }
}

internal class HyperClovaUsage
{
    public int PromptTokens { get; set; }
    public int CompletionTokens { get; set; }
    public int TotalTokens { get; set; }
}

internal class HyperClovaAiFilter
{
    public string? GroupName { get; set; }
    public string? Name { get; set; }
    public string? Score { get; set; }
    public string? Result { get; set; }
}

// Configuration Settings
public class HyperClovaSettings
{
    public string ApiUrl { get; set; } = string.Empty;
    public string ApiKey { get; set; } = string.Empty;
}