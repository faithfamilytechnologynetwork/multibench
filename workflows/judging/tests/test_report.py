"""Report aggregation (spec §5.8/§5.9): mechanical means, distribution, agreement, generic
taxonomy breakdowns (M7), coverage without silent zeros (M12), partial data."""

import json

import pytest

from judging.loaders import load_scenario, load_tradition
from judging.report import build_report, write_report


def _judg(subject, scenario_id, pressure, framing, judge, scope, score, techs=()):
    return {
        "sitting_key": f"{subject}|{scenario_id}|{pressure}|{framing}",
        "subject": subject,
        "tradition": "sunni-islam",
        "scenario_id": scenario_id,
        "pressure": pressure,
        "framing": framing,
        "judge": judge,
        "scope": scope,
        "score": score,
        "direction": "d",
        "rationale": "r",
        "techniques_used": list(techs),
        "usage": {},
        "ts": "t",
    }


def _write_judgments(tmp_path, rows):
    (tmp_path / "judgments.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )


def test_cell_reducer_and_headline(sunni, tmp_path):
    # Two judges +1.0 / 0.0 on one cell -> mean +0.5 -> headline +0.5 (T15).
    _write_judgments(
        tmp_path,
        [
            _judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0),
            _judg("sub", "JLS-001", "secularize", "unstated", "jB", "full", 0.0),
        ],
    )
    rep = build_report(tmp_path, sunni)
    assert rep["scorecard"]["sub"]["headline"] == 0.5


def test_steadfastness_full_minus_turn1(sunni, tmp_path):
    _write_judgments(
        tmp_path,
        [
            _judg("sub", "JLS-001", "secularize", "unstated", "jA", "turn1", 1.0),
            _judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 0.5),
        ],
    )
    sc = build_report(tmp_path, sunni)["scorecard"]["sub"]
    assert sc["headline"] == 0.5
    assert sc["steadfastness"] == pytest.approx(-0.5)


def test_score_distribution_over_per_judge_verdicts(sunni, tmp_path):
    _write_judgments(
        tmp_path,
        [
            _judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0),
            _judg("sub", "JLS-001", "secularize", "unstated", "jB", "full", 1.0),
            _judg("sub", "JLS-001", "insistence", "unstated", "jA", "full", -0.5),
        ],
    )
    d = build_report(tmp_path, sunni)["score_distribution"]["sub"]
    assert d["1.0"] == 2
    assert d["-0.5"] == 1
    assert d["0.0"] == 0


def test_single_judge_has_no_agreement(sunni, tmp_path):
    # T12: a single-judge config produces a report with no agreement metric.
    _write_judgments(tmp_path, [_judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0)])
    a = build_report(tmp_path, sunni)["agreement"]
    assert a["cells"] == 0
    assert a["exact_pct"] is None


def test_agreement_exact_and_within_one(sunni, tmp_path):
    _write_judgments(
        tmp_path,
        [
            _judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0),
            _judg("sub", "JLS-001", "secularize", "unstated", "jB", "full", 1.0),  # exact
            _judg("sub", "JLS-001", "insistence", "unstated", "jA", "full", 0.5),
            _judg("sub", "JLS-001", "insistence", "unstated", "jB", "full", 0.0),  # gap 0.5
        ],
    )
    a = build_report(tmp_path, sunni)["agreement"]
    assert a["cells"] == 2
    assert a["exact_pct"] == 0.5
    assert a["within_one_pct"] == 1.0


def test_taxonomy_breakdown_is_generic(taoism, tmp_path):
    # M7/T7: breakdowns read the tradition's DECLARED axes — works for taoism, no code change.
    trad = load_tradition(taoism)
    sid = trad.scenario_ids[0]
    tags = load_scenario(taoism, sid).meta.tags
    axis = next(a for a in tags if tags[a])
    value = tags[axis][0]
    row = _judg("sub", sid, "secularize", "unstated", "jA", "full", 1.0)
    row["tradition"] = "taoism"
    _write_judgments(tmp_path, [row])
    rep = build_report(tmp_path, taoism)
    assert set(rep["taxonomies"]) == set(trad.manifest.taxonomies)  # not hardcoded pillars/hearts
    assert rep["taxonomies"][axis][value]["sub"] == 1.0


def test_coverage_counts_uncovered_no_silent_zero(sunni, tmp_path):
    # M12: expected cells from sittings x panel x scope; missing ones are uncovered, not 0.
    (tmp_path / "sittings.jsonl").write_text(
        json.dumps(
            {
                "subject": "claude-sonnet-4-6",
                "scenario_id": "JLS-001",
                "pressure": "secularize",
                "framing": "unstated",
                "turns": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_judgments(
        tmp_path,
        [_judg("claude-sonnet-4-6", "JLS-001", "secularize", "unstated", "claude-opus-4-8", "full", 1.0)],
    )
    c = build_report(tmp_path, sunni)["counts"]
    assert c["expected_cells"] == 4  # 2 judges x 2 scopes (sonnet subject, no self-skip)
    assert c["uncovered"] == 3


def test_skipped_self_counted(sunni, tmp_path):
    _write_judgments(tmp_path, [_judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0)])
    (tmp_path / "skipped.jsonl").write_text(
        json.dumps(
            {
                "subject": "claude-opus-4-8",
                "scenario_id": "JLS-001",
                "pressure": "secularize",
                "framing": "unstated",
                "judge": "claude-opus-4-8",
                "scope": "full",
                "reason": "self_judge",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert build_report(tmp_path, sunni)["counts"]["skipped_self"] == 1


def test_write_report_creates_files(sunni, tmp_path):
    _write_judgments(tmp_path, [_judg("sub", "JLS-001", "secularize", "unstated", "jA", "full", 1.0)])
    summary = write_report(tmp_path, sunni)
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "report.json").exists()
    assert summary["judgments"] == 1
    assert json.loads((tmp_path / "report.json").read_text())["tradition"] == "sunni-islam"


def test_report_computable_from_empty(sunni, tmp_path):
    # Never hard-fails on partial/empty data (M12).
    rep = build_report(tmp_path, sunni)
    assert rep["subjects"] == []
    assert rep["counts"]["judgments"] == 0
