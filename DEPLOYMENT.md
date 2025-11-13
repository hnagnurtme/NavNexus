# 🚀 NavNexus Deployment Guide

Complete guide for deploying NavNexus using Docker, Docker Compose, and CI/CD pipelines.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker Compose](#quick-start-with-docker-compose)
- [Environment Configuration](#environment-configuration)
- [Manual Docker Build](#manual-docker-build)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Platforms](#deployment-platforms)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software
- Docker Engine 24.0+ ([Install Docker](https://docs.docker.com/engine/install/))
- Docker Compose 2.0+ (included with Docker Desktop)
- Docker Buildx (for multi-arch builds)

### Required Credentials
Before deploying, you need to obtain API keys and credentials:

1. **Naver Cloud Platform**
   - [Object Storage (NOS)](https://console.ncloud.com/) - For document storage
   - [Papago API](https://developers.naver.com/) - For translation
   - [HyperCLOVA X](https://clovastudio.naver.com/) - For LLM processing

2. **Firebase**
   - [Firebase Console](https://console.firebase.google.com/) - For authentication

3. **JWT Secret**
   - Generate a secure random key (minimum 32 characters)
   - Command: `openssl rand -base64 32`

---

## 🚀 Quick Start with Docker Compose

### 1. Clone the Repository
```bash
git clone https://github.com/hnagnurtme/NavNexus.git
cd NavNexus
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

**Important:** Fill in all required values in `.env`. See [Environment Configuration](#environment-configuration) for details.

### 3. Start All Services
```bash
# Start all services (Frontend, Backend, Neo4j, Qdrant)
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ this will delete all data)
docker compose down -v
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474 (credentials in .env)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## ⚙️ Environment Configuration

### Required Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Neo4j Database
NEO4J_URL=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password

# Qdrant Vector Database
QDRANT_URL=http://qdrant:6333

# Naver Object Storage
NOS_KEY=your-nos-access-key
NOS_SECRET=your-nos-secret-key
NOS_ENDPOINT=https://kr.object.ncloudstorage.com
NOS_BUCKET=navnexus-documents

# Papago Translation
PAPAGO_CLIENT_ID=your-papago-client-id
PAPAGO_CLIENT_SECRET=your-papago-client-secret

# HyperCLOVA X LLM
LLM_API_KEY=your-hyperclova-api-key
LLM_API_URL=https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003

# Firebase
FIREBASE_PROJECT_ID=navnexus-demo
FIREBASE_CREDENTIALS=your-base64-encoded-credentials

# JWT
JWT_KEY=your-super-secret-jwt-key-minimum-32-characters
JWT_ISSUER=NavNexus
JWT_AUDIENCE=NavNexusUsers

# Frontend
VITE_API_BASE_URL=http://localhost:8080/api
```

### Environment-Specific Configurations

**Development:**
```bash
ASPNETCORE_ENVIRONMENT=Development
NODE_ENV=development
LOG_LEVEL=Debug
```

**Production:**
```bash
ASPNETCORE_ENVIRONMENT=Production
NODE_ENV=production
LOG_LEVEL=Information
```

---

## 🐳 Manual Docker Build

### Build Individual Services

**Backend:**
```bash
cd Backend
docker build -t navnexus-backend:latest .
docker run -p 8080:8080 --env-file ../.env navnexus-backend:latest
```

**Frontend:**
```bash
cd Frontend
docker build -t navnexus-frontend:latest .
docker run -p 3000:80 navnexus-frontend:latest
```

### Multi-Architecture Build (AMD64 + ARM64)

Use the provided `render.sh` script:

```bash
# Build and push both services
./render.sh latest all

# Build only backend
./render.sh latest backend

# Build only frontend
./render.sh latest frontend

# Build with custom version
./render.sh v1.0.0 all
```

**Script Requirements:**
- Docker Buildx enabled
- Docker Hub credentials configured
- Set `DOCKER_USERNAME` environment variable (default: trunganh0106)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The repository includes an automated CI/CD pipeline (`.github/workflows/deploy.yml`) that:

1. **Tests** - Runs backend and frontend tests
2. **Builds** - Creates multi-arch Docker images (amd64, arm64)
3. **Pushes** - Uploads images to Docker Hub
4. **Deploys** - Triggers deployment on merge to `main`
5. **Scans** - Performs security vulnerability scanning

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

```
DOCKER_USERNAME        - Docker Hub username
DOCKER_PASSWORD        - Docker Hub password/token
CODECOV_TOKEN         - (Optional) Codecov token for coverage
RENDER_BACKEND_DEPLOY_HOOK   - (Optional) Render.com deploy hook for backend
RENDER_FRONTEND_DEPLOY_HOOK  - (Optional) Render.com deploy hook for frontend
```

### Trigger Workflow

The workflow triggers automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

---

## 🌐 Deployment Platforms

### Render.com

**Backend Deployment:**
1. Create a new Web Service
2. Connect to your GitHub repository
3. Configure:
   - **Build Command:** `docker build -t navnexus-backend ./Backend`
   - **Start Command:** Auto-detected from Dockerfile
   - **Environment Variables:** Add all required variables from `.env.example`

**Frontend Deployment:**
1. Create a new Static Site or Web Service
2. Configure:
   - **Build Command:** `cd Frontend && npm ci && npm run build`
   - **Publish Directory:** `Frontend/dist`
   - **Environment Variables:** `VITE_API_BASE_URL`

### Docker Hub

Images are automatically pushed to Docker Hub:
- Backend: `trunganh0106/navnexus-backend:latest`
- Frontend: `trunganh0106/navnexus-frontend:latest`

### Self-Hosted / VPS

**Using Docker Compose:**
```bash
# On your server
git clone https://github.com/hnagnurtme/NavNexus.git
cd NavNexus
cp .env.example .env
# Edit .env with your credentials
nano .env

# Start services
docker compose up -d

# Setup nginx reverse proxy (recommended)
# See nginx configuration example below
```

**Nginx Reverse Proxy Example:**
```nginx
server {
    listen 80;
    server_name navnexus.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Monitoring & Logs

### View Logs

**All services:**
```bash
docker compose logs -f
```

**Specific service:**
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f neo4j
docker compose logs -f qdrant
```

**Last N lines:**
```bash
docker compose logs --tail=100 backend
```

### Health Checks

All services include health checks:
```bash
# Check service health
docker compose ps

# Inspect specific service
docker inspect navnexus-backend --format='{{.State.Health.Status}}'
```

### Performance Monitoring

**Resource Usage:**
```bash
docker stats
```

**Service Status:**
```bash
docker compose ps
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Change ports in docker-compose.yml
# Example: "3001:80" instead of "3000:80"
```

**2. Permission Denied**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

**3. Out of Disk Space**
```bash
# Clean up old images and containers
docker system prune -a --volumes

# Warning: This removes all unused containers, networks, images, and volumes
```

**4. Backend Cannot Connect to Databases**
- Check that Neo4j and Qdrant are healthy: `docker compose ps`
- Verify network connectivity: `docker compose exec backend ping neo4j`
- Check environment variables: `docker compose exec backend env | grep NEO4J`

**5. Frontend Cannot Reach Backend**
- Verify `VITE_API_BASE_URL` is set correctly in `.env`
- Check backend is running: `curl http://localhost:8080/health`
- Check browser console for CORS errors

### Debug Mode

**Enable verbose logging:**
```bash
# In .env file
LOG_LEVEL=Debug
ASPNETCORE_ENVIRONMENT=Development
```

**Restart services:**
```bash
docker compose down
docker compose up -d
docker compose logs -f
```

### Get Support

- **Documentation:** [README.md](./README.md)
- **Issues:** [GitHub Issues](https://github.com/hnagnurtme/NavNexus/issues)
- **Flow Documentation:** [docs/flow.md](./docs/flow.md)

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use strong passwords** - Minimum 16 characters for Neo4j
3. **Rotate secrets regularly** - Change JWT keys periodically
4. **Use HTTPS in production** - Setup SSL certificates (Let's Encrypt)
5. **Regular updates** - Keep Docker images updated
6. **Limit exposure** - Use firewall rules to restrict access
7. **Monitor logs** - Check for suspicious activity

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neo4j Docker Guide](https://neo4j.com/developer/docker/)
- [Qdrant Docker Guide](https://qdrant.tech/documentation/guides/installation/)
- [ASP.NET Core Docker Guide](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/docker/)

---

**Happy Deploying! 🚀**
