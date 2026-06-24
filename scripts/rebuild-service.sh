#!/usr/bin/env bash
# ============================================================================
# rebuild-service.sh - Resync a single compose service from current host source
# ============================================================================
# Docker Compose `develop.watch` (action: sync) only propagates additions and
# modifications to a running container, never deletions. After files have been
# deleted on the host the container retains stale copies, which then surface
# as missing-module errors inside the container (e.g. `pnpm typecheck` and
# `pnpm build` failing on imports to files that no longer exist on disk).
#
# This script rebuilds the named service image with the cache (the COPY layer
# hash invalidates on deleted files, so the rebuild is fast but correct) and
# recreates the container so the new image is in effect.
#
# Usage:
#   bash scripts/rebuild-service.sh <service>
#
# Examples:
#   bash scripts/rebuild-service.sh frontend
#   bash scripts/rebuild-service.sh backend
#   bash scripts/rebuild-service.sh orchestrator
# ============================================================================
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/rebuild-service.sh <service>" >&2
  exit 2
fi

service="$1"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "→ Rebuilding $service image (cached; deleted-file detection via COPY layer hash)..."
docker compose build "$service"

echo "→ Recreating $service container..."
docker compose up -d --force-recreate --no-deps "$service"

echo "✓ $service rebuilt. Container filesystem now matches host source."
