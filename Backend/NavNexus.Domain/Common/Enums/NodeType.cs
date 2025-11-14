namespace NavNexus.Domain.Common.Enums;

/// <summary>
/// Represents the type of a knowledge graph node
/// </summary>
public enum NodeType
{
    /// <summary>
    /// Document node representing research papers or source materials
    /// </summary>
    Document,

    /// <summary>
    /// Topic node representing main themes or subjects
    /// </summary>
    Topic,

    /// <summary>
    /// Evidence node representing extracted knowledge chunks
    /// </summary>
    Evidence,

    /// <summary>
    /// Gap node representing identified knowledge gaps
    /// </summary>
    Gap,

    /// <summary>
    /// Concept node representing abstract ideas or theories
    /// </summary>
    Concept,

    /// <summary>
    /// Entity node representing real-world entities (people, places, organizations)
    /// </summary>
    Entity
}
