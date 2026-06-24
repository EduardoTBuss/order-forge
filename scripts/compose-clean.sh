#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/compose-clean.sh [--project <name>] [--compose-file <path>]

Removes Docker Compose containers, images, networks, and volumes for this repo.

Options:
  --project <name>       Override COMPOSE_PROJECT_NAME for this run
  --compose-file <path>  Use a specific compose file (default: docker-compose.yml)
  -h, --help             Show help
EOF
}

compose_file="docker-compose.yml"
project_override=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      project_override="${2:-}"
      if [[ -z "$project_override" ]]; then
        echo "Missing value for --project" >&2
        exit 2
      fi
      shift 2
      ;;
    --compose-file|-f)
      compose_file="${2:-}"
      if [[ -z "$compose_file" ]]; then
        echo "Missing value for --compose-file" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ ! -f "$compose_file" ]]; then
  echo "Compose file not found: $compose_file" >&2
  exit 1
fi

env_get() {
  local key="$1"
  local default="${2:-}"
  local line
  if [[ ! -f .env ]]; then
    printf "%s" "$default"
    return
  fi
  line="$(grep -E "^[[:space:]]*${key}=" .env | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    printf "%s" "$default"
    return
  fi
  printf "%s" "${line#*=}"
}

if [[ -n "$project_override" ]]; then
  export COMPOSE_PROJECT_NAME="$project_override"
fi

project_name="${project_override:-${COMPOSE_PROJECT_NAME:-}}"
if [[ -z "$project_name" ]]; then
  project_name="$(env_get COMPOSE_PROJECT_NAME "invoice-workshop")"
fi

echo "→ Removing compose containers, images, and volumes"
docker compose -f "$compose_file" down --rmi all --remove-orphans

volumes=(
  "${project_name}_postgres_data"
  "${project_name}_cosmosdb_data"
  "${project_name}_cosmosdb_logs"
  "${project_name}_blobstorage_data"
  "${project_name}_blobstorageviewer_keys"
  "${project_name}_frontend_node_modules"
  "${project_name}_backend_venv"
)

failed=0
for volume in "${volumes[@]}"; do
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    if docker volume rm "$volume"; then
      echo "Removed volume: $volume"
    else
      echo "Could not remove volume: $volume (in use?)" >&2
      failed=1
    fi
  else
    echo "Volume not found: $volume"
  fi
done

docker system prune -a -f

exit "$failed"
