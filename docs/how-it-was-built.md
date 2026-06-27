# How this was built — an AI-agent workflow

Transparency note: this solution was built with **[Claude Code](https://claude.com/claude-code)**
driving a **custom multi-agent system I maintain** (specialist worker agents
coordinated by a few orchestrators). I did not prompt a single model to "build the
app." I ran it as a small engineering org: **ideate → put the architecture on
trial → implement with specialists → audit the delivery.** Every hand-off left a
written artifact, which is why this repo has real decision records instead of
vibes.

The point of documenting this is not novelty for its own sake — it is the same
discipline a senior engineer applies (challenge the design before building,
separate concerns, review before merge), just executed with an agent team.

## The pipeline

```mermaid
flowchart LR
    I[💡 Ideation] --> T[⚖️ Architecture tribunal]
    T --> S[🏗️ Implementation]
    S --> R[🔍 Code review]
    R -->|findings| S
```

### 1. 💡 Ideation
Framing the problem and the candidate approaches before committing to any of them
— what to build, what to deliberately leave out, where the real risk sits.

### 2. ⚖️ Architecture tribunal
The proposed architecture was put through an **adversarial review** before a line
of code was written: a **prosecutor** agent attacked every decision for fatal
flaws, a **defender** agent steel-manned it, and a **judge** agent ruled with
explicit, weighted criteria.

This is where the best calls came from. The prosecutor's wins became hard
requirements:
- the **day-1 spike-gate** that killed the unverified embedded-JSON assumption
  cheaply ([ADR-0003](./decisions/0003-llm-first-extraction-with-spike-gate.md));
- locking scope to **two customers**;
- the **UNOA/ASCII transliteration** bug, caught before it could silently corrupt
  EDIFACT ([ADR-0005](./decisions/0005-edifact-unoa-gate.md)).

The full record is the [architecture review](./decisions/architecture-review.md) —
accusation, defence, and a scored verdict, decision by decision.

### 3. 🏗️ Implementation
A software orchestrator coordinated specialist agents — architecture, backend API,
database/migrations, frontend, and testing — to build the module to the verdict's
spec, happy-path first (Bauprofil end-to-end to EDIFACT), then the hard case
(ConstruxAlu prose). Output: the `order_intake` module, the reconciliation UI, and
an 82-test suite.

### 4. 🔍 Post-delivery audit
A reviewer agent went over the delivered code for logic errors, broken
front/back contracts, and edge cases — the "merge review" step.

## Why this shows up in the repo

| Stage | Artifact you can read |
|-------|----------------------|
| Tribunal | [`decisions/architecture-review.md`](./decisions/architecture-review.md) + the [ADRs](./decisions/) |
| Implementation | the `order_intake` module + [architecture](./architecture/) |
| Validation | the [benchmark](./benchmark/README.md) + the 82-test suite |
| Honest self-assessment | the [requirements audit](./requirements-audit.md) |

## What was AI-assisted vs. mine

The reasoning, the scope decisions, the acceptance of (and pushback on) each
agent's output, and the final calls are **mine**. The agents are tools — fast
specialists and an adversarial critic — but a tool that disagrees with you is only
useful if you actually weigh the disagreement. The embedded-JSON cut, the
spec-first resolver, and the "ship two customers, document the rest as extensions"
calls are all examples of taking an agent's challenge and deciding deliberately.
