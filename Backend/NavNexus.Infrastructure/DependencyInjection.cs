using Microsoft.Extensions.DependencyInjection;
using NavNexus.Infrastructure.Services;

namespace NavNexus.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services)
    {
        services.AddSingleton<IFirebaseService, FirebaseService>();

        return services;
    }
}
