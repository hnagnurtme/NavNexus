namespace NavNexus.API.Contract.KnowledgeTree
{
    public class EvidenceResponse
    {
        public required string EvidenceId { get; set; }          // Id
        public required string Content { get; set; }              // Text
        public required string SourceFileId { get; set; }         // SourceId
        public required string SourceName { get; set; }           // SourceName
        public required string ChunkId { get; set; }              // ChunkId
        public required int Page { get; set; }                    // Page
        public required float Confidence { get; set; }            // Confidence
        public required DateTime CreatedAt { get; set; }          // CreatedAt

        public required string Language { get; set; }             // Language
        public required string SourceLanguage { get; set; }       // SourceLanguage
        public required string HierarchyPath { get; set; }        // HierarchyPath

        public required List<string> Claims { get; set; }         // Concepts
        public required List<string> KeyClaims { get; set; }      // KeyClaims
        public required List<string> QuestionsRaised { get; set; } // QuestionsRaised

        public required float EvidenceStrength { get; set; }      // EvidenceStrength
    }
}
