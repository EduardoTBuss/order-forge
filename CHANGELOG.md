# Changelog

This file records all changes to this repository.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
with extra conventions:

- entries are grouped by date (`## YYYY-MM-DD` headings)
- `Deprecated` and `[YANKED]` markers are not used
- every entry ends with plain `#pr` and `@user` references
- commit hashes are not listed in this file

## 2026-06-26

### Added

- "Clear all" reset for the order list. A `DELETE /custom/order-intake/orders`
  endpoint and a Clear button on the orders screen wipe every order, its uploaded
  PDF and generated `.edi` (the order-intake blob container) and the raw
  provenance documents, with a confirmation prompt and a "removed N orders / M
  files" notice. Customers, the learned code map and the catalog are kept, so you
  can immediately upload again. `#pr` @eduardotbuss
- Round-tube dimension parsing. Reconciliation now reads "Ø D × wall" (and
  "tube rond"/"round tube"/"rundrohr") as a round profile `(D, D, wall)`, so lines
  like "Tube rond Ø 40×3" resolve by dimension instead of falling to "No match".
  `#pr` @eduardotbuss

### Changed

- Reworded the `unmatched_code` confidence flag from "Code not in catalog" to
  "No catalog match — assign" (DE: "Kein Katalogtreffer — zuweisen"): it means the
  line did not resolve, which is not the same as the read code being absent from
  the catalog (the read code is often a valid code the spec resolution disagrees
  with). `#pr` @eduardotbuss


- Order Intake precision pass (section 7) — four changes that stop the LLM path
  from silently producing the wrong product or unit, and make reconciliation
  learn from the operator.
  - **(A) Resolve the internal code by specs, not by the code the model read.**
    For LLM customers the model-read `AE-XXXX-XXX` is no longer trusted to
    resolve — a cheap model swaps a digit, and a swapped digit can hit *another*
    valid catalog code (a silent wrong product, fatal in MetallSoft). The code is
    now resolved from the dimensions/alloy/fuzzy tiers, and the read code is kept
    only as a **cross-check**: when it disagrees with the spec-resolved code (and
    is itself a real catalog code) the line is flagged `code_mismatch` instead of
    resolving wrong. Deterministic sources (Bauprofil prints the real code) keep
    trusting their exact code. The reconciliation UI shows the read code next to
    the resolved one, highlighted on mismatch. `#pr` @eduardotbuss
  - **(B) Per-customer learned code map (auto-improving).** A new
    `oi_code_aliases` table maps `(customer, their printed code) -> internal AE`.
    Every operator inline edit teaches one row, so the next order from the same
    customer with the same code resolves deterministically (tier `learned`,
    trusted, no LLM) — the way Sabine's clerks "learn to recognise" repeat codes,
    and the answer to Nordic/FensterSystem codes that never match by string.
    `#pr` @eduardotbuss
  - **(C) Column-preserving PDF→markdown for the LLM path.** LLM strategies now
    feed the model a `pymupdf4llm` markdown rendering that keeps the table
    columns aligned (so the unit/quantity columns stay put and the model reads
    the right cell), falling back to the plain `pypdf` text if the lib is
    unavailable. Light and CPU-only (capped to the `pymupdf4llm` 0.0.x line so it
    pulls only PyMuPDF — no `onnxruntime`/ML layout extras, no GPU); scanned PDFs
    remain out of prototype scope. The deterministic Bauprofil parser keeps the
    raw `pypdf` text it is tuned to. `#pr` @eduardotbuss
  - **(D) Structured output with a unit enum.** The external-API extractor asks
    the provider for a JSON *schema* where `unit` is a strict enum
    `{PCE, MTR, KGM, TNE}`, so the model cannot invent a unit; providers that do
    not support `json_schema` fall back to `json_object` and then to plain text.
    French/metric unit aliases (`u`/`unité` -> PCE, `ml` -> MTR) were added to the
    normaliser as a safety net. `#pr` @eduardotbuss
- Tests for the new rules (now 79 backend tests passing): specs win over a wrong
  read code with a surfaced `code_mismatch`; a confirmed read code raises no flag;
  a customer's own non-catalog code is not a false mismatch; deterministic exact
  match stays trusted; the learned map resolves first and is taught end to end by
  an inline edit; the unit enum and `json_schema`/`json_object` fallback ordering;
  French unit aliases. `#pr` @eduardotbuss

## 2026-06-25

### Added

- Order Intake feature — Stage 1 (Bauprofil happy path, end to end). A new custom
  backend module `order_intake` ingests a customer purchase-order PDF, extracts
  its line items, reconciles them against the seeded product catalog by exact
  internal code (MetallSoft `UPPER(TRIM(...))` normalisation), and generates a
  validated EDIFACT ORDERS D.96A message. Generation is gated on every `PIA+1`
  resolving — a single unmatched code blocks the whole order, mirroring the
  MetallSoft constraint. Includes ASCII/UNOA transliteration of free-text
  segments (umlauts/accents → `ae`/`ss`/`e`…), three deterministic confidence
  signals (unmatched code, ambiguous unit, JSON≠text), and a reconciliation UI:
  upload, orders list with status badges, and a side-by-side view of the original
  PDF next to the reconciled lines with a gated "Generate EDIFACT" button and
  `.edi` download. Exercises all three stores — Blob (PDF + `.edi`), Postgres
  (orders/lines/catalog/exports), Mongo (raw extracted payload + provenance).
  `#pr` @eduardotbuss
- Day-1 spike-gate result recorded in the design: the real Bauprofil fixtures
  carry no embedded JSON (WeasyPrint output, no PieceInfo/attachments), so Stage 1
  extracts deterministically from the clean PDF text layer instead of embedded
  JSON. The customer PDFs already print AluProfil's `AE-XXXX-XXX` codes, so
  exact-match reconciliation needs no LLM on the happy path. The LLM spine is
  reserved for Stage 2 (ConstruxAlu prose). `#pr` @eduardotbuss
- Customer registry + explicit selection at upload. A new `oi_customers` table maps each customer to an extraction strategy (`bauprofil_text` deterministic vs. `llm` Stage-2 spine), seeded with the four charter customers. The upload screen now has a customer dropdown and a "New customer" form (`GET`/`POST /order-intake/customers`); the order is processed with the selected customer's strategy instead of guessing from the PDF text. Customers on the `llm` strategy return a clear "Stage 2 / needs key" message rather than a crash. `#pr` @eduardotbuss
- Stage 2 LLM extraction. An `llm` customer strategy reads any PDF's text with a small local model served by Ollama (OpenAI-compatible API) and returns structured JSON; reconciliation stays deterministic (the `PIA+1` is never produced by the model). Configurable via `OI_LLM_*` in `.env`; Ollama runs as a docker-compose service (`qwen2.5:3b` by default) so `./up.sh` brings it up. `#pr` @eduardotbuss
- Tiered reconciliation: exact code → alloy-alias + dimension → fuzzy (`rapidfuzz`). Non-exact matches are flagged `weak_match` for review; the `AE-XXXX-XXX` code always resolves to a real catalog row. `#pr` @eduardotbuss
- Operator inline editing. `PATCH /order-intake/orders/{id}/lines/{line_id}` assigns an internal code (validated against the active catalog), marking the line `manual`; the reconciliation UI gained a per-line code field and shows the match tier. `#pr` @eduardotbuss
- Three selectable extraction strategies per customer: `bauprofil_text` (deterministic), `ollama` (free local model), and `llm_api` (external OpenAI-compatible LLM using the customer's own API key, entered in the "New customer" form and stored locally — never returned by the API). Plus a units fix: the LLM prompt now maps units (Stk/pcs->PCE, m->MTR, kg->KGM, t->TNE) and a robust accent-insensitive normaliser clears the spurious "ambiguous unit" flags. `#pr` @eduardotbuss
- Customers can be deleted (`DELETE /order-intake/customers/{code}` + a per-customer delete chip in the UI). Clearer LLM errors: a provider 401 now returns a friendly "invalid API key" 400 (instead of a raw 500), and pasting a URL into the API-key field is rejected up front. `#pr` @eduardotbuss
- The `llm_api` strategy now works with any OpenAI-compatible provider, not just OpenAI: a customer can store its own base URL and model (e.g. OpenRouter `https://openrouter.ai/api/v1`) alongside its key. The "New customer" form shows base-URL and model fields when that strategy is picked. Friendlier validation too: an invalid customer code now shows a clear hint instead of a raw 422, and FastAPI error details surface as readable messages. `#pr` @eduardotbuss
- `llm_api` extraction hardened for real providers: model output wrapped in ```` ```json ```` markdown fences (or with preamble) is now parsed correctly, and `max_tokens` was raised (4096 for the API mode) so long orders are not truncated. Verified end to end against opencode zen (`claude-haiku-4-5`): the French ConstruxAlu order extracted 15 lines, 10 auto-matched and 5 custom dies flagged for review. `#pr` @eduardotbuss

### Changed

- Customers are no longer pre-seeded — the operator registers them explicitly at upload (the catalog product master data is still seeded, as the reconciliation needs it). `#pr` @eduardotbuss

### Fixed

- Backend container crash-looped because `entrypoint.sh` (and the other shell
  scripts) carried CRLF line endings under `core.autocrlf=true`, so the Linux
  container parsed `alembic upgrade head\r` as an unknown revision. Normalised the
  scripts to LF and added `.gitattributes` (`*.sh eol=lf`) so line endings stay
  correct across platforms. `#pr` @eduardotbuss
- Test harness `conftest.py` still imported `src.app.services.pdf` and referenced
  `azure_openai_*` settings/fixtures — modules removed during the workshop
  conversion — which broke pytest collection for the whole suite. Removed the dead
  references (and fixed the blob-cleanup helper to use the current service API).
  `#pr` @eduardotbuss

- Frontend file uploads failed in the browser with a zod error ("expected string, received File"). `@hey-api/openapi-ts` maps an OpenAPI binary body (`format: binary`, e.g. a FastAPI `UploadFile`) to `z.string()`, so the generated request validator rejected the real `File` before sending — breaking every upload. Disabled request-side zod validation in the SDK generation (`validator: false`); the backend validates authoritatively via Pydantic. `#pr` @eduardotbuss

## 2026-06-23

### Changed

- Converted the private template into a minimal public workshop starter —
  removed Azure SSO (replaced with a dev stub login), the orchestrator, and most
  backend modules (kept `postgresql`, `cosmosdb`, `blob_storage`, `info`);
  trimmed the frontend to a near-blank shell; curated skills; rebranded to
  Invoice Intake - Workshop. (@vitor.pinho)

### Added

- Created comprehensive source materials for the Order Intake workshop under
  `docs/sources/` — discovery meeting transcript (4 personas), EDIFACT ORDERS
  D.96A technical reference, 35-profile aluminum extrusion product catalog
  (JSON + CSV), 9 purchase order PDFs (8 clean + 1 simulated scan) from 4
  fictional European customers (Germany, Switzerland, France, Sweden) each with
  different formats and terminology, 8 EDIFACT sidecar files, a clerk error log,
  a customer change-order email thread, a follow-up technical email, and an
  Excalidraw whiteboard of the current manual intake process. (@jeanreinhold)

### Changed

- Reframed the workshop exercise from "Invoice Intake" to "Order Intake" in
  `docs/project.md` and `WORKSHOP.md` — scenario now centers on AluProfil
  Systemtechnik GmbH parsing customer PDF orders, reconciling against a product
  catalog, and producing EDIFACT. (@jeanreinhold)

## [Unreleased]

### Added

### Changed

### Fixed

- **Logged-in sessions were dropping after roughly an hour of inactivity
  instead of the configured 7 days.** Both the login callback and the silent
  refresh route set the `id_token` cookie with `expires: expiresOn`, which is
  Azure AD's ~1 h access-token expiry, not the `SESSION_MAX_AGE_SECONDS` (7 d)
  the rest of the auth code assumed. The constant was effectively only used
  as the JWT clock-tolerance window; the cookie itself never lived past the
  raw token expiry, so refresh worked at best for one extra hour and then
  bounced the user to login. Both call sites now use
  `maxAge: SESSION_MAX_AGE_SECONDS`; `verifyIdToken()` already grants the
  matching clock tolerance, so the cookie remains a valid session identifier
  for the full configured window.

### Removed
