using Microsoft.Extensions.Configuration;
using NavNexus.Application.Common.Interfaces.ExternalServices;

namespace NavNexus.Infrastructure.ExternalServices;

public class ClovaNlpService : IClovaNlpService
{
    private readonly IConfiguration _configuration;
    private readonly HttpClient _httpClient;

    public ClovaNlpService(IConfiguration configuration, HttpClient httpClient)
    {
        _configuration = configuration;
        _httpClient = httpClient;
    }

    public async Task<ClovaTextExtractionResult> ExtractTextAsync(string documentUrl, CancellationToken cancellationToken = default)
    {
        // TODO: Implement actual Clova OCR API call
        // This is a stub implementation
        await Task.Delay(500, cancellationToken);
        
        return new ClovaTextExtractionResult
        {
            Text = "Sample extracted text from document",
            PageCount = 1,
            Pages = new List<ClovaPage>
            {
                new ClovaPage { PageNumber = 1, Text = "Sample extracted text from document" }
            }
        };
    }

    public async Task<ClovaEntityExtractionResult> ExtractEntitiesAsync(string text, CancellationToken cancellationToken = default)
    {
        // TODO: Implement actual Clova NER API call
        await Task.Delay(300, cancellationToken);
        
        return new ClovaEntityExtractionResult
        {
            Entities = new List<ClovaEntity>()
        };
    }
}
