using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;
using NavNexus.Application.Common.Interfaces;
using NavNexus.Application.Common.Interfaces.Events;
using NavNexus.Application.Common.Interfaces.ExternalServices;
using NavNexus.Application.Common.Interfaces.Repositories;
using NavNexus.Application.Common.Interfaces.Security;
using NavNexus.Infrastructure.Events;
using NavNexus.Infrastructure.ExternalServices;
using NavNexus.Infrastructure.HealthChecks;
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
        AddExternalServices(services, configuration); // Thêm configuration parameter
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

    // -------------------------
    // Firebase
    // -------------------------
    private static void AddFirebase(IServiceCollection services, IConfiguration configuration)
    {
        var projectId = configuration["Firebase:ProjectId"];
        var privateKeyPath = configuration["Firebase:PrivateKeyPath"];
        var databaseUrl = configuration["Firebase:DatabaseUrl"];

        if (string.IsNullOrWhiteSpace(projectId))
            throw new ArgumentNullException(nameof(projectId), "Firebase:ProjectId is not configured.");
        if (string.IsNullOrWhiteSpace(privateKeyPath))
            throw new ArgumentNullException(nameof(privateKeyPath), "Firebase:PrivateKeyPath is not configured.");
        if (string.IsNullOrWhiteSpace(databaseUrl))
            throw new ArgumentNullException(nameof(databaseUrl), "Firebase:DatabaseUrl is not configured.");

        // 1. Đăng ký FirebaseConnection như một Singleton
        services.AddSingleton(new FirebaseConnection(projectId, privateKeyPath, databaseUrl));

        // 2. Đăng ký FirestoreDb như một Singleton
        services.AddSingleton(sp =>
        {
            var firebaseConnection = sp.GetRequiredService<FirebaseConnection>();
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
        services.AddScoped<IKnowledgetreeRepository, KnowledgeTreeRepository>();
        services.AddScoped<IJobRepository>(sp =>
        {
            var firebaseConnection = sp.GetRequiredService<FirebaseConnection>();
            var databaseUrl = firebaseConnection.GetDatabaseUrl();
            var privateKeyPath = sp.GetRequiredService<IConfiguration>()["Firebase:PrivateKeyPath"] ?? "";
            return new JobRepository(databaseUrl, privateKeyPath);
        });
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
    private static void AddExternalServices(IServiceCollection services, IConfiguration configuration)
    {
        services.AddScoped<IEmailSender, EmailSenderService>();
        
        // External API Services
        services.AddHttpClient<INaverObjectStorageService, NaverObjectStorageService>();
        services.AddHttpClient<IClovaNlpService, ClovaNlpService>();
        services.AddHttpClient<IPapagoTranslationService, PapagoTranslationService>();
        services.AddHttpClient<IQdrantService, QdrantService>();

        services.Configure<HyperClovaSettings>(configuration.GetSection("HyperClova"));
        services.AddHttpClient<ILlmService, HyperClovaService>();

        // Gap Suggestion Service
        services.AddScoped<IGapSuggestionService, GapSuggestionService>();

        // RabbitMQ Service với error handling
        AddRabbitMq(services, configuration);
    }

    // -------------------------
    // RabbitMQ
    // -------------------------
    private static void AddRabbitMq(IServiceCollection services, IConfiguration configuration)
    {
        // Validate RabbitMQ configuration
        var host = "chameleon-01.lmq.cloudamqp.com";
        var username = "odgfvgev:odgfvgev";
        var password = "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg";

        if (string.IsNullOrWhiteSpace(host))
        {
            throw new InvalidOperationException(
                "RabbitMQ:Host is not configured. Please check your appsettings.json");
        }

        if (string.IsNullOrWhiteSpace(username))
        {
            throw new InvalidOperationException(
                "RabbitMQ:Username is not configured. Please check your appsettings.json");
        }

        if (string.IsNullOrWhiteSpace(password))
        {
            throw new InvalidOperationException(
                "RabbitMQ:Password is not configured. Please check your appsettings.json");
        }

        // Register RabbitMQ service as Singleton with retry logic
        services.AddSingleton<IRabbitMQService>(sp =>
        {
            var logger = sp.GetRequiredService<ILogger<RabbitMqService>>();
            var maxRetries = 3;
            var retryDelay = TimeSpan.FromSeconds(2);

            for (int attempt = 1; attempt <= maxRetries; attempt++)
            {
                try
                {
                    logger.LogInformation(
                        "Attempting to initialize RabbitMQ service (Attempt {Attempt}/{MaxRetries})", 
                        attempt, maxRetries);

                    var service = new RabbitMqService(configuration, logger);
                    
                    logger.LogInformation("RabbitMQ service initialized successfully");
                    return service;
                }
                catch (Exception ex) when (attempt < maxRetries)
                {
                    logger.LogWarning(ex, 
                        "Failed to initialize RabbitMQ service on attempt {Attempt}/{MaxRetries}. Retrying in {Delay} seconds...", 
                        attempt, maxRetries, retryDelay.TotalSeconds);
                    
                    Thread.Sleep(retryDelay);
                }
                catch (Exception ex)
                {
                    logger.LogError(ex, 
                        "Failed to initialize RabbitMQ service after {MaxRetries} attempts. " +
                        "Please check: 1) RabbitMQ configuration in appsettings.json, " +
                        "2) Network connectivity to {Host}, " +
                        "3) RabbitMQ credentials are correct", 
                        maxRetries, host);
                    
                    throw new InvalidOperationException(
                        $"Failed to connect to RabbitMQ after {maxRetries} attempts. " +
                        $"Host: {host}, Username: {username}. " +
                        $"Please check the logs for more details.", ex);
                }
            }

            // This should never be reached, but needed for compilation
            throw new InvalidOperationException("Failed to initialize RabbitMQ service");
        });

        // Register health check for RabbitMQ (optional but recommended)
        services.AddHealthChecks()
            .AddCheck<RabbitMqHealthCheck>("rabbitmq", tags: new[] { "ready", "messaging" });
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