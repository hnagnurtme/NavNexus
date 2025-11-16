using System.Security.Policy;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.KnowledgeTree.Results;

public class  GetKnowledgeNodeResult
{
    public  string Id { get; set; }
    public  string Type { get; set; }
    public  string Name { get; set; }
    
    public  string Synthesis { get; set; }

    public  string WorkspaceId { get; set; }
    public  int Level { get; set; }
    public  int SourceCount { get; set; }
    public  List<NavNexus.Domain.Entities.Evidence> Evidences { get; set; }
    public  DateTime CreatedAt { get; set; }
    public  DateTime UpdatedAt { get; set; }
    public  List<KnowledgeNode> ChildNodes{ get; set; }

    public List<GapSuggestion>? GapSuggestions { get; set; }


    public GetKnowledgeNodeResult(
    string id,
    string type,
    string name,
    string synthesis,
    string workspaceId,
    int level,
    int sourceCount,
    List<NavNexus.Domain.Entities.Evidence> evidences,
    DateTime createdAt,
    DateTime updatedAt,
    List<KnowledgeNode> childNodes,
    List<GapSuggestion>? gapSuggestions = null
)
{
    Id = id;
    Type = type;
    Name = name;
    Synthesis = synthesis;
    WorkspaceId = workspaceId;
    Level = level;
    SourceCount = sourceCount;
    Evidences = evidences;
    CreatedAt = createdAt;
    UpdatedAt = updatedAt;
    ChildNodes = childNodes;
    GapSuggestions = gapSuggestions;
}


}