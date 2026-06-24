# WORKSHOP.md — Repository Charter (READ FIRST)

> **This is the authoritative purpose document for this repository.**
> Any AI agent or human contributor MUST read and respect this file before
> making changes. It overrides assumptions inherited from the original
> template's `README.md`, `AGENTS.md`, `docs/project.md`, and skills — those
> still describe the *full* private template, which this repo is being
> deliberately stripped down from.

---

## 1. What this repo is

This repository started life as a **private full-stack project template**
(FastAPI backend + Next.js frontend + durable-workflow orchestrator, wired for
Azure AD SSO, Azure OpenAI, Cosmos DB, Blob Storage, Document Intelligence,
Speech, etc.).

It is being converted into a **public, minimal workshop starter kit**.

- **Audience:** workshop participants (external, not employees).
- **Visibility:** PUBLIC GitHub repository.
- **Goal of the workshop:** participants build an **invoice intake
  application** — upload a PDF invoice, extract structured data from it with
  AI, and persist/display the result.

The starter is a **near-blank canvas, not a working app.** It must give
participants the *technology wiring and patterns* — the running
frontend + backend + docs stack, the AGENTS.md guidance, the SDK/proxy/module
plumbing, and one or two tiny examples of "how a feature is built here" — and
then get out of the way. Participants build the invoice feature (and anything
else) from almost nothing, learning the stack by extending it.

**Guiding principle:** when unsure whether to keep something, lean toward
removing it. A participant adding a missing piece is a *good* learning moment;
a participant deleting confusing pre-built machinery is wasted time. Prefer the
emptiest scaffold that still demonstrates each technology once.

## 2. Hard constraints (because it goes public)

1. **No company secrets, ever.** No real API keys, connection strings, tenant
   IDs, client IDs, internal URLs, customer names, or proprietary documents.
2. **No company-internal knowledge.** Strip anything that only makes sense
   inside the originating organization (the original private template's
   upstream/fork relationship, internal client deliverables, internal
   processes).
3. **`.env` must never be committed.** It is gitignored (`.gitignore` lines
   2–4). Only `.env.example` ships, and it must contain placeholders only.
4. **External AI is BYO-key.** The invoice feature needs an LLM. Participants
   supply their own `AZURE_OPENAI_*` (or equivalent) key at runtime via `.env`.
   Never commit one.
5. This repo is **not** a git repository yet — when published, do a fresh
   `git init`. There is no prior history to scrub, which keeps publishing safe.

## 3. What the participants build

A single coherent feature, end to end, as the workshop exercise:

**Order intake from customer PDFs** → upload a purchase order PDF (from any of
4 fictional European customers — German, Swiss, French, Swedish — each with
different formats and terminology) → extract line items, alloy specifications,
dimensions, quantities, delivery dates → reconcile against an internal product
catalog (35 aluminum extrusion profiles) → produce EDIFACT ORDERS output
compatible with a legacy ERP → show results in a reconciliation UI, flagging
ambiguous matches for human review.

**The starter ships almost none of this.** It provides the running stack, the
AGENTS.md conventions, and minimal "this is how a module / a page is built
here" examples. Participants implement the entire order intake feature themselves.
The starter must NOT contain a pre-built order intake or extraction feature — that
is the exercise.

Source materials (meeting transcript, example orders, catalog, EDI spec) are in
`docs/sources/`.

---

## 4. KEEP / STRIP decisions

These decisions are settled. Do not relitigate them; if a change is needed,
update this file first.

### 4.1 Authentication → **Trivial dev stub login**

- **Remove** all Azure AD / MSAL / RBAC machinery:
  `frontend/src/auth/msal.ts`, `tokens.ts`, `frontend/src/auth/roles/*`,
  the Graph API role auto-creation, the `AZURE_AD_*` env vars, the Codespace
  redirect-URI scripts (`scripts/codespace-redirect-uri-*.sh`), and the
  `.github/workflows/codespace-cleanup.yml` flow.
- **Keep** the *shape* of the auth layer — `session.ts`, the `proxy.ts` guard,
  the `(private)` route group, `requireSession()` — but back it with a
  **fake/no-op local login** (a hardcoded dev user / cookie). This teaches the
  proxy + protected-route pattern without any cloud identity provider.
- The backend proxy's `Authorization: Bearer ${BACKEND_API_KEY}` injection
  **stays** — it's a local shared secret, not Azure, and demonstrates the
  server-side API-key pattern.

### 4.2 Orchestrator → **Remove entirely**

- Delete the `orchestrator/` service, its `docker-compose.yml` entries
  (`orchestrator`, `orchestrator-inspector`), the frontend orchestrator SDK
  (`frontend/src/lib/orchestrator/`), the `/api/workflows` proxy, the
  `deploy-orchestrator.yaml` and `ci-orchestrator.yaml` workflows, and
  `orchestrator/AGENTS.md` / `orchestrator/README.md`.
- Invoice intake is a **plain synchronous backend endpoint** — no durable
  workflows needed for the workshop.

### 4.3 Backend modules

`backend/src/app/modules/core/` currently has: `async_wrapper`, `audio`,
`blob_storage`, `consumptions`, `cosmosdb`, `evaluate`, `info`, `notifications`,
`openai`, `pdf`, `postgresql`, `search`.

Under the near-blank-canvas principle, the backend ships **only enough modules
to demonstrate "how a module is built here."** The baseline is the three
storage examples (`postgresql`, `cosmosdb`, `blob_storage`) plus `info` —
covering relational, document, and file persistence so participants have a
worked module pattern for each. All AI/PDF integration is theirs to build.

| Module | Action | Reason |
|---|---|---|
| `postgresql` | **Keep** | Relational/CRUD module example + the persistence story |
| `cosmosdb` | **Keep** | Document-store module example (local Mongo-API container, no real Azure) |
| `blob_storage` | **Keep** | File-storage module example (Azurite locally — emulator, no secret) |
| `info` | **Keep** | Health/swagger/test-runner infra; not domain-specific |
| `openai` | **Remove** | AI integration is the participant's job to build, not pre-supplied |
| `pdf` | **Remove** | PDF parsing is a participant exercise |
| `async_wrapper` | **Remove** | Async job mgmt unneeded once orchestrator is gone |
| `audio` | **Remove** | Out of scope |
| `consumptions` | **Remove** | Internal usage/billing tracking |
| `evaluate` | **Remove** | Tied to the internal "Evaluation" QA feature |
| `notifications` | **Remove** | Push/VAPID complexity not needed |
| `search` | **Remove** | Semantic search out of scope |

#### RESOLVED → strip `pdf` and `openai`; keep the three storage modules + `info`

Final decisions:
- **Remove `pdf` and `openai`.** Building the AI/PDF integration is the
  exercise, so it must not be pre-supplied.
- **Keep `postgresql`, `cosmosdb`, `blob_storage`, `info`.** The three storage
  modules are the "how a module is built here" examples (one per persistence
  technology); `info` is infra. None embed company/domain logic.

When trimming the kept modules, strip any *internal/domain* logic that rode
along (e.g. evaluation-specific helpers) — keep only the generic
relational / document / file-storage capability.

> Reminder: `core/` is normally treated as read-only. For this one-time
> conversion, that rule is **suspended** — we are deleting/curating core
> modules by design. After the conversion, kept modules go back to read-only.

### 4.4 Backend services

`backend/src/app/services/` has: `audio`, `blob_storage`, `cosmosdb`,
`document_intelligence`, `openai`, `pdf`, `postgresql`, `scheduler`,
`semaphore`, `speech`.

- **Keep:** `postgresql`, `cosmosdb`, `blob_storage` (back the kept modules),
  and `semaphore` (generic concurrency helper).
- **Remove:** `openai`, `pdf` (modules stripped — §4.3),
  `document_intelligence` (Azure paid OCR), `speech` (Azure), `audio`,
  `scheduler` (recurring tasks out of scope).

### 4.5 Skills (`.agents/skills/`)

Keep a small curated set. Two tiers:

**Operational (needed for the scaffold to work and for agents to help):**
`backend-development`, `frontend-development`, `docker-operations`,
`debugging`, `changelog-management`, `schema-change`, `ui-exploration`.

**Workshop feature skills (the explicitly requested subset, to be SIMPLIFIED):**
- `excalidraw` — keep (diagram/mockup creation).
- `build-app` — keep but **trim to a "very basic" version**: drop the
  orchestrator/workflow steps, drop Azure/RBAC steps, reduce to
  document → backend endpoint → SDK regen → frontend page.
- `build-docs` — keep but **trim to a "very basic" version**: minimal
  feature-doc + diagram pipeline, no internal-source ingestion.

**Remove:** `orchestrator-workflows` (orchestrator gone), `app-identity-rbac`
(Azure), `contribute-upstream`, `sync-upstream` (internal fork machinery),
`generate-pdf-report`, `scheduler-service`, `media-to-transcript`,
`update-docs` (internal source-ingestion pipeline), `documentation-standards`
(fold essentials into `build-docs` if needed), `web-design-guidelines` and
`vercel-react-best-practices` (optional/heavy — remove unless a participant
asks; the 88KB react skill in particular).

### 4.6 Azure / cloud surface to strip beyond auth

- `document_intelligence` and `speech` services + their `AZURE_*` env vars.
- `AZURE_STORAGE_*` real-account vars (keep only the local Azurite emulator
  config, which needs no real account).
- **Not stripped:** `cosmosdb` and `blob_storage` stay (§4.3). They run fully
  locally — Cosmos via the Mongo-API container, Blob via Azurite — so no real
  Azure account is needed. Keep `AZURE_COSMOSDB_CONNECTION_STRING` pointed at
  the local `cosmosdb` container and the Azurite vars at the local emulator;
  these are local defaults, not secrets.
- **All GitHub Actions removed** (`.github/` is gone): deploy workflows
  referenced Azure infra, and the workshop isn't deployed anywhere, so CI adds
  no value. Quality is enforced via local checks only (`prek`, `pnpm lint`/
  `typecheck`, `./backend/run-tests.sh`). Docs reference local checks, not CI.

### 4.6b Compose services (`docker-compose.yml`)

Twelve services today. With cosmos and blob kept, the only removals are the two
orchestrator services — everything else (app + stores + dev viewers) stays.

| Service | Action | Reason |
|---|---|---|
| `postgres` | **Keep** | Backs `postgresql` |
| `cosmosdb` | **Keep** | Backs `cosmosdb` (local Mongo-API) |
| `blobstorage` (Azurite) | **Keep** | Backs `blob_storage` |
| `backend` | **Keep** | Core |
| `frontend` | **Keep** | Core |
| `backend-test` | **Keep** | Integration-test runner (part of the taught workflow) |
| `dbviewer` (pgweb) | **Keep** | Browser UI to inspect Postgres |
| `cosmosdbviewer` (mongo-express) | **Keep** | Browser UI to inspect Cosmos |
| `blobstorageviewer` | **Keep** | Browser UI to inspect blobs. ⚠️ Runs `linux/amd64` via emulation on Apple Silicon — slower; acceptable but the most droppable if it causes friction |
| `logviewer` (Dozzle) | **Keep** | Browser UI for container logs — lowers the Docker-debugging floor |
| `orchestrator` | **Remove** | §4.2 |
| `orchestrator-inspector` | **Remove** | Follows orchestrator |

### 4.7 Branding / domain content to neutralize

- App identity `MLM` / `Template App` → a neutral workshop name
  (e.g. "Order Intake Workshop"). Update the four sync points:
  `docs/project.md`, `backend/src/settings.py`,
  `frontend/src/config/app-identity.ts`, `frontend/src/messages/*.json`.
- `docs/project.md` documents the **Order Intake** workshop exercise
  for AluProfil Systemtechnik GmbH — an aluminum extrusion manufacturer
  needing to intake customer PDF orders, reconcile them against a product
  catalog, and produce EDIFACT output for a legacy ERP.
- Source materials (meeting transcript, customer orders, catalog, EDI spec)
  live under `docs/sources/`.

### 4.8 Frontend → strip feature pages to a near-blank shell

The frontend currently ships demo/feature pages: `extract/`, `classify/`,
`evaluate/{extract,classify}/`, `consumptions/`, and a `components/` gallery.

- **Remove** all domain feature pages (`extract`, `classify`, `evaluate`,
  `consumptions`). They are either internal-feature demos or pre-build the
  workshop exercise.
- **Keep** the bare shell: the `(public)` landing page, the `(private)` layout
  with the dev-stub session guard, the header/nav, the SDK + `/api` proxy
  plumbing, and i18n scaffolding.
- **Keep ONE tiny example page** that demonstrates the "client component →
  generated SDK → backend module" round-trip against the `postgresql` (or
  `info`) module — so participants have a single worked example of the pattern,
  nothing more.
- The `components/` gallery: keep a *trimmed* version only if it stays small;
  otherwise remove. Lean toward removing.
- Remove push-notification / PWA wiring tied to the removed `notifications`
  module (service worker subscription flow, `NotificationSettingsDialog`).

### 4.9 Component AGENTS.md files → **KEEP**

`backend/AGENTS.md` and `frontend/AGENTS.md` **stay** — they teach the
conventions participants must follow (module layout, typing, SDK rules, file
placement). Update them so they no longer reference removed pieces (orchestrator,
Azure, removed modules), but keep the per-component guidance intact. The
`orchestrator/AGENTS.md` and `docs/AGENTS.md` follow their components
(orchestrator gone → remove; docs simplified → keep, trimmed).

---

## 5. Conversion plan (ordered checklist)

Execute in this order; each step is reviewable. **Status: NOT STARTED — awaiting
review of this charter.**

- [x] **0. Adopt this charter** — `WORKSHOP.md` is pointed to by a "READ FIRST"
      callout at the top of `AGENTS.md` (which opencode reads natively) and from
      `README.md`, so agents and contributors see it up front. **DONE.**
- [ ] **1. Remove orchestrator** (service, compose, frontend SDK, proxy, CI,
      deploy, docs, skill).
- [ ] **2. Replace Azure auth with dev stub login** (strip MSAL/RBAC, keep
      session/guard shape, wire fake local user).
- [ ] **3. Trim backend modules** to `postgresql, cosmosdb, blob_storage, info`
      (§4.3). Delete the rest + their tests + registrations; strip any
      internal/domain logic from the kept ones.
- [ ] **3b. Strip frontend feature pages** to the near-blank shell (§4.8):
      keep landing + private layout + one example page; remove
      extract/classify/evaluate/consumptions/PWA.
- [ ] **4. Trim backend services** to `postgresql, cosmosdb, blob_storage,
      semaphore`; remove `openai`/`pdf` and Azure OCR/Speech/`audio`/`scheduler`.
- [ ] **5. Strip Azure env vars** from `.env.example`, `docker-compose.yml`,
      `backend/src/settings.py`, and frontend env validation.
- [ ] **6. Trim compose** (§4.6b): remove only `orchestrator` +
      `orchestrator-inspector`; keep postgres, cosmosdb, blobstorage, backend,
      frontend, backend-test, and all three dev viewers + logviewer.
- [ ] **7. Curate skills** to the keep-list; simplify `build-app` and
      `build-docs` to their "very basic" forms.
- [ ] **8. Neutralize branding & docs** — rebrand app identity, rewrite
      `docs/project.md` around invoice intake, delete internal source artifacts.
- [ ] **9. Remove deploy workflows + internal upstream/fork references.**
- [ ] **10. Update `README.md` and `AGENTS.md`** to describe the slim workshop
      repo (and to point at this file).
- [ ] **11. Final secret sweep** — grep for `AZURE`, real keys, internal names,
      `mlm`; confirm `.env` is not tracked; verify the stack still boots
      (`./up.sh`) and the kept backend endpoints respond.

## 6. Guardrails for agents working in this repo

- **Do not reintroduce Azure SSO, MSAL, RBAC, the orchestrator, or removed
  modules** "to be helpful." If a participant needs them, that's their choice
  to add — the starter stays minimal.
- **Never commit a real secret or an internal name.** When in doubt, use an
  obvious placeholder and note it in `.env.example`.
- The original `AGENTS.md`/`README.md`/skills still describe the *full* private
  template. Where they conflict with this charter, **this charter wins.** Once
  the conversion is done, those files should be rewritten to match.
- Keep the kept `core/` modules read-only again after conversion.
