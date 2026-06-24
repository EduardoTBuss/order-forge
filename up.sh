#!/usr/bin/env bash
# ============================================================================
# up.sh - Start the Invoice Intake Workshop app
# ============================================================================
# Main entry point for starting the application. Use this script instead of
# running `docker compose up` directly.
#
# Usage:
#   ./up.sh [docker-compose-up-args...]
#
# Examples:
#   ./up.sh                    # Start all services with --watch (default)
#   ./up.sh --no-watch         # Start without file sync
#   ./up.sh -d backend         # Start backend detached with --watch
#   ./up.sh --build            # Rebuild images before starting
#
# Note: --watch is added by default. Use --no-watch to disable.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

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
echo "   Starting $APP_NAME..."
echo ""
print_separator

# ============================================================================
# Step 1: Configure Docker environment
# ============================================================================
print_separator
print_step "Step 1: Docker Environment Setup"

# Export DOCKER_GID for logviewer (Dozzle) to access the Docker socket.
# Required for Docker-in-Docker (DinD) environments like Codespaces/devcontainers.
if [[ -S /var/run/docker.sock ]]; then
  export DOCKER_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo "997")
  print_success "Docker socket configured (GID: $DOCKER_GID)"
else
  print_warning "Docker socket not found"
fi

# ============================================================================
# Step 2: Process arguments
# ============================================================================
print_separator
print_step "Step 2: Processing Arguments"

HAS_WATCH=false
HAS_NO_WATCH=false
HAS_BUILD=false
FILTERED_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --watch)
      HAS_WATCH=true
      FILTERED_ARGS+=("$arg")
      ;;
    --no-watch)
      HAS_NO_WATCH=true
      # Don't add --no-watch to args, just skip adding --watch later
      ;;
    --build)
      HAS_BUILD=true
      FILTERED_ARGS+=("$arg")
      ;;
    *)
      FILTERED_ARGS+=("$arg")
      ;;
  esac
done

# Add --watch by default unless --no-watch was specified or --watch already present
if [[ "$HAS_NO_WATCH" == "false" ]] && [[ "$HAS_WATCH" == "false" ]]; then
  FILTERED_ARGS+=("--watch")
  echo "  Added default --watch flag for hot reload"
fi

echo "  Arguments: ${FILTERED_ARGS[*]:-none}"

# ============================================================================
# Step 3: Prune Docker resources (if --build requested)
# ============================================================================
print_separator
print_step "Step 3: Pruning Docker Resources"
if [[ "$HAS_BUILD" == "true" ]]; then
  bash "$SCRIPT_DIR/scripts/docker-prune.sh"
  print_success "Docker resources pruned"
else
  echo "  Skipped (no --build flag)"
fi

# ============================================================================
# Step 4: Start Docker Compose services
# ============================================================================
print_separator
print_step "Step 4: Starting Services"
echo ""
echo "  Running: docker compose up ${FILTERED_ARGS[*]:-}"
echo ""
print_separator
echo ""

# Run docker compose up with processed arguments
cd "$PROJECT_ROOT"
exec docker compose up "${FILTERED_ARGS[@]}"
