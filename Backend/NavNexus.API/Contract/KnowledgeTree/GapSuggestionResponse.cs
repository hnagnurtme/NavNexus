namespace NavNexus.API.Contract.KnowledgeTree;
public class GapSuggestionResponse
{
    public required string Id { get; set; }               // unique ID
    public required string SuggestionText { get; set; }  // mô tả gợi ý
    public required string TargetNodeId { get; set; }    // node cần nối
    public required string TargetFileId { get; set; }    // file cần nối
    public required float SimilarityScore { get; set; }  // từ Qdrant/LLM
}