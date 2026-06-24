# Invoice Intake — Workshop Starter

A minimal, public **full-stack workshop starter**: a FastAPI backend and a
Next.js frontend wired together with Docker Compose. It gives you the plumbing —
a server-side API proxy, a generated TypeScript SDK, a few example backend
modules, and a dev login shell — and then gets out of your way so you can build
features.

> **Read [`WORKSHOP.md`](./WORKSHOP.md) first.** It explains the purpose, what
> the starter intentionally does **not** include, and the constraints (this repo
> is public — no secrets, no company-internal content).

## The workshop exercise

Build **invoice intake from PDF**: upload a PDF invoice → extract structured
fields (vendor, invoice number, date, line items, totals) → show and optionally
store the result. The starter ships **none** of this feature — building it is
the point. See [`docs/project.md`](docs/project.md) and
`.agents/skills/build-app/SKILL.md`.

## Architecture at a glance

- Docker Compose runs: `postgres`, `cosmosdb` (Mongo-API), `blobstorage`
  (Azurite), `backend`, `frontend`, and browser dev viewers (`dbviewer`,
  `cosmosdbviewer`, `blobstorageviewer`, `logviewer`).
- **Backend**: FastAPI (`backend/src/asgi.py`) with auto-discovered modules and
  HTTPBearer (shared API-key) auth.
- **Frontend**: Next.js App Router (`frontend/src/app`) with a dev stub login, an
  `/api` proxy, and a generated OpenAPI SDK.

### Request flow

1. Browser hits Next.js.
2. The proxy (`frontend/src/proxy.ts`) requires a session cookie (set by the dev
   stub login — see `frontend/src/auth`). There is **no** identity provider.
3. The frontend calls `/api/*`, handled by
   `frontend/src/app/api/[...path]/route.ts`.
4. The proxy injects `Authorization: Bearer ${BACKEND_API_KEY}` and forwards to
   `BACKEND_API_URL`.
5. FastAPI validates the key and routes to a module under `/core/` or `/custom/`.

## Backend modules

Example **core** modules (read-only — treat as a library):

| Module | Prefix | Purpose |
|--------|--------|---------|
| `postgresql` | `/core/postgresql/*` | Relational CRUD — example data module |
| `cosmosdb` | `/core/cosmosdb/*` | Document storage — example data module |
| `blob-storage` | `/core/blob-storage/*` | File upload/download — example data module |
| `info` | `/core/info/*` | Health, swagger helpers, on-demand test runner |

Build your own feature as a **custom** module under
`backend/src/app/modules/custom/` (see `backend/AGENTS.md` and the `build-app`
skill). There is no pre-built AI/PDF module — wire your own integration and keep
any API key in `.env` (never commit it).

## Authentication (dev stub)

This template ships a **fake local login** — clicking "login" sets a session
cookie holding a hardcoded dev user; logout clears it. The login → protected
route → logout flow is real and demonstrates the proxy/guard pattern, but there
is no Azure AD / MSAL / OAuth. Swap in a real provider
(`frontend/src/auth/`) when taking the app beyond the workshop.

## Quick start

```bash
cp .env.example .env
./up.sh
```

> Always use `./up.sh` / `./down.sh` instead of `docker compose` directly — they
> add `--watch` (hot reload) and handle disk hygiene.

URLs (local):
- Frontend: http://localhost:3000
- Backend: http://localhost:8000 · docs at http://localhost:8000/docs
- Postgres viewer (pgweb): http://localhost:8081
- Cosmos viewer (mongo-express): http://localhost:8082
- Blob viewer: http://localhost:8083
- Logs (Dozzle): http://localhost:8084

## Frontend ↔ Backend SDK

After changing any backend endpoint, regenerate the typed client (backend must
be running):

```bash
./scripts/update-api-client.sh
```

The generated SDK lives in `frontend/src/lib/backend/generated` (never edit by
hand). Call it from **client components only**. See
`.agents/skills/schema-change/SKILL.md`.

## Testing

Backend integration tests run against the real local services:

```bash
./backend/run-tests.sh --fast            # quick iteration
./backend/run-tests.sh -- src/app/modules/custom/<module>/tests.py -v
```

## Repository layout

```text
.
├── WORKSHOP.md           # Repo charter — READ FIRST
├── backend/              # FastAPI service
├── frontend/             # Next.js app
├── docs/                 # Project + feature docs
├── docker-compose.yml    # Local stack
├── scripts/              # Setup / compose helpers
├── CHANGELOG.md          # App changelog
└── .env.example          # Local env template
```

## Documentation index

- Charter: `WORKSHOP.md`
- Project overview: `docs/project.md`
- Backend conventions: `backend/README.md`, `backend/AGENTS.md`
- Frontend conventions: `frontend/README.md`, `frontend/AGENTS.md`
- Universal rules / connection map: `AGENTS.md`
