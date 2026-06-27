# ADR-0002 — Resolve `PIA+1` from specs, never from the LLM's read code

**Status:** Accepted · **Date:** 2026-06-25 (hardened 2026-06-26) · **Scope:** core

## Context

MetallSoft rejects the **entire order** if a single `PIA+1` internal article code
is unknown. Worse, a *wrong* code can hit **another valid** catalog entry — a
**silent wrong product**. The client's IT manager was explicit: *"the AI needs to
get the code 100 % right; an automated system that generates bad EDIFACT just
creates faster chaos."*

Cheap LLMs swap digits when transcribing long code lists. If the LLM's transcribed
code is trusted as the source of truth, one swapped digit becomes a shipped wrong
profile that no flag catches.

## Decision

The internal `AE-` code is **resolved deterministically from the item's specs**
(dimensions, alloy, profile, fuzzy description) — it **never comes out of the
LLM**. The code the model *reads* from the PDF is kept only as a **cross-check**:

- Resolution tiers, in decreasing confidence:
  `exact → dimension → alloy-alias (6060 = AlMgSi0.5 = EN AW-6060 = 3.3206) →
  fuzzy → learned`.
- If the read code points at a **different** valid catalog code than the
  spec-resolved one, the line is flagged **`code_mismatch`** (*"Read code ≠
  resolved"*) for the operator to verify.
- Deterministic sources that print the real code (Bauprofil's DIN table) keep
  trusting their printed code via the `exact` tier.

A per-customer **learned alias map** (`oi_code_aliases`) makes every operator
correction stick: `(customer, the code they printed) → internal AE`. The next
order from that customer with that code resolves on its own via the `learned`
tier — no AI. This is the system answer to customers whose codes never match by
string (Nordic, FensterSystem).

## Consequences

- ✅ Eliminates the "swapped digit → silent wrong product" failure mode.
- ✅ The hard constraint (correct `PIA+1`) is satisfied by **verifiable** matching,
  not model output.
- ✅ The system improves with use instead of re-asking the LLM every time.
- ⚠️ **Recall trade-off:** spec-based resolution only auto-resolves lines whose
  specs are unambiguous in the catalog. On first contact with an LLM-extracted
  customer, many lines stay unresolved and lean on the operator + the learned
  map. This is by design (safety over coverage) and is the main avenue for future
  improvement — see the [benchmark](../benchmark/README.md).
