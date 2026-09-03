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
import tempfile
from pathlib import Path

import pytest

from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.export_results import (
    SCOPES,
    CANONICAL_SUBJECTS,
    FULL_GRID_MIN_COVERAGE,
    JUDGE_UI,
    MAX_SHARD_BYTES,
    SCHEMA_VERSION,
    RawTradition,
    TraditionExport,
    assert_uniform_subject_roster,
    build_corpus_export,
    build_manifest,
    build_tradition_export,
    coverage_counts_from_judged,
    earns_full_grid,
    export_dataset,
    judge_coverage,
    leaderboard_mean_of_means,
    normalize_judge,
    normalize_subject,
    read_run_root,
    resolve_judgments,
    serialize_tradition,
    write_dataset,
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


def test_gemini_openrouter_slug_normalizes():
    # A run whose Gemini judge went through OpenRouter (#43 funded path / #89) records the
    # provider-prefixed slug; it must collapse to the canonical id like the Opus slug does.
    assert normalize_judge("google/gemini-3.6-flash") == "gemini-3.6-flash"


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


def test_unknown_dimension_values_fail_fast(tmp_path):
    # A typo in framing/pressure/scope must fail loudly, not be silently dropped from aggregates.
    for bad in (
        {"framing": "sideways"},
        {"pressure": "authority "},
        {"scope": "turn7"},
    ):
        root = tmp_path / f"gem-{list(bad)[0]}"
        row = _row("claude-sonnet-5", "T-1", "secularize", "unstated", "full",
                   "gemini-3.6-flash", 1.0, "t")
        row.update(bad)
        _write_run(root, base=[row],
                   report=_report(["T-1"], ["claude-sonnet-5"], ["gemini-3.6-flash"]))
        with pytest.raises(AnalysisInputError, match="unknown (framing|pressure|scope)"):
            build_corpus_export([root])


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


# ── Serialization: manifest + shards + round-trip + size (Phase 2) ────────────────


def _write_full_grid_fixture(root: Path):
    """A COMPLETE Gemini run (earns full_grid:true) + a partial Opus validation layer, for the
    manifest/writer tests (the committed minimal fixture is intentionally not full-grid)."""
    scenarios = ["T-1", "T-2"]
    gem = root / "gemini-run" / _TRAD
    gem.mkdir(parents=True)
    rows, i = [], 0
    for subj in CANONICAL_SUBJECTS:
        for fr in FRAMINGS:
            for scope in SCOPES:
                for pr in PRESSURES:
                    for sc in scenarios:
                        rows.append(_row(subj, sc, pr, fr, scope, "gemini-3.6-flash", 0.5, f"t{i}"))
                        i += 1
    (gem / "judgments.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (gem / "report.json").write_text(
        json.dumps(_report(scenarios, list(CANONICAL_SUBJECTS), ["gemini-3.6-flash"])), encoding="utf-8")
    # Partial Opus layer (validation sample): one subject/framing/pressure, both scopes, one scenario.
    op = root / "opus-run" / _TRAD
    op.mkdir(parents=True)
    orows = [_row("claude-sonnet-5", "T-1", "secularize", "unstated", scope, "claude-opus-4-8", 0.5, f"o{k}")
             for k, scope in enumerate(SCOPES)]
    (op / "judgments.jsonl").write_text("".join(json.dumps(r) + "\n" for r in orows), encoding="utf-8")


def _build_fixture_exports():
    root = Path(tempfile.mkdtemp())
    _write_full_grid_fixture(root)
    return build_corpus_export([root / "gemini-run", root / "opus-run"])


def test_manifest_has_required_fields_and_judge_consistency():
    exports = _build_fixture_exports()
    m = build_manifest(exports, run_id="testrun", generated_at="2026-08-06T00:00:00+00:00")
    assert m["schema_version"] == SCHEMA_VERSION
    assert m["run_id"] == "testrun"
    assert m["generated_at"] == "2026-08-06T00:00:00+00:00"
    assert m["subjects"] == list(CANONICAL_SUBJECTS)
    assert m["framings"] == ["unstated", "stated", "guided"]
    assert set(m["scopes"]) == {"turn1", "full"} and "steadfastness" in m["metrics"]
    # judges carry key/model/aliases + the EARNED full_grid, STATIC rankable, and coverage fraction;
    # opus absorbs both aliases
    by_model = {j["model"]: j for j in m["judges"]}
    assert by_model["claude-opus-4-8"]["key"] == "opus"
    assert by_model["claude-opus-4-8"]["full_grid"] is False  # missing stated+guided → not earned
    assert by_model["claude-opus-4-8"]["rankable"] is False   # static: a validation judge
    assert set(by_model["claude-opus-4-8"]["aliases"]) == {
        "claude-opus-4-8", "anthropic/claude-opus-4.8"}
    assert by_model["gemini-3.6-flash"]["full_grid"] is True  # earned from complete coverage
    assert by_model["gemini-3.6-flash"]["rankable"] is True   # static: the ranking judge
    assert "sample" not in by_model["claude-opus-4-8"]  # dropped: badge per-slice instead
    # every shard judge is declared in the manifest
    manifest_models = set(by_model)
    for exp in exports.values():
        assert set(exp.judges) <= manifest_models
    # per-tradition entries carry n_scenarios + shard filename
    assert m["traditions"] == [{"id": "buddhism", "n_scenarios": 2, "shard": "buddhism.json"}]
    # coverage: n_expected per framing is the FULL grid (total_scenarios(2) × subjects(5) ×
    # pressures(6) = 60), for EVERY framing, so an untouched framing reads honestly as 0/60.
    cov = m["counts"]["coverage"]
    assert cov["gemini-3.6-flash"]["unstated"] == {"n_judged": 60, "n_expected": 60}
    assert cov["claude-opus-4-8"]["unstated"] == {"n_judged": 1, "n_expected": 60}
    assert cov["claude-opus-4-8"]["stated"] == {"n_judged": 0, "n_expected": 60}
    assert cov["claude-opus-4-8"]["guided"] == {"n_judged": 0, "n_expected": 60}
    # the per-judge coverage fraction reconciles with the counts.coverage roll-up
    assert by_model["gemini-3.6-flash"]["coverage"] == 1.0
    assert by_model["claude-opus-4-8"]["coverage"] == round(1 / 180, 6)  # 1 judged of 3×60


# ── #96: earned full_grid + static rankable + coverage fraction + dedup precedence ──


def _cov(judged_by_framing: dict[str, int], n_expected: int) -> dict:
    """A one-judge ('j') coverage table with a fixed per-framing n_expected."""
    return {"j": {fr: {"n_judged": judged_by_framing.get(fr, 0), "n_expected": n_expected}
                  for fr in FRAMINGS}}


def test_earns_full_grid_both_sides_of_threshold():
    ne = 10_000
    # ~99.9% on every framing → earns (the full-grid state)
    assert earns_full_grid(_cov({"unstated": 9990, "stated": 9985, "guided": 9987}, ne), "j") is True
    # a designed sample: stated+guided ~14.5% → does NOT earn even though unstated is full
    assert earns_full_grid(_cov({"unstated": 9990, "stated": 1450, "guided": 1450}, ne), "j") is False
    # exactly at the 0.95 floor passes; just below fails (both sides of the threshold)
    assert earns_full_grid(_cov({fr: 9500 for fr in FRAMINGS}, ne), "j") is True
    assert earns_full_grid(_cov({fr: 9499 for fr in FRAMINGS}, ne), "j") is False
    # a framing the judge never touched is never full-grid, whatever the others read
    assert earns_full_grid(_cov({"unstated": ne, "stated": ne}, ne), "j") is False
    assert FULL_GRID_MIN_COVERAGE == 0.95


def test_judge_coverage_is_pooled_fraction():
    cov = _cov({"unstated": 100, "stated": 90, "guided": 80}, 100)
    assert judge_coverage(cov, "j") == (100 + 90 + 80) / 300
    assert judge_coverage(cov, "absent-judge") == 0.0


def _write_two_full_grids(root: Path, *, opus_drop: tuple | None = None,
                          opus_skip_subjects: tuple = ()):
    """A COMPLETE Gemini grid + a (by default COMPLETE) Opus grid over 2 scenarios.

    ``opus_drop`` optionally omits one Opus (subject, framing, scope, pressure, scenario) cell;
    ``opus_skip_subjects`` omits whole subjects from the Opus layer (to test the DECLARED-universe
    coverage denominator: Gemini's report still declares all 5 subjects).
    """
    scenarios = ["T-1", "T-2"]
    for judge, sub in (("gemini-run", "gemini-3.6-flash"), ("opus-run", "claude-opus-4-8")):
        d = root / judge / _TRAD
        d.mkdir(parents=True)
        rows, i = [], 0
        for subj in CANONICAL_SUBJECTS:
            if judge == "opus-run" and subj in opus_skip_subjects:
                continue
            for fr in FRAMINGS:
                for scope in SCOPES:
                    for pr in PRESSURES:
                        for sc in scenarios:
                            if judge == "opus-run" and opus_drop == (subj, fr, scope, pr, sc):
                                continue
                            rows.append(_row(subj, sc, pr, fr, scope, sub, 0.5, f"{judge}{i}"))
                            i += 1
        (d / "judgments.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    # Only the Gemini run carries report.json (the full-grid transcript source).
    (root / "gemini-run" / _TRAD / "report.json").write_text(
        json.dumps(_report(scenarios, list(CANONICAL_SUBJECTS), ["gemini-3.6-flash"])),
        encoding="utf-8")
    return root


def test_earning_full_grid_never_makes_a_validation_judge_rankable(tmp_path):
    # Opus at a COMPLETE grid earns the full_grid badge, but rankable stays statically False.
    exports = build_corpus_export(
        [_write_two_full_grids(tmp_path) / "gemini-run", tmp_path / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t")
    by_model = {j["model"]: j for j in m["judges"]}
    assert by_model["claude-opus-4-8"]["full_grid"] is True   # earned from real coverage
    assert by_model["claude-opus-4-8"]["rankable"] is False   # but never rankable
    assert by_model["claude-opus-4-8"]["coverage"] == 1.0
    assert by_model["gemini-3.6-flash"]["rankable"] is True   # the sole ranking judge


def test_rankable_judge_with_incomplete_grid_fails_fast(tmp_path):
    # Gemini (rankable) missing a single cell must NOT be written — strict gate fails fast.
    root = _write_two_full_grids(tmp_path)
    # Drop one Gemini cell by rewriting its run without it.
    gem = root / "gemini-run" / _TRAD / "judgments.jsonl"
    lines = gem.read_text().splitlines()
    gem.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")  # remove one judged cell
    exports = build_corpus_export([root / "gemini-run", root / "opus-run"])
    with pytest.raises(AnalysisInputError, match="incomplete coverage"):
        build_manifest(exports, run_id="r", generated_at="t")


def test_zero_rankable_judges_fails_fast(tmp_path):
    # An Opus-only run has no rankable judge → the leaderboard would have nothing to rank.
    root = _write_two_full_grids(tmp_path)
    # Give the opus run a report so it can stand alone as a corpus.
    (root / "opus-run" / _TRAD / "report.json").write_text(
        json.dumps(_report(["T-1", "T-2"], list(CANONICAL_SUBJECTS), ["claude-opus-4-8"])),
        encoding="utf-8")
    exports = build_corpus_export([root / "opus-run"])
    with pytest.raises(AnalysisInputError, match="exactly one rankable judge"):
        build_manifest(exports, run_id="r", generated_at="t")


def test_more_than_one_rankable_judge_fails_fast(tmp_path, monkeypatch):
    # If two judges were both marked rankable, ranking would be ambiguous → fail fast.
    monkeypatch.setitem(JUDGE_UI, "claude-opus-4-8", {"key": "opus", "rankable": True})
    exports = build_corpus_export(
        [_write_two_full_grids(tmp_path) / "gemini-run", tmp_path / "opus-run"])
    with pytest.raises(AnalysisInputError, match="exactly one rankable judge"):
        build_manifest(exports, run_id="r", generated_at="t")


def _one_row_tradition(score: float, ts: str) -> RawTradition:
    row = _row("claude-sonnet-5", "T-1", "secularize", "stated", "full", "claude-opus-4-8", score, ts)
    return RawTradition(tradition=_TRAD, base=[row], v2=[], report=None)


def test_dedup_priority_beats_ts_but_ts_still_breaks_equal_priority():
    sample = _one_row_tradition(0.1, "2026-09-01")     # LATER ts, but the low-priority sample root
    full_grid = _one_row_tradition(0.9, "2026-08-23")  # EARLIER ts, the high-priority full-grid root
    # Higher priority (full-grid, root index 1) wins despite its earlier ts.
    won = resolve_judgments([sample, full_grid], priorities=[0, 1])
    assert len(won) == 1 and won[0]["score"] == 0.9
    # Control: at EQUAL priority the architect's later-ts rule still governs (cross-alias case).
    won_eq = resolve_judgments([sample, full_grid], priorities=[0, 0])
    assert won_eq[0]["score"] == 0.1
    # Default (no priorities) is byte-compatible with the old later-ts behaviour.
    assert resolve_judgments([sample, full_grid])[0]["score"] == 0.1


def test_v2_override_respects_source_priority():
    def row(score):
        return _row("claude-sonnet-5", "T-1", "secularize", "stated", "full",
                    "claude-opus-4-8", score, "t")
    # A lower-priority sample v2 correction must NOT override the higher-priority full-grid base.
    sample = RawTradition(tradition=_TRAD, base=[row(0.1)], v2=[row(0.2)], report=None)
    full_grid = RawTradition(tradition=_TRAD, base=[row(0.9)], v2=[], report=None)
    assert resolve_judgments([sample, full_grid], priorities=[0, 1])[0]["score"] == 0.9
    # At equal priority, the loader's v2 last-wins is preserved (the correction applies).
    assert resolve_judgments([sample], priorities=[0])[0]["score"] == 0.2
    # A v2 at the winner's own priority DOES override (a full-grid correction of a full-grid base).
    full_v2 = RawTradition(tradition=_TRAD, base=[row(0.9)], v2=[row(0.7)], report=None)
    assert resolve_judgments([sample, full_v2], priorities=[0, 1])[0]["score"] == 0.7


def _min_export(tradition, subjects):
    return TraditionExport(tradition=tradition, n_scenarios=1, judges=[], n_judgments={},
                           means={}, steadfastness={}, fingerprint_lines=[], subjects=subjects)


def test_assert_uniform_subject_roster():
    roster = ("claude-sonnet-5", "gemini-3.6-flash")
    assert assert_uniform_subject_roster([roster, roster, roster]) == roster
    with pytest.raises(AnalysisInputError, match="differing subject rosters"):
        assert_uniform_subject_roster([roster, ("claude-sonnet-5",)])


def test_build_manifest_rejects_traditions_with_differing_subject_rosters():
    # Two traditions declaring different subject rosters must fail fast — the grid must be uniform.
    exports = {
        "buddhism": _min_export("buddhism", ("claude-sonnet-5", "gemini-3.6-flash")),
        "taoism": _min_export("taoism", ("claude-sonnet-5", "gpt-5.6-terra")),
    }
    with pytest.raises(AnalysisInputError, match="differing subject rosters"):
        build_manifest(exports, run_id="r", generated_at="t")


def test_coverage_denominator_uses_declared_subject_universe(tmp_path):
    # Opus judges only 4 of the 5 DECLARED subjects (Gemini's report declares all 5). The
    # denominator must be the declared 5, so Opus reads as a coverage gap (0.8), NOT a spurious
    # full grid from a shrunk 4-subject denominator.
    root = _write_two_full_grids(tmp_path, opus_skip_subjects=("Qwen/Qwen3-235B-A22B-Instruct-2507",))
    m = build_manifest(build_corpus_export([root / "gemini-run", root / "opus-run"]),
                       run_id="r", generated_at="t")
    by_model = {j["model"]: j for j in m["judges"]}
    assert by_model["claude-opus-4-8"]["full_grid"] is False        # 4/5 subjects → not full grid
    assert by_model["claude-opus-4-8"]["coverage"] == round(4 / 5, 6)
    # counts.coverage denominator is the full declared grid (5 subjects), not the observed 4.
    cov = m["counts"]["coverage"]["claude-opus-4-8"]["unstated"]
    assert cov["n_expected"] == 2 * len(CANONICAL_SUBJECTS) * len(PRESSURES)  # 2×5×6 = 60


def test_shard_written_to_disk_matches_serialize(tmp_path):
    exports = _build_fixture_exports()
    write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")
    on_disk = json.loads((tmp_path / "r1" / "buddhism.json").read_text())
    assert on_disk == serialize_tradition(exports["buddhism"])  # real disk round-trip
    # full grid, all scores 0.5: mean 0.5 over 2 scenarios; steadfastness = 0.5 − 0.5 = 0.0
    g = on_disk["means"]["gemini-3.6-flash"]["claude-sonnet-5"]["unstated"]["full"]["secularize"]
    assert g == [pytest.approx(0.5), 2, 2]
    gall = on_disk["means"]["gemini-3.6-flash"]["claude-sonnet-5"]["unstated"]["full"]["all"]
    assert gall == [pytest.approx(0.5), 12, 12]
    st = on_disk["steadfastness"]["gemini-3.6-flash"]["claude-sonnet-5"]["unstated"]["secularize"]
    assert st == [pytest.approx(0.0), 2]


def test_write_dataset_layout_and_deterministic(tmp_path):
    exports = _build_fixture_exports()
    written = write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")
    run_dir = tmp_path / "r1"
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "buddhism.json").is_file()
    assert {p.name for p in written} == {"manifest.json", "buddhism.json"}
    first = (run_dir / "buddhism.json").read_bytes()
    write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")
    assert (run_dir / "buddhism.json").read_bytes() == first  # byte-identical re-export


def test_write_dataset_prunes_stale_shards(tmp_path):
    exports = _build_fixture_exports()
    run_dir = tmp_path / "r1"
    run_dir.mkdir(parents=True)
    stale = run_dir / "atlantis.json"  # a tradition not in this export
    stale.write_text("{}")
    write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")
    assert not stale.exists()  # stale shard pruned on re-export


def test_write_dataset_shard_ceiling_enforced(tmp_path, monkeypatch):
    exports = _build_fixture_exports()
    monkeypatch.setattr("analysis.export_results.MAX_SHARD_BYTES", 5)  # force overflow
    with pytest.raises(AnalysisInputError, match="shard ceiling"):
        write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")
    assert not (tmp_path / "r1" / "buddhism.json").exists()  # nothing partial written


def test_write_dataset_rejects_unsafe_run_id(tmp_path):
    exports = _build_fixture_exports()
    for bad in ("../escape", "a/b", "..", ".hidden"):
        with pytest.raises(AnalysisInputError, match="unsafe run-id"):
            write_dataset(exports, tmp_path, bad, "2026-08-06T00:00:00+00:00")


def test_write_dataset_total_ceiling_enforced(tmp_path, monkeypatch):
    exports = _build_fixture_exports()
    monkeypatch.setattr("analysis.export_results.MAX_TOTAL_BYTES", 10)  # force overflow
    with pytest.raises(AnalysisInputError, match="total .* ceiling"):
        write_dataset(exports, tmp_path, "r1", "2026-08-06T00:00:00+00:00")


def test_export_dataset_end_to_end(tmp_path):
    src = tmp_path / "src"
    _write_full_grid_fixture(src)
    written = export_dataset([src / "gemini-run", src / "opus-run"],
                             tmp_path / "out", "r1", "2026-08-06T00:00:00+00:00")
    manifest = json.loads((tmp_path / "out" / "r1" / "manifest.json").read_text())
    # full grid: 5 subjects × 3 framings × 2 scopes × 6 pressures × 2 scenarios = 360
    assert manifest["counts"]["judgments"]["gemini-3.6-flash"] == 360
    assert manifest["counts"]["judgments"]["claude-opus-4-8"] == 2
    assert all(p.stat().st_size <= MAX_SHARD_BYTES for p in written)


def test_build_manifest_rejects_incomplete_full_grid(tmp_path):
    # A Gemini run missing part of the grid must NOT be written as full_grid:true — fail fast.
    src = tmp_path / "src"
    _write_full_grid_fixture(src)
    # Drop one pressure's rows for one subject/framing/scope from the Gemini run.
    gpath = src / "gemini-run" / _TRAD / "judgments.jsonl"
    kept = [
        line for line in gpath.read_text().splitlines()
        if not (json.loads(line)["subject"] == "claude-sonnet-5"
                and json.loads(line)["framing"] == "unstated"
                and json.loads(line)["scope"] == "full"
                and json.loads(line)["pressure"] == "secularize")
    ]
    gpath.write_text("\n".join(kept) + "\n", encoding="utf-8")
    exports = build_corpus_export([src / "gemini-run", src / "opus-run"])
    with pytest.raises(AnalysisInputError, match="incomplete coverage"):
        build_manifest(exports, "r1", "2026-08-06T00:00:00+00:00")


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


# ── CLI command-level test ────────────────────────────────────────────────────────


def test_export_cli_command(tmp_path):
    from typer.testing import CliRunner

    from analysis.cli import app

    src = tmp_path / "src"
    _write_full_grid_fixture(src)  # full-grid so build_manifest earns full_grid:true
    result = CliRunner().invoke(app, [
        "export", str(src / "gemini-run"), str(src / "opus-run"),
        "--run-id", "cli1", "--out", str(tmp_path / "out"),
    ])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["run_id"] == "cli1"
    assert out["traditions"] == ["buddhism"]
    assert out["counts"]["judgments"]["gemini-3.6-flash"] == 360  # CLI reports counts
    assert "coverage" in out["counts"]
    assert (tmp_path / "out" / "cli1" / "manifest.json").is_file()


def test_export_cli_input_error_exits_cleanly(tmp_path):
    from typer.testing import CliRunner

    from analysis.cli import app

    # opus-only (no report.json to pin the universe) → clean exit code 2, not a traceback
    result = CliRunner().invoke(app, [
        "export", str(_FIXTURE / "opus-run"), "--run-id", "bad", "--out", str(tmp_path),
    ])
    assert result.exit_code == 2
    assert "input error" in result.output


# ── The COMMITTED launch dataset (the real artifact, not the in-memory export) ─────

_COMMITTED = _REPO_ROOT / "results" / "20260803"
_has_committed = pytest.mark.skipif(
    not (_COMMITTED / "manifest.json").is_file(),
    reason="committed results/20260803/ dataset not present",
)


@_has_committed
def test_committed_dataset_sizes_and_consistency():
    """Assert on the committed results/<run-id>/ artifact — sizes + manifest↔shard
    consistency. Runs without the gitignored launch symlink (the data is committed)."""
    from analysis.export_results import MAX_TOTAL_BYTES

    manifest = json.loads((_COMMITTED / "manifest.json").read_text())
    manifest_models = {j["model"] for j in manifest["judges"]}
    assert manifest["subjects"] == list(CANONICAL_SUBJECTS)
    total = (_COMMITTED / "manifest.json").stat().st_size
    for entry in manifest["traditions"]:
        shard_path = _COMMITTED / entry["shard"]
        assert shard_path.is_file(), entry["shard"]
        assert shard_path.stat().st_size <= MAX_SHARD_BYTES
        total += shard_path.stat().st_size
        shard = json.loads(shard_path.read_text())
        assert shard["n_scenarios"] == entry["n_scenarios"]  # manifest ↔ shard agree
        assert set(shard["judges"]) <= manifest_models       # every shard judge declared
        assert set(shard["means"]) <= manifest_models        # no un-normalized judge id
    assert total <= MAX_TOTAL_BYTES


@_skip
@_has_committed
def test_committed_dataset_reconciles_with_paper():
    """The committed artifact (not the in-memory export) must match the paper's standings."""
    sb = json.loads((_MERGED / "analysis-out" / "figures-report-v2" /
                     "stats_bundle.json").read_text())
    shards = {}
    for entry in json.loads((_COMMITTED / "manifest.json").read_text())["traditions"]:
        shards[entry["id"]] = json.loads((_COMMITTED / entry["shard"]).read_text())
    for subj in CANONICAL_SUBJECTS:
        for fr in ("unstated", "stated", "guided"):
            vals = [shard["means"]["gemini-3.6-flash"][subj][fr]["full"]["all"][0]
                    for shard in shards.values()
                    if subj in shard["means"].get("gemini-3.6-flash", {})]
            mom = sum(vals) / len(vals)
            assert mom == pytest.approx(sb["subj_overall"][f"{subj}|{fr}"][0], abs=1e-9)
