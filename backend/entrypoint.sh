#!/bin/bash

# Server configuration
ENV_WORKERS=${ENV_WORKERS:-1}
ENV_TIMEOUT=${ENV_TIMEOUT:-60}
ENV_HOST=${ENV_HOST:-"0.0.0.0"}
ENV_PORT=${ENV_PORT:-8000}

# OpenTelemetry configuration
export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-""}
export OTEL_EXPORTER_OTLP_HEADERS=${OTEL_EXPORTER_OTLP_HEADERS:-""}
export OTEL_EXPORTER_OTLP_PROTOCOL=${OTEL_EXPORTER_OTLP_PROTOCOL:-"http/protobuf"}
export OTEL_TRACES_EXPORTER=${OTEL_TRACES_EXPORTER:-"otlp"}


# Activate the virtual environment
source .venv/bin/activate

# Run Migrations
echo "✯ Running Migrations"
alembic upgrade head

echo "✯ Starting uvicorn"

# --reload and --workers are mutually exclusive; --reload disables worker
# crash recovery. Only enable for local dev. (https://uvicorn.dev/settings/#production)
RELOAD_ARG=""
if [[ "${ENV_RELOAD:-false}" == "true" ]]; then
    RELOAD_ARG="--reload"
fi

exec uvicorn src.asgi:app \
    $RELOAD_ARG \
    --workers $ENV_WORKERS \
    --log-level info \
    --access-log \
    --host $ENV_HOST \
    --port $ENV_PORT \
    --timeout-keep-alive $ENV_TIMEOUT
