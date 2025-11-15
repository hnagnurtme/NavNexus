using ErrorOr;
using MediatR;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.KnowledgeTree.Results;
using NavNexus.Domain.Entities;

namespace NavNexus.Application.KnowledgeTree.Queries
{
    public class GetKnowledgeNodeQueryHandler : IRequestHandler<GetKnowledgeNodeQuery, ErrorOr<GetKnowledgeNodeResult>>
    {
        private readonly IKnowledgetreeRepository _knowledgeTreeRepository;

        public GetKnowledgeNodeQueryHandler(IKnowledgetreeRepository knowledgeTreeRepository)
        {
            _knowledgeTreeRepository = knowledgeTreeRepository;
        }

        public async Task<ErrorOr<GetKnowledgeNodeResult>> Handle(GetKnowledgeNodeQuery request, CancellationToken cancellationToken)
        {
            // 1. Lấy node từ repository
            KnowledgeNode? node;

            if (string.IsNullOrEmpty(request.NodeId))
            {
                node = await _knowledgeTreeRepository.GetRootNodeByWorkspaceIdAsync(request.WorkspaceId, cancellationToken);
                if (node == null)
                    return Error.NotFound("KnowledgeNode.NotFound", $"Root node for workspace '{request.WorkspaceId}' not found.");
            }
            else
            {
                node = await _knowledgeTreeRepository.GetNodeByIdAsync(request.NodeId, cancellationToken);
                if (node == null)
                    return Error.NotFound("KnowledgeNode.NotFound", $"Knowledge node with ID '{request.NodeId}' not found.");
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
