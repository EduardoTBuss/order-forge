"""Confidence signals.

Confidence is never a model probability — it is a set of concrete, deterministic
``if`` checks (Thomas: "92% confidence ... is worse than useless"). A line with no
flags is a one-click green approval; any flag is red and needs a human look.

Signals:
- ``unmatched_code``  — no catalog match at all (the MetallSoft gate).
- ``weak_match``      — resolved via a non-exact tier (dimension/fuzzy); review.
- ``ambiguous_unit``  — quantity/unit missing or not an EDIFACT unit.
- ``code_mismatch``   — the model-read code is a *different* valid catalog code
                        than the spec-resolved one (the swapped-digit / silent
                        wrong-product danger). The read code is a cross-check, not
                        the source of truth — this surfaces the disagreement.
- ``metadata_mismatch`` — embedded JSON disagrees with text (inert in stage 1).
"""

from src.app.modules.custom.order_intake.logic.extract.base import ExtractedLine
from src.app.modules.custom.order_intake.logic.reconcile import (
    CODE_CHECK_MISMATCH,
    TRUSTED_TIERS,
    ReconResult,
)

# EDIFACT unit-of-measure codes MetallSoft accepts (DE 6411).
ALLOWED_UNITS = {"PCE", "MTR", "KGM", "TNE"}

FLAG_UNMATCHED_CODE = "unmatched_code"
FLAG_WEAK_MATCH = "weak_match"
FLAG_AMBIGUOUS_UNIT = "ambiguous_unit"
FLAG_CODE_MISMATCH = "code_mismatch"
FLAG_METADATA_MISMATCH = "metadata_mismatch"


def compute_flags(line: ExtractedLine, recon: ReconResult) -> list[str]:
    """Return the confidence flags raised for a reconciled line."""
    flags: list[str] = []

    # Signal 1 — the MetallSoft gate: a code that did not resolve to the catalog.
    if not recon.resolved_internal_code:
        flags.append(FLAG_UNMATCHED_CODE)
    elif recon.match_tier not in TRUSTED_TIERS:
        # Signal 2 — resolved, but via a lower-confidence tier; review it.
        flags.append(FLAG_WEAK_MATCH)

    # Signal 3 — ambiguous/missing unit ("Menge: 50, fifty what?").
    if (
        line.quantity is None
        or line.unit is None
        or line.unit not in ALLOWED_UNITS
    ):
        flags.append(FLAG_AMBIGUOUS_UNIT)

    # Signal 4 — the read code points at a *different* real catalog item than the
    # spec-resolved one. A swapped digit that hits a valid code would otherwise be
    # a silent wrong product; surfacing it lets the operator verify.
    if recon.code_check == CODE_CHECK_MISMATCH:
        flags.append(FLAG_CODE_MISMATCH)

    # Signal 5 — embedded JSON disagrees with the visible text. Inert in stage 1.

    return flags
