#!/bin/bash
# render.sh - Build & push multi-arch Docker image for NavNexus Worker

set -e

# ==== Cấu hình ====
IMAGE_NAME="trunganh0106/navnexus-worker"
VERSION="${1:-latest}"  # default latest
ARCHS="linux/amd64,linux/arm64"
DOCKERFILE_PATH="Dockerfile"
CONTEXT_PATH="."
# ==== Buildx builder setup ====
docker buildx inspect navnexus-builder >/dev/null 2>&1 || \
    docker buildx create --name navnexus-builder --use
docker buildx use navnexus-builder

# ==== Build & Push multi-arch image ====
echo "==> Building multi-arch image for: $ARCHS"

docker buildx build \
    --platform $ARCHS \
    --push \
    -t $IMAGE_NAME:$VERSION \
    -f $DOCKERFILE_PATH \
    $CONTEXT_PATH

echo "==> Image pushed successfully:"
echo "Backend: $IMAGE_NAME:$VERSION"
echo "Done!"