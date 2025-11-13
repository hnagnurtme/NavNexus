# ============================
# 🧱 STAGE 1: BUILD
# ============================
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy solution file
COPY NavNexus.sln ./

# Copy project files for dependency restoration (layer caching)
COPY NavNexus.API/NavNexus.API.csproj ./NavNexus.API/
COPY NavNexus.Domain/NavNexus.Domain.csproj ./NavNexus.Domain/
COPY NavNexus.Application/NavNexus.Application.csproj ./NavNexus.Application/
COPY NavNexus.Infrastructure/NavNexus.Infrastructure.csproj ./NavNexus.Infrastructure/

# Restore dependencies (cached layer)
RUN dotnet restore NavNexus.API/NavNexus.API.csproj

# Copy all source code
COPY NavNexus.API ./NavNexus.API
COPY NavNexus.Domain ./NavNexus.Domain
COPY NavNexus.Application ./NavNexus.Application
COPY NavNexus.Infrastructure ./NavNexus.Infrastructure

# Build and publish
WORKDIR /src/NavNexus.API
RUN dotnet publish -c Release -o /app/publish \
    --no-restore \
    /p:UseAppHost=false

# ============================
# 🚀 STAGE 2: RUNTIME
# ============================
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime
WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1000 appuser && \
    adduser -u 1000 -G appuser -s /bin/sh -D appuser

# Copy publish output from build stage
COPY --from=build --chown=appuser:appuser /app/publish .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

# Set environment for production
ENV ASPNETCORE_URLS=http://+:8080 \
    ASPNETCORE_ENVIRONMENT=Production

# Run application
ENTRYPOINT ["dotnet", "NavNexus.API.dll"]
