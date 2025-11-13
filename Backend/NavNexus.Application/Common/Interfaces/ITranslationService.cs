namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for translation operations (Papago API)
/// </summary>
public interface ITranslationService
{
    /// <summary>
    /// Detects the language of the text
    /// </summary>
    Task<string> DetectLanguageAsync(string text, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Translates text to target language
    /// </summary>
    Task<string> TranslateAsync(string text, string sourceLanguage, string targetLanguage, CancellationToken cancellationToken = default);
}
