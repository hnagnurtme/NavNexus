using NavNexus.Domain.Common.Events;
using NavNexus.Domain.Common.Enums;

namespace NavNexus.Domain.Events;

public record KnowledgeNodeCreatedDomainEvent(Guid NodeId, Guid WorkspaceId, NodeType Type) : IDomainEvent;
