using NavNexus.Domain.Common.Enums;

namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for translating text between languages
/// Interface for external translation service (e.g., Naver Cloud Translation API)
/// </summary>
public interface ITranslationService
{
    Task<string> TranslateAsync(
        string text, 
        LanguageCode sourceLanguage, 
        LanguageCode targetLanguage, 
        CancellationToken cancellationToken = default);

    Task<Dictionary<LanguageCode, string>> TranslateToMultipleAsync(
        string text, 
        LanguageCode sourceLanguage, 
        List<LanguageCode> targetLanguages, 
        CancellationToken cancellationToken = default);

    Task<LanguageCode> DetectLanguageAsync(string text, CancellationToken cancellationToken = default);
}
