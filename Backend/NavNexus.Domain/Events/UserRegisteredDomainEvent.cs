using MediatR;
namespace NavNexus.Domain.Common.Events;

public record UserRegisteredDomainEvent(String UserId, string Email) 
    : IDomainEvent, INotification
{
    public DateTime OccurredOn { get; } = DateTime.UtcNow;
}
