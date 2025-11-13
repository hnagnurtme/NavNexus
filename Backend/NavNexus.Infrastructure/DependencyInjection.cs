using Microsoft.Extensions.DependencyInjection;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Infrastructure.Services;

namespace NavNexus.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services)
    {
        services.AddSingleton<IFirebaseService, FirebaseService>();
        
        // File and storage services
        services.AddSingleton<IFileStorageService, FileStorageService>();
        services.AddSingleton<IFirestoreService, FirestoreMetadataService>();
        
        // Database services
        services.AddSingleton<INeo4jService, Neo4jGraphService>();
        services.AddSingleton<IQdrantService, QdrantVectorService>();
        
        // AI services
        services.AddSingleton<ILlmService, LlmExtractionService>();
        services.AddSingleton<ITranslationService, PapagoTranslationService>();

        return services;
    }
}
