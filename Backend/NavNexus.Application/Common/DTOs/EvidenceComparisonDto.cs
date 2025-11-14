using NavNexus.Domain.Entities;

namespace NavNexus.Application.Common.DTOs;

/// <summary>
/// Result of comparing two evidence items
/// </summary>
public class EvidenceComparisonResult
{
    public Guid Evidence1Id { get; set; }
    public Guid Evidence2Id { get; set; }
    public double SimilarityScore { get; set; }
    public List<string> Similarities { get; set; } = new();
    public List<string> Differences { get; set; } = new();
    public List<string> KeyTerms { get; set; } = new();
    public string Synthesis { get; set; } = string.Empty;
    public DateTime ComparedAt { get; set; }
}

/// <summary>
/// Request to compare two evidence items
/// </summary>
public class CompareEvidenceRequest
{
    public Guid Evidence1Id { get; set; }
    public Guid Evidence2Id { get; set; }
    public string? TargetLanguage { get; set; }
}

/// <summary>
/// Batch comparison request
/// </summary>
public class BatchCompareRequest
{
    public List<Guid> EvidenceIds { get; set; } = new();
    public int TopN { get; set; } = 5;
    public double MinimumSimilarity { get; set; } = 0.7;
}

/// <summary>
/// Result of batch comparison
/// </summary>
public class BatchComparisonResult
{
    public List<EvidenceComparisonResult> Comparisons { get; set; } = new();
    public int TotalComparisons { get; set; }
    public DateTime CompletedAt { get; set; }
}
