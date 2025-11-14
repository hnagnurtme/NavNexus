namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface IPapagoTranslationService
{
    Task<string> TranslateAsync(string text, string sourceLang, string targetLang, CancellationToken cancellationToken = default);
    Task<List<TranslationResult>> TranslateBatchAsync(List<string> texts, string sourceLang, string targetLang, CancellationToken cancellationToken = default);
}

public class TranslationResult
{
    public string OriginalText { get; set; } = string.Empty;
    public string TranslatedText { get; set; } = string.Empty;
    public string SourceLanguage { get; set; } = string.Empty;
    public string TargetLanguage { get; set; } = string.Empty;
}
