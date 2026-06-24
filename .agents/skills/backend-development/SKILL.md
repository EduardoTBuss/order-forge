---
name: backend-development
description: Backend development reference for the FastAPI codebase. Use when writing or reviewing backend Python — custom module structure, pre-commit compliance, Pydantic I/O models, integration tests, and the core modules.
metadata:
  version: "2.0.0"
---

# Backend Development Reference (Workshop)

Reference for building backend features in this FastAPI app. Use it when
creating a custom module, designing Pydantic models, or writing tests. For the
end-to-end feature flow see `.agents/skills/build-app/SKILL.md`; for the
schema↔SDK flow see `.agents/skills/schema-change/SKILL.md`.

---

## 1. Pre-commit compliance (essentials)

Pre-commit runs ruff (lint + format), ty (type check, Python 3.14), and pytest.
Before committing, run:

```bash
cd backend && prek run --all-files
```

The rules that matter:

- **88-character line length** (code, comments, docstrings, strings). Break long
  lines at logical points; use parenthesized/implicit string concatenation.
- **Full type annotations** on every function (params and return). Use built-in
  generics (`list[str]`, `dict[str, int]`, `str | None`) — never `List`,
  `Optional`, `Union` from `typing`. Avoid bare `Any`/`dict`; prefer Pydantic
  models, `TypedDict`, or parameterized generics. `dict[str, Any]` is fine only
  for genuinely dynamic data (user-defined JSON, third-party payloads).
- **Imports**: all at the top of the file, all absolute (`from src.app...`),
  sorted stdlib → third-party → local. No relative imports, no inline imports.
- **Logging, not `print()`**. English only, in code and comments.

---

## 2. Custom module structure (required)

All new backend code goes in `backend/src/app/modules/custom/`. Each module
follows this mandatory layout:

```
custom/my_module/
├── routes.py            # FastAPI router — register routes, light validation only
├── tests.py             # Integration tests for every endpoint
├── logic/
│   └── main.py          # Business logic entry point (routes delegate here)
└── schemas/
    └── io.py            # One input + one output Pydantic model per endpoint
```

- **routes.py**: register routes, handle light validation (missing params, 404s),
  catch known exceptions. **No business logic** — delegate to `logic/`.
- **logic/**: all business logic; `main.py` is the entry point from routes.
- **schemas/io.py**: dedicated I/O models (see §3).

Modules are auto-discovered by folder name (underscores become hyphens in the
route), so creating the folder registers it. **Never edit `modules/core/`** —
treat it as a read-only library.

Use `async def` for any I/O-bound endpoint (DB, external API, file/cloud).

---

## 3. Pydantic I/O models (required per endpoint)

Every endpoint needs **one input model and one output model** in `schemas/io.py`,
and **every field needs `description` and `examples`**. These become the
TypeScript types in the generated frontend SDK, so good metadata → good DX.

```python
from pydantic import BaseModel, Field


class CreateInvoiceInput(BaseModel):
    vendor: str = Field(
        description="Vendor / supplier name on the invoice",
        examples=["Acme Corp"],
    )
    total: float = Field(
        description="Invoice total in the document currency",
        examples=[1234.56],
    )


class CreateInvoiceOutput(BaseModel):
    id: str = Field(
        description="Identifier of the stored invoice",
        examples=["inv_001"],
    )
```

Never return a raw `dict` or `Any` from an endpoint — always a typed output
model.

---

## 4. Testing

Focus on **endpoint integration tests against the real local services** — no
unit tests for internal functions, no mocked services. Each module's `tests.py`
should cover every endpoint: success, validation errors, and edge cases.

```python
import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.postgresql, pytest.mark.integration]


@pytest.mark.asyncio
async def test_endpoint_success(
    async_client: AsyncClient,
    api_prefix: str,
    headers: dict[str, str],
) -> None:
    """Endpoint returns the expected response."""
    response = await async_client.post(
        f"{api_prefix}/endpoint", json={"field": "value"}, headers=headers
    )
    assert response.status_code == 200
    assert "result" in response.json()
```

Run tests:

```bash
./backend/run-tests.sh --fast                                   # quick iteration
./backend/run-tests.sh -- src/app/modules/custom/my_module/tests.py -v
```

Markers: `postgresql`, `cosmosdb`, `blobstorage`, `slow`, `integration`. Tests
run against real PostgreSQL / Cosmos (Mongo API) / Azurite via Docker Compose,
and migrations run automatically before the suite.

---

## 5. Frontend integration (generated SDK)

FastAPI exposes its schema at `/openapi.json`. After changing any endpoint or
model, regenerate the typed client (backend must be running):

```bash
./scripts/update-api-client.sh
```

This rebuilds `frontend/src/lib/backend/generated/`. The frontend calls it via
`backend.<module>.<method>(...)` from **client components only** — never edits
the generated files by hand, never casts around missing fields (regenerate
first — see the `schema-change` skill).

---

## 6. Core modules (read-only)

These ship as worked examples of "how a module is built here" — one per
persistence technology, plus infra. Use them as references and as building
blocks via their endpoints/services; do not edit them.

| Module | Prefix | Purpose |
|--------|--------|---------|
| `postgresql` | `/core/postgresql/*` | Relational CRUD — example data module |
| `cosmosdb` | `/core/cosmosdb/*` | Document storage — example data module |
| `blob_storage` | `/core/blob-storage/*` | File upload/download — example data module |
| `info` | `/core/info/*` | Health, swagger helpers, on-demand test runner |

Shared service clients live in `backend/src/app/services/` (postgresql, cosmosdb,
blob_storage, semaphore) — import and use them; don't re-implement connection
logic.

---

## 7. File size limits

| Level | Lines | Action |
|-------|-------|--------|
| Ideal | 150–400 | Target for hand-written `.py` files |
| Soft warning | 400 | Look for a split point |
| Hard limit | 600 | Pre-commit blocks the commit |

Split by **responsibility** (e.g. `logic/validation.py`, `logic/pdf.py`), never
by number (`logic_1.py` is forbidden). Test files are exempt from the hard
limit. To bypass legitimately, add `# file-size-exception: <reason>` in the
first 5 lines.

---

## Checklist before committing

- [ ] Lines ≤88 chars; all functions type-annotated
- [ ] Imports at top, absolute, sorted; no unused imports/vars
- [ ] Each endpoint has dedicated input + output models with `description` + `examples`
- [ ] Integration tests cover the new endpoints
- [ ] `prek run --all-files` passes
