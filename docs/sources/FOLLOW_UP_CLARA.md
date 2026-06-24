# Follow-Up — Technical Clarifications (Email)

**From:** Clara Mendes <c.mendes@machineslikeme.com>
**To:** Thomas Keller <t.keller@aluprofil.de>
**CC:** Sabine Vogt <s.vogt@aluprofil.de>, Marco Berger <m.berger@aluprofil.de>
**Date:** 2026-06-11, 14:23
**Subject:** Order Intake — Follow-Up Questions from Yesterday

---

Hallo Thomas,

Danke nochmals für das Treffen gestern. Really helpful. I have a few technical
questions I'd like to clarify before we start building the prototype. No rush on
these — before end of week is fine.

## EDIFACT Validation

1. **PIA segment strictness.** You said MetallSoft rejects the entire order if
   any PIA+1 code doesn't match an active article. Does it also validate that
   the LIN item number is sequential (1, 2, 3…) or starting from 1? Or is LIN
   purely a counter the ERP ignores?

2. **Missing PIA.** What happens if a line item has no PIA at all — just LIN+IMD?
   Rejected, or does MetallSoft fall back to the LIN article number?

3. **Unit codes.** MetallSoft's accepted unit list — is it exactly PCE, MTR, KGM,
   TNE? Or would a customer's "Stk." crash it if someone mapped it wrong?

4. **Character encoding.** You mentioned UNOA charset. The Bauprofil orders
   contain "ü" and "ß" in descriptions. Do you strip these before feeding to
   MetallSoft, or does the ERP handle Latin-1 / UNOC?

## Article Master

5. **Article code format.** Does MetallSoft's Stammdaten use exactly the same
   codes as your internal catalog (AE-2024-XXX)? Or is there a separate
   MetallSoft-specific article number we need to map to?

6. **Custom dies / customer-owned tooling.** These have codes like
   "PR-CUS-FSA-2024-D01" — do they exist in MetallSoft's article master? If not,
   how are they handled today? Does Sabine's team create a temporary article
   number?

## Process

7. **Order splitting.** When a single PDF contains items with different delivery
   dates (like FensterSystem's call-offs), do you create one EDIFACT message per
   delivery date, or one message with different DTM segments per line item?

8. **Error handling.** If a clerk makes a typo in MetallSoft, what's the
   correction process? Is there an amendment workflow, or do they just delete and
   re-enter?

9. **Peak volumes.** Marco mentioned ~400 orders/month. Is that consistent
   year-round, or are there seasonal peaks (construction season March–October)?

## One More Thing

Sabine mentioned that some PDFs have machine-readable data embedded. Do you have
any examples of those? If the metadata is reliable, it could dramatically
simplify the intake — we might not need full OCR/AI for those customers. Could
you ask Sabine to forward a few examples?

---

Vielen Dank! I'll incorporate your answers into the technical spec and share a
draft prototype plan by end of next week.

Beste Grüße,
Clara

—
Clara Mendes · Senior Business Analyst
Machines Like Me GmbH
c.mendes@machineslikeme.com
