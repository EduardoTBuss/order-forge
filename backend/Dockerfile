# syntax=docker/dockerfile:1

FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/src/app

# Install system dependencies required by WeasyPrint, poppler-utils, libreoffice and binutils
# Using --no-install-recommends reduces image size by ~200MB
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    libpq-dev \
    libjpeg62-turbo-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-dev \
    libpango1.0-dev \
    poppler-utils \
    libreoffice \
    binutils \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libtesseract-dev \
    ffmpeg \
    pandoc \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-xetex

# Upgrade system setuptools and wheel to fix known vulnerabilities
RUN pip install --upgrade setuptools wheel

# Copy dependency metadata and install Python dependencies
# Cache mount speeds up rebuilds when only code changes
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PATH="/usr/src/app/.venv/bin:${PATH}"

EXPOSE 80 5000

COPY . .

RUN mkdir -p static

CMD ["bash", "entrypoint.sh"]
