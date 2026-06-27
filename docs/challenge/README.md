# The Challenge — Order Intake @ SACOMP 2026

This folder explains **what was asked** and **why it is hard**. It is the
problem statement that the solution in this repository answers.

## Origin

This repository is a **fork of the workshop starter** used in a **mini-course run
by people from Machines Like Me** (a document-intake / automation company) at
**SACOMP 2026** (Semana Acadêmica da Computação). The mini-course hands participants a deliberately *near-blank*
full-stack scaffold and a realistic, messy business problem, then asks them to
build the feature end to end — learning the stack by extending it.

- **Upstream starter** → the running FastAPI + Next.js + Docker scaffold, plus
  the source materials in [`docs/sources/`](../sources/). It ships **none** of
  the feature.
- **This fork** → my implementation of the challenge: the full
  `order_intake` module. See the [root README](../../README.md) for the story.

> The authoritative charter for the starter is [`WORKSHOP.md`](../../WORKSHOP.md).

## The business problem

**AluProfil Systemtechnik GmbH** (a fictional Düsseldorf aluminium-extrusion
manufacturer) receives ~**300 purchase orders per month as PDFs** from ~100
customers. Four clerks re-type them by hand into a 2009-era ERP (**MetallSoft
7.3**) with a **~30 % re-keying error rate**. Wrong alloy codes, wrong
quantities, wrong dates — each costs a scrapped profile or a missed delivery.

The ask: **read the PDF → extract the lines → reconcile them to the internal
catalog → generate EDIFACT for the ERP → let an operator approve.**

The full discovery meeting (three client personas + the MLM analyst) is the
primary source document:

📄 **[`docs/sources/ORDER_INTAKE_DISCOVERY.md`](../sources/ORDER_INTAKE_DISCOVERY.md)**

## The four customers (one problem, four dialects)

| Customer | Country | Format | Why it's hard |
|----------|---------|--------|---------------|
| **Bauprofil** | 🇩🇪 DE | Structured DIN table | The easy case — prints the real `AE-` codes |
| **FensterSystem** | 🇨🇭 CH | Semi-structured, calendar weeks, CHF | Competitor codes, Swiss-German prose |
| **ConstruxAlu** | 🇫🇷 FR | French prose, custom dies | Polite paragraphs, half the items custom |
| **Nordic Aluminium** | 🇸🇪 SE | Minimalist, dimensions-only | `prod_id` often blank, sometimes scanned |

## The non-negotiable constraints (from the client's IT)

These shaped every architectural decision (see [`../decisions/`](../decisions/)):

1. **All-or-nothing ERP.** MetallSoft rejects the **entire order** if a single
   `PIA+1` (internal article code) is unknown — *"47 tonnes rejected because of
   one trailing space."* No partial processing.
2. **The code must be 100 % right.** A guessed code that happens to hit *another*
   valid article ships the **wrong product, silently**. So the internal code may
   **never** be invented by an LLM.
3. **Charset is UNOA/ASCII.** Umlauts and accents (ä, ß, é, ç) **silently corrupt**
   EDIFACT text segments → transliteration is mandatory.
4. **Confidence must be real**, not a model probability — *"92 % confidence
   because it doesn't know what it doesn't know is worse than useless."*
5. **A human approves every order** before it reaches the ERP.

## Requirements checklist (from [`docs/project.md`](../project.md))

1. Parse customer PDFs across DE / FR / CH / SE formats.
2. Extract line items — quantity, alloy, dimensions, delivery date.
3. Reconcile to the catalog — code mismatches, dimension-only orders, alloy
   aliases, custom dies.
4. Flag unresolved items for human review.
5. Output **EDIFACT ORDERS D.96A** with correct `PIA+1` codes.
6. Build a reconciliation UI: what was found vs. what is ambiguous.

➡️ **How well the solution meets each of these:** see the
**[Requirements audit](../requirements-audit.md)**.

## Source materials index

| File | What it is |
|------|------------|
| [`sources/ORDER_INTAKE_DISCOVERY.md`](../sources/ORDER_INTAKE_DISCOVERY.md) | The discovery meeting transcript + analyst notes |
| [`sources/edi/metallsoft-orders-mapping.md`](../sources/edi/metallsoft-orders-mapping.md) | EDIFACT ORDERS D.96A interface spec |
| [`sources/catalog/`](../sources/catalog/) | 35-profile internal product catalog (JSON + CSV) |
| [`sources/orders/`](../sources/orders/) | 8 sample PDFs (4 customers × 2) + EDIFACT sidecars |
