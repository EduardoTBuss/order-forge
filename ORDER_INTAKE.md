# Order Intake — Run & Use Guide

The **Order Intake** feature: upload a customer purchase-order PDF → extract the
line items with AI (or a deterministic parser) → reconcile them against the
internal product catalog (35 aluminium profiles, `AE-XXXX-XXX` codes) → review on
a reconciliation screen → generate **EDIFACT ORDERS D.96A** for the legacy ERP.

> Context & rules live in [`WORKSHOP.md`](./WORKSHOP.md) (charter) and
> [`docs/architecture/`](./docs/architecture/) (architecture). This file is the
> **operator's run/use guide**.

---

## 1. Prerequisites

- **Docker Desktop** running (Linux containers). Give it **≥ 4 GB RAM** — for the
  local LLM bump to 6–8 GB (Settings → Resources → Memory).
- **Git Bash** (or any POSIX shell) on Windows. The repo is normalised to LF
  (`.gitattributes`); do not re-introduce CRLF in `*.sh`.
- No cloud account needed — Postgres, Mongo (Cosmos API) and Blob (Azurite) all
  run locally in containers.

## 2. Run from zero

```bash
# 1. Configure env (never commit .env — it is gitignored).
cp .env.example .env                # placeholders are fine for the local stack

# 2. Bring the whole stack up (backend, frontend, 3 stores, viewers, ollama).
./up.sh                             # foreground + hot reload; Ctrl+C to stop
# or detached:  docker compose up -d --build

# 3. (Optional, for the free local LLM) pull a small model into Ollama:
docker compose exec ollama ollama pull qwen2.5:1.5b

# 4. Open the app:
#    http://localhost:3000/order-intake     (dev-stub login is automatic)

# Stop everything:
./down.sh
```

First boot runs the database migrations automatically (`alembic upgrade head`)
and seeds the 35-row catalog. The login is a **dev stub** (a local cookie) — there
is no real identity provider.

### URLs

| What | URL |
|------|-----|
| **App (Order Intake)** | http://localhost:3000/order-intake |
| Backend API | http://localhost:8000 (Bearer `backend-secret-api-key`) |
| API docs (Swagger) | http://localhost:8000/docs |
| Postgres viewer (pgweb) | http://localhost:8081 |
| Mongo viewer (mongo-express) | http://localhost:8082 |
| Blob viewer (Azurite) | http://localhost:8083 |
| Container logs (Dozzle) | http://localhost:8084 |

## 3. Use it

1. **Create a customer** — click **"+ New customer"**, pick an *extraction
   strategy* (see §4), and save. (The catalog is pre-seeded; customers are not —
   you register them.)
2. **Upload a PDF** — choose the customer, pick a PDF, **Upload**. Sample PDFs
   live in `docs/sources/orders/<customer>/`.
3. **Reconcile** — the screen shows the original PDF on the left and the extracted
   & reconciled lines on the right. Each line shows:
   - the **resolved internal code** (`AE-…`) and the **match tier**
     (`exact` / `dimension` / `fuzzy` / `manual` / `learned`);
   - **`Read:`** — the code the AI transcribed from the PDF (a cross-check only);
   - **confidence flags** (red) — `No catalog match`, `Weak match`,
     `Ambiguous unit`, **`Read code ≠ resolved`**;
   - two per-line buttons:
     - **Set** — type a code and assign it (a correction);
     - **Confirm** — one click to accept the resolved code the system guessed.
   Both **Set** and **Confirm** *teach* a per-customer mapping (see §5).
4. **Generate EDIFACT** — the button is **gated**: it only unlocks when *every*
   line has a resolved internal code (MetallSoft rejects the whole order if one
   `PIA+1` is unmapped). Generate → download the `.edi`.
5. **Clear all** — the orders list has a **Clear all** button that removes every
   order, its uploaded PDF and generated `.edi`, and the provenance. Customers,
   the learned map and the catalog are kept.

## 4. Extraction strategies (per customer)

| Strategy | Cost | Best for | Notes |
|----------|------|----------|-------|
| **Deterministic (DIN table parser)** `bauprofil_text` | free | Bauprofil's structured DIN table | 100% reliable, no AI; only that layout |
| **Local model (Ollama)** `ollama` | free | structured PDFs | small model `qwen2.5:1.5b`; weak on prose, RAM-bound |
| **External LLM (API key)** `llm_api` | your key | hard cases (French prose) | OpenAI-compatible; per-customer **key + Base URL + Model** |

For `llm_api`, the **API key never leaves the server** and is never committed.
Examples of Base URL: OpenAI `https://api.openai.com/v1`, OpenRouter
`https://openrouter.ai/api/v1`, opencode zen `https://opencode.ai/zen/v1`.

LLM defaults (overridable per customer or via `.env`):
`OI_LLM_BASE_URL` (Ollama), `OI_LLM_MODEL` (`qwen2.5:1.5b`),
`OI_LLM_API_BASE_URL`, `OI_LLM_API_MODEL`.

## 5. How matching stays correct (precision rules)

- **The internal `AE-` code is resolved from specs, never from the code the LLM
  read.** Cheap models swap digits, and a swapped digit can hit *another* valid
  code (a silent wrong product). So for LLM customers the AE is resolved by
  dimension/alloy/fuzzy, and the read code is only a **cross-check**: if it points
  at a *different* valid catalog code, the line is flagged **`Read code ≠
  resolved`**. Deterministic sources (Bauprofil prints the real code) keep
  trusting their printed code.
- **The system learns from you.** Every **Set** or **Confirm** stores a
  `(customer, the code they printed) → internal AE` mapping. The next order from
  the same customer with the same code resolves on its own (tier **`learned`**,
  no AI). This is the answer to customers whose codes never match by string.
- **Structured output** constrains the unit to `{PCE, MTR, KGM, TNE}` (the model
  cannot invent a unit), and the LLM is fed a **column-aligned markdown** render
  of the PDF so it reads the right cell.
- **EDIFACT** transliterates all free text to UNOA/ASCII (ä→ae, ß→ss, é→e…) and
  validates every `PIA+1` before emitting.

## 6. Test

```bash
./backend/run-tests.sh                                                  # full suite
./backend/run-tests.sh -- src/app/modules/custom/order_intake/tests.py -v   # this module
```

The suite runs in a container against real Postgres/Mongo/Blob.

## 7. Troubleshooting

- **UI looks stale after a change** → hard refresh (Ctrl+Shift+R); if needed
  `docker compose restart frontend` or `./down.sh && ./up.sh`.
- **Local LLM gets OOM-killed** (`llama-server killed`) → the model is too big for
  Docker's RAM. Stay on `qwen2.5:1.5b`, or raise Docker memory to 6–8 GB to use
  `qwen2.5:3b` (`OI_LLM_MODEL=qwen2.5:3b` in `.env`).
- **`alembic upgrade head\r` error / scripts fail in the container** → CRLF line
  endings. The repo is LF-normalised via `.gitattributes`; do not revert it.
- **Changed a backend endpoint?** Regenerate the SDK:
  ```bash
  docker compose exec frontend sh -c "BACKEND_API_URL=http://backend:8000 pnpm update-api-client"
  docker compose cp frontend:/app/src/lib/backend/generated/. frontend/src/lib/backend/generated/
  ```
- **Full reset of data** → use the in-app **Clear all** button, or wipe the dev DB
  rows directly (`oi_orders`, `oi_customers`, `oi_code_aliases`) keeping
  `oi_catalog`.

## 8. Endpoints (under `/custom/order-intake`)

`GET/POST/DELETE /customers` · `POST /orders` (multipart) · `GET /orders` ·
`DELETE /orders` (clear all) · `GET /orders/{id}` · `GET /orders/{id}/source-pdf`
· `PATCH /orders/{id}/lines/{line_id}` (Set/Confirm) · `POST /orders/{id}/edifact`.

## 9. Scope

Prototype scope (locked): **Bauprofil** (easy, deterministic) and **ConstruxAlu**
(hard, French prose). FensterSystem / Nordic and scanned-PDF OCR are documented
extensions, out of the prototype.
