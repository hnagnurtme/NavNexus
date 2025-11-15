namespace NavNexus.Domain.Entities;

public class GapSuggestion
{
    public string Id { get; set; }               // unique ID
    public string SuggestionText { get; set; }  // mô tả gợi ý
    public string TargetNodeId { get; set; }    // node cần nối
    public string TargetFileId { get; set; }    // file cần nối
    public float SimilarityScore { get; set; }  // từ Qdrant/LLM

    public GapSuggestion()
    {
        Id = Guid.NewGuid().ToString();
        SuggestionText = string.Empty;
        TargetNodeId = string.Empty;
        TargetFileId = string.Empty;
        SimilarityScore = 0.0f;
    }

}