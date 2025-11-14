namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for generating embeddings for text
/// Interface for vector database service (e.g., Qdrant)
/// </summary>
public interface IEmbeddingService
{
    Task<float[]> GenerateEmbeddingAsync(string text, CancellationToken cancellationToken = default);

    Task<List<float[]>> GenerateBatchEmbeddingsAsync(List<string> texts, CancellationToken cancellationToken = default);

    Task<List<(Guid Id, double Score)>> SearchSimilarAsync(
        float[] queryEmbedding, 
        int topK = 10, 
        CancellationToken cancellationToken = default);
}
