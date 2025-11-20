using System.Security.Policy;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.KnowledgeTree.Results;


public class GetRootKnowledgeNodeResult
{
    public int TotalNodes { get; set; }
    public required List<GetKnowledgeNodeResult> RootNode { get; set; }
}