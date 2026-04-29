#!/usr/bin/env bash
# Commit patched files and build a Docker image locally (do not auto-push)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Files to commit (adjust if you changed other files)
FILES=(api/admin.py services/db.py services/face_embeddings.py CHANGELOG.md)

echo "Staging files: ${FILES[*]}"
git add "${FILES[@]}"

MSG="chore: patch Postgres datetime conversion and face-embedding DDL (2026-02-24)"
git commit -m "$MSG" || { echo "No changes to commit or commit failed"; }

# Tag the commit
TAG="fras-backend-patch-$(date +%Y%m%d%H%M%S)"
git tag -a "$TAG" -m "Patch: $MSG"
echo "Created tag $TAG"

# Build Docker image (adjust image name as needed)
IMAGE_NAME="fras-backend:$TAG"
echo "Building Docker image $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f Dockerfile .

echo "Build complete. To push the image to a registry, tag and push accordingly."
echo "Local image: $IMAGE_NAME"

exit 0
