#!/usr/bin/env bash
# ============================================================================
# down.sh - Stop the Invoice Intake Workshop app
# ============================================================================
# Main entry point for stopping the application. Use this script instead of
# running `docker compose down` directly.
#
# Usage:
#   ./down.sh [--keep-disk] [docker-compose-down-args...]
#
# Examples:
#   ./down.sh                  # Stop all + auto-prune safe defaults (default)
#   ./down.sh --keep-disk      # Stop all but skip the auto-prune
#   ./down.sh -v               # Stop and remove volumes (destructive)
#   ./down.sh --rmi all        # Stop and remove images
#
# Notes:
#   --keep-disk is intercepted by this script and NOT passed to docker compose.
#   All other args are forwarded to `docker compose down`.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Intercept --keep-disk (down.sh-specific); forward everything else to compose.
KEEP_DISK=false
COMPOSE_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --keep-disk) KEEP_DISK=true ;;
    *) COMPOSE_ARGS+=("$arg") ;;
  esac
done

# ============================================================================
# Logging helpers
# ============================================================================
print_separator() {
  echo ""
  echo "════════════════════════════════════════════════════════════════════════════════"
}

print_step() {
  local step="$1"
  echo "▶ $step"
}

print_success() {
  local msg="$1"
  echo "✓ $msg"
}

print_warning() {
  local msg="$1"
  echo "⚠ $msg"
}

# ============================================================================
# App Identity
# ============================================================================
APP_NAME="Invoice Intake Workshop"

print_separator
echo ""
echo "   Stopping $APP_NAME..."
echo ""
print_separator

# ============================================================================
# Step 1: Stop Docker Compose services
# ============================================================================
print_separator
print_step "Step 1: Stopping Services"
echo ""
echo "  Running: docker compose down ${COMPOSE_ARGS[*]:-}"
echo ""

cd "$PROJECT_ROOT"
docker compose down ${COMPOSE_ARGS[@]+"${COMPOSE_ARGS[@]}"}
DOWN_EXIT_CODE=$?

if [[ $DOWN_EXIT_CODE -eq 0 ]]; then
  print_success "Services stopped"
else
  print_warning "docker compose down exited with code $DOWN_EXIT_CODE"
fi

# ============================================================================
# Step 2: Disk Hygiene
# ============================================================================
# Default: actively reclaim safe disk (`scripts/docker-prune.sh` without
# --volumes — dangling images + build cache + anonymous hex-named volumes
# only; named project volumes like `<project>_postgres_data` are NEVER
# touched, guaranteed by the regex `^[0-9a-f]{60,}$` in docker-prune.sh).
#
# After the prune, runs an invariant check: every named project volume that
# existed BEFORE the prune must still exist AFTER. The check reads the
# project's expected volumes from the live compose config (via
# `docker compose config --volumes`) and the effective project name from
# `docker compose config --format json | jq .name`, so it adapts if the
# project is ever renamed. If the invariant breaks, prints a loud warning
# but does not fail the script — preserves the existing exit-code contract.
#
# Pass --keep-disk to skip the prune (e.g. mid-debug of a build-cache issue);
# in that case, falls back to the report-only behavior.
print_separator
print_step "Step 2: Disk Hygiene"
echo ""

if [[ "$KEEP_DISK" == "true" ]]; then
  echo "  --keep-disk specified; skipping auto-prune."
  echo ""

  anonymous_count=$(docker volume ls --filter dangling=true --format '{{.Name}}' 2>/dev/null | grep -cE '^[0-9a-f]{60,}$' || true)
  anonymous_count=${anonymous_count:-0}

  reclaim_summary=$(docker system df --format '{{.Type}}	{{.Reclaimable}}' 2>/dev/null \
    | awk -F'\t' '$2 !~ /^0B/ {printf "    %-15s %s\n", $1":", $2}' || true)

  if [[ "$anonymous_count" -gt 0 || -n "$reclaim_summary" ]]; then
    if [[ "$anonymous_count" -gt 0 ]]; then
      echo "  $anonymous_count dangling anonymous volume(s) reclaimable."
    fi
    if [[ -n "$reclaim_summary" ]]; then
      echo "$reclaim_summary"
    fi
    echo ""
    echo "  → bash scripts/docker-prune.sh         (safe defaults)"
    echo "  → bash scripts/docker-prune.sh --volumes  (also wipes project DBs)"
  else
    echo "  Nothing reclaimable."
  fi
else
  # Snapshot named project volumes from live compose config (project-name
  # agnostic — adapts if the project ever gets renamed).
  compose_project="$(docker compose config --format json 2>/dev/null | jq -r '.name // empty' 2>/dev/null || true)"
  expected_volume_keys="$(docker compose config --volumes 2>/dev/null || true)"

  present_before=()
  if [[ -n "$compose_project" && -n "$expected_volume_keys" ]]; then
    while IFS= read -r vol; do
      [[ -z "$vol" ]] && continue
      full_name="${compose_project}_${vol}"
      if docker volume inspect "$full_name" >/dev/null 2>&1; then
        present_before+=("$full_name")
      fi
    done <<<"$expected_volume_keys"
  fi

  # Run the safe prune (NEVER the --volumes destructive variant).
  bash "$SCRIPT_DIR/scripts/docker-prune.sh"

  # Invariant: every named volume present before must still be present after.
  echo ""
  missing=()
  for vol in ${present_before[@]+"${present_before[@]}"}; do
    if ! docker volume inspect "$vol" >/dev/null 2>&1; then
      missing+=("$vol")
    fi
  done

  if [[ ${#present_before[@]} -eq 0 ]]; then
    echo "  (No project volumes to verify — compose config returned none.)"
  elif [[ ${#missing[@]} -eq 0 ]]; then
    print_success "Project volumes intact: ${#present_before[@]}/${#present_before[@]} (project: ${compose_project})"
  else
    print_warning "Invariant breach: ${#missing[@]} project volume(s) went missing during prune:"
    for vol in "${missing[@]}"; do
      echo "    ✗ $vol"
    done
    echo "  This is unexpected — the safe prune in scripts/docker-prune.sh should never"
    echo "  remove named volumes. Investigate the script before continuing."
  fi
  echo ""
  echo "  (Use --keep-disk to skip this prune; --volumes on docker-prune.sh for full wipe.)"
fi

print_separator
echo ""
echo "   $APP_NAME stopped."
echo ""
print_separator

exit $DOWN_EXIT_CODE
