using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.IdentityModel.Tokens;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Common.Interfaces.Events;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Infrastructure.Events;
using NavNexus.Infrastructure.ExternalServices;
using NavNexus.Infrastructure.Identity;
using NavNexus.Infrastructure.Persistence;
using NavNexus.Infrastructure.Persistence.Repositories;
using NavNexus.Infrastructure.Security;

namespace NavNexus.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        AddNeo4j(services, configuration);
        AddFirebase(services, configuration);
        AddRepositories(services);
        AddDomainEvents(services);
        AddExternalServices(services);
        AddSecurityServices(services, configuration);

        return services;
    }

    // -------------------------
    // Neo4j
    // -------------------------
    private static void AddNeo4j(IServiceCollection services, IConfiguration configuration)
    {
        var neo4jUri = configuration["Neo4j:Uri"] ?? "bolt://localhost:7687";
        var neo4jUsername = configuration["Neo4j:Username"] ?? "neo4j";
        var neo4jPassword = configuration["Neo4j:Password"] ?? "password123";

        services.AddSingleton(sp => new Neo4jConnection(neo4jUri, neo4jUsername, neo4jPassword));

        // Shared IAsyncSession per request
        services.AddScoped(sp =>
        {
            var conn = sp.GetRequiredService<Neo4jConnection>();
            return conn.GetAsyncSession();
        });
    }

    private static void AddFirebase(IServiceCollection services, IConfiguration configuration)
{
    var projectId = configuration["Firebase:ProjectId"];
    // Tên biến của bạn là privateKeyPath, hoàn toàn ổn
    var privateKeyPath = configuration["Firebase:PrivateKeyPath"]; 

    if (string.IsNullOrWhiteSpace(projectId))
        throw new ArgumentNullException(nameof(projectId), "Firebase:ProjectId is not configured.");
    if (string.IsNullOrWhiteSpace(privateKeyPath))
        throw new ArgumentNullException(nameof(privateKeyPath), "Firebase:PrivateKeyPath is not configured.");

    // 1. Đăng ký FirebaseConnection như một Singleton
    //    (Giống như bạn đã làm - BƯỚC NÀY ĐÚNG)
    services.AddSingleton(new FirebaseConnection(projectId, privateKeyPath));

    // 2. ĐĂNG KÝ THÊM: Đăng ký FirestoreDb như một Singleton,
    //    sử dụng factory để lấy nó từ FirebaseConnection đã đăng ký ở trên.
    services.AddSingleton(sp =>
    {
        // Lấy dịch vụ FirebaseConnection đã đăng ký
        var firebaseConnection = sp.GetRequiredService<FirebaseConnection>();
        
        // Trả về đối tượng FirestoreDb
        return firebaseConnection.GetFirestore();
    });
}
    // -------------------------
    // Repositories
    // -------------------------
    private static void AddRepositories(IServiceCollection services)
    {
        
        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<ITokenRepository, TokenRepository>();
    }



    // -------------------------
    // Domain events
    // -------------------------
    private static void AddDomainEvents(IServiceCollection services)
    {
        services.AddScoped<IDomainEventDispatcher, DomainEventDispatcher>();
    }

    // -------------------------
    // External / Utility services
    // -------------------------
    private static void AddExternalServices(IServiceCollection services)
    {
        services.AddScoped<IEmailSender, EmailSenderService>();
        // External API Services
        services.AddHttpClient<INaverObjectStorageService, NaverObjectStorageService>();
        services.AddHttpClient<IClovaNlpService, ClovaNlpService>();
        services.AddHttpClient<IPapagoTranslationService, PapagoTranslationService>();
        services.AddHttpClient<IQdrantService, QdrantService>();
        services.AddHttpClient<ILlmService, LlmService>();
    }

    // -------------------------
    // Security / Authentication
    // -------------------------
    private static void AddSecurityServices(IServiceCollection services, IConfiguration configuration)
    {
        var privatePemPath = configuration["Jwt:PrivateKeyPath"];
        var publicPemPath = configuration["Jwt:PublicKeyPath"];
        var keyId = configuration["Jwt:KeyId"];

        if (string.IsNullOrWhiteSpace(privatePemPath))
            throw new ArgumentNullException(nameof(privatePemPath), "Jwt:PrivateKeyPath is not configured.");
        if (string.IsNullOrWhiteSpace(publicPemPath))
            throw new ArgumentNullException(nameof(publicPemPath), "Jwt:PublicKeyPath is not configured.");
        if (string.IsNullOrWhiteSpace(keyId))
            throw new ArgumentNullException(nameof(keyId), "Jwt:KeyId is not configured.");

        var rsaKeyStore = new RsaKeyStore(privatePemPath, publicPemPath, keyId);
        services.AddSingleton<IRsaKeyStore>(rsaKeyStore);

        services.AddScoped<IHashService, BCryptHashService>();
        services.AddScoped<IJwtService, JwtService>();
        services.AddScoped<IJwksProvider, JwksProvider>();
        services.AddScoped<IRefreshTokenGenerator, RefreshTokenGenerator>();
        services.AddHttpContextAccessor();
        services.AddScoped<ICurrentUserService, CurrentUserService>();

        var issuer = configuration["Jwt:Issuer"] ?? "NavNexus";
        var audience = configuration["Jwt:Audience"] ?? "NavNexusClients";

        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer = true,
                    ValidIssuer = issuer,
                    ValidateAudience = true,
                    ValidAudience = audience,
                    ValidateLifetime = true,
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = rsaKeyStore.GetPublicKey()
                };
                options.RequireHttpsMetadata = false; // production: true
            });
    }
}
