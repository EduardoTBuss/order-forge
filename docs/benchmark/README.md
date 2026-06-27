# Benchmark — extraction strategies, head to head

A real run of all **4 customers × 3 extraction strategies** (12 runs), comparing
each result against the **reference EDIFACT** (`*.edi` ground-truth sidecars in
[`docs/sources/orders/`](../sources/orders/)). Goal: pick the right strategy per
customer with **evidence**, not vibes.

> Method note: the position-by-position comparison is exact only where the line
> count matches the ground truth (that is where the error figures below are
> drawn). Several expected codes are **custom dies** (`CUSTOM-NOR-*`, `PR-WIN-*`,
> `PROF-CUS-*`) that are *not* in the catalog — those are expected to be left
> **unresolved for the operator**, so auto-resolving them counts as a false
> positive, not a win. Catalog (`AE-`) lines expected across all customers: 27.

## ⏱️ Speed (seconds per PDF)

| Strategy | DE | FR | SE | CH | **Avg** | vs. API |
|----------|----|----|----|----|---------|---------|
| **Deterministic** (DIN parser) | 0.7 | 0.2 | 0.1 | 0.2 | **0.3 s** | ~28× faster |
| **External LLM** (opencode · claude-haiku-4-5) | 9.6 | 10.5 | 4.6 | 9.3 | **8.5 s** | — |
| **Local Ollama** (qwen2.5:1.5b) | 110 | 179 | 74 | 140 | **126 s** | ~15× slower |

## 🎯 Correctness (per customer)

`AE_ok` = catalog code resolved correctly · `AE_err` = resolved to a *different*
catalog code (dangerous) · `unit` = unit-of-measure correctness.

| Customer | Expected | Strategy | Lines | AE_ok | AE_err | Unit | Verdict |
|----------|----------|----------|-------|-------|--------|------|---------|
| **DE** (7 AE) | 7 | Deterministic | 7 | **7/7** | 0 | 7/7 | ✅ **perfect — generated EDIFACT** |
| | | External LLM | 7 ✓ | 1/7 | 2 | 7/7 | extraction ✓, resolver weak |
| | | Ollama | 7 ✓ | 1/7 | 2 | 7/7 | same, 160× slower |
| **FR** (12 AE + 3 custom) | 15 | Deterministic | 12 ✗ | — | — | — | wrong layout — unreliable |
| | | External LLM | **15 ✓** | 2/12 | 3 | **15/15** | extraction perfect, resolver weak |
| | | Ollama | 0 ✗ | 0 | 0 | — | **failed** on French prose |
| **SE** (0 AE + 6 custom) | 6 | Deterministic | 0 ✗ | — | — | — | layout unknown |
| | | External LLM | **6 ✓** | n/a | — | **6/6** | 3 false positives ⚠ |
| | | Ollama | 6 ✓ | n/a | — | 6/6 | 3 false positives ⚠ |
| **CH** (8 AE + 4 custom) | 12 | Deterministic | 0 ✗ | — | — | — | layout unknown |
| | | External LLM | **12 ✓** | 1/8 | 1 | **12/12** | extraction perfect, resolver weak |
| | | Ollama | 13 ✗ | 0/8 | 1 | 11/11 | miscounted (13 ≠ 12) |

## Key findings

1. **The bottleneck is reconciliation, not reading.** The external LLM nailed the
   **line count in 4/4 customers** and **units 100 %** — extraction is excellent.
   What stays low is the deterministic **spec resolver** turning specs into the
   right `AE-`. Quality work belongs there, plus the learned alias map.
2. **`AE_err` is the "silent wrong product" risk made visible.** A few lines
   resolved to a *different* valid catalog code. The design catches this — every
   such line is flagged and the EDIFACT gate stays shut — but it shows the
   dimension resolver's precision is imperfect. See
   [ADR-0002](../decisions/0002-resolve-codes-from-specs-not-llm.md).
3. **Deterministic is a per-layout scalpel.** Instant and perfect where it was
   built (DE: 7/7, the only run that produced EDIFACT), useless elsewhere.
4. **Local Ollama 1.5b is the worst trade here:** 15–40× slower, failed French
   entirely, miscounted CH — same weak resolution as the API with none of the
   upside beyond being free/offline.
5. **Only DE-deterministic generated EDIFACT — and that is correct.** The custom
   dies in FR/SE/CH *must* go to manual review on a first, history-free order.
   That gap closes via the per-customer **learned map** on repeat orders.

## Recommendation

| Customer | Best strategy | Why |
|----------|--------------|-----|
| **Bauprofil (DE)** | Deterministic | prints the `AE-` code; 7/7, instant, free, generates EDIFACT directly |
| **ConstruxAlu (FR)** | External LLM | only one that reads the full French prose (15/15 lines + units) |
| **Nordic (SE)** | External LLM + learning | extracts cleanly; the 6 custom dies need the learned map to close |
| **FensterSystem (CH)** | External LLM + learning | 12/12 lines; mix of catalog + custom |

**One-liner:** deterministic wins where it exists (Bauprofil); for everything else
the external API is the only viable extractor — fast and accurate at reading; the
remaining work is not *more AI* but a **stronger spec resolver** fed by the
**per-customer learned map**.

## Reproduce

```bash
./up.sh
# create one customer per strategy, upload docs/sources/orders/<customer>/<file>.pdf,
# then POST /custom/order-intake/orders/{id}/edifact when the gate opens.
```

See [`../../ORDER_INTAKE.md`](../../ORDER_INTAKE.md) §6 for the full run/test
commands.
