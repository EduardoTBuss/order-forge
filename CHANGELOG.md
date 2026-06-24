# Changelog

This file records all changes to this repository.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
with extra conventions:

- entries are grouped by date (`## YYYY-MM-DD` headings)
- `Deprecated` and `[YANKED]` markers are not used
- every entry ends with plain `#pr` and `@user` references
- commit hashes are not listed in this file

## 2026-06-23

### Changed

- Converted the private template into a minimal public workshop starter —
  removed Azure SSO (replaced with a dev stub login), the orchestrator, and most
  backend modules (kept `postgresql`, `cosmosdb`, `blob_storage`, `info`);
  trimmed the frontend to a near-blank shell; curated skills; rebranded to
  Invoice Intake - Workshop. (@vitor.pinho)

### Added

- Created comprehensive source materials for the Order Intake workshop under
  `docs/sources/` — discovery meeting transcript (4 personas), EDIFACT ORDERS
  D.96A technical reference, 35-profile aluminum extrusion product catalog
  (JSON + CSV), 9 purchase order PDFs (8 clean + 1 simulated scan) from 4
  fictional European customers (Germany, Switzerland, France, Sweden) each with
  different formats and terminology, 8 EDIFACT sidecar files, a clerk error log,
  a customer change-order email thread, a follow-up technical email, and an
  Excalidraw whiteboard of the current manual intake process. (@jeanreinhold)

### Changed

- Reframed the workshop exercise from "Invoice Intake" to "Order Intake" in
  `docs/project.md` and `WORKSHOP.md` — scenario now centers on AluProfil
  Systemtechnik GmbH parsing customer PDF orders, reconciling against a product
  catalog, and producing EDIFACT. (@jeanreinhold)

## [Unreleased]

### Added

### Changed

### Fixed

- **Logged-in sessions were dropping after roughly an hour of inactivity
  instead of the configured 7 days.** Both the login callback and the silent
  refresh route set the `id_token` cookie with `expires: expiresOn`, which is
  Azure AD's ~1 h access-token expiry, not the `SESSION_MAX_AGE_SECONDS` (7 d)
  the rest of the auth code assumed. The constant was effectively only used
  as the JWT clock-tolerance window; the cookie itself never lived past the
  raw token expiry, so refresh worked at best for one extra hour and then
  bounced the user to login. Both call sites now use
  `maxAge: SESSION_MAX_AGE_SECONDS`; `verifyIdToken()` already grants the
  matching clock tolerance, so the cookie remains a valid session identifier
  for the full configured window.

### Removed
