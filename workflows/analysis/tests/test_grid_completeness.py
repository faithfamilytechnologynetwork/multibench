"""Grid-completeness of the two-judge `20260803` run (issue #120, Phase 1).

After grid completion (re-judging the Opus empty-response cells, #116) both judges must cover the
canonical 93,420-cell universe **except** the two documented, architect-approved residual cells
that persistently returned an empty/truncated Opus verdict (reported, not imputed). This guards
that invariant so the combined two-judge mean has at most those two single-judge cells.

Design notes:
- **Compare each judge against the canonical universe, not judge-vs-judge** — two judges can share
  a set that omits the same cells; equality would pass while both are incomplete (plan-review).
- The pure gap computation (:func:`missing_cells_by_judge`) is unit-tested on an in-memory fixture
  so the guard's logic runs in CI; the real-data tests below skip where the gitignored
  ``tmp/judging-runs/`` roots are absent (they run in the main checkout, post-merge).
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.export_results import (
    CANONICAL_SUBJECTS,
    SCOPES,
    read_run_root,
    resolve_judgments,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RUNS = _REPO_ROOT / "tmp" / "judging-runs"
_ROOT_NAMES = (
    "20260803-merged",
    "20260803-unstated-opus",
    "20260803-framings-opus-sample",
    "20260823-opus-fullgrid",
)
_ROOTS = [_RUNS / n for n in _ROOT_NAMES]
_JUDGES = ("gemini-3.6-flash", "claude-opus-4-8")

# The two cells that persistently returned an empty/truncated Opus verdict after the re-judge
# (3 passes / >=9 provider attempts each) — reported, NOT imputed (architect, 2026-09-05). The
# combined score uses their single (Gemini) verdict; the manifest discloses them via
# `ranking.single_judge_cells`. MUST stay in lockstep with that manifest field (Phase 2/4).
# Keyed (tradition, subject, scenario_id, pressure, framing, scope), Opus-missing.
_KNOWN_RESIDUAL_OPUS_MISSING = {
    ("judaism", "gemini-3.6-flash", "MSR-025", "insistence", "unstated", "full"),
    ("sunni-islam", "Qwen/Qwen3-235B-A22B-Instruct-2507", "JLS-122", "flattery", "guided", "full"),
}

_have = all(r.is_dir() for r in _ROOTS)
_skip = pytest.mark.skipif(not _have, reason="launch run data (tmp/judging-runs/) unavailable")


def missing_cells_by_judge(
    rows: list[dict], subjects, scenarios, pressures, framings, scopes, judges,
) -> dict[str, set[tuple]]:
    """Pure gap computation: judge -> the canonical cells that judge did NOT score.

    Universe = subjects x scenarios x pressures x framings x scopes. A row covers its
    (subject, scenario_id, pressure, framing, scope) cell for its judge. Unit-tested below.
    """
    universe = set(itertools.product(subjects, scenarios, pressures, framings, scopes))
    covered: dict[str, set[tuple]] = {j: set() for j in judges}
    for r in rows:
        cell = (r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
        covered.setdefault(r["judge"], set()).add(cell)
    return {j: universe - covered.get(j, set()) for j in judges}


def _resolved_rows_and_universe(tradition, per_root):
    present = [(i, root[tradition]) for i, root in enumerate(per_root) if tradition in root]
    rows = resolve_judgments([rt for _i, rt in present], [i for i, _rt in present])
    reports = [rt.report for _i, rt in present if rt.report is not None]
    assert reports, f"{tradition}: no report.json among roots"
    universes = [frozenset(r.get("by_scenario", {})) for r in reports]
    assert len(set(universes)) == 1, f"{tradition}: roots disagree on the by_scenario universe"
    scenarios = sorted(universes[0])
    assert scenarios, f"{tradition}: empty by_scenario universe"
    return rows, scenarios


# ── Pure-logic unit test (runs in CI, no data needed) ──────────────────────────────


def test_missing_cells_by_judge_pure():
    subjects, scenarios, pressures, framings, scopes = (["s1"], ["S-1"], ["p1"], ["unstated"], ["full"])
    # g covers the one cell; o does not.
    rows = [{"judge": "g", "subject": "s1", "scenario_id": "S-1", "pressure": "p1",
             "framing": "unstated", "scope": "full"}]
    miss = missing_cells_by_judge(rows, subjects, scenarios, pressures, framings, scopes, ["g", "o"])
    assert miss["g"] == set()
    assert miss["o"] == {("s1", "S-1", "p1", "unstated", "full")}


# ── Real-data guards (skip where the gitignored roots are absent) ───────────────────


@_skip
def test_both_judges_complete_over_canonical_universe_except_documented_residual():
    """Every judge covers the canonical universe, except the 2 documented residual Opus empties."""
    per_root = [read_run_root(str(r)) for r in _ROOTS]
    traditions = sorted({t for root in per_root for t in root})

    unexpected: dict[str, dict[str, tuple]] = {}  # tradition -> judge -> (count, sample)
    for tradition in traditions:
        rows, scenarios = _resolved_rows_and_universe(tradition, per_root)
        miss = missing_cells_by_judge(
            rows, CANONICAL_SUBJECTS, scenarios, PRESSURES, FRAMINGS, SCOPES, _JUDGES
        )
        for judge, gaps in miss.items():
            if judge == "claude-opus-4-8":
                gaps = {c for c in gaps if (tradition, *c) not in _KNOWN_RESIDUAL_OPUS_MISSING}
            if gaps:
                unexpected.setdefault(tradition, {})[judge] = (len(gaps), sorted(gaps)[:5])

    assert not unexpected, (
        "UNEXPECTED single-judge cells beyond the 2 documented residual Opus empties "
        f"(tradition -> judge -> (count, sample)): {unexpected}"
    )


@_skip
def test_residual_single_judge_cells_are_exactly_the_documented_two():
    """The residual Opus-missing set is exactly the 2 documented cells — no more, no fewer.

    Fails if a later re-judge recovered one (update the allowlist + `ranking.single_judge_cells`)
    or a new empty appeared. Keeps the disclosed count honest against the real data.
    """
    per_root = [read_run_root(str(r)) for r in _ROOTS]
    traditions = sorted({t for root in per_root for t in root})
    residual: set = set()
    for tradition in traditions:
        rows, _scenarios = _resolved_rows_and_universe(tradition, per_root)
        by_cell: dict[tuple, set] = {}
        for r in rows:
            cell = (r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
            by_cell.setdefault(cell, set()).add(r["judge"])
        for cell, judges in by_cell.items():
            if "claude-opus-4-8" not in judges:
                residual.add((tradition, *cell))
    assert residual == _KNOWN_RESIDUAL_OPUS_MISSING, f"residual Opus-missing set changed: {sorted(residual)}"
