#!/usr/bin/env bash
# ==============================================================================
# Container Image Build & Tagging Utility (Podman / Docker Compatible)
# ACEest Fitness & Gym Management System
# Author: Kiran K Das (2025TM93130)
# ==============================================================================

set -euo pipefail

# Auto-detect container runtime (prefer podman if docker is not active)
if command -v podman &> /dev/null; then
    CONTAINER_CLI="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CLI="docker"
else
    echo "ERROR: Neither Podman nor Docker was found on this system."
    exit 1
fi

REGISTRY_USER="kirankdas"
IMAGE_BASE="${REGISTRY_USER}/aceest-fitness"

echo "================================================================="
echo " Building Container Images with: [${CONTAINER_CLI}]"
echo " Target Repository: ${IMAGE_BASE}"
echo "================================================================="

VERSIONS=("1.0.0" "1.1.0" "2.0.0" "2.2.0" "3.0.0")

for VER in "${VERSIONS[@]}"; do
    echo "==> Building Version ${VER}..."
    ${CONTAINER_CLI} build \
        --build-arg APP_VERSION="${VER}" \
        -t "${IMAGE_BASE}:${VER}" \
        -t "${IMAGE_BASE}:v${VER}" \
        -f Dockerfile .
done

# Tag version 3.0.0 as latest
${CONTAINER_CLI} tag "${IMAGE_BASE}:3.0.0" "${IMAGE_BASE}:latest"

echo "================================================================="
echo " Successfully built all application version images:"
${CONTAINER_CLI} images | grep "${IMAGE_BASE}" || true
echo "================================================================="
echo " To push images to Docker Hub:"
echo "   ${CONTAINER_CLI} login"
echo "   ${CONTAINER_CLI} push ${IMAGE_BASE}:3.0.0"
echo "   ${CONTAINER_CLI} push ${IMAGE_BASE}:latest"
