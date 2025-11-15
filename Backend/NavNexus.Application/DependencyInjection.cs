using FluentValidation;
using Microsoft.Extensions.DependencyInjection;
using System.Reflection;
using MediatR;
using NavNexus.Application.Common;

namespace NavNexus.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        // Đăng ký MediatR: scan toàn bộ assembly Application
        services.AddMediatR(cfg => 
            cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly()));

        // Đăng ký tất cả FluentValidation validators trong assembly này
        services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());

        // Thêm ValidationBehavior vào pipeline của MediatR
        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));

        return services;
    }
}
