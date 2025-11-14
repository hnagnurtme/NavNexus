namespace NavNexus.Application.Common.Interfaces.ExternalServices;

public interface IQdrantService
{
    Task<string> CreateVectorAsync(Guid evidenceId, float[] embedding, Dictionary<string, object> metadata, CancellationToken cancellationToken = default);
    Task<List<SimilarEvidence>> SearchSimilarAsync(float[] queryEmbedding, int limit = 10, float threshold = 0.7f, CancellationToken cancellationToken = default);
    Task<bool> DeleteVectorAsync(string vectorId, CancellationToken cancellationToken = default);
    Task<float[]> GenerateEmbeddingAsync(string text, CancellationToken cancellationToken = default);
}

public class SimilarEvidence
{
    public Guid EvidenceId { get; set; }
    public float Score { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
}
