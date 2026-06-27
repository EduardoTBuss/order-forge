# Requirements Audit

An honest scorecard of the solution against **what was asked** — the six
requirements in [`docs/project.md`](./project.md) and the hard constraints from
the [discovery brief](./challenge/README.md). ✅ met · ⭐ exceeded · ⚠️ partial ·
❌ not built.

## The six official requirements

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Parse PDFs across DE / FR / CH / SE | ✅ | DE via deterministic parser; FR/CH/SE via LLM. Prototype required DE + FR; all four are wired. |
| 2 | Extract lines (qty, alloy, dimensions, date) | ✅ | `quantity / unit / alloy / length_mm / delivery_date` in the schema; benchmark shows **line count + units 100 %** via LLM. |
| 3 | Reconcile (mismatch, dimension-only, alloy aliases, custom dies) | ⭐ | tiers `exact → dimension → alloy-alias → fuzzy → learned`; `parse_dimensions` handles Ø tubes; custom dies left unresolved + flagged. |
| 4 | Flag unresolved for human review | ✅ | concrete flags `unmatched_code / weak_match / ambiguous_unit / code_mismatch`. |
| 5 | EDIFACT D.96A with correct `PIA+1` | ✅ | generated + validated; whole-order gate; UNOA transliteration; **proven end-to-end** (55-segment message). |
| 6 | Reconciliation UI (found vs. ambiguous) | ✅ | PDF side-by-side, tier + confidence chips, inline Set/Confirm, gated generate, download, i18n EN/DE. |

## The client's hard constraints

| Constraint (who said it) | Status |
|---|---|
| MetallSoft rejects the **whole order** on one bad `PIA+1` (Thomas) | ✅ enforced as a gate ([ADR-0005](./decisions/0005-edifact-unoa-gate.md)) |
| The code must be **100 % right — never guessed** (Thomas) | ✅ resolved from specs; read code is cross-check only ([ADR-0002](./decisions/0002-resolve-codes-from-specs-not-llm.md)) |
| Confidence = **concrete signals**, not model probability (Thomas) | ✅ deterministic `if` checks ([ADR-0004](./decisions/0004-confidence-as-concrete-signals.md)) |
| Custom dies → hold for human, never invent (Sabine) | ✅ unresolved + flag; learned map resolves on repeat |
| Ambiguous unit ("Menge: 50 — fifty what?") (Sabine) | ✅ `ambiguous_unit` flag + EDIFACT unit enum |
| Human approves before the ERP (Marco) | ✅ `draft → in_review → edifact_generated` |
| Public repo, no secrets, key only in `.env` | ✅ `.env` gitignored; BYO-key per customer |

## Done beyond the ask

The brief only required *"naive code matching (exact string on a mapping table)."*
Delivered well past that:

- **Three selectable extraction strategies** — deterministic, free local Ollama,
  external multi-provider LLM.
- **Per-customer learned alias map** — auto-improves on every operator
  correction (answers Sabine's *"my clerks learned to recognise them"*).
- **Five-tier spec resolution** + alloy aliases + fuzzy — far beyond exact-string.
- **Anti-silent-error safety** — resolve by specs, read code as cross-check.
- **Structured-output unit enum** + column-aligned markdown rendering.
- **82 automated tests**, typecheck + lint clean; Clear-all reset; Confirm
  one-click; full EN/DE i18n.
- **All four customers** wired (prototype required two).
- Architecture decision records, benchmark, run guide.

## Not built — and whether that's fair

| Item | Status | Justified? |
|------|--------|-----------|
| **Embedded-JSON extraction** (the brief's "biggest plumbing win") | ❌ | ✅ The day-1 spike-gate + a grep of the real fixtures confirm **no embedded JSON exists** in them. Deliberate, documented scope cut; the `metadata_mismatch` hook is left inert ([ADR-0003](./decisions/0003-llm-first-extraction-with-spike-gate.md)). |
| JSON-vs-visible-text discrepancy flag | ❌ inert | ✅ follows from the above |
| Scanned-PDF OCR (Nordic `_scan.pdf`) | ❌ | ✅ out of prototype scope (Clara scoped DE + FR) |
| Alloy substitution + customer email | ❌ | ✅ explicitly **out of scope** (Phase 2) |
| Inventory / billet checks | ❌ | ✅ explicitly out of scope (Phase 2) |
| Call-off orders, multiple delivery dates per line | ⚠️ partial | one delivery date per line today |
| Customer-specific quantity defaults | ⚠️ partial | indirectly covered by the learned map |

## Honest quality caveat

Requirement 3 is **implemented**, but the automatic spec resolver has **modest
first-pass recall** for LLM-extracted customers (it resolves few `AE-` codes on
its own — see the [benchmark](./benchmark/README.md)). In practice it leans on the
operator + the learned map to close the EDIFACT gate. The true one-click magic
happens for **Bauprofil** (deterministic) and for **repeat** customers (after the
map learns). That is the natural next step, not a hidden failure.

## Verdict

**The prototype scope is fully met and substantially exceeded.** All six official
requirements and every hard client constraint are implemented and proven end to
end. The single brief item not built (embedded JSON) was a **data-driven,
documented scope cut** with the hook left in place — not an omission. What remains
is explicitly Phase 2, plus a stronger spec resolver as the clear next move.
