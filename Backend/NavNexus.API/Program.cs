using FluentValidation;
using Microsoft.AspNetCore.Mvc;
using Serilog;
using NavNexus.Domain;
using NavNexus.Application;
using NavNexus.Infrastructure;
using NavNexus.API;
using NavNexus.API.Middleware;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// =========================
// Serilog
// =========================
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .CreateLogger();
builder.Host.UseSerilog();

// =========================
// Services
// =========================
builder.Services.AddDomain();
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);
builder.Services.AddApi();

// FluentValidation
builder.Services.AddValidatorsFromAssembly(typeof(Program).Assembly);

// Controllers
builder.Services.AddControllers();

builder.Services.Configure<ApiBehaviorOptions>(options =>
{
    options.SuppressModelStateInvalidFilter = true;
});
// =========================
// Build app
// =========================
var app = builder.Build();

// =========================
// Middleware pipeline
// =========================

// HTTPS redirect (must be early, before Swagger)
app.UseHttpsRedirection();

// Swagger (after HTTPS redirect)
{
    app.UseSwagger(c =>
    {
        c.SerializeAsV2 = false; // Use OpenAPI 3.0
    });
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "NavNexus API v1");
        c.RoutePrefix = "swagger"; // /swagger
        c.DocExpansion(Swashbuckle.AspNetCore.SwaggerUI.DocExpansion.None);
    });
}

// Exception handling
app.UseExceptionHandling();

// CORS
app.UseCors("AllowAll");

// Auth
app.UseAuthentication();
app.UseAuthorization();

// Controllers
app.MapControllers();

app.Run();

public partial class Program { }
