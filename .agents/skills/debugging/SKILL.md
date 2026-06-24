---
name: debugging
description: Debugging and troubleshooting guide for the development environment. Use when investigating errors, inspecting logs, testing endpoints directly, or diagnosing service issues.
metadata:
  version: "1.0.0"
---

# Debugging and Troubleshooting

Use this skill when investigating errors, inspecting service logs, testing
backend endpoints directly, or diagnosing connectivity and runtime issues.

## When to Use This Skill

Reference these guidelines when:
- An error occurs in the frontend or backend
- You need to inspect container logs for stack traces or error messages
- You want to test a backend endpoint directly (without the frontend)
- You need to check if services are running and healthy
- You're diagnosing database, blob storage, or external service issues

---

## 1. Ensure Services Are Running

Always start services with `./up.sh` (not `docker compose` directly):

```bash
./up.sh -d          # Start all services in detached mode
./up.sh -d backend  # Start only the backend (and its dependencies)
```

Check running containers:

```bash
docker compose ps
```

---

## 2. Reading Container Logs

### Via Docker CLI (preferred for agents)

```bash
docker compose logs backend --tail 100        # Last 100 lines
docker compose logs backend -f                # Follow live (background this)
docker compose logs backend --since 5m        # Last 5 minutes
docker compose logs frontend --tail 50        # Frontend logs
docker compose logs postgres --tail 30        # Database logs
```

Combine multiple services:

```bash
docker compose logs backend frontend --tail 50
```

### Via Dozzle Web UI

The `logviewer` service (Dozzle) runs at **http://localhost:8084** and provides
a web UI for browsing all container logs in real time. Useful for visual
inspection but the CLI is better for searching and filtering.

---

## 3. Testing Backend Endpoints Directly

The backend runs at **http://localhost:8000** and is protected by an API key.

### API Key for Local Development

The API key is hardcoded in `docker-compose.yml`:

```
API_KEY: backend-secret-api-key
```

Pass it as a Bearer token in the `Authorization` header.

### Quick Health Check (no auth required)

```bash
curl http://localhost:8000/core/info/health
```

### Calling Protected Endpoints

```bash
curl -X POST http://localhost:8000/core/postgresql/query \
  -H "Authorization: Bearer backend-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1"}'
```

### Interactive API Docs

FastAPI auto-generates interactive docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Use the Swagger UI "Authorize" button with `backend-secret-api-key` to test
endpoints interactively.

### Running Tests via API

The backend has built-in test runner endpoints (require auth):

```bash
# List available test modules
curl http://localhost:8000/core/info/tests/modules \
  -H "Authorization: Bearer backend-secret-api-key"

# Trigger a test run (all modules)
curl -X POST http://localhost:8000/core/info/tests/run \
  -H "Authorization: Bearer backend-secret-api-key"

# Trigger tests for a specific module
curl -X POST "http://localhost:8000/core/info/tests/run?module=postgresql" \
  -H "Authorization: Bearer backend-secret-api-key"

# Check test status
curl http://localhost:8000/core/info/tests/status \
  -H "Authorization: Bearer backend-secret-api-key"
```

---

## 4. Inspecting Databases

### PostgreSQL (pgweb)

- **Web UI**: http://localhost:8081
- **Direct connection** (from host): `postgres://postgres:postgres@localhost:5432/app`

```bash
# Run a query via docker exec
docker compose exec postgres psql -U postgres -d app -c "SELECT * FROM my_table LIMIT 5;"
```

### Cosmos DB / MongoDB (mongo-express)

- **Web UI**: http://localhost:8082

### Blob Storage (Azure Storage Explorer)

- **Web UI**: http://localhost:8083

---

## 5. Common Debugging Scenarios

### Backend returns 500

1. Check backend logs: `docker compose logs backend --tail 100`
2. Look for Python tracebacks — the error and line number are in the log
3. If it's a database error, check postgres logs: `docker compose logs postgres --tail 30`

### Frontend shows "Failed to fetch" or network errors

1. Check if backend is running: `curl http://localhost:8000/core/info/health`
2. Check frontend logs: `docker compose logs frontend --tail 50`
3. Verify the proxy is working — frontend proxies `/api/*` to the backend

### Service won't start

1. Check the specific service logs: `docker compose logs <service> --tail 50`
2. Check if the port is already in use: `lsof -i :<port>`
3. Try restarting: `docker compose restart <service>`
4. If persistent, rebuild: `bash scripts/compose-build.sh <service>`

### Database migration errors

1. Check backend startup logs for Alembic output: `docker compose logs backend | grep -i alembic`
2. Migrations run automatically on backend startup via `entrypoint.sh`
3. To reset the database: `bash scripts/compose-clean-postgres.sh` then restart

### Docker out of disk space

```bash
bash scripts/docker-prune.sh              # Safe cleanup
bash scripts/docker-prune.sh --volumes    # Also prune unused volumes
bash scripts/compose-clean.sh             # Full destructive cleanup
```

---

## 6. Useful Docker Commands

```bash
# Restart a single service
docker compose restart backend

# Shell into a running container
docker compose exec backend bash
docker compose exec frontend sh

# Check resource usage
docker stats --no-stream

# View environment variables in a container
docker compose exec backend env | sort

# Check if a port is accessible
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/core/info/health
```

---

## 7. Local Development Credentials

All local development credentials are in `docker-compose.yml` (not `.env`):

| Service | Credential | Value |
|---------|-----------|-------|
| Backend API | `Authorization` header | `Bearer backend-secret-api-key` |
| PostgreSQL | User / Password | `postgres` / `postgres` |
| PostgreSQL | Database | `app` |
| Blob Storage | Account Name | `warehouselocal` |
| Cosmos DB | Connection | `mongodb://cosmosdb:27017/` |

External service keys (if you add an AI/OCR integration) are pulled from
the host environment via `${VAR:-}` syntax and are optional for local dev.
