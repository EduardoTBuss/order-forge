---
client_name: AluProfil Systemtechnik GmbH
project_name: Order Intake
display_name: Order Intake — Workshop
---

# Order Intake — Workshop

## Overview

This is a **minimal, public workshop starter** for building a full-stack app.
It ships a running FastAPI backend + Next.js frontend with the plumbing already
wired — auth shell, API proxy, generated SDK, example backend modules — and then
gets out of your way. It is a **near-blank canvas**: you build the actual features.

The workshop exercise is **order intake from customer PDFs**: an aluminum
extrusion manufacturer receives purchase orders as PDFs from ~70% of their
customers. These must be parsed, reconciled against an internal product catalog,
and converted into EDIFACT ORDERS messages for a legacy ERP system ("MetallSoft
7.3"). The starter does **not** include this feature — building it is the
exercise.

See `WORKSHOP.md` at the repo root for the full charter.

## The Scenario

**AluProfil Systemtechnik GmbH** (Düsseldorf, Germany) manufactures extruded
aluminum profiles. Large customers send EDIFACT ORDERS directly into MetallSoft
ERP. But ~70% of order volume arrives as PDFs via email — in wildly different
formats, languages, and naming conventions. Four clerks manually re-type these
orders with a ~30% error rate.

### Source Materials

All client-supplied materials live in [`docs/sources/`](./sources/):

| Source | Description |
|--------|-------------|
| [`ORDER_INTAKE_DISCOVERY.md`](./sources/ORDER_INTAKE_DISCOVERY.md) | First discovery meeting transcript — 3 client personas + MLM analyst |
| [`edi/metallsoft-orders-mapping.md`](./sources/edi/metallsoft-orders-mapping.md) | EDIFACT ORDERS D.96A interface spec for MetallSoft ERP |
| [`orders/`](./sources/orders/) | 8 example purchase order PDFs from 4 customers + EDIFACT sidecar files |
| [`catalog/`](./sources/catalog/) | AluProfil internal product catalog (35 profiles, JSON + CSV) |

### The Exercise

1. Parse customer PDF orders — handle German, French, Swiss, Swedish formats
2. Extract line items with quantities, alloys, dimensions, delivery dates
3. Reconcile against the internal catalog — handle code mismatches, dimension-only
   orders, alloy aliases, and custom dies not in the catalog
4. Flag unresolved items for human review (TBD items, unmatched codes)
5. Output EDIFACT ORDERS D.96A messages with correct PIA+1 catalog codes
6. Build a reconciliation UI showing the operator what was found vs what's
   ambiguous

## What's included

- **FastAPI backend** with a modular structure and automatic OpenAPI docs.
  Example core modules: `postgresql` (relational), `cosmosdb` (document),
  `blob_storage` (files), and `info` (health/test-runner) — one worked example
  per persistence technology.
- **Next.js frontend** (App Router) with a server-side API proxy and an
  auto-generated, fully-typed SDK.
- **Dev stub auth** — a fake local "login" that sets a session cookie. The
  login → protected-route → logout flow is real; no identity provider needed.
- **Local data services** via Docker Compose: PostgreSQL, a Mongo-API container
  (Cosmos-compatible), and Azurite (Blob Storage emulator) — all local, no
  cloud account required.
- **Browser dev tools**: pgweb, mongo-express, an Azurite explorer, and Dozzle.

## App Identity

| Field | Value |
|-------|-------|
| Client Name | AluProfil Systemtechnik GmbH |
| Project Name | Order Intake |
| Display Name | Order Intake — Workshop |

The identity is defined in a few places that must stay in sync:

1. **This file** (`docs/project.md`) — authoritative source
2. **Backend** (`backend/src/settings.py`)
3. **Frontend** (`frontend/src/config/app-identity.ts`)
4. **Frontend i18n** (`frontend/src/messages/*.json`)

## Target Users

- Workshop participants learning a FastAPI + Next.js stack
- Anyone wanting a minimal, runnable full-stack starter to build on

## Getting Started

See the root [README.md](../README.md) for setup and [AGENTS.md](../AGENTS.md)
for the development workflow and conventions.
