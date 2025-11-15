namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface ILlmService
{
    Task<string> CompareEvidenceAsync(string evidence1, string evidence2, string context, CancellationToken cancellationToken = default);
    Task<List<string>> ExtractTopicsAsync(string text, CancellationToken cancellationToken = default);
    Task<string> SummarizeTextAsync(string text, int maxLength = 500, CancellationToken cancellationToken = default);
}
