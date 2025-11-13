using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.Interfaces;

/// <summary>
/// Service for Qdrant vector database operations
/// </summary>
public interface IQdrantService
{
    /// <summary>
    /// Creates a collection for a workspace if it doesn't exist
    /// </summary>
    Task EnsureCollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Stores vector chunks in Qdrant
    /// </summary>
    Task<List<string>> UpsertChunksAsync(string collectionName, List<QdrantChunkPayload> chunks, List<float[]> vectors, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Searches for similar chunks (context retrieval)
    /// </summary>
    Task<List<QdrantChunkPayload>> SearchSimilarChunksAsync(string collectionName, float[] queryVector, int limit = 5, CancellationToken cancellationToken = default);
    
    /// <summary>
    /// Generates embedding vector from text
    /// </summary>
    Task<float[]> GenerateEmbeddingAsync(string text, CancellationToken cancellationToken = default);
}
