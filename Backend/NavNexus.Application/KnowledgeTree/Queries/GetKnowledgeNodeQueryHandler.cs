using ErrorOr;
using MediatR;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.KnowledgeTree.Results;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.KnowledgeTree.Queries
{
    public class GetKnowledgeNodeQueryHandler : IRequestHandler<GetKnowledgeNodeQuery, ErrorOr<GetRootKnowledgeNodeResult>>
    {
        private readonly IKnowledgetreeRepository _knowledgeTreeRepository;

        public GetKnowledgeNodeQueryHandler(IKnowledgetreeRepository knowledgeTreeRepository)
        {
            _knowledgeTreeRepository = knowledgeTreeRepository;
        }

        public async Task<ErrorOr<GetRootKnowledgeNodeResult>> Handle(GetKnowledgeNodeQuery request, CancellationToken cancellationToken)
        {
            var workspaceId = request.WorkspaceId;
            List<KnowledgeNode> nodes = await _knowledgeTreeRepository.GetAllRootNodesByWorkspaceIdAsync(workspaceId, cancellationToken);
            if (nodes == null || nodes.Count == 0)
            {
                return Error.NotFound(
                    code: "ROOT_KNOWLEDGE_NODE_NOT_FOUND",
                    description: $"Root knowledge node not found for Workspace ID: {workspaceId}"
                );
            }
            
            int totalNode = nodes.Count;

            var result = new GetRootKnowledgeNodeResult
            {
                TotalNodes = totalNode,
                RootNode = nodes.Select(node => new GetKnowledgeNodeResult(
                    id: node.Id,
                    type: node.Type,
                    name: node.Name,
                    synthesis: node.Synthesis,
                    workspaceId: node.WorkspaceId,
                    level: node.Level,
                    sourceCount: node.SourceCount,
                    evidences: node.Evidences,
                    createdAt: node.CreatedAt,
                    updatedAt: node.UpdatedAt,
                    childNodes: node.Children,
                    gapSuggestions: node.IsLeafNode() ? node.GapSuggestions : null
                )).ToList()
            };

            return result;
        }
    }
}
