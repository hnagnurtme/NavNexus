# ============================
# 🧱 STAGE 1: BUILD
# ============================
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy toàn bộ source code
COPY NavNexus.API ./NavNexus.API
COPY NavNexus.Domain ./NavNexus.Domain
COPY NavNexus.Application ./NavNexus.Application
COPY NavNexus.Infrastructure ./NavNexus.Infrastructure

# Restore dependencies
WORKDIR /src/NavNexus.API
RUN dotnet restore

# Build project
RUN dotnet publish -c Release -o /app/publish

# ============================
# 🚀 STAGE 2: RUNTIME
# ============================
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runtime
WORKDIR /app

# Copy publish output từ stage build
COPY --from=build /app/publish .

# Use environment variable PORT if available (Render, Heroku)
ENV ASPNETCORE_URLS=http://*:${PORT:-8080}
EXPOSE ${PORT:-8080}

# Chạy ứng dụng
ENTRYPOINT ["dotnet", "NavNexus.API.dll"]
