using MediatR;
using NavNexus.Application.KnowledgeTree.Results;
using ErrorOr;

namespace NavNexus.Application.KnowledgeTree.Queries;

public record GetKnowledgeNodeByIdQuery(
    string NodeId
) : IRequest<ErrorOr<GetKnowledgeNodeResult>>;