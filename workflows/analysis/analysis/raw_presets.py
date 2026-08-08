"""Generic preset helpers for a ``results-raw/`` catalog (Spec 51 / #54).

Extracted from :mod:`analysis.export_raw` so a second catalog type (the AFB before/after
explorer, #54) reuses the *cap* + *one-entry-per-item, round-robin-across-groups* selection
without importing MultiBench code. These operate purely on the generic **entry** shape
(``{"params": {"group", "item", ...}, ...}``) — nothing MB-specific. The MB-specific
``_entry``/`_models_split`/… builders stay in :mod:`analysis.export_raw`.
"""

from __future__ import annotations

from collections import defaultdict

PRESET_CAP = 12


def dedup_per_item(sorted_entries) -> list[dict]:
    """Dedup to one entry per (group, item), then round-robin across groups up to PRESET_CAP.

    On real data hundreds of scenarios tie at the max magnitude (e.g. a −1↔+1 spread), so a
    straight magnitude+lexicographic cut fills all 12 slots from one tradition. To make the
    preset an actually *curated* cross-tradition view, we keep each group's candidates in the
    incoming (magnitude-sorted, deterministic) order and interleave them by group — the
    strongest from each tradition first, then the next, etc. Fully deterministic (groups are
    visited in sorted name order); with a single group (e.g. AFB's ``afb-150``) it degenerates
    to plain magnitude order.
    """
    seen: set[tuple] = set()
    by_group: dict[str, list[dict]] = defaultdict(list)
    for e in sorted_entries:
        ident = (e["params"]["group"], e["params"]["item"])
        if ident in seen:
            continue
        seen.add(ident)
        by_group[e["params"]["group"]].append(e)

    out: list[dict] = []
    groups = sorted(by_group)
    round_i = 0
    while len(out) < PRESET_CAP and any(round_i < len(by_group[g]) for g in groups):
        for g in groups:
            if round_i < len(by_group[g]):
                out.append(by_group[g][round_i])
                if len(out) >= PRESET_CAP:
                    break
        round_i += 1
    return out
