# Build Application from Documentation (Workshop — Basic)

A minimal, end-to-end recipe for building a feature in this workshop starter:
**docs → backend module → SDK → frontend page**. This is the "very basic"
version used in the Invoice Intake workshop. There is no orchestrator, no Azure,
and no RBAC — keep features simple and synchronous.

Read `WORKSHOP.md` (repo root) for the overall purpose and constraints before
building.

## When to Use

Use this when implementing a feature (e.g. invoice intake) from a short spec in
`docs/`. For deeper conventions, read the component skills:
`.agents/skills/backend-development/SKILL.md` and
`.agents/skills/frontend-development/SKILL.md`. For the schema↔SDK flow, read
`.agents/skills/schema-change/SKILL.md`.

## The pipeline

1. **Write a short spec** in `docs/` describing the feature: what the user does,
   the inputs/outputs, and any data you need to store. Keep it to a page.

2. **Build a backend custom module** under
   `backend/src/app/modules/custom/<feature>/` with the mandatory layout:
   ```
   custom/<feature>/
   ├── routes.py        # FastAPI router — thin, delegates to logic/
   ├── tests.py         # integration tests for every endpoint
   ├── logic/main.py    # business logic
   └── schemas/io.py    # one input + one output Pydantic model per endpoint
   ```
   - Every endpoint needs dedicated input/output Pydantic models with
     `description` and `examples` on each field.
   - Use the kept core modules as building blocks via their HTTP endpoints or
     shared services: `postgresql`, `cosmosdb`, `blob_storage`. (There is no
     pre-built AI/PDF module — wire your own integration if the feature needs
     one, and keep any API key in `.env`, never committed.)
   - Modules are auto-registered by folder name (underscores become hyphens in
     the route), so just create the folder.

3. **Add a DB layer if you need persistence**: `db/models.py` (SQLAlchemy) +
   `db/queries.py`, and an Alembic migration. Migrations run automatically on
   backend startup via `entrypoint.sh`.

4. **Test the backend**: `./backend/run-tests.sh --fast -- src/app/modules/custom/<feature>/tests.py -v`

5. **Regenerate the SDK** (backend must be running):
   `./scripts/update-api-client.sh`
   This rebuilds `frontend/src/lib/backend/generated`. Never hand-write SDK
   types or cast around missing fields — regenerate first (see the
   `schema-change` skill).

6. **Build the frontend page** under `src/app/(private)/<feature>/`:
   - A server component `page.tsx` that calls `await requireSession()` and
     renders a client component.
   - A client component (`"use client"`) that calls the generated SDK
     (`backend.<module>.<method>(...)`) — SDK calls happen in client components
     only, never server components.
   - Install any shadcn component before importing it: `pnpm shadcn add <name>`.

7. **Validate**: `cd frontend && pnpm lint && pnpm typecheck`, then smoke-test
   on the dev server (browse the route, watch the container logs).

8. **Update `CHANGELOG.md`** (see the `changelog-management` skill) and commit
   only after the user confirms.

## Rules to respect

- Never edit `backend/src/app/modules/core/**` — treat it as read-only.
- All data flows through real backend endpoints — no mock data in the frontend.
- Keep files within the size limits (Python ≤600 lines, TS ≤500 lines).
- All user-facing text uses i18n keys in `src/messages/*.json`.
