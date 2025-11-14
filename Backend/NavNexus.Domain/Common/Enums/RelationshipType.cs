namespace NavNexus.Domain.Common.Enums;

/// <summary>
/// Represents the type of relationship between knowledge graph nodes
/// </summary>
public enum RelationshipType
{
    /// <summary>
    /// Hierarchical relationship - parent-child structure
    /// </summary>
    Hierarchy,

    /// <summary>
    /// Similarity relationship - semantically similar nodes
    /// </summary>
    Similarity,

    /// <summary>
    /// Causal relationship - cause and effect
    /// </summary>
    Causality,

    /// <summary>
    /// Temporal relationship - time-based sequence
    /// </summary>
    Temporal,

    /// <summary>
    /// Reference relationship - citations or cross-references
    /// </summary>
    Reference,

    /// <summary>
    /// Contradiction relationship - conflicting information
    /// </summary>
    Contradiction,

    /// <summary>
    /// Support relationship - evidence supporting a claim
    /// </summary>
    Support,

    /// <summary>
    /// Derivation relationship - derived or inferred from
    /// </summary>
    Derivation,

    /// <summary>
    /// Association relationship - general association
    /// </summary>
    Association
}
