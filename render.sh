#!/bin/bash
# render.sh - Build & push multi-arch Docker images for NavNexus

set -e

# ==== Configuration ====
DOCKER_USERNAME="${DOCKER_USERNAME:-trunganh0106}"
VERSION="${1:-latest}"
SERVICE="${2:-all}"  # Options: all, backend, frontend
ARCHS="linux/amd64,linux/arm64"

BACKEND_IMAGE="$DOCKER_USERNAME/navnexus-backend"
FRONTEND_IMAGE="$DOCKER_USERNAME/navnexus-frontend"

# ==== Colors for output ====
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==== Functions ====
print_info() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

build_backend() {
    print_info "Building Backend (ASP.NET Core) for: $ARCHS"
    docker buildx build \
        --platform $ARCHS \
        --push \
        -t $BACKEND_IMAGE:$VERSION \
        -t $BACKEND_IMAGE:latest \
        -f Backend/Dockerfile \
        Backend
    print_success "Backend image pushed: $BACKEND_IMAGE:$VERSION"
}

build_frontend() {
    print_info "Building Frontend (React + Vite) for: $ARCHS"
    docker buildx build \
        --platform $ARCHS \
        --push \
        -t $FRONTEND_IMAGE:$VERSION \
        -t $FRONTEND_IMAGE:latest \
        -f Frontend/Dockerfile \
        Frontend
    print_success "Frontend image pushed: $FRONTEND_IMAGE:$VERSION"
}

# ==== Main Script ====
print_info "NavNexus Multi-arch Docker Build & Push"
print_info "Version: $VERSION | Service: $SERVICE | Platforms: $ARCHS"

# Setup buildx builder
print_info "Setting up Docker Buildx builder..."
docker buildx create --use --name navnexus-builder 2>/dev/null || docker buildx use navnexus-builder
docker buildx inspect --bootstrap

# Build based on service selection
case $SERVICE in
    "backend")
        build_backend
        ;;
    "frontend")
        build_frontend
        ;;
    "all")
        build_backend
        build_frontend
        ;;
    *)
        print_warning "Invalid service: $SERVICE"
        echo "Usage: $0 [VERSION] [SERVICE]"
        echo "  VERSION: Docker image tag (default: latest)"
        echo "  SERVICE: all | backend | frontend (default: all)"
        exit 1
        ;;
esac

print_success "All images built and pushed successfully!"
echo ""
echo "📦 Images:"
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "backend" ]; then
    echo "  Backend:  $BACKEND_IMAGE:$VERSION"
fi
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "frontend" ]; then
    echo "  Frontend: $FRONTEND_IMAGE:$VERSION"
fi
echo ""
print_info "Done!"
