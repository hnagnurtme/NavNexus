using NavNexus.Domain.Common.Events;

namespace NavNexus.Application.Common.Interfaces.Events;

public interface IDomainEventDispatcher
{
    Task DispatchEventsAsync(IEnumerable<IDomainEvent> domainEvents, CancellationToken cancellationToken = default);
}
