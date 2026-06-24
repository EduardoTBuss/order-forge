---
name: docker-operations
description: Docker and development environment reference. Use when working with Docker, starting/stopping services, managing disk space, running tests via Docker, or troubleshooting infrastructure issues.
metadata:
  version: "1.0.0"
---

# Docker and Development Environment

Use this skill when working with Docker, starting/stopping services, managing disk space,
running tests via Docker, or troubleshooting infrastructure issues.

## When to Use This Skill

Reference these guidelines when:
- Starting or stopping Docker Compose services
- Understanding service communication and architecture
- Managing disk space and Docker resources
- Running backend tests via Docker
- Troubleshooting infrastructure or connectivity issues
- Using convenience scripts for builds and cleanup
- Configuring environment variables for containers

---

## Connection Map

Docker compose (`docker-compose.yml`) runs:

- `postgres` for persistence (pgvector image)
- `cosmosdb` for Cosmos DB (Mongo API) development
- `blobstorage` for Blob Storage development (Azurite)
- `backend` (FastAPI) exposed on `:8000`
- `frontend` (Next.js) exposed on `:3000`
- `dbviewer` (pgweb) exposed on `:8081`
- `cosmosdbviewer` (mongo-express) exposed on `:8082`
- `blobstorageviewer` (Azure Storage web explorer UI) exposed on `:8083`
  - Note: on Apple Silicon, this runs as `linux/amd64` via emulation
- `logviewer` (Dozzle Docker log UI) exposed on `:8084`

---

## Service Communication

```
Internet → Frontend (public) → Backend (private)
```

- Frontend can call Backend
- Backend talks to external services (Blob Storage, etc.)
- Backend is in a private network, not accessible from internet

The frontend never calls the backend directly from the browser. All requests
go through the Next.js `/api` proxy.

---

## Authentication and Request Flow

1. User hits the Next.js app.
2. `frontend/src/proxy.ts` runs the auth middleware
   (`frontend/src/auth/proxy.ts`) and requires a valid session cookie
   (a dev stub session cookie — there is no identity provider).
3. Requests to `/api/*` are handled by
   `frontend/src/app/api/[...path]/route.ts`.
4. The proxy injects `Authorization: Bearer ${BACKEND_API_KEY}` and forwards the
   request to `BACKEND_API_URL`.
5. `backend/src/asgi.py` validates the bearer token and routes the request to a
   module under one of the bucketed prefixes (`/core/`, `/custom/`, or `/auto/`).

---

## Backend Module Wiring

- `backend/src/app/helpers/register_modules.py` scans module folders and mounts
  `routes.py` automatically.
- Module prefixes:
  - Core modules: `/core/<module-name>`
  - Custom modules: `/custom/<module-name>`
- Folder names with underscores are converted to hyphenated route names.

---

## Data and Services

- Postgres is used for persistence; Alembic migrations run at backend startup
  via `backend/entrypoint.sh`.
- External integrations are wrapped in `backend/src/app/services/*`
  (Blob Storage, Cosmos DB, PostgreSQL, etc.).
- Request context and optional OpenTelemetry are configured in
  `backend/src/app/middleware` when `CONTAINER_APP_HOSTNAME` is set.

---

## Environment Variable Mapping

- Backend settings are read directly from environment variables (e.g. `API_KEY`, `POSTGRES_HOST`).
- Docker compose provides these values to the backend container (see `docker-compose.yml`).
- `BACKEND_API_KEY` is the shared secret between the frontend proxy and backend
  HTTPBearer validation.

---

## Development Workflow

**Both backend and frontend run in Docker with hot reload:**

```bash
# Start all services with hot reload (MANDATORY - use ./up.sh)
./up.sh
```

> ⚠️ **MANDATORY:** Always use `./up.sh` and `./down.sh` instead of `docker compose`
> directly. These scripts:
> - Add `--watch` by default for hot reload
> - Prune Docker resources when using `--build`
> - Provide consistent logging and startup experience

This works with [Docker Compose `watch`](https://docs.docker.com/compose/how-tos/file-watch/), which automatically syncs the changed files with the conainer. This is different from a mount, because it can also watch for specific files and rebuild the container if they change.

| Service   | Source sync?       | Hot Reload?            | Auto Rebuild?                |
| --------- | ------------------ | ---------------------- | ---------------------------- |
| Backend   | ✅ `./backend/src`  | ✅ Yes (auto-restart)   | ✅ On `package.json` change   |
| Frontend  | ✅ `./frontend/src` | ✅ Yes (Next.js dev)    | ✅ On `pyproject.toml` change |
| Databases | ❌ Docker volumes   | ❌ Persistent, isolated | ❌ No                         |

The frontend container uses a `dev` target, which is a simplified Dockerfile that just installs all dependencies and runs `pnpm dev`.

---

## Disk Space Management

Development machines (and especially GitHub Codespaces) have limited disk space. Repeated Docker rebuilds can leave behind **dangling images** that quickly consume space.

### Preventive maintenance (recommended)

- **MANDATORY:** When rebuilding Docker images, always use `./scripts/compose-build.sh` (it prunes dangling images automatically before every build).
  - **Do not** run `docker compose build ...` directly if you want pruning to be guaranteed.

### Disk hygiene

`./down.sh` auto-prunes dangling images and build cache safely (it never
touches named project volumes). Pass `--keep-disk` to skip that prune, and use
the `scripts/compose-clean*.sh` scripts for full wipes (destructive — they
delete local database data).

### Container has stale files (e.g. after deleting a source file)

Docker Compose `develop.watch` (`action: sync`) propagates additions and
modifications from host to container but never deletions. After deleting a
file on the host, the container retains the stale copy in its image layer,
and inside-container builds (`pnpm typecheck` / `pnpm build`) fail on
imports to files that no longer exist on disk.

```bash
# Rebuilds the image (cached — deleted files invalidate the COPY layer hash)
# and force-recreates the container.
bash scripts/rebuild-service.sh frontend
```

### `pnpm build` (and `pnpm build:docker`) currently broken upstream

`next@16.2.6` build fails during static export of `/_global-error` with
`TypeError: Cannot read properties of null (reading 'useContext')`. Known
upstream bug — no maintainer fix as of writing. See
[#84994](https://github.com/vercel/next.js/issues/84994),
[#85668](https://github.com/vercel/next.js/issues/85668),
[#86178](https://github.com/vercel/next.js/issues/86178),
[#87719](https://github.com/vercel/next.js/issues/87719). Local
verification path until upstream ships a fix:

```bash
cd frontend
pnpm format && pnpm lint && pnpm typecheck
# Plus dev-server smoke test on the changed routes — the dev server is
# unaffected; only next build's static-export step trips on this.
docker logs --tail 40 invoice-workshop-frontend-1
```

CI still runs raw `pnpm build` because the CI environment handles export
differently and the bug doesn't always reproduce there. When upstream ships
a fix, remove this section + the matching note in `frontend/AGENTS.md`.

### Full cleanup (destructive)

```bash
# Tears down containers/images/volumes (includes database data)
bash scripts/compose-clean.sh
```

---

## Command Execution Guidelines

When running shell commands, **always use timeouts for commands that might hang or take a long time**. This prevents the agent from getting stuck indefinitely.

### Commands That Need Timeouts

Use timeouts (via `timeout` command or `block_until_ms` parameter) for:

- **Docker operations**: `docker compose up`, `docker build`, `docker pull`
- **Package installations**: `npm install`, `pnpm install`, `pip install`
- **Long-running processes**: dev servers, watch modes, database operations
- **Network-dependent commands**: API calls, downloads, health checks
- **Test suites**: `pytest`, `pnpm test`, especially with coverage

### Timeout Strategies

1. **Background long-running processes**: Use `block_until_ms: 0` to immediately background dev servers and watchers, then monitor the terminal file for output.

2. **Set reasonable timeouts**: For commands expected to complete:
   ```bash
   # Use the timeout command for shell operations
   timeout 60 docker compose build   # 60 second timeout
   timeout 30 pnpm install           # 30 second timeout
   ```

3. **Monitor backgrounded commands**: Read the terminal file periodically to check status. Kill hung processes using the PID from the terminal file header.

4. **Fail gracefully**: If a command times out, report the issue rather than retrying indefinitely.

### Example Patterns

```bash
# BAD: Can hang indefinitely waiting for build
docker compose up backend

# GOOD: Background immediately, monitor separately
# Use block_until_ms: 0, then read terminal file to check status

# BAD: npm install can hang on network issues
npm install

# GOOD: Use timeout
timeout 120 npm install
```

⚠️ **Never run potentially blocking commands without a timeout strategy.** If a command is expected to run indefinitely (like a dev server), background it immediately and monitor via terminal files.

---

## Convenience Scripts

### Main Entry Points (Root)

- **`./up.sh`**: Start the application (MANDATORY - use instead of `docker compose up`)
- **`./down.sh`**: Stop the application (MANDATORY - use instead of `docker compose down`)

### Backend Scripts

- **`./backend/run-tests.sh`**: Run backend integration tests against real services

### Build and Maintenance Scripts (scripts/)

- `scripts/compose-build.sh`: Build images with BuildKit (faster, prunes before build)
- `scripts/compose-clean.sh`: Tear down compose, remove images, delete all compose volumes in a loop, then prune unused images. **Destructive** (wipes local data).
- `scripts/compose-clean-postgres.sh`: Stop/remove Postgres services and delete the Postgres volume.
- `scripts/compose-clean-cosmos.sh`: Stop/remove Cosmos DB services and delete the Cosmos DB volumes.
- `scripts/compose-clean-blob.sh`: Stop/remove blob storage services and delete blob storage volumes.
- `scripts/env-setup.sh`: Bootstrap local dev environment (creates `.env`, installs hooks, prints compose summary).
- `scripts/docker-vuln-scan.sh`: Scans Docker images for security vulnerabilities (see below).

---

## Docker Vulnerability Scanning

A `scripts/docker-vuln-scan.sh` exists that scans the frontend and backend
images with [Trivy](https://trivy.dev/). It's optional for the workshop — run
`bash scripts/docker-vuln-scan.sh` if you want to check images for known
vulnerabilities.

---

## Test Container Code Sync

The `backend-test` container uses **volume mounts** to always run tests against
your latest local code:

```yaml
# From docker-compose.yml - these volumes are already configured
volumes:
  - ./backend/src:/usr/src/app/src:ro
  - ./backend/conftest.py:/usr/src/app/conftest.py:ro
  - ./backend/pyproject.toml:/usr/src/app/pyproject.toml:ro
  - ./backend/alembic:/usr/src/app/alembic:ro
```

**What this means:**
- Edit any `.py` file → run tests immediately (no rebuild needed)
- Add/modify test files → run tests immediately (no rebuild needed)
- Change database migrations → run tests immediately (no rebuild needed)

**When you MUST rebuild the test image:**

```bash
# Rebuild is required after adding new Python dependencies
bash scripts/compose-build.sh backend-test

# Or rebuild both backend images together
bash scripts/compose-build.sh backend backend-test
```

Rebuild is needed when:
- Adding new packages to `pyproject.toml` (e.g., `pip install newpackage`)
- Changing the `Dockerfile`
- Modifying `entrypoint.sh` or other build-time files

**Why volumes for tests vs. `watch` for dev server:**
- The dev server uses `docker compose --watch` which syncs files to running containers
- The test container is one-shot (`docker compose run`), so `watch` doesn't apply
- Volume mounts give instant access to the latest code for one-shot containers

**Method 1: Convenience Script** (recommended for manual runs):
```bash
# Run all integration tests
./backend/run-tests.sh

# Skip slow tests for faster iteration
./backend/run-tests.sh --fast

# Run specific module tests
./backend/run-tests.sh -- src/app/modules/custom/my_feature/tests.py -v
```

**Method 2: Direct Docker Compose** (when services are already running):
```bash
# Run all tests
docker compose --profile test run --rm backend-test

# With pytest arguments (use PYTEST_ARGS, not direct override)
PYTEST_ARGS="-k test_something" docker compose --profile test run --rm backend-test
```

⚠️ **Never run** `docker compose ... backend-test pytest ...` — this bypasses migrations.

---

## Quick Reference

| Task                              | Command                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------- |
| **Start all services**            | `./up.sh` (MANDATORY - adds --watch by default)                               |
| **Stop all services**             | `./down.sh` (MANDATORY)                                                       |
| Start backend only                | `./up.sh -d backend`                                                          |
| **Run tests (manual)**            | `./backend/run-tests.sh` (starts services, runs migrations, cleans up)        |
|  Run tests (skip slow)             | `./backend/run-tests.sh --fast`                                   |
| Run specific module tests         | `./backend/run-tests.sh -- src/app/modules/custom/my_module/tests.py -v`      |
| Run tests (services running)      | `docker compose --profile test run --rm backend-test`                         |
| Run pre-commit                    | `prek run --all-files`                                                        |
| **Update OpenAPI clients**        | `./scripts/update-api-client.sh`                                              |
| Run frontend dev server           | `cd frontend && pnpm dev`                                                     |
| Run frontend lint                 | `cd frontend && pnpm lint`                                                    |
| Run frontend type check           | `cd frontend && pnpm typecheck`                                               |
| Run frontend build (host)         | `cd frontend && pnpm build` (requires env in shell + see Next 16 bug below)   |
| Run frontend build (Docker)       | `cd frontend && pnpm build:docker` (env works but trips Next 16 bug below)    |
| Resync a container with host source | `bash scripts/rebuild-service.sh <service>` (after deleting host files)     |
| **Run frontend checks**        | `cd frontend && pnpm lint && pnpm typecheck && pnpm build`                    |
| Run vulnerability scan            | `bash scripts/docker-vuln-scan.sh`                                            |
| Skip vuln scan on commit          | `SKIP_VULN_SCAN=1 git commit -m "..."`                                        |

> ⚠️ **Always run `./scripts/update-api-client.sh` after modifying backend
> endpoints**, and before making frontend changes. This ensures TypeScript types are in sync
> with the backend schema.
