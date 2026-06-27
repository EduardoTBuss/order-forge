# AGENTS

Universal guardrails for all AI agents working in this repository.
For detailed reference, read the relevant skill before starting work.

> **Read `WORKSHOP.md` first.** This repository is a minimal public workshop
> starter (FastAPI backend + Next.js frontend), not a full product. The goal is
> for participants to build an **invoice intake** feature on top of a near-blank
> scaffold. When unsure whether to keep something, lean toward keeping the
> scaffold minimal — see `WORKSHOP.md` for the authoritative charter.

---

## Mandatory Rules

1. **Use `./up.sh` and `./down.sh`** instead of `docker compose` directly
2. **Never modify `core/` modules** — treat `backend/src/app/modules/core/` as read-only
3. **Always use the generated SDK** for API calls — never use `fetch()` directly
4. **SDK calls must be in client components only** (`"use client"` directive)
5. **Run `./scripts/update-api-client.sh`** after any backend endpoint changes
6. **Use `bash scripts/compose-build.sh`** when rebuilding Docker images (prunes dangling images)
7. **No mock data** — all data must flow through real backend endpoints
8. **Update `CHANGELOG.md`** with every commit
9. **Never commit without user confirmation** — always ask first
10. **Never skip pre-commit hooks** — `--no-verify` is forbidden
11. **Use timeouts** for potentially blocking commands (Docker builds, installs, etc.)
12. **All custom modules** go in `backend/src/app/modules/custom/` with the mandatory folder layout
13. **Respect file size limits** — Python ≤600 lines, TypeScript ≤500 lines (see component skills for details). Split by domain, never by number (`_1.py` is forbidden)
14. **No temporary workarounds for missing prerequisites** — if code would be clean *after* a follow-up step (SDK regen, alembic upgrade, container rebuild, dependency install), do that step first. Never ship a cast/shim/stub/comment-marked-TODO with intent to clean up later. The workaround IS the bug. If running the prerequisite needs user confirmation (rebuild, push, destructive op), *ask and wait* — don't write the shim and continue. See `backend/AGENTS.md` for the canonical schema↔SDK flow.

---

## Component Guidelines

**Read the component-specific AGENTS.md before making changes:**

| Area | Guardrails |
|------|-----------|
| **Backend** | `backend/AGENTS.md` |
| **Frontend** | `frontend/AGENTS.md` |
| **Documentation** | `docs/AGENTS.md` |

---

## Development Pipeline (Summary)

1. **Document** — Create specs in `docs/` before coding (use `build-docs` skill)
2. **Backend** — Build endpoints in `backend/src/app/modules/custom/`
3. **Test** — Run `prek run --all-files` and `./backend/run-tests.sh`
4. **Generate SDK** — Run `./scripts/update-api-client.sh`
5. **Frontend** — Build UI using the generated SDK
6. **Validate** — Run `cd frontend && pnpm lint && pnpm typecheck && pnpm build`
7. **Commit** — Update `CHANGELOG.md`, ask user, then commit

---

## Quick Reference

| Task | Command |
|------|---------|
| **Start all services** | `./up.sh` |
| **Stop all services** | `./down.sh` |
| **Run backend tests** | `./backend/run-tests.sh --fast` |
| **Run pre-commit** | `prek run --all-files` |
| **Update API client** | `./scripts/update-api-client.sh` |
| **Frontend checks** | `cd frontend && pnpm lint && pnpm typecheck` |
| **Rebuild Docker images** | `bash scripts/compose-build.sh <service>` |

---

## Local checks before committing

This workshop starter has **no CI / GitHub Actions** (it isn't deployed
anywhere). Run the quality checks locally before committing:

| Area | Command |
|---|---|
| Backend lint + type + tests | `prek run --all-files` and `./backend/run-tests.sh --fast` |
| Frontend lint | `cd frontend && pnpm lint` |
| Frontend types | `cd frontend && pnpm typecheck` |

> `pnpm build` (frontend) may fail locally due to a known upstream Next.js
> issue — see `frontend/AGENTS.md`. `pnpm typecheck` plus a dev-server smoke
> test is the practical verification path.

### Security basics

Whether or not anything scans for it, write code that would pass a security
review:

- **No SQL injection** — use parameterised queries / the ORM only
- **No XSS** — never render `dangerouslySetInnerHTML` with user input
- **No command injection** — never pass user input to `subprocess` / `exec`
- **No hardcoded secrets** — use env vars; never commit `.env`

---

## Commit and Changelog

- Follow [Keep a Changelog](https://keepachangelog.com/) conventions
- Record all changes in `CHANGELOG.md` (this is a standalone repo — there is no
  separate template changelog)
- `CHANGELOG.md` groups entries by date by default (`## YYYY-MM-DD`); every
  bullet ends with plain `#pr` and `@user` references (do not list commit hashes)
- Write from user/developer perspective, not implementation details
- **Include context** — both the commit message body and the changelog entry must make clear what the user asked the agent to do (not a literal transcript, but a concise summary of the request that triggered the change)
- **Never commit without explicit user confirmation**
- **Never use `--no-verify`** — fix hook failures, re-stage, commit again

### Changelog vs Timeline

The project tracks changes in two places:

| File | Audience | Focus |
|---|---|---|
| `CHANGELOG.md` | Developers | Technical changes: infra, tooling, features |
| Timeline in `docs/project.md` | Stakeholders / domain | New capabilities, modified features, user-facing impact |

- **User-facing feature work** → update both the Timeline and `CHANGELOG.md`.
- **Purely technical work** (refactoring, performance, infra) → update
  `CHANGELOG.md` only; no Timeline entry needed.

---

## Strict Typing

All code must use explicit, precise types. No `any`/`# type: ignore` escape
hatches; no temporary casts to make the SDK compile. Backend uses precise Python
type hints; the frontend runs TypeScript in strict mode.
