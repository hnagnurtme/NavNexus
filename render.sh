#!/bin/bash
# render.sh - Build & push multi-arch Docker image for NavNexus Backend

set -e

# ==== Cấu hình ====
IMAGE_NAME="trunganh0106/navnexus"
VERSION="${1:-latest}"  # Nếu không truyền version, dùng latest
ARCHS="linux/amd64,linux/arm64"

# ==== Buildx builder setup ====
docker buildx create --use --name navnexus-builder || true

# ==== Build & Push multi-arch image ====
echo "==> Building multi-arch image for: $ARCHS"

docker buildx build \
    --platform $ARCHS \
    --push \
    -t $IMAGE_NAME:$VERSION \
    -f Backend/Dockerfile \
    Backend

echo "==> Image pushed successfully:"
echo "Backend: $IMAGE_NAME:$VERSION"
echo "Done!"
