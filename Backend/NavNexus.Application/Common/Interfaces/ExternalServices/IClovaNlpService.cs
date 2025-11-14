namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface IClovaNlpService
{
    Task<ClovaTextExtractionResult> ExtractTextAsync(string documentUrl, CancellationToken cancellationToken = default);
    Task<ClovaEntityExtractionResult> ExtractEntitiesAsync(string text, CancellationToken cancellationToken = default);
}

public class ClovaTextExtractionResult
{
    public string Text { get; set; } = string.Empty;
    public int PageCount { get; set; }
    public List<ClovaPage> Pages { get; set; } = new();
}

public class ClovaPage
{
    public int PageNumber { get; set; }
    public string Text { get; set; } = string.Empty;
}

public class ClovaEntityExtractionResult
{
    public List<ClovaEntity> Entities { get; set; } = new();
}

public class ClovaEntity
{
    public string Text { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public int StartPosition { get; set; }
    public int EndPosition { get; set; }
    public float Confidence { get; set; }
}
