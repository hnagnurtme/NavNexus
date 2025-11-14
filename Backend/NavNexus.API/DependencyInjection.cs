using AutoMapper;
using Microsoft.AspNetCore.Mvc;
using Microsoft.OpenApi.Models;
using NavNexus.API.Filter;

namespace NavNexus.API;

public static class DependencyInjection
{
    // ============================
    // Main API registration
    // ============================
    public static IServiceCollection AddApi(this IServiceCollection services)
    {
        services.AddApiControllers();
        services.AddApiSwagger();
        services.AddApiCors();
        services.AddApiMappings();
        return services;
    }

    // ============================
    // Controllers + Validation
    // ============================
    private static IServiceCollection AddApiControllers(this IServiceCollection services)
    {
        services.AddControllers(options =>
        {
            options.Filters.Add<ValidationFilter>();
        })
        .ConfigureApiBehaviorOptions(options =>
        {
            options.SuppressModelStateInvalidFilter = true;
            options.InvalidModelStateResponseFactory = CreateValidationErrorResponse;
        });

        return services;
    }

    private static IActionResult CreateValidationErrorResponse(ActionContext context)
    {
        var errors = context.ModelState
            .SelectMany(x => x.Value?.Errors ?? Enumerable.Empty<Microsoft.AspNetCore.Mvc.ModelBinding.ModelError>())
            .Select(x => new
            {
                ErrorCode = "VALIDATION_ERROR",
                Message = x.ErrorMessage
            })
            .ToList();

        var response = new NavNexus.API.Common.ApiResponse<object>
        {
            Success = false,
            Message = errors.FirstOrDefault()?.Message ?? "Validation error",
            StatusCode = 400,
            Data = null,
            Meta = null,
            ErrorCode = errors.FirstOrDefault()?.ErrorCode ?? "VALIDATION_ERROR"
        };

        return new ObjectResult(response) { StatusCode = 400 };
    }

    // ============================
    // Swagger
    // ============================
    private static IServiceCollection AddApiSwagger(this IServiceCollection services)
    {
        services.AddEndpointsApiExplorer();
        services.AddSwaggerGen(c =>
        {

            c.SwaggerDoc("v1", new OpenApiInfo
            {
                Title = "NavNexus API",
                Version = "v1",
                Description = "NavNexus is a robust platform for event ticket management, providing secure authentication, user management, and seamless event operations. This API enables integration with NavNexus's core features, supporting both internal and third-party applications.",
                TermsOfService = new Uri("https://NavNexus.com/terms"),
                Contact = new OpenApiContact
                {
                    Name = "NavNexus Support",
                    Email = "support@NavNexus.com",
                    Url = new Uri("https://NavNexus.com/contact")
                },
                License = new OpenApiLicense
                {
                    Name = "MIT License",
                    Url = new Uri("https://opensource.org/licenses/MIT")
                }
            });

            c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
            {
                Name = "Authorization",
                Type = SecuritySchemeType.ApiKey,
                Scheme = "Bearer",
                BearerFormat = "JWT",
                In = ParameterLocation.Header,
                Description = "Nhập 'Bearer {token}'"
            });

            c.AddSecurityRequirement(new OpenApiSecurityRequirement
            {
                {
                    new OpenApiSecurityScheme
                    {
                        Reference = new OpenApiReference
                        {
                            Type = ReferenceType.SecurityScheme,
                            Id = "Bearer"
                        }
                    },
                    Array.Empty<string>()
                }
            });

            c.EnableAnnotations();
        });
        return services;
    }

    // ============================
    // CORS
    // ============================
    private static IServiceCollection AddApiCors(this IServiceCollection services)
    {
        services.AddCors(options =>
        {
            options.AddPolicy("AllowAll", builder =>
                builder.AllowAnyOrigin()
                       .AllowAnyMethod()
                       .AllowAnyHeader());
        });
        return services;
    }

    // ============================
    // AutoMapper
    // ============================
    private static IServiceCollection AddApiMappings(this IServiceCollection services)
    {
        services.AddAutoMapper(typeof(Program).Assembly);
        return services;
    }
}
