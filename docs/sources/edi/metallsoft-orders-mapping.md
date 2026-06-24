# MetallSoft ERP — EDIFACT ORDERS D.96A: Technical Interface Specification

**Document reference:** IT-SPEC-EDIFACT-ORDERS-v3.2
**Last updated:** 2024-03-15
**Author:** Thomas Keller, IT-Infrastruktur
**Status:** INTERN — nicht zur Weitergabe an Dritte
**Classification:** Vertraulich / Confidential

---

## Overview

MetallSoft ERP 7.3 (installiert 2009) accepts inbound purchase orders via
UN/EDIFACT ORDERS D.96A message format. This document defines the exact
segment structure, qualifier values, and validation rules expected by
MetallSoft as of software patch level 7.3.14 (2024-02).

Orders are received via a watched directory on the MetallSoft application
server (`E:\MetallSoft\inbound\edi\orders\`). Files with extension `.edi`
are processed sequentially every 60 seconds. Successful orders generate an
ORDRSP (purchase order response) in the same directory under
`..\outbound\`. Rejected orders are moved to `..\rejected\` with an
appended error log (`.err` file).

---

## Interchange Envelope

Every message must be wrapped in a valid EDIFACT interchange envelope.

### UNB — Interchange Header

```
UNB+UNOA:2+GLN_SENDER+GLN_RECIPIENT+YYMMDD:HHMM+MESSAGE_REF'
```

| Field | Value | Notes |
|-------|-------|-------|
| Syntax identifier | `UNOA:2` | UN/ECE level A, version 2. No umlauts, no accents. Only ISO 646 (ASCII). |
| Sender ID | Customer GLN (13 digits) | e.g. `4012345600007` for Bauprofil |
| Recipient ID | `4012345123456` | AluProfil's fixed GLN. Hardcoded in MetallSoft config. |
| Date/Time | `YYMMDD:HHMM` | Generation timestamp |
| Message ref | Unique interchange ref | Max 14 alphanumeric characters |

### UNZ — Interchange Trailer

```
UNZ+NUM_MESSAGES+MESSAGE_REF'
```

| Field | Value |
|-------|-------|
| Message count | Number of UNH..UNT groups (normally 1) |
| Interchange ref | Must match UNB message ref |

---

## Order Message Structure

```
UNH+MSG_REF+ORDERS:D:96A:UN'
BGM+220+ORDER_NUMBER+9'
DTM+137:YYYYMMDD:102'
RFF+ON:PURCHASER_ORDER_REF'
NAD+BY+BUYER_GLN::9'
NAD+SU+SUPPLIER_GLN::9'
NAD+DP+DELIVERY_PARTY_GLN::9'
CUX+2:EUR:9'
PAT+1++5:3:D:30'
  [ segment group 25 — line items; repeats per line ]
  LIN+LINE_NUMBER++ITEM_CODE:SA'
  PIA+1+INTERNAL_CODE:SA'
  IMD+F++:::DESCRIPTION_TEXT'
  QTY+21:QUANTITY:UOM'
  MEA+PD+AAC+LENGTH_VALUE:MMT'
  DTM+2:DELIVERY_DATE:102'
  [ end segment group 25 ]
UNS+S'
CNT+2:NUM_LINE_ITEMS'
UNT+SEGMENT_COUNT+MSG_REF'
```

### Segment Glossary

| Segment | Purpose | Repeat |
|---------|---------|--------|
| `UNH` | Message header | 1 |
| `BGM` | Beginning of message; identifies order type | 1 |
| `DTM` | Document date (137) | 1 |
| `RFF` | Customer's own order reference number | 0..1 |
| `NAD` | Name and address: BY (buyer), SU (supplier), DP (delivery party) | 3 |
| `CUX` | Currency | 1 |
| `PAT` | Payment terms | 0..1 |
| `LIN` | Line item | 1..999 |
| `PIA` | Additional product ID — CRITICAL: carries internal catalog code | 1 per LIN |
| `IMD` | Item description (free text) | 0..1 per LIN |
| `QTY` | Ordered quantity (qualifier 21) | 1 per LIN |
| `MEA` | Physical dimensions | 0..5 per LIN (custom profiles) |
| `DTM` | Delivery date (qualifier 2) | 1 per LIN |
| `UNS` | Section control (S = detail/summary separation) | 1 |
| `CNT` | Control total (line item count) | 1 |
| `UNT` | Message trailer | 1 |

---

## The PIA Segment: Critical for Order Acceptance

The `PIA+1` segment carries the supplier's internal article number. MetallSoft
validates every LIN against the article master database (`Artikelstamm`) after
the entire interchange is parsed.

### PIA Segment Anatomy

```
PIA+1+AE-2018-127:SA'
```

| Data element | Value | Meaning |
|---|---|---|
| PIA | Segment tag | Additional product ID |
| 4347 | `1` | Product ID function qualifier — "Additional identification" |
| C212/7140 | e.g. `AE-2018-127` | The internal AluProfil article code |
| C212/7143 | `SA` | Item number type — "Supplier's article number" |

### Validation Rules

1. **Code must exist** — `C212/7140` must match an active `Artikelnummer` in
   MetallSoft's `Artikelstamm` table (`Status = 'A'` — aktiv).
2. **No fuzzy matching** — trailing spaces, case differences, or invisible
   characters cause rejection. The match is `LIKE` in SQL but the application
   layer trims and normalises before query. The effective comparison is
   `UPPER(TRIM(code)) = UPPER(TRIM(input))`.
3. **No partial acceptance** — if ANY `PIA+1` on ANY `LIN` fails validation,
   the ENTIRE order is rejected. No line items are posted. No partial
   fulfilment.
4. **Rejection response** — MetallSoft generates an APERAK message (application
   error and acknowledgement) listing each failed `LIN` index and the invalid
   code. The APERAK is written to `E:\MetallSoft\outbound\edi\orders\` for
   automated pickup or email forwarding.

### Common Rejection Scenarios

| Error | Example | Consequence |
|-------|---------|-------------|
| Code not in master | `PIA+1+ZZ-999999:SA'` | Entire order rejected |
| Trailing whitespace | `PIA+1+AE-2018-127 :SA'` | Entire order rejected |
| Wrong qualifier | `PIA+5+AE-2018-127:SA'` (5 = product ID, not additional ID) | Line skipped silently in some MetallSoft patch versions; accepted in others. **Do not use qualifier 5 for inbound orders.** |
| Missing PIA entirely | `LIN+1++ITEM:SA'` with no following PIA | Entire order rejected |
| Inactive article | Code exists but `Status != 'A'` (e.g. discontinued) | Entire order rejected |

---

## Validated Code Lists

### Item Number Type Qualifiers (DE 7143)

| Code | Meaning | Usage at AluProfil |
|------|---------|-------------------|
| `SA` | Supplier's article number | **Required.** Used on PIA+1 for AluProfil internal code (e.g. `AE-2018-127`). |
| `BP` | Buyer's part number | Optional on LIN for customer's own reference code. Not validated. |
| `EN` | International Article Number (EAN) | Not currently used. Reserved for future. |

### Product ID Function Qualifiers (DE 4347)

| Code | Meaning | Usage |
|------|---------|-------|
| `1` | Additional identification | **Required on PIA.** Carries the internal catalog code. |
| `5` | Product identification | DO NOT USE for inbound orders. Causes inconsistent behaviour across MetallSoft patch levels. |

### Quantity Qualifiers (DE 6063)

| Code | Meaning | Typical Use |
|------|---------|-------------|
| `21` | Ordered quantity | Standard order line quantity |
| `113` | Quantity to be delivered | Used for call-off / partial delivery orders |
| `192` | Item gross weight | For logistical planning |

### Unit of Measure Codes (DE 6411)

| Code | Meaning | Description |
|------|---------|-------------|
| `PCE` | Piece | Individual profiles (typically 6m standard lengths). Most common. |
| `MTR` | Metre | Bulk length measurement. Used for cut-to-length orders or when customer orders a running length. |
| `KGM` | Kilogram | Weight-based ordering. Used by some Scandinavian customers. |
| `TNE` | Tonne (metric ton) | Bulk orders. Rare for PDF customers, used by EDIFACT customers for billet orders. |

### Delivery Date Qualifiers (DE 2005)

| Code | Meaning |
|------|---------|
| `2` | Delivery date requested |
| `10` | Shipment date requested |

### Date/Time/Period Format Qualifiers (DE 2379)

| Code | Meaning | Format |
|------|---------|--------|
| `102` | CCYYMMDD | Must use this. `20260615` for 15 June 2026. |

---

## Full Example: Realistic Aluminium Profile Order

The following is a valid EDIFACT ORDERS D.96A message for a three-line order
from FensterSystem Alu AG to AluProfil. This message would be accepted by
MetallSoft 7.3 provided all three AE- codes exist and are active.

```
UNB+UNOA:2+7612345600008+4012345123456+260610:0915+FS260610001'
UNH+FS260610001A+ORDERS:D:96A:UN'
BGM+220+FS-2026-0417+9'
DTM+137:20260610:102'
RFF+ON:FS-PO-20260417'
NAD+BY+7612345600008::9++FensterSystem Alu AG+Brandstrasse 34+Schlieren++8952+CH'
NAD+SU+4012345123456::9++AluProfil Systemtechnik GmbH+Industriestrasse 42+Düsseldorf++40589+DE'
NAD+DP+7612345600008::9++FensterSystem Alu AG+Brandstrasse 34+Schlieren++8952+CH'
CUX+2:CHF:9'
PAT+1++5:3:D:30'
LIN+1++PRO-045-0020:BP'
PIA+1+AE-2018-127:SA'
IMD+F++:::Fensterprofil Rahmen 60mm EN AW-6060 T66 anodisiert EV1'
QTY+21:120:PCE'
MEA+PD+AAC+6000:MMT'
DTM+2:20260818:102'
LIN+2++PRO-045-0021:BP'
PIA+1+AE-2018-128:SA'
IMD+F++:::Fensterprofil Flügel 60mm EN AW-6060 T66 anodisiert EV1'
QTY+21:80:PCE'
MEA+PD+AAC+6000:MMT'
DTM+2:20260818:102'
LIN+3++PRO-052-0003:BP'
PIA+1+AE-2019-042:SA'
IMD+F++:::Alu-T-Stück Verbinder 40x40 EN AW-6063 T5 pressblank'
QTY+21:400:PCE'
MEA+PD+AAC+150:MMT'
DTM+2:20260825:102'
UNS+S'
CNT+2:3'
UNT+24+FS260610001A'
UNZ+1+FS260610001'
```

### Line-by-Line Annotations

| Line | Segment | Explanation |
|------|---------|-------------|
| 1 | `UNB` | Interchange header. Sender = FensterSystem GLN `7612345600008` (CH), recipient = AluProfil GLN `4012345123456` (DE). Reference = `FS260610001`. |
| 2 | `UNH` | Message header. ORDERS D.96A. |
| 3 | `BGM+220` | Purchase order type. FensterSystem order number `FS-2026-0417`. |
| 4 | `DTM+137` | Document date: 10 June 2026. |
| 5 | `RFF+ON` | FensterSystem's own purchase order reference. |
| 6 | `NAD+BY` | Buyer: FensterSystem Alu AG, Brandstrasse 34, 8952 Schlieren, CH. |
| 7 | `NAD+SU` | Supplier: AluProfil Systemtechnik GmbH, Industriestraße 42, 40589 Düsseldorf, DE. |
| 8 | `NAD+DP` | Delivery party: same as buyer (ship to their own facility). |
| 9 | `CUX+2:CHF` | Currency: Swiss francs (FensterSystem pays in CHF per their Rahmenvertrag). |
| 10 | `PAT` | Payment terms: net 30 days. |
| 11-16 | `LIN+1` | Line 1: Fensterprofil Rahmen 60mm. 120 pieces × 6000mm length. EN AW-6060 T66, anodized EV1 (natural silver). Internal code `AE-2018-127`. Delivery 18 August 2026 (calendar week 34). |
| 17-22 | `LIN+2` | Line 2: Fensterprofil Flügel (sash) 60mm. 80 pieces × 6000mm. Same alloy and finish. Internal code `AE-2018-128`. Same delivery date. |
| 23-28 | `LIN+3` | Line 3: T-connector 40×40mm. 400 pieces × 150mm. EN AW-6063 T5, mill finish (pressblank). Internal code `AE-2019-042`. Delivery 25 August 2026 (one week later — call-off). |
| 29 | `UNS+S` | Section separator: detail ends, summary begins. |
| 30 | `CNT+2:3` | Control total: 3 line items. |
| 31 | `UNT+24+...` | Message trailer: 24 segments, message ref must match UNH. |
| 32 | `UNZ+1+...` | Interchange trailer: 1 message, interchange ref must match UNB. |

---

## Order Acceptance / Rejection Rules Summary

### Immediate Rejection (entire order, no processing)

| Rule | Check |
|------|-------|
| R1 | `UNB` syntax identifier must be `UNOA:2` |
| R2 | `UNB` recipient GLN must match `4012345123456` |
| R3 | `UNB` date must parse as valid `YYMMDD` |
| R4 | `UNH` message type must be `ORDERS:D:96A:UN` |
| R5 | `BGM` document type must be `220` (purchase order) |
| R6 | At least one `LIN` segment must exist |
| R7 | `CNT+2` value must equal actual `LIN` count |
| R8 | `UNT` segment count must equal actual segment count |
| R9 | `UNZ` message count must match actual `UNH..UNT` groups |

### Line-Item Validation (any failure = entire order rejected)

| Rule | Check |
|------|-------|
| L1 | Every `LIN` must have a following `PIA+1` segment |
| L2 | `PIA+1` item number type must be `SA` |
| L3 | `PIA+1` code must exist in `Artikelstamm` with `Status = 'A'` |
| L4 | `QTY+21` quantity must be numeric and > 0 |
| L5 | `QTY+21` unit must be in the allowed list: `PCE`, `MTR`, `KGM`, `TNE` |
| L6 | `DTM+2` date must be valid `CCYYMMDD` and not in the past (> 6 months tolerance) |
| L7 | Maximum 999 `LIN` segments per order |

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| No partial processing | A single invalid `PIA+1` code rejects the entire order. This is a MetallSoft 7.3 architectural constraint. The vendor (MetallSoft GmbH, Karlsruhe) has confirmed this will not change in the 7.x line. |
| Date format strictness | All dates must use format qualifier `102` (`CCYYMMDD`). No other format is accepted. Calendar week notation (e.g. "KW34") is NOT supported natively and must be converted before constructing the EDIFACT message. |
| Character set | `UNOA` (ASCII) only. No umlauts (ä, ö, ü, ß), no accents (é, è, ê, ç). These characters cause silent corruption in the `IMD` free-text segments. For item descriptions containing special characters, use ASCII equivalents (`ae` for `ä`, `ss` for `ß`, `e` for `é`, etc.). |
| Maximum line items | 999 per order. Exceeding this triggers rejection by rule L7. For larger orders, split into multiple interchange groups. |
| GLN validation | All `NAD` party identifiers must be valid 13-digit GLNs. MetallSoft cross-references the first 7 digits (company prefix) against a local GLN directory. Unknown prefixes generate a warning in the processing log but do NOT reject the order. |
| `PIA` qualifier `5` | Behaviour is inconsistent across MetallSoft 7.3 patch levels. On 7.3.12 and earlier, `PIA+5` caused the line to be silently skipped (no error, no processing). On 7.3.13+, it is treated identically to `PIA+1`. Current production runs 7.3.14. For inbound orders, always use `PIA+1`. Never generate `PIA+5`. |

---

## Test Environment

A test instance of MetallSoft 7.3 is available on the internal network at
`\\metallsoft-test\edi\orders\`. This instance runs against a copy of the
production `Artikelstamm` (refreshed weekly, Saturday 02:00). Use this for
integration testing of EDIFACT generation.

**Connection details:**
- Host: `metallsoft-test.alprofil.local`
- Watched directory: `E:\MetallSoft\inbound\edi\orders\` (via SMB share
  `\\metallsoft-test\edi-inbound` from the development network)
- Authentication: domain credentials (request access via IT-Ticket)

---

## References

- UN/EDIFACT ORDERS D.96A — United Nations Directories for Electronic Data
  Interchange for Administration, Commerce and Transport
- DIN EN 755-9:2016 — Aluminium and aluminium alloys — Extruded rod/bar,
  tube and profiles — Part 9: Profiles, tolerances on dimensions and form
- DIN EN 12020-2:2017 — Aluminium and aluminium alloys — Extruded precision
  profiles in alloys EN AW-6060 and EN AW-6063 — Part 2: Tolerances on
  dimensions and form
- MetallSoft 7.3 Administrationshandbuch (internal document, available on
  `\\metallsoft-docs\handbuch\admin-v7.3.pdf`)

---

**Document history:**
- v1.0 — 2010-01-12 — Initial documentation (TK)
- v2.0 — 2016-06-03 — Added validation rules and rejection scenarios (TK)
- v3.0 — 2022-11-18 — Updated for patch 7.3.12; added PIA qualifier 5
  warning (TK)
- v3.1 — 2023-09-04 — Added GLN directory cross-reference note (TK)
- v3.2 — 2024-03-15 — Updated for patch 7.3.14; added CNT validation;
  expanded test environment section (TK)
