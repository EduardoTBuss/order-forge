# Architecture Review — the adversarial design trial

Before a line of the `order_intake` feature was written, the proposed
architecture was put on trial: a **prosecutor** attacked every decision for fatal
flaws, a **defender** steel-manned it, and a **judge** ruled with explicit,
weighted criteria. This is the English record of that review. The decisions it
produced are captured as [ADRs](./README.md); how it was run with an agent team
is in [How it was built](../how-it-was-built.md).

> Verdict: **PROCEED WITH CHANGES**, subject to three mandatory conditions.
> Date: 2026-06-25.

## The charges (what was on trial)

The architecture proposal for the prototype:

1. **Format C** — one `custom/order_intake/` module with an explicit internal
   pipeline, vs. Format A (monolith) and Format B (four independent modules).
2. **Deterministic-first extraction** — embedded JSON (~40 %) → per-customer
   template → LLM only for prose; reconciliation always deterministic.
3. **Three stores** — Blob (PDFs), Postgres (orders/lines/catalog/exports),
   Mongo (raw payload + provenance).
4. **Confidence from concrete signals** rather than model probability.

Context: a teaching prototype (2-week scope, minimalist charter), success =
*"PDF in → operator approves → `.edi` out"* for the easy case (Bauprofil) and the
hard case (ConstruxAlu prose), respecting the MetallSoft constraint.

## Prosecution (key attacks)

- **Deterministic-first triples the code paths** that must all work for the demo;
  LLM-first covers both demo cases with one prompt. → make deterministic optional,
  LLM-first the spine.
- **Embedded-JSON-in-PDF is an unverified assumption** treated as fact — schema
  varies per customer; risk of losing days fighting attachments. → one-hour
  spike-gate on day 1.
- **Three stores is over-engineering** — Postgres with JSONB does the same.
- **Format C is Format B in disguise** + orchestration; a 9-state machine models
  out-of-scope work (alloy substitution, article-master creation).
- **Scope already creeping to four customers** while pretending to be two; Nordic
  breaks the deterministic premise (empty `prod_id`, scans). → lock to two.
- **`edifact.py` omits ASCII/UNOA transliteration** → silent corruption of text
  segments (DE/FR/CH have ü, ß, é, ç).

## Defence (what held, what conceded)

- **Conceded:** LLM-first is the shortest delivery path (invert *build order*, not
  the architecture); the JSON assumption needs the spike-gate; the state machine
  must be pruned to `draft → in_review → edifact_generated`; scope locks to two
  customers; six confidence signals trim to three; transliteration is missing and
  must be added.
- **Held:** the "fatal" label on deterministic-first is false — the demo needs two
  paths, not three, and the deterministic `PIA+1` reconciliation is required by
  the MetallSoft constraint *regardless* of who extracts the text. Mongo is not
  decoration *in this repo* — it is a charter KEEP-decision (the mandatory
  document-store example), not a decision of this feature. Format C gives B's
  testable separation with A's single SDK surface, avoiding the inter-module
  orchestration the charter forbids.

## Verdict (scored)

| # | Question | Winner | Ruling |
|---|----------|--------|--------|
| 1 | Deterministic-first vs LLM-first | Defence (middle) | LLM-first is the spine; embedded JSON becomes a shortcut on top with fallback. `PIA+1` always deterministic. |
| 2 | Is embedded JSON verified? | Prosecution | Day-1 spike-gate; if it fails, JSON leaves the critical path. |
| 3 | Cut Mongo? | Defence | Keep all three stores — charter KEEP-decision, not this feature's call. |
| 4 | Format C + state machine | Middle | Keep C; `pipeline.py` → `flow.py`; prune states. |
| 5 | Two vs four customers | Prosecution | Lock to Bauprofil + ConstruxAlu. |
| 6 | Six confidence signals | Prosecution | Three MVP signals. |
| 7 | ASCII/UNOA | Prosecution | Add transliteration. |

> The prosecution won 4 of 7 points (Q2, Q5, Q6, Q7) but lost the two of highest
> architectural weight (stores, architecture) by litigating outside the brief
> (Mongo is a charter decision) or confusing *build order* with *structure*.

## Mandatory conditions

1. **Day-1 spike-gate** on embedded JSON, with a written demotion rule (the most
   critical — see [ADR-0003](./0003-llm-first-extraction-with-spike-gate.md)).
2. **`PIA+1` stays deterministic** ([ADR-0002](./0002-resolve-codes-from-specs-not-llm.md)).
3. **Scope locked to two customers**, deterministic built on top of the LLM spine.

If condition 1 fails, the design degrades gracefully to pure LLM-first — acceptable,
not fatal. (It did fail: the fixtures have no embedded JSON, so that path was
demoted exactly as the rule prescribed.)
