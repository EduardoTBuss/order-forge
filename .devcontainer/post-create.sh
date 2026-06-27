#!/usr/bin/env bash
set -euo pipefail

# Named volume for ~/.claude (see devcontainer.json) is created owned by root;
# hand ownership back to the dev user so Claude Code can write to it.
echo "Ensuring $HOME/.claude is owned by $USER..."
sudo mkdir -p "$HOME/.claude"
sudo chown -R "$USER:$USER" "$HOME/.claude"

echo "Aligning docker group to socket..."
if [ -S /var/run/docker.sock ]; then
  SOCK_GID=$(stat -c '%g' /var/run/docker.sock)
  GROUP_NAME=$(getent group "$SOCK_GID" | cut -d: -f1 || true)
  if [ -z "$GROUP_NAME" ]; then
    GROUP_NAME="docker-host"
    sudo groupadd -g "$SOCK_GID" "$GROUP_NAME"
  fi
  sudo usermod -aG "$GROUP_NAME" "$USER"
else
  echo "Docker socket not mounted; skipping docker group setup."
fi

echo "Checking docker access..."
if docker version >/dev/null 2>&1; then
  docker compose version
else
  echo "Warning: Docker is not available in the devcontainer; skipping docker checks and continuing."
fi

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

PNPM_VERSION="${PNPM_VERSION:-11.1.2}"
echo "Enabling pnpm..."
corepack enable
echo "Preparing pnpm ${PNPM_VERSION}..."
corepack prepare "pnpm@${PNPM_VERSION}" --activate

echo "Setting up pnpm global bin directory..."
export SHELL="${SHELL:-/bin/bash}"
pnpm setup
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"

echo "Setting up biome..."
pnpm add --global @biomejs/biome@2.4.15

echo "Installing frontend deps..."
cd frontend
pnpm install
cd ..

echo "Installing backend deps..."
cd backend
uv sync
cd ..

echo "Setting up prek (pre-commit hooks)..."
prek install -f || true

echo "Installing + configuring opencode (AI coding agent)..."
# Devcontainer already has Docker/Node/uv, so only the opencode bits are needed.
# opencode zen needs just an API key. Set OPENCODE_API_KEY as a Codespace secret
# and it's applied here automatically; otherwise authenticate later in a terminal
# with:  opencode → /connect → "opencode zen" → paste the key.
if [[ -x scripts/setup-workshop.sh ]]; then
  bash scripts/setup-workshop.sh --opencode-only || echo "Warning: opencode setup skipped/failed (non-fatal)."
fi

echo "Starting compose build in background..."
if docker version >/dev/null 2>&1; then
  if [[ -x scripts/compose-build.sh ]]; then
    nohup bash scripts/compose-build.sh >/tmp/compose-build.log 2>&1 &
  else
    echo "Warning: scripts/compose-build.sh not found or not executable."
  fi
else
  echo "Warning: Docker is not available; skipping compose build."
fi

echo "Post-create setup complete!"
echo "Run './up.sh' to start all services."
