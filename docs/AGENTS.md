# Documentation Agent Guidelines

Read the root `AGENTS.md` first, then follow these documentation-specific guardrails.
For detailed conventions, read `.agents/skills/documentation-standards/SKILL.md`.

---

## Mandatory Rules

1. **All documentation in English** — regardless of input document language
2. **One Excalidraw file per page/screen** in `docs/interfaces/`
3. **Per-feature folder structure** in `docs/features/[feature-name]/`
4. **Every automation MUST have a visualization page** in `docs/interfaces/`
5. **Export all diagrams to PNG** — Excalidraw via `excalidraw-render`, BPMN via `bpmn-to-image`
6. **Embed all PNGs in `docs/project.md`** — no diagram without its PNG embedded

---

## Feature Folder Structure

```
docs/features/[feature-name]/
├── README.md              # Feature overview (embeds PNGs)
├── entities.md            # Domain entities
├── entities.excalidraw    # Entity diagram
├── endpoints.md           # API design (core vs custom)
├── migrations/            # SQL files (if DB needed)
├── automations/           # BPMN workflows (if automated)
└── tests/                 # Test cases with samples
```

---

## Diagram Export Commands

```bash
# Excalidraw → PNG
excalidraw-render docs/features/[feature]/entities.excalidraw \
  -o docs/features/[feature]/entities.png

# BPMN → PNG
bpmn-to-image docs/features/[feature]/automations/[workflow]/flow.bpmn:flow.png

# Batch export all
find docs -name "*.excalidraw" -exec sh -c \
  'excalidraw-render "$1" -o "${1%.excalidraw}.png"' _ {} \;
find docs -name "flow.bpmn" -exec sh -c \
  'bpmn-to-image "$1:${1%.bpmn}.png"' _ {} \;
```

---

## Skills (read before detailed work)

- Documentation structure & BPMN: `.agents/skills/documentation-standards/SKILL.md`
- Building docs from requirements: `.agents/skills/build-docs/SKILL.md`
- Updating docs from new sources: `.agents/skills/update-docs/SKILL.md`
- Excalidraw diagram creation: `.agents/skills/excalidraw/SKILL.md`
- Changelog workflow: `.agents/skills/changelog-management/SKILL.md`
