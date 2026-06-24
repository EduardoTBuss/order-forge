---
name: schema-change
description: Canonical workflow for editing a backend Pydantic/SQLAlchemy schema and propagating it to the frontend SDK without writing temporary workaround code. Use whenever you edit any file under backend/src/app/modules/custom/**/schemas/ or **/db/models_*.py.
---

# Schema change → SDK regen → client code

When you change a backend schema (a Pydantic model, ORM model, or an endpoint
signature), the auto-generated frontend SDK becomes stale until you regenerate
it. The temptation is to write client code that "compiles around" the missing
fields with a cast, intersect, `as any`, or `// TODO: regen later` — **do not
do this** (root rule 14). Follow this flow exactly.

## The 5-step flow

1. **Edit the backend schema or model**
   - Pydantic I/O in `backend/src/app/modules/custom/<name>/schemas/io.py`
   - ORM models in `backend/src/app/modules/custom/<name>/db/models_*.py`
   - Endpoint signatures in `backend/src/app/modules/custom/<name>/routes*.py`

2. **Get the change into the running backend container**
   - Preferred — if the user has `./up.sh` watch active: edits sync automatically
     and uvicorn `--reload` picks them up. Verify with `ps -ef | grep "docker compose.*watch"`.
   - If watch is **not** active (no process, or container source isn't current):
     - For a single-file change: `docker cp <local-path> invoice-workshop-backend-1:<container-path>`
       uvicorn `--reload` notices the mtime change and reloads in ~1s.
     - For a multi-file change or anything touching `pyproject.toml`:
       `bash scripts/compose-build.sh backend` (the wrapper — never raw `docker compose build`).
   - **Never** edit files inside the container directly (`docker exec ... vi`) —
     the edit doesn't propagate back to host and gets lost on next sync/restart.

3. **Confirm the live schema reflects your change** — poll `/openapi.json`:
   ```bash
   curl -s http://localhost:8000/openapi.json \
     | python3 -c "import sys,json; d=json.load(sys.stdin); \
       print(list(d['components']['schemas']['<YourSchemaName>'].get('properties',{}).keys()))"
   ```
   Don't proceed until the new field/endpoint shows up. If it doesn't appear after
   ~10s, the file didn't sync — go back to step 2.

4. **Regenerate the SDK**
   ```bash
   ./scripts/update-api-client.sh
   ```
   This regenerates `frontend/src/lib/backend/generated/`. The script hits
   `localhost:8000`, so the backend server must be running.

   Verify the new field landed in `frontend/src/lib/backend/generated/types.gen.ts`
   before continuing.

5. **NOW write the frontend code** that uses the new field.
   - You should be able to access it via the proper generated type, no casts.
   - If you find yourself wanting `as { new_field?: X } & InvoiceItem`,
     you're back at step 1 — go finish the flow before continuing.

## Discipline (nothing enforces this — it's on you)

Nothing in this repo automatically blocks the mistake; the rule is a convention.
The failure mode to avoid: you edit a backend schema, then immediately write
frontend code that wants a field the generated SDK doesn't have yet, and
"work around" it with a cast. Don't. Finish the regen (step 4) first, then
write the client code against the real generated type.

## What counts as a workaround (and what doesn't)

Forbidden by rule 14:
- `as (InvoiceItem & { new_field?: string | null })` — pretending the SDK has the field
- `// @ts-expect-error new field, will work after SDK regen`
- `(invoice as any).new_field`
- A hand-written shim in `frontend/src/lib/backend/<name>.ts` (forbidden — use the generated typed SDK)
- A `// TODO: remove after regen` comment next to code that depends on the regen
- A useEffect that fetches the value separately because "the SDK doesn't have it yet"

Legitimate (not workarounds):
- A real fallback path that handles the field being absent in production (e.g.
  an optional invoice field like `purchase_order` → render a dash). The branch
  exists because the field is genuinely optional in the domain, not because the
  SDK is stale.
- A migration that backfills data on rollout. That's a real one-time step.
- A type cast at a system boundary (parsing external JSON, third-party SDKs).
  Not the same as casting around your own backend's types.

## When the prerequisite is heavier than a regen

If the right next step is a container rebuild (`bash scripts/compose-build.sh
backend`) or a destructive op (alembic downgrade, dropping a volume), **ask the
user first** — you have authorization to do the step, not to choose the step.
The shape of the right answer doesn't change: do the step, *then* write the
clean code. Never write the shim and continue.
