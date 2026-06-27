# Documentation Agent Guidelines

Read the root `AGENTS.md` first, then follow these documentation-specific rules.

## Mandatory rules

1. **All documentation in English** — regardless of the input document's language.
   (A single Portuguese mirror of the top-level README is allowed as
   `README.pt.md`; the English version stays the canonical showcase.)
2. **Diagrams are Mermaid**, inline in the Markdown — they render natively on
   GitHub, need no build step, and leave no binary image files to maintain.
   Screenshots are the only images we keep (under `docs/assets/`).
3. **Keep `docs/project.md` current** — when a capability changes, update the
   plain-language description there.

## Where things live

| Path | What it holds |
|------|---------------|
| [`challenge/`](./challenge/README.md) | the problem statement (context + brief) |
| [`decisions/`](./decisions/README.md) | Architecture Decision Records |
| [`architecture/`](./architecture/README.md) | structure + flow (Mermaid diagrams) |
| [`benchmark/`](./benchmark/README.md) | measured strategy comparison |
| [`requirements-audit.md`](./requirements-audit.md) | requirements scorecard |
| [`how-it-was-built.md`](./how-it-was-built.md) | the AI-agent workflow |
| [`sources/`](./sources/) | client-supplied source materials (read-only) |
| `assets/` | screenshots embedded in docs |

The authoritative project identity lives in `docs/project.md` and must stay in
sync with `backend/src/settings.py`, `frontend/src/config/app-identity.ts`, and
`frontend/src/messages/*.json`.
