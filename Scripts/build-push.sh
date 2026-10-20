#!/bin/bash
# Builds all six component images from Dockerfiles/ and pushes them to
# Docker Hub as $DOCKERHUB_USERNAME/<app>:$IMAGE_TAG (both read from .env).
#
# Images are built for the host's architecture by default, which matches the
# VMs Vagrant creates on that host. Set PLATFORMS=linux/amd64,linux/arm64 to
# publish a multi-arch image instead (needs docker buildx).
#
# Run `docker login` first.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi
: "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME must be set in .env}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

for app in inventory-db billing-db rabbit-queue inventory-app billing-app api-gateway-app; do
    image="${DOCKERHUB_USERNAME}/${app}:${IMAGE_TAG}"
    echo "==> ${image}"
    if [ -n "${PLATFORMS:-}" ]; then
        docker buildx build --platform "$PLATFORMS" -t "$image" --push "Dockerfiles/${app}"
    else
        docker build -t "$image" "Dockerfiles/${app}"
        docker push "$image"
    fi
done
