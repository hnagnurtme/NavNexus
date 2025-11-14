using NavNexus.Domain.Common.Events;

namespace NavNexus.Domain.Events;

public record WorkspaceCreatedDomainEvent(Guid WorkspaceId, Guid OwnerId) : IDomainEvent;
