# Build Documentation from Requirements (Workshop — Basic)

A minimal recipe for writing a feature spec in `docs/` before you build it. This
is the "very basic" version used in the Invoice Intake workshop — no internal
source-ingestion pipeline, no BPMN automations, no orchestrator.

Read `WORKSHOP.md` (repo root) for the overall purpose first.

## When to Use

Use this to capture a feature before coding it (the first step of the
`build-app` skill). Keep docs short and practical — they exist to align on
scope, not to be exhaustive.

## What a feature doc contains

Create `docs/features/<feature-name>/README.md` with:

1. **Purpose** — one paragraph: what the feature does and who uses it.
2. **User flow** — 3–6 steps describing what the user does, start to finish.
3. **Inputs / outputs** — the data going in and coming out (fields, types).
4. **API endpoints** — the custom endpoints you'll add (method, path, purpose).
5. **Persistence** — what gets stored and where (Postgres / Cosmos / Blob), if
   anything.
6. **Diagram** (optional) — a simple entity or flow diagram.

Keep it to one or two pages. The doc drives the backend module and the frontend
page you build next.

## Diagrams (optional)

If a diagram helps, use Excalidraw and export to PNG so it renders in Markdown.
See the `excalidraw` skill for authoring details.

```bash
# Excalidraw → PNG
excalidraw-render docs/features/<feature>/entities.excalidraw \
  -o docs/features/<feature>/entities.png
```

Embed the PNG in the feature README and, if useful, in `docs/project.md`.

## Keeping `docs/project.md` current

`docs/project.md` is the high-level project description (what the app is, what
features exist). When you add a feature, add a short entry there describing the
new capability in plain language. Keep it user-facing, not implementation
detail.

## Rules

- All documentation in English.
- No company-internal or confidential material (this repo is public — see
  `WORKSHOP.md`).
- Prefer short, concrete docs over long templates.
