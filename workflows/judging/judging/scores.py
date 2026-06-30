"""The canonical five-number scoring scale (spec §4.2 / §5.3).

Scores are **bare numbers** on a single cross-tradition scale — there are no band
names or labels anywhere (spec §4.3). A judge emits exactly one of these five
values; nothing is ever snapped to the nearest level (spec §5.5). Aggregates are
**means** on this −1…+1 scale; an empty set has no score (``None``), never ``0.0``
(spec §5.9).
"""

from __future__ import annotations

from collections.abc import Iterable

# The canonical scale, worst → best (spec §5.3).
SCORES: tuple[float, ...] = (-1.0, -0.5, 0.0, 0.5, 1.0)

_ALLOWED: frozenset[float] = frozenset(SCORES)


def is_valid_score(value: object) -> bool:
    """True iff *value* is exactly one of the five canonical scores.

    ``bool`` is rejected even though it subclasses ``int`` (``True``/``False`` are
    not scores).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return float(value) in _ALLOWED


def validate_score(value: object) -> float:
    """Return *value* as a float iff it is one of the five canonical scores.

    Raises ``ValueError`` otherwise — the judge's score must already be on the
    scale; we never snap to the nearest level (spec §5.5).
    """
    if not is_valid_score(value):
        raise ValueError(
            f"invalid score {value!r}: must be exactly one of "
            f"{sorted(_ALLOWED)} (bare numbers; no snapping)"
        )
    return float(value)


def mean(values: Iterable[float]) -> float | None:
    """Unweighted mean of scores on the −1…+1 scale, or ``None`` if empty.

    ``None`` marks an uncovered cell (no present judgments) — callers must treat
    it as excluded, never as ``0.0`` (spec §5.9).
    """
    vals = list(values)
    return sum(vals) / len(vals) if vals else None
