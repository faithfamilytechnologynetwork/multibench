"""CI-runnable coverage of the committed paper-bundle generator (#120).

`build_paper_bundle` is the reproducible, committed replacement for the old gitignored figs script.
This exercises the WHOLE pipeline on a tiny fixture (its taxonomy is parameterized) and asserts the
generator's `subj_overall` point reconciles with the results-export combined mean-of-means — so the
bundle-reconciliation is verified in CI without the gitignored launch roots. A real-data test that
reconciles against the shipped v3 bundle also lives in `test_export_results.py` (skip-when-absent).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.combined_stats import export_combined_mean_of_means
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.paper_bundle import build_paper_bundle

_SUBJECTS = ["claude-sonnet-5", "gpt-5.6-terra"]
_TRADS = ["buddhism", "taoism"]
_SCENARIOS = ["T-1", "T-2"]
_SCOPES = ["turn1", "full"]
# valid discrete verdicts (raw scores must be in the -1..+1 set); gemini != opus, and both VARY by
# scenario so per-slice variance is non-zero (no NaN corrcoef in the fixture's dual_judge).
_GEM = {("unstated", "T-1"): 0.0, ("unstated", "T-2"): 0.5, ("stated", "T-1"): 0.5,
        ("stated", "T-2"): 1.0, ("guided", "T-1"): 1.0, ("guided", "T-2"): 0.5}
_OPUS = {("unstated", "T-1"): -0.5, ("unstated", "T-2"): 0.0, ("stated", "T-1"): 0.0,
         ("stated", "T-2"): 0.5, ("guided", "T-1"): 0.5, ("guided", "T-2"): 1.0}


def _row(subject, tradition, scenario, pressure, framing, judge, scope, score, ts):
    return {"subject": subject, "tradition": tradition, "scenario_id": scenario, "pressure": pressure,
            "framing": framing, "judge": judge, "scope": scope, "score": score, "ts": ts}


def _write(root: Path, run: str, tradition: str, rows: list[dict], report: bool = False):
    d = root / run / tradition
    d.mkdir(parents=True, exist_ok=True)
    (d / "judgments.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    if report:
        (d / "report.json").write_text(json.dumps({
            "tradition": tradition, "subjects": _SUBJECTS, "judges": ["gemini-3.6-flash"],
            "by_scenario": {s: {} for s in _SCENARIOS},
        }), encoding="utf-8")


def _write_fixture(root: Path) -> list[str]:
    """Four roots (README order) with a tiny full grid: Gemini in merged (+report); Opus split
    unstated→unstated-opus, stated/guided→opus-fullgrid (framings-sample carries a copy so the
    dual_judge sample path is non-empty)."""
    for t in _TRADS:
        gem, opus_un, opus_sg = [], [], []
        for subj in _SUBJECTS:
            for fr in FRAMINGS:
                for scope in _SCOPES:
                    for pr in PRESSURES:
                        for sc in _SCENARIOS:
                            gem.append(_row(subj, t, sc, pr, fr, "gemini-3.6-flash", scope, _GEM[(fr, sc)], "g"))
                            orow = _row(subj, t, sc, pr, fr, "claude-opus-4-8", scope, _OPUS[(fr, sc)], "o")
                            (opus_un if fr == "unstated" else opus_sg).append(orow)
        _write(root, "merged", t, gem, report=True)
        _write(root, "unstated-opus", t, opus_un)
        _write(root, "framings-opus-sample", t, opus_sg)
        _write(root, "opus-fullgrid", t, opus_sg)
    return [str(root / r) for r in ("merged", "unstated-opus", "framings-opus-sample", "opus-fullgrid")]


def test_paper_bundle_reconciles_with_export_on_a_fixture(tmp_path):
    roots = _write_fixture(tmp_path)
    tiers = {"easy": _TRADS}
    expected_cells = len(_SUBJECTS) * len(_TRADS) * len(_SCENARIOS) * len(PRESSURES) * len(FRAMINGS) * len(_SCOPES)
    bundle = build_paper_bundle(roots, subjects=_SUBJECTS, traditions=_TRADS, tiers=tiers,
                                top2=_SUBJECTS[:1], expected_cells=expected_cells, n_boot=25)
    mom = export_combined_mean_of_means(roots)
    # The generator's subj_overall POINT == the results-export combined mean-of-means (both are the
    # mean over traditions of breakdown_mean(cell_scores(all judges), …, full), so equal by construction).
    for s in _SUBJECTS:
        for f in FRAMINGS:
            assert bundle["subj_overall"][f"{s}|{f}"][0] == pytest.approx(mom[f"{s}|{f}"], abs=1e-12), f"{s}|{f}"
    # combined unstated = mean over 2 scenarios of (T-1 (0.0+-0.5)/2=-0.25, T-2 (0.5+0.0)/2=0.25) = 0.0.
    assert mom["claude-sonnet-5|unstated"] == pytest.approx(0.0)
    # Schema: all paper-bundle keys present, incl. the dual_judge full_grid recompute.
    assert {"tier", "subj_overall", "trad_pooled", "model_tier", "gaps_pooled",
            "steadfastness_by_framing", "dual_judge"} <= set(bundle)
    assert "full_grid" in bundle["dual_judge"] and "rank" in bundle["dual_judge"]["full_grid"]


def test_paper_bundle_rejects_wrong_cell_count(tmp_path):
    roots = _write_fixture(tmp_path)
    with pytest.raises(ValueError, match="expected .* combined cells"):
        build_paper_bundle(roots, subjects=_SUBJECTS, traditions=_TRADS, tiers={"easy": _TRADS},
                           top2=_SUBJECTS[:1], expected_cells=999999, n_boot=10)
