#!/bin/bash
set -euo pipefail

export BACKEND_API_URL=http://localhost:8000

echo "Updating frontend API client..."
pnpm -C frontend update-api-client

echo "API client updated successfully."
