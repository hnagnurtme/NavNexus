using NavNexus.API.Contract.KnowledgeTree;
using NavNexus.Domain.Entities;

namespace NavNexus.API.Contract.KnowledgeTree;

public class GetRootKnowledgeResponse
{
    public int TotalNodes { get; set; }
    public required List<GetKnowledgeNodeResponse> RootNode { get; set; }
}