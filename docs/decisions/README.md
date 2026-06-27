# Architecture Decision Records (ADRs)

Short, dated records of the **significant decisions** behind the `order_intake`
feature — the *why*, not just the *what*. Each one states the context, the
decision, and its consequences, so a future contributor (or an AI agent) can
understand the reasoning without re-deriving it.

Every decision below was stress-tested in an **adversarial design review**
(prosecutor → defender → judge) before any code was written. The full record is
the [architecture review](./architecture-review.md). How that review was run with
an agent team is described in [How it was built](../how-it-was-built.md).

## Index

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](./0001-single-synchronous-module.md) | One synchronous `custom/` module — no orchestrator | ✅ Accepted |
| [0002](./0002-resolve-codes-from-specs-not-llm.md) | The `PIA+1` code is resolved deterministically from specs, never from the LLM | ✅ Accepted |
| [0003](./0003-llm-first-extraction-with-spike-gate.md) | LLM-first extraction spine; deterministic shortcuts on top, gated by a day-1 spike | ✅ Accepted |
| [0004](./0004-confidence-as-concrete-signals.md) | Confidence = concrete deterministic signals, never a model probability | ✅ Accepted |
| [0005](./0005-edifact-unoa-gate.md) | EDIFACT: UNOA/ASCII transliteration + validate every `PIA+1` before emitting | ✅ Accepted |

## What "Accepted" means here

These are prototype decisions for a 2-week workshop scope, not eternal law. Where
a decision was a deliberate *scope cut* (e.g. embedded-JSON extraction in
ADR-0003), the record says so and leaves the hook in place. Anything explicitly
out of scope (alloy substitution, email, inventory) is tracked in the
[challenge brief](../challenge/README.md), not here.
