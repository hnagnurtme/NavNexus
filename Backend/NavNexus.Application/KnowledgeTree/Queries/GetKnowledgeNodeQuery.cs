using MediatR;
using NavNexus.Application.KnowledgeTree.Results;
using ErrorOr;

namespace NavNexus.Application.KnowledgeTree.Queries;

public record GetKnowledgeNodeQuery(
    string WorkspaceId
) : IRequest<ErrorOr<GetRootKnowledgeNodeResult>>;