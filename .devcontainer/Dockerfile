FROM mcr.microsoft.com/devcontainers/python:3-3.14-bookworm

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Remove broken yarn apt source (NO_PUBKEY noise) before updating
RUN rm -f /etc/apt/sources.list.d/yarn.list

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        gnupg \
        gh \
        ripgrep \
        fzf \
        postgresql-client \
        poppler-utils \
        ffmpeg \
        libcairo2-dev \
        libpango1.0-dev \
        libjpeg-dev \
        libgif-dev \
        librsvg2-dev \
        chromium \
        texlive-xetex \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Prek (pre-commit wrapper)
RUN pip install --no-cache-dir prek

# Node.js v24 from official tarball + corepack (yarn/pnpm)
RUN set -eux; \
    NODE_VERSION=24.15.0; \
    ARCH="$(dpkg --print-architecture)"; \
    case "$ARCH" in \
      amd64) NODE_ARCH=x64 ;; \
      arm64) NODE_ARCH=arm64 ;; \
      *) echo "unsupported arch: $ARCH"; exit 1 ;; \
    esac; \
    curl -fsSLo /tmp/node.tar.xz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"; \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner; \
    rm /tmp/node.tar.xz; \
    corepack enable; \
    node --version; \
    npm --version

# Puppeteer: use system chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Claude Code CLI — install globally as root so non-root users can run it
RUN npm install -g @anthropic-ai/claude-code && claude --version || true

# opencode CLI — install globally via npm so non-root users can execute it.
RUN npm install -g opencode-ai@1.14.48 && opencode --version

ENV DEBIAN_FRONTEND=dialog
