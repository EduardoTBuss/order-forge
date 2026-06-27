# ADR-0005 — EDIFACT: UNOA/ASCII transliteration + validate every `PIA+1` before emitting

**Status:** Accepted · **Date:** 2026-06-25 · **Scope:** core

## Context

The output target is **UN/EDIFACT ORDERS D.96A** for MetallSoft 7.3. Two of the
ERP's failure modes are unforgiving:

1. **All-or-nothing `PIA+1`.** One unknown internal code rejects the whole order.
2. **UNOA/ASCII charset.** German/French/Swiss free text (ä, ö, ü, ß, é, ç) in
   `IMD`/`NAD` segments **silently corrupts** the message — the order looks fine
   and fails downstream.

The first draft of the EDIFACT generator omitted transliteration — a latent
silent-corruption bug caught in the design review.

## Decision

The EDIFACT generator (`logic/edifact.py`) is a **pure, testable** function that:

1. **Transliterates all free text to UNOA/ASCII** before building any segment
   (`ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, `é/è/ê→e`, `ç→c`, …).
2. **Validates every `PIA+1` against the catalog before emitting** — the whole
   order depends on it, so generation is a hard gate, not a warning.
3. Is exposed behind a **gated "Generate EDIFACT" button**: the UI only unlocks it
   when *every* line has a resolved internal code, mirroring the ERP's own rule on
   the operator's side.

## Consequences

- ✅ No silent charset corruption reaches the ERP.
- ✅ The all-or-nothing constraint is enforced *before* a file is produced, so the
  operator can never generate an order MetallSoft would bounce.
- ✅ Pure function → covered by golden-style unit tests.
- ✅ Verified end-to-end: a Bauprofil order produced a valid 55-segment
  `ORDERS:D:96A:UN` message with correct `UNB…UNZ` envelope and transliterated
  `IMD` segments. See the [benchmark](../benchmark/README.md).
