"""The shared **source fingerprint** over a resolved-judgments stream (#51, Decision 2).

Both tiers — the #49 score export (``export_results``) and the #51 raw export
(``export_raw``) — stamp this hash into their manifests, computed from the SAME input shape
(the global list of canonical resolved judgments). A per-run equality check then upgrades
"produced by the same loaders" from a convention into a checkable invariant: if the two
tiers were exported from different input states, their fingerprints differ and the viewer
(or CI) flags it. Lives in its own module so both exporters can import it without a cycle.

Field order is fixed here and must never change silently — a change re-hashes every run.
"""

from __future__ import annotations

import hashlib
import json


def _fingerprint_tuple(row: dict) -> list:
    """One resolved judgment reduced to its fingerprinted fields (canonical order).

    ``tradition`` is included so the identity is globally unique even if two traditions ever
    shared a ``scenario_id``. ``direction``/``rationale`` normalize to ``""`` when absent so
    the serialization is stable.
    """
    return [
        row["tradition"], row["subject"], row["scenario_id"], row["pressure"], row["framing"],
        row["judge"], row["scope"],
        row["score"],
        row.get("direction") or "",
        row.get("rationale") or "",
    ]


def fingerprint_line(row: dict) -> str:
    """One resolved judgment's canonical serialized line (the unit both tiers accumulate).

    Streaming callers extract this small string per row and discard the full dict, so the
    fingerprint never forces the whole resolved stream (with transcripts/rationales as live
    dicts) to be held at once.
    """
    return json.dumps(_fingerprint_tuple(row), ensure_ascii=False, separators=(",", ":"))


def combine_fingerprint(lines) -> str:
    """``sha256:<hex>`` over the sorted fingerprint lines (order-independent, byte-stable)."""
    return "sha256:" + hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def source_fingerprint(resolved: list[dict]) -> str:
    """``sha256:<hex>`` over a resolved-judgments stream (convenience over the two helpers).

    ``resolved`` is the **global** list of canonical (normalized) resolved judgments across
    all traditions — exactly what ``resolve_judgments`` returns, concatenated. The sort key
    is the exact serialized line that is hashed, so the result is order-independent.
    """
    return combine_fingerprint(fingerprint_line(r) for r in resolved)
