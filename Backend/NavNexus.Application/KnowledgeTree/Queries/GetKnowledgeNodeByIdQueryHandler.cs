using ErrorOr;
using MediatR;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.KnowledgeTree.Results;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.KnowledgeTree.Queries
{
    public class GetKnowledgeNodeByIdQueryHandler : IRequestHandler<GetKnowledgeNodeByIdQuery, ErrorOr<GetKnowledgeNodeResult>>
    {
        private readonly IKnowledgetreeRepository _knowledgeTreeRepository;

        public GetKnowledgeNodeByIdQueryHandler(IKnowledgetreeRepository knowledgeTreeRepository)
        {
            _knowledgeTreeRepository = knowledgeTreeRepository;
        }

        public async Task<ErrorOr<GetKnowledgeNodeResult>> Handle(GetKnowledgeNodeByIdQuery request, CancellationToken cancellationToken)
        {
            var nodeId = request.NodeId;
            var node = await _knowledgeTreeRepository.GetNodeByIdAsync(nodeId);
            if (node == null)
            {
                return Error.NotFound(
                    code: "KNOWLEDGE_NODE_NOT_FOUND",
                    description: $"Knowledge node not found with ID: {nodeId}"
                );
            }


            var result = new GetKnowledgeNodeResult(
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
            );

            return result;
        }
    }
}
