"""Grid-completeness of the two-judge `20260803` run (issue #120, Phase 1).

After grid completion (re-judging the Opus empty-response cells, #116) **both** judges must be
strictly complete over the canonical 93,420-cell universe — so the combined two-judge mean has no
single-judge fallback. This guards that invariant.

Design notes:
- **Compare each judge against the canonical universe, not judge-vs-judge.** Two judges can share
  an identical set that omits the same cells; equality would then pass while both are incomplete
  (plan-review finding). The universe is `subjects × scenarios × framings × pressures × scopes`
  per tradition, with `scenarios` taken from each tradition's ``report.json`` ``by_scenario`` (the
  declared full grid) — the same denominator the exporter pins ``n_scenarios`` to.
- **Real-data, skip-when-absent.** Like the other launch-data tests, this reads the gitignored
  ``tmp/judging-runs/`` roots and skips when they are not present (a fixtures-only checkout / the
  builder worktree). It runs where the data lives (the main checkout, post-merge).
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
# The four roots in results/README.md order (full-grid Opus last for source precedence).
_ROOTS = [
    _RUNS / "20260803-merged",
    _RUNS / "20260803-unstated-opus",
    _RUNS / "20260803-framings-opus-sample",
    _RUNS / "20260823-opus-fullgrid",
]
_JUDGES = ("gemini-3.6-flash", "claude-opus-4-8")

_have = all(r.is_dir() for r in _ROOTS)
_skip = pytest.mark.skipif(not _have, reason="launch run data (tmp/judging-runs/) unavailable")

# The two cells that persistently returned an empty/truncated Opus verdict after the re-judge
# (issue #120 Phase 1: 3 passes, 9+ attempts) — reported, NOT imputed (architect instruction,
# 2026-09-05). The combined score uses their single (Gemini) verdict; the manifest discloses
# them via `ranking.single_judge_cells`. This allowlist keeps the test an honest guard: any OTHER
# missing cell (or a regression on these) fails. Keyed (tradition, subject, scenario, pressure,
# framing, scope), Opus-missing.
_KNOWN_RESIDUAL_OPUS_MISSING = {
    ("judaism", "gemini-3.6-flash", "MSR-025", "insistence", "unstated", "full"),
    ("sunni-islam", "Qwen/Qwen3-235B-A22B-Instruct-2507", "JLS-122", "flattery", "guided", "full"),
}


@_skip
def test_both_judges_strictly_complete_over_canonical_universe():
    """Every judge covers every canonical cell, except the 2 documented residual Opus empties."""
    per_root = [read_run_root(str(r)) for r in _ROOTS]
    traditions = sorted({t for root in per_root for t in root})

    missing: dict[str, dict[str, int]] = {}  # tradition -> judge -> count missing
    for tradition in traditions:
        present = [(i, root[tradition]) for i, root in enumerate(per_root) if tradition in root]
        raws = [rt for _i, rt in present]
        priorities = [i for i, _rt in present]
        rows = resolve_judgments(raws, priorities)

        # Declared full-grid scenario universe from report.json (matches the exporter's pinning).
        reports = [rt.report for rt in raws if rt.report is not None]
        assert reports, f"{tradition}: no report.json among roots"
        scenarios = sorted(reports[0].get("by_scenario", {}))
        assert scenarios, f"{tradition}: empty by_scenario universe"

        universe = set(
            itertools.product(CANONICAL_SUBJECTS, scenarios, PRESSURES, FRAMINGS, SCOPES)
        )
        by_judge: dict[str, set] = {j: set() for j in _JUDGES}
        for r in rows:
            cell = (r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
            by_judge.setdefault(r["judge"], set()).add(cell)

        for judge in _JUDGES:
            gaps = universe - by_judge.get(judge, set())
            # Opus's documented, persistent residual empties are allowed (reported, not imputed).
            if judge == "claude-opus-4-8":
                gaps = {c for c in gaps if (tradition, *c) not in _KNOWN_RESIDUAL_OPUS_MISSING}
            if gaps:
                missing.setdefault(tradition, {})[judge] = sorted(gaps)[:5]

    assert not missing, (
        "grid has UNEXPECTED single-judge cells beyond the 2 documented residual Opus empties: "
        f"{missing}"
    )


@_skip
def test_residual_single_judge_cells_are_exactly_the_documented_two():
    """The residual Opus-missing set is exactly the 2 documented cells — no more, no fewer.

    Fails if a re-judge recovered one (update the allowlist + `single_judge_cells`) or if a new
    empty appeared (investigate). Keeps the disclosed count honest against the real data.
    """
    per_root = [read_run_root(str(r)) for r in _ROOTS]
    traditions = sorted({t for root in per_root for t in root})
    residual: set = set()
    for tradition in traditions:
        present = [(i, root[tradition]) for i, root in enumerate(per_root) if tradition in root]
        rows = resolve_judgments([rt for _i, rt in present], [i for i, _rt in present])
        by_cell: dict[tuple, set] = {}
        for r in rows:
            cell = (r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
            by_cell.setdefault(cell, set()).add(r["judge"])
        for cell, judges in by_cell.items():
            if "claude-opus-4-8" not in judges:
                residual.add((tradition, *cell))
    assert residual == _KNOWN_RESIDUAL_OPUS_MISSING, (
        f"residual Opus-missing set changed: {sorted(residual)}"
    )
