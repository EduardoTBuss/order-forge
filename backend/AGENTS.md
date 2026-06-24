# Backend Agent Guidelines

Read the root `AGENTS.md` first, then follow these backend-specific guardrails.
For detailed conventions, read `.agents/skills/backend-development/SKILL.md`.

---

## Mandatory Rules

1. **Python 3.14** — use built-in generics (`list`, `dict`, `str | None`), not `typing` module
2. **88-character line length** — strictly enforced by pre-commit
3. **All functions must have type annotations** — parameters and return types
4. **Absolute imports only** — no relative imports
5. **Use `logging`** — `print()` is not allowed
6. **Never modify `core/` modules** — treat as read-only library
7. **Custom modules go in `custom/`** with the mandatory folder layout (below)
8. **Every endpoint needs dedicated I/O Pydantic models** with `description` and `examples`
9. **Integration tests required** for all endpoints in `tests.py`
10. **English only** — all code, comments, and descriptions

---

## Custom Module Structure (Required)

```
backend/src/app/modules/custom/
└── my_module/
    ├── routes.py            # FastAPI router (NO business logic)
    ├── tests.py             # Integration tests for all endpoints
    ├── logic/
    │   └── main.py          # Business logic entry-point
    └── schemas/
        └── io.py            # Dedicated input/output Pydantic models
```

- **routes.py**: Register routes, light validation only, delegate to `logic/`
- **logic/**: All business logic, keep routes thin
- **schemas/io.py**: One input model + one output model per endpoint, every field needs `description` and `examples`

---

## Prek Tools

| Tool        | Purpose           | Key Setting         |
| ----------- | ----------------- | ------------------- |
| ruff-check  | Linting           | Auto-fix enabled    |
| ruff-format | Formatting        | 88 chars            |
| ty-check    | Type checking     | Python 3.14, strict |
| pytest      | Integration tests | Real services       |

```bash
prek run --all-files                         # Full check
prek run ruff-format ruff-check --all-files  # Quick lint only
```

---

## Running Tests

```bash
./backend/run-tests.sh --fast                  # Quick iteration
./backend/run-tests.sh -- src/app/modules/custom/my_module/tests.py -v  # Specific module
```

Never run `docker compose ... backend-test pytest ...` — this bypasses migrations.
Use `PYTEST_ARGS` instead.

---

## Skills (read before detailed work)

- Backend conventions & examples: `.agents/skills/backend-development/SKILL.md`
- Schema/model → frontend SDK flow: `.agents/skills/schema-change/SKILL.md` (mandatory whenever you touch `schemas/io.py` or `db/models_*.py`)
- Docker & testing infrastructure: `.agents/skills/docker-operations/SKILL.md`
- Debugging & inspecting services: `.agents/skills/debugging/SKILL.md`
- Changelog workflow: `.agents/skills/changelog-management/SKILL.md`
