using MediatR;
using NavNexus.Application.KnowledgeTree.Results;
using ErrorOr;

namespace NavNexus.Application.KnowledgeTree.Commands;

public record CreateKnowledgeNodeCommand(
    string WorkspaceId,
    List<string> FilePaths
) : IRequest<ErrorOr<RabbitMqSendingResult>>;

