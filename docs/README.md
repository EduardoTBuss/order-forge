# Documentation

The story behind this project, from problem to solution. **All docs are in
English.** Start at the [root README](../README.md), then dig in here.

## Map

| Folder / file | What's inside |
|---------------|---------------|
| 🎯 [`challenge/`](./challenge/README.md) | **What was asked** — the SACOMP 2026 / Machines Like Me mini-course context, the AluProfil problem, the four customers, and the hard constraints. |
| ⚖️ [`decisions/`](./decisions/README.md) | **Why it's built this way** — Architecture Decision Records, each stress-tested in an adversarial design review. |
| 🏗️ [`architecture/`](./architecture/README.md) | **How it fits together** — stack, module layout, processing flow (with diagrams). |
| 📊 [`benchmark/`](./benchmark/README.md) | **Evidence** — 4 customers × 3 extraction strategies, measured for speed and correctness against ground truth. |
| ✅ [`requirements-audit.md`](./requirements-audit.md) | **Honest scorecard** — every requirement vs. what shipped, including what was deliberately cut. |
| 🤖 [`how-it-was-built.md`](./how-it-was-built.md) | **The AI workflow** — the multi-agent pipeline (ideate → tribunal → build → review). |

## Source materials (client-supplied)

The raw inputs the solution is built from live in [`sources/`](./sources/): the
[discovery transcript](./sources/ORDER_INTAKE_DISCOVERY.md), the
[EDIFACT spec](./sources/edi/metallsoft-orders-mapping.md), the
[catalog](./sources/catalog/), and the [sample orders](./sources/orders/).

## Run & use

To run the app and use the feature, see the operator guide at
[`../ORDER_INTAKE.md`](../ORDER_INTAKE.md) and the quick start in the
[root README](../README.md).

---

<details>
<summary>About the starter scaffold (upstream)</summary>

This repo is a fork of a workshop starter; some scaffolding docs describe that
template. The authoritative charter is [`../WORKSHOP.md`](../WORKSHOP.md);
`project.md` holds the domain identity; `AGENTS.md` holds doc conventions.

### App identity (kept in sync across four files)

| Location | What to update |
|----------|----------------|
| `docs/project.md` | authoritative source |
| `backend/src/settings.py` | `client_name`, `project_name` |
| `frontend/src/config/app-identity.ts` | `CLIENT_NAME`, `APP_SLUG`, `DEFAULT_PROJECT_NAME` |
| `frontend/src/messages/{en,de}.json` | `common.clientName`, `common.projectName`, `common.appName` |

</details>
