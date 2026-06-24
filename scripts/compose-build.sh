#!/usr/bin/env bash

set -euo pipefail

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
export COMPOSE_BAKE=true

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Prevent Codespaces disk exhaustion from repeated rebuilds.
# This only removes dangling (unused) images, not images referenced by containers.
echo "→ Pruning dangling Docker images before build..."
docker image prune -f

docker compose build --no-cache --pull
