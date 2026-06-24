#!/usr/bin/env bash
# ============================================================================
# setup-workshop.sh — one-shot dev environment setup for the workshop
# ============================================================================
# Installs the tooling participants need to build the solution on their own
# machine (not just in a GitHub Codespace):
#
#   1. Docker            — to run the app stack (./up.sh)
#   2. uv + Python       — backend tooling (ruff/ty/uv sync, local pre-commit)
#   3. Node + pnpm       — frontend tooling + SDK regeneration
#   4. opencode          — the AI coding agent used to develop the solution
#
# It then sets up opencode with the workshop "opencode zen" API key.
#
# Usage:
#   ./scripts/setup-workshop.sh                 # interactive (prompts for key)
#   OPENCODE_API_KEY=zen_xxx ./scripts/setup-workshop.sh   # non-interactive
#   ./scripts/setup-workshop.sh --skip-opencode-config     # install only
#
# Re-running is safe: anything already installed is detected and skipped.
# ============================================================================
set -euo pipefail

# This script uses bash features (arrays, here-strings). Refuse to run under sh/dash.
if [ -z "${BASH_VERSION:-}" ]; then
  echo "Please run with bash, not sh:  bash scripts/setup-workshop.sh" >&2
  exit 1
fi

# ── Facilitator config (override via env when running) ──────────────────────
# The workshop shares an "opencode zen" API key. opencode zen is opencode's
# hosted model gateway — there is NO base URL or model config to set; the key
# is all a participant needs. Provide it via OPENCODE_API_KEY or be prompted.
OPENCODE_API_KEY="${OPENCODE_API_KEY:-}"

SKIP_OPENCODE_CONFIG=false
ONLY_OPENCODE=false
for arg in "$@"; do
  case "$arg" in
    --skip-opencode-config) SKIP_OPENCODE_CONFIG=true ;;
    --opencode-only) ONLY_OPENCODE=true ;;   # install + configure opencode only (devcontainer already has Docker/Node/uv)
    -h|--help) sed -n '2,28p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# ── Logging ─────────────────────────────────────────────────────────────────
bold() { printf '\033[1m%s\033[0m\n' "$*"; }
step() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m⚠\033[0m %s\n' "$*"; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; }
has()  { command -v "$1" >/dev/null 2>&1; }

# ── Platform detection ────────────────────────────────────────────────────────
IS_WSL=false
case "$(uname -s)" in
  Darwin) PLATFORM=mac ;;
  Linux)
    PLATFORM=linux
    # WSL reports "Linux"; the linux path works, with one Docker caveat noted below.
    if grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then IS_WSL=true; fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    err "Native Windows (Git Bash / MSYS / Cygwin) is not supported for this Docker-based workshop."
    err "Install WSL2 + Ubuntu, then run this script inside the Ubuntu shell:"
    err "  https://learn.microsoft.com/windows/wsl/install"
    err "(Docker Desktop for Windows also requires the WSL2 backend.)"
    exit 1 ;;
  *)
    PLATFORM=other
    warn "Unrecognized OS '$(uname -s)' — will attempt the generic Linux path; some steps may need manual installs." ;;
esac

# curl underpins every installer below.
if ! has curl; then
  err "curl is required but not installed."
  [ "$PLATFORM" = linux ] && err "  Debian/Ubuntu: sudo apt-get install -y curl   ·   Fedora/RHEL: sudo dnf install -y curl"
  [ "$PLATFORM" = mac ] && err "  curl ships with macOS — check your PATH."
  exit 1
fi

# Make freshly-installed tools available within this same run.
ensure_path() {
  export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$HOME/.cargo/bin:$PATH"
}
ensure_path

bold "Workshop environment setup ($PLATFORM)"

# ── 1. Docker ─────────────────────────────────────────────────────────────────
install_docker() {
  step "1/4 Docker"
  if has docker; then
    if docker info >/dev/null 2>&1; then
      ok "Docker installed and the daemon is running ($(docker --version | awk '{print $3}' | tr -d ,))"
    else
      warn "Docker is installed but the daemon isn't running — start Docker Desktop / the docker service, then re-run ./up.sh."
    fi
    return
  fi
  if [ "$PLATFORM" = mac ]; then
    if has brew; then
      warn "Docker not found — installing Docker Desktop via Homebrew (you must launch it once afterwards)."
      brew install --cask docker || warn "brew install failed; install Docker Desktop manually: https://www.docker.com/products/docker-desktop/"
    else
      warn "Docker not found. Install Docker Desktop for Mac: https://www.docker.com/products/docker-desktop/"
    fi
  elif [ "$PLATFORM" = linux ]; then
    warn "Docker not found."
    if [ "$IS_WSL" = true ]; then
      warn "WSL detected: easiest is Docker Desktop for Windows with WSL integration enabled for this distro"
      warn "  (Settings → Resources → WSL integration). Or install Docker Engine in WSL via the prompt below."
    fi
    if [ -t 0 ]; then
      read -r -p "  Install Docker Engine now via get.docker.com (needs sudo)? [y/N] " reply
      if [[ "$reply" =~ ^[Yy]$ ]]; then
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker "$USER" 2>/dev/null || true
        warn "Added you to the 'docker' group — log out/in (or run 'newgrp docker') for it to take effect."
      else
        warn "Skipped. Install later: https://docs.docker.com/engine/install/"
      fi
    else
      warn "Non-interactive shell; skipping auto-install. See https://docs.docker.com/engine/install/"
    fi
  else
    warn "Unknown platform; install Docker manually: https://docs.docker.com/get-docker/"
  fi
}

# ── 2. uv + Python ─────────────────────────────────────────────────────────────
install_uv() {
  step "2/4 uv + Python"
  if has uv; then
    ok "uv installed ($(uv --version | awk '{print $2}'))"
  else
    warn "Installing uv (Astral)…"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ensure_path
    has uv && ok "uv installed ($(uv --version | awk '{print $2}'))" || { err "uv install failed"; return; }
  fi
  # The backend targets Python 3.14; uv can fetch it (used for local lint/type tooling).
  if uv python find 3.14 >/dev/null 2>&1; then
    ok "Python 3.14 available to uv"
  else
    warn "Fetching Python 3.14 via uv…"
    uv python install 3.14 || warn "Could not pre-install Python 3.14 (uv will fetch it on first use)."
  fi
}

# ── 3. Node + pnpm ──────────────────────────────────────────────────────────────
install_node_pnpm() {
  step "3/4 Node + pnpm"
  if ! has node; then
    if [ "$PLATFORM" = mac ] && has brew; then
      warn "Installing Node via Homebrew…"; brew install node || warn "brew install node failed."
    elif [ "$PLATFORM" = linux ]; then
      warn "Installing Node via fnm…"
      curl -fsSL https://fnm.vercel.app/install | bash >/dev/null 2>&1 || true
      export PATH="$HOME/.local/share/fnm:$HOME/.fnm:$PATH"
      has fnm && eval "$(fnm env)" 2>/dev/null || true
      has fnm && fnm install --lts >/dev/null 2>&1 && fnm use --lts >/dev/null 2>&1 || true
    fi
  fi
  if has node; then
    ok "Node installed ($(node -v))"
    if has corepack; then
      corepack enable pnpm >/dev/null 2>&1 || true
      ok "pnpm enabled via corepack ($(pnpm -v 2>/dev/null || echo 'run: corepack prepare pnpm@latest --activate'))"
    else
      warn "corepack not found; install pnpm manually: npm i -g pnpm"
    fi
  else
    warn "Node not installed. Needed for ./scripts/update-api-client.sh and frontend lint/typecheck on the host."
    warn "  Install Node 22+ from https://nodejs.org/ then run: corepack enable pnpm"
  fi
}

# ── 4. opencode ─────────────────────────────────────────────────────────────────
install_opencode() {
  step "4/4 opencode"
  if has opencode; then
    ok "opencode installed ($(opencode --version 2>/dev/null || echo present))"
    return
  fi
  warn "Installing opencode…"
  if [ "$PLATFORM" = mac ] && has brew; then
    brew install sst/tap/opencode || curl -fsSL https://opencode.ai/install | bash
  else
    curl -fsSL https://opencode.ai/install | bash
  fi
  ensure_path
  has opencode && ok "opencode installed ($(opencode --version 2>/dev/null || echo present))" \
    || warn "opencode not on PATH yet — open a new terminal, or add ~/.opencode/bin to your PATH."
}

# ── opencode zen key setup ───────────────────────────────────────────────────────
# opencode zen authenticates with a single API key. The reliable, always-works
# path is the interactive `opencode` → /connect → "opencode zen" → paste key.
# For convenience (and for headless/Codespaces setup), if a key is supplied we
# also persist OPENCODE_API_KEY, which opencode uses for the zen provider.
configure_opencode() {
  step "opencode zen key"
  if [ "$SKIP_OPENCODE_CONFIG" = true ]; then warn "Skipped (--skip-opencode-config)."; return; fi

  if [ -z "$OPENCODE_API_KEY" ]; then
    if [ -t 0 ]; then
      read -r -p "  Paste the workshop opencode zen key (blank to set it up later): " OPENCODE_API_KEY
    else
      warn "No OPENCODE_API_KEY set and no TTY — skipping."
    fi
  fi

  if [ -z "$OPENCODE_API_KEY" ]; then
    warn "No key provided. Authenticate any time with:"
    warn "    opencode  →  /connect  →  select 'opencode zen'  →  paste the key"
    return
  fi

  # Persist the zen key so opencode picks it up non-interactively.
  export OPENCODE_API_KEY
  local persisted=false rc
  for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    [ -f "$rc" ] || continue
    if grep -q "OPENCODE_API_KEY" "$rc" 2>/dev/null; then
      persisted=true
      continue
    fi
    printf '\n# opencode zen key (workshop)\nexport OPENCODE_API_KEY=%q\n' "$OPENCODE_API_KEY" >> "$rc"
    persisted=true
    ok "Added OPENCODE_API_KEY to $rc"
  done
  [ "$persisted" = false ] && warn "No shell profile found to persist the key (it's exported for this session only)."

  ok "opencode zen key set."
  warn "Verify it works: run 'opencode' and check it's connected. If not, use the"
  warn "  guaranteed path:  opencode → /connect → 'opencode zen' → paste the key."
}

# ── Run ───────────────────────────────────────────────────────────────────────
if [ "$ONLY_OPENCODE" = true ]; then
  install_opencode
  configure_opencode
  step "Done (opencode only)"
  exit 0
fi

install_docker
install_uv
install_node_pnpm
install_opencode
configure_opencode

step "Done"
cat <<'NEXT'
  Next steps (from the repo root):
    1. cp .env.example .env          # create your local env file
    2. ./up.sh                       # start the stack (frontend :3000, backend :8000)
    3. opencode                      # start coding with the agent
       └─ if it's not connected: /connect → "opencode zen" → paste the key

  If a tool isn't found, open a NEW terminal so PATH changes take effect.
NEXT
