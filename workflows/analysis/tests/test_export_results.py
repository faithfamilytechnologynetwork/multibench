"""Tests for the results export core (#49, Phase 1).

Two tiers:
* **Deterministic unit tests** on tiny synthetic run roots built in ``tmp_path`` — no
  dependence on the git-ignored ``tmp/judging-runs/`` symlink, so they run in CI / for
  any builder. They cover normalization (incl. the Qwen ``-Instruct`` case + fail-fast),
  the ``judgments_v2.jsonl`` overlay, the Opus alias-collision dedup (later-``ts`` wins),
  full-grid coverage vs an Opus subset, and matched-cell steadfastness on an asymmetric
  panel.
* **Real-data parity** (``skipif`` when the symlink is absent): the sealed launch runs'
  Gemini leaderboard mean-of-means equals the paper's ``subj_overall`` and per-tradition
  steadfastness equals ``report.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.export_results import (
    CANONICAL_SUBJECTS,
    build_corpus_export,
    build_tradition_export,
    leaderboard_mean_of_means,
    normalize_judge,
    normalize_subject,
    read_run_root,
    resolve_judgments,
)
from analysis.loaders import AnalysisInputError

# ── Synthetic-fixture helpers ─────────────────────────────────────────────────────

_TRAD = "buddhism"  # any real tradition name works; rows just must be self-consistent


def _row(subject, scenario, pressure, framing, scope, judge, score, ts):
    return {
        "subject": subject, "tradition": _TRAD, "scenario_id": scenario,
        "pressure": pressure, "framing": framing, "judge": judge,
        "scope": scope, "score": score, "ts": ts,
    }


def _write_run(root: Path, *, base, v2=None, report=None) -> Path:
    """Write a one-tradition run root: <root>/<trad>/{judgments,[v2],[report]}."""
    d = root / _TRAD
    d.mkdir(parents=True)
    (d / "judgments.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in base), encoding="utf-8"
    )
    if v2:
        (d / "judgments_v2.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in v2), encoding="utf-8"
        )
    if report is not None:
        (d / "report.json").write_text(json.dumps(report), encoding="utf-8")
    return root


def _report(scenarios, subjects, judges):
    return {
        "tradition": _TRAD,
        "subjects": subjects,
        "judges": judges,
        "by_scenario": {s: {} for s in scenarios},
    }


# ── Normalization ─────────────────────────────────────────────────────────────────


def test_subject_normalization_maps_all_variants_incl_qwen_instruct():
    assert normalize_subject("qwen/qwen3-235b-a22b-2507") == "Qwen/Qwen3-235B-A22B-Instruct-2507"
    assert normalize_subject("anthropic/claude-sonnet-5") == "claude-sonnet-5"
    assert normalize_subject("thinkingmachines/inkling") == "thinkingmachines/Inkling"
    # canonical ids map to themselves
    for canon in CANONICAL_SUBJECTS:
        assert normalize_subject(canon) == canon
    assert len(CANONICAL_SUBJECTS) == 5


def test_unmapped_subject_and_judge_fail_fast():
    with pytest.raises(AnalysisInputError, match="unmapped subject"):
        normalize_subject("mystery/model-9")
    with pytest.raises(AnalysisInputError, match="unmapped judge"):
        normalize_judge("mystery/judge-9")


def test_judge_alias_collapses_to_one_opus():
    assert normalize_judge("anthropic/claude-opus-4.8") == "claude-opus-4-8"
    assert normalize_judge("claude-opus-4-8") == "claude-opus-4-8"
    assert normalize_judge("gemini-3.6-flash") == "gemini-3.6-flash"


# ── Overlay + alias-collision dedup ───────────────────────────────────────────────


def test_disjoint_aliases_both_survive_count_equals_sum(tmp_path):
    # Distinct identities, one under each Opus alias → both survive normalization,
    # deduped count == sum of the two alias row counts (no loss, no collision).
    base = [
        _row("anthropic/claude-sonnet-5", "T-1", "flattery", "unstated", "full",
             "claude-opus-4-8", 0.5, "a"),
        _row("anthropic/claude-sonnet-5", "T-2", "flattery", "unstated", "full",
             "anthropic/claude-opus-4.8", -0.5, "b"),  # different scenario → distinct id
    ]
    raws = [read_run_root(_write_run(tmp_path, base=base))[_TRAD]]
    rows = resolve_judgments(raws)
    assert len(rows) == len(base) == 2  # count == sum, nothing collapsed
    assert all(r["judge"] == "claude-opus-4-8" for r in rows)
    assert {r["scenario_id"] for r in rows} == {"T-1", "T-2"}


def test_v2_duplicate_precedence_is_file_order_not_ts(tmp_path):
    # Two v2 rows for the SAME identity: the LAST in file order wins even though its ts
    # is EARLIER (loader last-wins parity; ts is not used for same-file v2 dedup).
    base = [_row("claude-sonnet-5", "T-1", "flattery", "unstated", "full",
                 "claude-opus-4-8", 0.0, "base")]
    v2 = [
        _row("claude-sonnet-5", "T-1", "flattery", "unstated", "full",
             "claude-opus-4-8", 0.5, "2026-08-05T00:00:09+00:00"),  # later ts, earlier line
        _row("claude-sonnet-5", "T-1", "flattery", "unstated", "full",
             "claude-opus-4-8", 1.0, "2026-08-05T00:00:01+00:00"),  # earlier ts, LAST line
    ]
    raws = [read_run_root(_write_run(tmp_path, base=base, v2=v2))[_TRAD]]
    rows = resolve_judgments(raws)
    assert len(rows) == 1
    assert rows[0]["score"] == 1.0  # last v2 line wins, not the later-ts one


def test_resolve_judgments_dedup_and_overlay(tmp_path):
    base = [
        # identity A — alias collision: two aliases, same identity, later ts = -1.0 wins
        _row("anthropic/claude-sonnet-5", "T-1", "flattery", "unstated", "full",
             "claude-opus-4-8", 0.5, "2026-08-01T00:00:00Z"),
        _row("anthropic/claude-sonnet-5", "T-1", "flattery", "unstated", "full",
             "anthropic/claude-opus-4.8", -1.0, "2026-08-02T00:00:00Z"),
        # identity B (different scenario) — a base row that a v2 row will override
        _row("claude-sonnet-5", "T-2", "flattery", "unstated", "full",
             "claude-opus-4-8", 0.0, "2026-08-01T00:00:00Z"),
    ]
    v2 = [
        _row("claude-sonnet-5", "T-2", "flattery", "unstated", "full",
             "claude-opus-4-8", 1.0, "2026-08-03T00:00:00Z"),  # v2 wins over base
    ]
    raws = [read_run_root(_write_run(tmp_path, base=base, v2=v2))[_TRAD]]
    rows = resolve_judgments(raws)
    # 2 distinct identities remain (the collision collapsed to one; T-2 once, v2-overridden)
    assert len(rows) == 2
    scores = sorted(r["score"] for r in rows)
    assert scores == [-1.0, 1.0]  # -1.0 (collision later-ts on T-1), 1.0 (v2 override on T-2)
    # both variants normalized to the canonical subject + one Opus judge
    assert all(r["subject"] == "claude-sonnet-5" for r in rows)
    assert all(r["judge"] == "claude-opus-4-8" for r in rows)


# ── Coverage + full grid vs subset ────────────────────────────────────────────────


def _full_grid_rows(subject, judge, scopes=("turn1", "full")):
    rows = []
    for sc in ("T-1", "T-2", "T-3"):
        for scope in scopes:
            rows.append(_row(subject, sc, "secularize", "unstated", scope, judge, 1.0,
                             f"2026-08-01T00:00:0{len(rows)}Z"))
    return rows


def test_coverage_full_grid_vs_opus_subset(tmp_path):
    # Gemini covers all 3 scenarios; Opus covers only 1 → honest low coverage.
    gem_root = tmp_path / "gem"
    _write_run(gem_root,
               base=_full_grid_rows("claude-sonnet-5", "gemini-3.6-flash"),
               report=_report(["T-1", "T-2", "T-3"], ["claude-sonnet-5"], ["gemini-3.6-flash"]))
    opus_root = tmp_path / "opus"
    _write_run(opus_root, base=[
        _row("anthropic/claude-sonnet-5", "T-1", "secularize", "unstated", "full",
             "claude-opus-4-8", 1.0, "2026-08-01T00:00:00Z"),
    ])
    exp = build_corpus_export([gem_root, opus_root])[_TRAD]
    assert exp.n_scenarios == 3
    g = exp.means[("gemini-3.6-flash", "claude-sonnet-5", "unstated", "full", "secularize")]
    assert g.n_judged == 3 and g.n_expected == 3  # full grid
    o = exp.means[("claude-opus-4-8", "claude-sonnet-5", "unstated", "full", "secularize")]
    assert o.n_judged == 1 and o.n_expected == 3  # honest 1/3, not ~100%


def test_stray_scenario_outside_universe_fails(tmp_path):
    gem_root = tmp_path / "gem"
    _write_run(gem_root,
               base=[_row("claude-sonnet-5", "T-9", "secularize", "unstated", "full",
                          "gemini-3.6-flash", 1.0, "t")],
               report=_report(["T-1", "T-2"], ["claude-sonnet-5"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="not in the full-grid"):
        build_corpus_export([gem_root])


def test_missing_report_universe_fails(tmp_path):
    opus_root = tmp_path / "opus"
    _write_run(opus_root, base=[_row("claude-sonnet-5", "T-1", "secularize", "unstated",
                                     "full", "claude-opus-4-8", 1.0, "t")])
    with pytest.raises(AnalysisInputError, match="no run root provides report.json"):
        build_corpus_export([opus_root])


# ── Matched-cell steadfastness on an asymmetric panel ─────────────────────────────


def test_matched_cell_steadfastness_takes_intersection(tmp_path):
    # T-1 has both scopes; T-2 has only turn1 (asymmetric). Steadfastness must use only
    # the matched cell(s), i.e. T-1: full(1.0) - turn1(-1.0) = 2.0, matched_n == 1.
    rows = [
        _row("claude-sonnet-5", "T-1", "secularize", "unstated", "turn1",
             "gemini-3.6-flash", -1.0, "a"),
        _row("claude-sonnet-5", "T-1", "secularize", "unstated", "full",
             "gemini-3.6-flash", 1.0, "b"),
        _row("claude-sonnet-5", "T-2", "secularize", "unstated", "turn1",
             "gemini-3.6-flash", 0.5, "c"),  # no matching full → excluded
    ]
    root = tmp_path / "gem"
    _write_run(root, base=rows,
               report=_report(["T-1", "T-2"], ["claude-sonnet-5"], ["gemini-3.6-flash"]))
    exp = build_tradition_export(_TRAD, [read_run_root(root)[_TRAD]])
    st = exp.steadfastness[("gemini-3.6-flash", "claude-sonnet-5", "unstated", "secularize")]
    assert st.matched_n == 1
    assert st.value == pytest.approx(2.0)


# ── Committed multi-run fixture (end-to-end, always runs) ─────────────────────────

_FIXTURE = Path(__file__).parent / "fixtures" / "export"


def test_committed_fixture_end_to_end():
    exp = build_corpus_export([_FIXTURE / "gemini-run", _FIXTURE / "opus-run"])["buddhism"]
    assert exp.n_scenarios == 2
    assert set(exp.judges) == {"gemini-3.6-flash", "claude-opus-4-8"}
    S, PR, FR = "claude-sonnet-5", "secularize", "unstated"
    # Gemini full grid: mean of full scores (1.0, 0.5) = 0.75, full coverage 2/2
    g = exp.means[("gemini-3.6-flash", S, FR, "full", PR)]
    assert g.mean == pytest.approx(0.75) and (g.n_judged, g.n_expected) == (2, 2)
    # Gemini steadfastness: full mean 0.75 − turn1 mean (-0.5) = 1.25 over 2 matched cells
    gst = exp.steadfastness[("gemini-3.6-flash", S, FR, PR)]
    assert gst.value == pytest.approx(1.25) and gst.matched_n == 2
    # Opus: variant subject normalized; alias collision on T-1 overridden by v2 → 1.0;
    # honest coverage 1/2 (only T-1 judged).
    o = exp.means[("claude-opus-4-8", S, FR, "full", PR)]
    assert o.mean == pytest.approx(1.0) and (o.n_judged, o.n_expected) == (1, 2)


def test_committed_fixture_v2_orphan_rejected(tmp_path):
    # A v2 row with no matching base identity must be rejected (never adds a vote).
    root = tmp_path / "gem"
    _write_run(
        root,
        base=[_row("claude-sonnet-5", "T-1", "secularize", "unstated", "full",
                   "gemini-3.6-flash", 1.0, "a")],
        v2=[_row("claude-sonnet-5", "T-2", "secularize", "unstated", "full",
                 "gemini-3.6-flash", 0.5, "b")],  # T-2 has no base → orphan
        report=_report(["T-1", "T-2"], ["claude-sonnet-5"], ["gemini-3.6-flash"]),
    )
    with pytest.raises(AnalysisInputError, match="never adds a vote"):
        build_corpus_export([root])


def test_same_file_duplicate_base_identity_rejected(tmp_path):
    root = tmp_path / "gem"
    dup = _row("claude-sonnet-5", "T-1", "secularize", "unstated", "full",
               "gemini-3.6-flash", 1.0, "a")
    _write_run(root, base=[dup, dict(dup, score=0.5, ts="b")],
               report=_report(["T-1"], ["claude-sonnet-5"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="duplicate base identity"):
        build_corpus_export([root])


# ── Real-data parity (sealed launch runs) ─────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MERGED = _REPO_ROOT / "tmp" / "judging-runs" / "20260803-merged"
_UNSTATED_OPUS = _REPO_ROOT / "tmp" / "judging-runs" / "20260803-unstated-opus"
_FRAMINGS_OPUS = _REPO_ROOT / "tmp" / "judging-runs" / "20260803-framings-opus-sample"
_HAS_LAUNCH = _MERGED.is_dir() and _UNSTATED_OPUS.is_dir() and _FRAMINGS_OPUS.is_dir()
_skip = pytest.mark.skipif(not _HAS_LAUNCH, reason="launch run data (tmp/judging-runs/) unavailable")


@pytest.fixture(scope="module")
def launch_export():
    return build_corpus_export([_MERGED, _UNSTATED_OPUS, _FRAMINGS_OPUS])


@_skip
def test_launch_two_judges_five_subjects(launch_export):
    # Assert the OBSERVED normalized sets from the real merged data — not just constants.
    observed_judges: set[str] = set()
    observed_subjects: set[str] = set()
    for exp in launch_export.values():
        observed_judges |= set(exp.judges)
        observed_subjects |= {key[1] for key in exp.means}  # subject is means-key[1]
    assert observed_judges == {"gemini-3.6-flash", "claude-opus-4-8"}
    assert observed_subjects == set(CANONICAL_SUBJECTS)
    assert len(observed_subjects) == 5


@_skip
def test_launch_opus_alias_collision_deduped():
    # The live sunni-islam collision: many identities appear under BOTH Opus aliases.
    # After normalization the export must count each once — so the deduped Opus cell
    # count is strictly less than the raw row count by exactly the collision count.
    from analysis.export_results import read_run_root, resolve_judgments
    raws = [root["sunni-islam"] for root in
            (read_run_root(_FRAMINGS_OPUS),) if "sunni-islam" in root]
    rows = resolve_judgments(raws)
    opus = [r for r in rows if r["judge"] == "claude-opus-4-8"]
    raw_opus = sum(1 for r in raws[0].base) + sum(1 for r in raws[0].v2)
    # dedup actually removed rows (the collision is real, not theoretical)
    assert len(opus) < raw_opus
    # every surviving identity is unique
    ids = {(r["subject"], r["scenario_id"], r["pressure"], r["framing"], r["scope"])
           for r in opus}
    assert len(ids) == len(opus)


@_skip
def test_launch_gemini_by_framing_matches_report(launch_export):
    for trad, exp in launch_export.items():
        rep = json.loads((_MERGED / trad / "report.json").read_text())
        for subj in CANONICAL_SUBJECTS:
            for fr in ("unstated", "stated", "guided"):
                got = exp.means[("gemini-3.6-flash", subj, fr, "full", "all")].mean
                assert got == pytest.approx(rep["scorecard"][subj]["by_framing"][fr],
                                            abs=1e-9), f"{trad}/{subj}/{fr}"


@_skip
def test_launch_gemini_leaderboard_matches_paper(launch_export):
    sb = json.loads((_MERGED / "analysis-out" / "figures-report-v2" /
                     "stats_bundle.json").read_text())
    for subj in CANONICAL_SUBJECTS:
        for fr in ("unstated", "stated", "guided"):
            mom = leaderboard_mean_of_means(launch_export, "gemini-3.6-flash", subj, fr,
                                            "full", "all")
            paper = sb["subj_overall"][f"{subj}|{fr}"][0]
            assert mom == pytest.approx(paper, abs=1e-9), f"{subj}|{fr}"


@_skip
def test_launch_gemini_steadfastness_matches_report(launch_export):
    for trad, exp in launch_export.items():
        rep = json.loads((_MERGED / trad / "report.json").read_text())
        for subj in CANONICAL_SUBJECTS:
            st = exp.steadfastness[("gemini-3.6-flash", subj, "unstated", "all")]
            assert st.value == pytest.approx(rep["scorecard"][subj]["steadfastness"], abs=1e-9)
            for pr, want in rep["scorecard"][subj]["steadfastness_by_pressure"].items():
                got = exp.steadfastness[("gemini-3.6-flash", subj, "unstated", pr)]
                assert got.value == pytest.approx(want, abs=1e-9), f"{trad}/{subj}/{pr}"
