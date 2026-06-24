#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/docker-prune.sh [--volumes] [--help]

Safely reclaim disk space in Codespaces by removing unused Docker resources.

Default actions (safe; does not affect running containers):
  - Remove dangling images (old build outputs not used by any container)
  - Remove build cache
  - Remove anonymous volumes (hex-named, leftover from previous container
    rebuilds; never matches docker-compose named project volumes like
    invoice-workshop_postgres_data)

Optional:
  --volumes   Also prune ALL unused volumes including detached named project
              volumes — can delete data for stopped services. Only use after
              ./down.sh if you intend to wipe local databases.
  --help      Show this help
EOF
}

prune_volumes=0

for arg in "$@"; do
  case "$arg" in
    --volumes)
      prune_volumes=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo >&2
      usage >&2
      exit 2
      ;;
  esac
done

echo "🧹 Cleaning up unused Docker resources..."

images_freed=""
cache_freed=""
volumes_removed=0
volumes_pruned_freed=""

echo "→ Removing dangling images..."
image_output=$(docker image prune -f 2>&1)
echo "$image_output"
images_freed=$(echo "$image_output" | sed -n 's/^Total reclaimed space: //p' || true)

echo "→ Removing build cache..."
cache_output=$(docker builder prune -f 2>&1)
echo "$cache_output"
cache_freed=$(echo "$cache_output" | sed -n 's/^Total:[[:space:]]*//p' || true)

echo "→ Removing dangling anonymous volumes (hex-named only, never project volumes)..."
# Pure hex names (60+ chars) are docker-assigned anonymous volume ids.
# Compose-named volumes are always <project>_<name>, so this regex can't match them.
anonymous_volumes="$(docker volume ls --filter dangling=true --format '{{.Name}}' | grep -E '^[0-9a-f]{60,}$' || true)"
if [[ -n "$anonymous_volumes" ]]; then
  volumes_removed=$(echo "$anonymous_volumes" | wc -l | tr -d ' ')
  echo "$anonymous_volumes" | xargs docker volume rm >/dev/null
  echo "  Removed $volumes_removed anonymous volume(s)."
else
  echo "  None found."
fi

if [[ "$prune_volumes" -eq 1 ]]; then
  echo "→ Removing all unused volumes (destructive)..."
  vp_output=$(docker volume prune -f 2>&1)
  echo "$vp_output"
  volumes_pruned_freed=$(echo "$vp_output" | sed -n 's/^Total reclaimed space: //p' || true)
fi

summary_parts=()
[[ -n "$images_freed" && "$images_freed" != "0B" ]] && summary_parts+=("images $images_freed")
[[ -n "$cache_freed" && "$cache_freed" != "0B" ]] && summary_parts+=("build cache $cache_freed")
[[ "$volumes_removed" -gt 0 ]] && summary_parts+=("$volumes_removed anonymous volume(s)")
[[ -n "$volumes_pruned_freed" && "$volumes_pruned_freed" != "0B" ]] && summary_parts+=("named volumes $volumes_pruned_freed")

if [[ ${#summary_parts[@]} -gt 0 ]]; then
  echo ""
  echo "✅ Freed: $(IFS=', '; echo "${summary_parts[*]}")."
else
  echo ""
  echo "✅ Nothing to clean up."
fi
echo "  Tagged images are kept for fast restart — use --volumes for full wipe."
