"""Aggregation tests (spec T3): recomputed aggregates reproduce the upstream
``report.json`` to ≤1e−9 for every field the spec names, and the cell reducer
averages present judges only (asymmetric-panel correctness, D5).
"""

from pathlib import Path

import pytest

from analysis.aggregate import (
    TECHNIQUE_IDS,
    aggregate_tradition,
    cell_scores,
    check_parity,
    mean,
)
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.loaders import load_run_dir

FIX = Path(__file__).resolve().parent / "fixtures"
TRADITIONS = ["buddhism", "taoism"]


@pytest.mark.parametrize("trad", TRADITIONS)
def test_parity_with_report_json(trad):
    # The load-bearing self-check (M3): recomputing from judgments (+v2 overlay) must
    # match the report.json produced by the real judging aggregator.
    agg = aggregate_tradition(load_run_dir(FIX / trad))
    diffs = check_parity(agg, tol=1e-9)
    assert diffs == [], "parity mismatches:\n" + "\n".join(diffs)


@pytest.mark.parametrize("trad", TRADITIONS)
def test_recomputed_headline_matches_exactly(trad):
    run = load_run_dir(FIX / trad)
    agg = aggregate_tradition(run)
    for s in run.subjects:
        assert agg.scorecard[s]["headline"] == pytest.approx(
            run.report["scorecard"][s]["headline"], abs=1e-12
        )


def test_universal_core_axes():
    assert tuple(FRAMINGS) == ("unstated", "stated", "guided")
    assert set(PRESSURES) == {
        "secularize", "insistence", "false_authority",
        "good_cause", "flattery", "personal_appeal",
    }
    assert len(TECHNIQUE_IDS) == 7


def test_mean_empty_is_none_not_zero():
    assert mean([]) is None
    assert mean([1.0, 0.0]) == 0.5


def test_cell_reducer_averages_present_judges_only():
    # Asymmetric panel (D5): a sonnet cell judged by two judges averages both; an opus
    # cell judged by one judge is that single score — never diluted by an absent judge.
    judgments = [
        {"subject": "claude-sonnet-4-6", "scenario_id": "X-1", "pressure": "secularize",
         "framing": "unstated", "scope": "full", "judge": "claude-opus-4-8", "score": 1.0},
        {"subject": "claude-sonnet-4-6", "scenario_id": "X-1", "pressure": "secularize",
         "framing": "unstated", "scope": "full", "judge": "gemini-3.5-flash", "score": 0.0},
        {"subject": "claude-opus-4-8", "scenario_id": "X-1", "pressure": "secularize",
         "framing": "unstated", "scope": "full", "judge": "gemini-3.5-flash", "score": -0.5},
    ]
    cs = cell_scores(judgments)
    assert cs[("claude-sonnet-4-6", "X-1", "secularize", "unstated", "full")] == 0.5
    assert cs[("claude-opus-4-8", "X-1", "secularize", "unstated", "full")] == -0.5


def test_partial_run_uncovered_scenario_stays_in_cluster_set():
    # CMAP finding (PR #27): a scenario that was collected but produced ZERO judgments
    # (present in report.json's by_scenario — upstream keys it by judgments ∪ sittings —
    # but absent from judgments.jsonl) must remain in the bootstrap cluster set, else the
    # cluster count is understated and the CIs are too tight.
    import copy
    import dataclasses

    from analysis.stats import compute_tradition_stats

    run = load_run_dir(FIX / "buddhism")
    judged = sorted({j["scenario_id"] for j in run.judgments})
    assert set(run.report["by_scenario"]) == set(judged)  # fixture is a full run

    # Simulate a partial run: an extra collected-but-unjudged scenario in by_scenario only.
    report = copy.deepcopy(run.report)
    report["by_scenario"]["BUD-900"] = {s: None for s in run.subjects}
    partial = dataclasses.replace(run, report=report)

    agg = aggregate_tradition(partial)
    assert "BUD-900" in agg.scenario_ids
    assert len(agg.scenario_ids) == len(judged) + 1
    assert agg.by_scenario["BUD-900"] == {s: None for s in run.subjects}

    # The bootstrap now resamples over the fuller cluster set (N+1), not the judged-only set.
    st = compute_tradition_stats(agg, n_boot=50, seed=12345)
    assert len(agg.scenario_ids) == len(st.scenario_ids)
    assert "BUD-900" in st.scenario_ids


def test_techniques_and_agreement_are_recomputed():
    # Guard that these are genuinely recomputed (not read through) — the parity check
    # would still pass if they were read through, so assert they came from judgments.
    run = load_run_dir(FIX / "buddhism")
    agg = aggregate_tradition(run)
    for s in run.subjects:
        assert set(agg.techniques[s]) == set(TECHNIQUE_IDS)
    assert agg.agreement["cells"] >= 1
    assert 0.0 <= agg.agreement["exact_pct"] <= 1.0
