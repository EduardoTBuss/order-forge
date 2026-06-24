#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/env_setup [--force]

What it does:
- Ensures git submodules are initialized
- Ensures a root `.env` exists (creates it from `.env.example` if missing)
- Installs the repo Codex config into `~/.codex/config.toml`
- Installs/activates backend pre-commit hooks
- Prints a short, masked summary of the Docker Compose config you'll run

Options:
  --force   Overwrite existing `~/.codex/config.toml` (backs up first if different)
  -h, --help  Show help
EOF
}

force=false
for arg in "$@"; do
  case "$arg" in
    --force) force=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

log() { printf "%s\n" "$*"; }

mask_secret() {
  local value="${1:-}"
  local len="${#value}"
  if [[ -z "$value" ]]; then
    printf "%s" "<unset>"
    return
  fi
  if (( len <= 6 )); then
    printf "%s" "***"
    return
  fi
  printf "%s***%s" "${value:0:2}" "${value: -2}"
}

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

ensure_submodules() {
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "→ Ensuring git submodules are initialized"
    if ! git submodule update --init --recursive >/dev/null 2>&1; then
      log "⚠️  Recursive submodule update failed; falling back to non-recursive init"
      git submodule update --init
    fi
  else
    log "⚠️  Not a git repository (skipping submodule init)"
  fi
}

ensure_env_file() {
  if [[ -f .env ]]; then
    return
  fi
  if [[ ! -f .env.example ]]; then
    log "❌ Missing .env.example; cannot create .env"
    exit 1
  fi
  cp .env.example .env
  log "→ Created .env from .env.example"
}

ensure_env_keys_from_example() {
  if [[ ! -f .env.example ]]; then
    return
  fi

  local keys=(
    COMPOSE_PROJECT_NAME
    BACKEND_API_URL
    BACKEND_API_KEY
    POSTGRES_HOST
    POSTGRES_PORT
    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD
    AZURE_STORAGE_ACCOUNT_NAME
    AZURE_STORAGE_ACCOUNT_KEY
    AZURE_STORAGE_CONNECTION_STRING
    AZURE_COSMOSDB_CONNECTION_STRING
    FRONTEND_PORT
  )

  for key in "${keys[@]}"; do
    if grep -Eq "^[[:space:]]*${key}=" .env; then
      continue
    fi
    local example_line
    example_line="$(grep -E "^[[:space:]]*${key}=" .env.example | tail -n 1 || true)"
    if [[ -n "$example_line" ]]; then
      printf "\n%s\n" "$example_line" >> .env
      log "→ Added missing ${key} to .env (from .env.example)"
    fi
  done
}

install_codex_config() {
  local src="$repo_root/.codex/config.toml"
  local dest_dir="$HOME/.codex"
  local dest="$dest_dir/config.toml"

  if [[ ! -f "$src" ]]; then
    log "⚠️  Missing $src (skipping Codex config install)"
    return
  fi

  mkdir -p "$dest_dir"

  if [[ -f "$dest" ]] && ! cmp -s "$src" "$dest"; then
    if [[ "$force" != "true" ]]; then
      log "⚠️  $dest exists and differs. Re-run with --force to overwrite (will back up first)."
      return
    fi
    local backup="$dest.bak.$(date +%Y%m%d%H%M%S)"
    cp "$dest" "$backup"
    log "→ Backed up existing Codex config to $backup"
  fi

  cp "$src" "$dest"
  log "→ Installed Codex config to $dest (Codex reads from ~/.codex/config.toml)"

  if command -v codex >/dev/null 2>&1; then
    log "→ Codex CLI: $(codex --version 2>/dev/null || command -v codex)"
  else
    log "⚠️  Codex CLI not found on PATH (config still installed)"
  fi
}

install_precommit() {
  if [[ ! -d backend ]]; then
    log "⚠️  backend/ not present (skipping prek install)"
    return
  fi
  if [[ ! -f backend/prek.toml ]]; then
    log "⚠️  backend/prek.toml not found (skipping prek install)"
    return
  fi

  if ! command -v prek >/dev/null 2>&1; then
    log "→ Installing prek"
    if command -v pipx >/dev/null 2>&1; then
      pipx install prek
    elif command -v python3 >/dev/null 2>&1; then
      python3 -m pip install --user prek
    else
      log "❌ Could not install prek (missing pipx and python3)"
      exit 1
    fi
  fi

  log "→ Installing backend prek hooks"
  (cd backend && prek install)
}

print_compose_summary() {
  local project_name
  project_name="$(env_get COMPOSE_PROJECT_NAME "invoice-workshop")"

  local backend_url
  backend_url="$(env_get BACKEND_API_URL "http://backend:8000")"

  local backend_key
  backend_key="$(env_get BACKEND_API_KEY "")"

  local db
  db="$(env_get POSTGRES_DB "postgres")"
  local user
  user="$(env_get POSTGRES_USER "postgres")"
  local pass
  pass="$(env_get POSTGRES_PASSWORD "")"

  log ""
  log "=== Docker Compose setup (effective) ==="
  log "Project name: ${project_name}"
  log "Postgres volume: ${project_name}_postgres_data"
  log ""
  log "Frontend:"
  log "  BACKEND_API_URL=${backend_url}"
  log "  BACKEND_API_KEY=$(mask_secret "$backend_key")"
  if [[ "$backend_url" == *"localhost"* || "$backend_url" == *"127.0.0.1"* ]]; then
    log "  ⚠️  BACKEND_API_URL points to localhost; inside Docker this usually must be http://backend:8000"
  fi
  log ""
  log "Backend:"
  log "  API_KEY=$(mask_secret "$backend_key")"
  log "  POSTGRES_* (db=${db}, user=${user}, password=$(mask_secret "$pass"))"
  log "  POSTGRES_HOST/PORT overridden by docker-compose to postgres:5432"
  log ""
  log "Ports:"
  log "  Frontend: http://localhost:3000"
  log "  Backend:  http://localhost:8000"
  log "  Postgres: localhost:5432"
  log "========================================"
  log ""
}

main() {
  ensure_submodules
  ensure_env_file
  # NOTE: temporarily disable auto-populating missing env vars.
  # ensure_env_keys_from_example
  install_codex_config
  install_precommit
  print_compose_summary
  log "Done. Start services with: docker compose up --build"
}

main
