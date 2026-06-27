# ADR-0004 — Confidence is concrete deterministic signals, not a model probability

**Status:** Accepted · **Date:** 2026-06-25 · **Scope:** core

## Context

The reconciliation screen needs to tell the operator which lines to trust at a
glance: green = one-click approve, red = investigate. The obvious approach — show
the model's self-reported confidence — was rejected by the client's IT manager in
the discovery meeting:

> *"A model that says '92 % confidence' because it doesn't know what it doesn't
> know is worse than useless. The confidence metric has to reflect actual risk."*

## Decision

Confidence is computed as a set of **concrete, deterministic `if` checks** over
the extracted line and its reconciliation result — never a model probability. A
line with **no** flags is a green one-click approval; **any** flag is red.

Signals (`logic/confidence.py`):

| Flag | Fires when | Maps to the client's words |
|------|-----------|----------------------------|
| `unmatched_code` | no catalog match at all | the MetallSoft all-or-nothing gate |
| `weak_match` | resolved via a non-exact tier (dimension/fuzzy) | "matched, but check it" |
| `ambiguous_unit` | quantity/unit missing or not an EDIFACT unit | *"Menge: 50 — fifty what?"* |
| `code_mismatch` | read code ≠ spec-resolved code | the silent-wrong-product danger (ADR-0002) |
| `metadata_mismatch` | embedded JSON disagrees with text | *"JSON says 180, table says 200"* — **inert** (ADR-0003) |

## Consequences

- ✅ Every red flag corresponds to a **real, explainable risk**, so the operator
  can act on it instead of second-guessing a number.
- ✅ The signals are pure functions of the data → trivially unit-tested.
- ✅ Directly satisfies requirement 4 (flag unresolved for human review) and the
  "confidence must be real" constraint.
- ⚠️ `metadata_mismatch` stays inert until embedded-JSON extraction exists; it is
  kept in the model so the screen is ready for it.
