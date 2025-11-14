using MediatR;
namespace NavNexus.Domain.Common.Events;

public record UserRegisteredDomainEvent(Guid UserId, string Email) 
    : IDomainEvent, INotification
{
    public DateTime OccurredOn { get; } = DateTime.UtcNow;
}
