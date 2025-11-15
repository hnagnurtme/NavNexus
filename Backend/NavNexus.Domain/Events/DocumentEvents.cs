using NavNexus.Domain.Common.Events;

namespace NavNexus.Domain.Events;

public record DocumentUploadedDomainEvent(Guid DocumentId, Guid UserId, Guid WorkspaceId) : IDomainEvent;

public record DocumentProcessedDomainEvent(Guid DocumentId) : IDomainEvent;
