using NavNexus.Domain.Common.Events;
using NavNexus.Domain.Common.Enums;

namespace NavNexus.Domain.Events;

public record RelationshipCreatedDomainEvent(
    Guid RelationshipId, 
    Guid SourceNodeId, 
    Guid TargetNodeId, 
    RelationshipType Type) : IDomainEvent;
