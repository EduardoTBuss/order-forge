# ADR-0003 — LLM-first extraction spine, deterministic shortcuts on top (spike-gated)

**Status:** Accepted · **Date:** 2026-06-25 · **Scope:** core

## Context

The demo must cover two very different inputs: **Bauprofil** (structured DIN
table) and **ConstruxAlu** (French prose, custom dies). The discovery notes also
claimed ~40 % of PDFs carry **embedded JSON metadata** — *"sometimes the biggest
win isn't the AI, it's the plumbing."*

Two construction orders were debated:

- **Deterministic-first:** embedded-JSON → per-customer template → LLM only for
  prose. *Risk:* triples the code paths that must all work for the demo, and bets
  the schedule on an **unverified assumption** (that the fixtures actually contain
  extractable embedded JSON).
- **LLM-first:** one prompt with a structured-output schema covers both cases;
  deterministic paths are added on top as optimizations with automatic fallback.

## Decision

**LLM-first is the spine.** One extraction call with `response_format` (JSON
schema, `unit` constrained to an EDIFACT enum) handles every format. Deterministic
paths are shortcuts layered on top, each with a fallback to the spine:

- **`bauprofil_text`** — a deterministic DIN-table parser for the one layout that
  prints real `AE-` codes (free, 100 % reliable, that layout only).
- **`ollama`** — a small local model (`qwen2.5:1.5b`) for offline/free runs.
- **`llm_api`** — an external OpenAI-compatible provider (per-customer key + base
  URL + model) for the hard cases.

To de-risk the embedded-JSON assumption, a **day-1 spike-gate** was mandated:
spend one hour checking the *real* fixtures for extractable embedded JSON, with a
written demotion rule.

### Outcome of the spike-gate

The real fixtures contain **no embedded JSON** (verified — no `EmbeddedFile`,
no piece-info, no `art_code`/`items`). Per the written rule, embedded-JSON
extraction was **demoted out of the critical path**. The corresponding
`metadata_mismatch` confidence signal is **wired but inert**, ready if such PDFs
ever appear. This is recorded in `logic/ingest.py`.

The PDF is rendered to **column-aligned markdown** (`pymupdf4llm`, capped to the
lightweight CPU-only build) before the LLM, so the model reads the right cell and
units stop drifting.

## Consequences

- ✅ One path delivers all four customer formats; the demo never depends on a
  format-specific parser existing.
- ✅ Three selectable strategies trade cost vs. quality per customer (measured in
  the [benchmark](../benchmark/README.md)).
- ✅ The unverified assumption was killed cheaply on day 1 instead of costing days
  3–6.
- ⚠️ Extraction non-determinism is real, but it is **contained downstream** by the
  deterministic reconciliation of [ADR-0002](./0002-resolve-codes-from-specs-not-llm.md).
- ❌ The "embedded-JSON plumbing win" from the brief is intentionally **not**
  built — justified by data, not skipped by omission.
