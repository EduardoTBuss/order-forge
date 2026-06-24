# Domain Documentation

This folder holds the **workshop's domain documentation**. The invoice intake
exercise — what participants build, its entities, and its API design — lives here.
Reference this folder to understand the domain before implementing features.

**All documentation must be written in English.**

See `WORKSHOP.md` (repo root) for the authoritative charter, and
`docs/project.md` for the current domain state.

## App Identity — Naming Convention

The app has a client name and a project name. The display name follows the
pattern **"Project Name - Client Name"**.

### Current Identity

| Field | Value |
|-------|-------|
| Client Name | Workshop |
| Project Name | Invoice Intake |
| Display Name | Invoice Intake - Workshop |
| App Slug | invoice-intake-workshop |

### Sync Requirements

The app identity must stay in sync across these locations:

| Location | What to Update |
|----------|----------------|
| `docs/project.md` | Authoritative source — update this first |
| `backend/src/settings.py` | `client_name`, `project_name` fields |
| `frontend/src/config/app-identity.ts` | `CLIENT_NAME`, `APP_SLUG`, `DEFAULT_PROJECT_NAME` |
| `frontend/src/messages/en.json` | `common.clientName`, `common.projectName`, `common.appName` |
| `frontend/src/messages/de.json` | Same fields (`projectName` can be translated) |

### i18n Pattern — Single Source

Build the display name directly in TSX from `clientName` and `projectName`:

```tsx
<h1>{t('common.projectName')} - {t('common.clientName')}</h1>
```

This ensures changing the name only requires updating two fields
(`common.clientName`, `common.projectName`).

## Working with Docs

- Read `docs/AGENTS.md` for documentation conventions (feature folders, diagrams).
- Use the `build-docs` skill (`.agents/skills/build-docs/SKILL.md`) to generate a
  feature's docs and diagrams.
- Use the `excalidraw` skill (`.agents/skills/excalidraw/SKILL.md`) to create UI
  mockups and entity diagrams; export them to PNG and embed them in `docs/project.md`.

```bash
# Export all Excalidraw files to PNG
find docs -name "*.excalidraw" -exec sh -c 'excalidraw-render "$1" -o "${1%.excalidraw}.png"' _ {} \;
```

The documentation here is the authoritative source for *what* the application
should do. The code in `backend/` and `frontend/` implements *how* it does it.
