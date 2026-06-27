# ADR-0001 — One synchronous `custom/` module, no orchestrator

**Status:** Accepted · **Date:** 2026-06-25 · **Scope:** prototype

## Context

The starter ships an auto-discovered module system (`backend/src/app/modules/`).
The charter ([`WORKSHOP.md`](../../WORKSHOP.md) §4.2) explicitly removed the
durable-workflow orchestrator and demands a *"synchronous & simple"* scaffold.
Three module shapes were on the table:

- **A — Monolith:** everything in one `logic/`. Honest for "PDF in, `.edi` out",
  but `ingest + extract + reconcile + edifact` in one file blows the size limits
  in `backend/AGENTS.md`.
- **B — Four independent modules:** maximum separation, but multiplies the
  generated-SDK surface and forces **inter-module orchestration** — exactly the
  plumbing the charter forbids.
- **C — One module, internal stages:** a single `custom/order_intake/` with an
  internal `flow.py` that calls `ingest → extract → reconcile → confidence →
  edifact` in order.

## Decision

Adopt **Format C**: a single `order_intake/` module exposing **one SDK namespace**
(`backend.orderIntake.*`), with cleanly separated, independently testable internal
stages. The sequencing function is a plain **synchronous `flow.py`** — not a
durable orchestrator and not a state machine engine. (It was deliberately renamed
from `pipeline.py` to `flow.py` to avoid evoking the removed orchestrator.)

The order lifecycle is pruned to exactly the states the scope needs:

```
draft → in_review → edifact_generated
```

No `needs_new_article` / substitution states — those model out-of-scope work.

## Consequences

- ✅ Format B's testable separation **and** Format A's single SDK surface, without
  the inter-module orchestration the charter bans.
- ✅ Maps 1:1 to the analyst's 7-step workflow; easy to build happy-path-first.
- ✅ Each stage (`ingest`, `extract/`, `reconcile`, `confidence`, `edifact`) is a
  small, mockable unit — good for tests and for an AI agent editing one stage.
- ⚠️ A single module can still grow large; the stage split inside `logic/` is what
  keeps each file within the size budget.

This is the structure the user intuited ("swap the `leitor_pdf` module, not the
whole codebase") — the swappable extraction strategies live under `extract/`
(see [ADR-0003](./0003-llm-first-extraction-with-spike-gate.md)).
