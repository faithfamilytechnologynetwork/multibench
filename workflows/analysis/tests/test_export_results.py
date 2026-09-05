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
                          opus_skip_subjects: tuple = (), score_fn=None):
    """A COMPLETE Gemini grid + a (by default COMPLETE) Opus grid over 2 scenarios.

    ``opus_drop`` optionally omits one Opus (subject, framing, scope, pressure, scenario) cell;
    ``opus_skip_subjects`` omits whole subjects from the Opus layer (to test the DECLARED-universe
    coverage denominator: Gemini's report still declares all 5 subjects). ``score_fn(sub, subj, fr,
    scope, pr, sc) -> float`` sets per-cell scores (default: a flat 0.5); pass a varying one to
    exercise aggregation with non-uniform, judge-differing data.
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
                            score = 0.5 if score_fn is None else score_fn(sub, subj, fr, scope, pr, sc)
                            rows.append(_row(subj, sc, pr, fr, scope, sub, score, f"{judge}{i}"))
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


def test_no_strictly_complete_judge_fails_fast(tmp_path):
    # #120 re-shaped gate: the combined ranking needs AT LEAST ONE strictly-complete real judge.
    # If BOTH judges are gappy, there is nothing to rank on → fail fast.
    root = _write_two_full_grids(tmp_path)
    for run in ("gemini-run", "opus-run"):  # drop a cell from EACH judge → neither complete
        p = root / run / _TRAD / "judgments.jsonl"
        lines = p.read_text().splitlines()
        p.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    exports = build_corpus_export([root / "gemini-run", root / "opus-run"])
    with pytest.raises(AnalysisInputError, match="no strictly-complete real judge"):
        build_manifest(exports, run_id="r", generated_at="t")


def test_one_incomplete_judge_still_ranks_on_the_complete_one(tmp_path):
    # #120: if Gemini is complete but Opus has a gap, the combined ranking is still well-defined
    # (Gemini covers the grid). The export must SUCCEED — the old "rankable must be complete" gate
    # is gone; what matters is >=1 strictly-complete judge.
    root = _write_two_full_grids(tmp_path)
    opus = root / "opus-run" / _TRAD / "judgments.jsonl"
    lines = opus.read_text().splitlines()
    opus.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")  # Opus loses one cell
    exports = build_corpus_export([root / "gemini-run", root / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t")  # no raise
    assert m["ranking"]["rule"] == "mean_of_judges"


def test_opus_only_complete_run_ranks_on_combined(tmp_path):
    # #120: a single strictly-complete real judge (Opus alone) is enough — combined == that judge.
    root = _write_two_full_grids(tmp_path)
    (root / "opus-run" / _TRAD / "report.json").write_text(
        json.dumps(_report(["T-1", "T-2"], list(CANONICAL_SUBJECTS), ["claude-opus-4-8"])),
        encoding="utf-8")
    exports = build_corpus_export([root / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t")  # no raise (Opus is complete)
    assert m["ranking"]["judges"] == ["claude-opus-4-8"]
    assert m["ranking"]["score_key"] == "combined"


def test_two_rankable_judges_is_allowed_now(tmp_path, monkeypatch):
    # #120: ranking is on the combined mean, so the old "exactly one rankable" ambiguity is gone —
    # two judges flagged rankable is fine (rankable is now legacy selector/fallback metadata).
    monkeypatch.setitem(JUDGE_UI, "claude-opus-4-8", {"key": "opus", "rankable": True})
    exports = build_corpus_export(
        [_write_two_full_grids(tmp_path) / "gemini-run", tmp_path / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t")  # no raise
    assert m["ranking"]["rule"] == "mean_of_judges"


# ── #120: combined two-judge block + ranking declaration ───────────────────────────

def _combined_fixture(rows: list[dict], scenarios: list[str]) -> "object":
    """Build one TraditionExport from explicit rows (both judges), report over `scenarios`."""
    rep = _report(scenarios, list(CANONICAL_SUBJECTS), ["gemini-3.6-flash", "claude-opus-4-8"])
    raw = RawTradition(tradition=_TRAD, base=rows, v2=[], report=rep)
    return build_tradition_export(_TRAD, [raw])


def test_combined_equals_mean_of_per_judge_means_when_fully_double_judged():
    # Every cell scored by BOTH judges → the combined breakdown mean equals the mean of the two
    # per-judge breakdown means, exactly (the equivalence the spec requires on double-judged sets).
    S, FR, SCP, PR = "claude-sonnet-5", "unstated", "full", "secularize"
    rows = []
    for sc, g, o in (("T-1", 0.8, 0.4), ("T-2", 0.6, 0.2)):
        rows.append(_row(S, sc, PR, FR, SCP, "gemini-3.6-flash", g, f"g{sc}"))
        rows.append(_row(S, sc, PR, FR, SCP, "claude-opus-4-8", o, f"o{sc}"))
    exp = _combined_fixture(rows, ["T-1", "T-2"])
    gem = exp.means[("gemini-3.6-flash", S, FR, SCP, PR)].mean          # (0.8+0.6)/2 = 0.7
    opus = exp.means[("claude-opus-4-8", S, FR, SCP, PR)].mean          # (0.4+0.2)/2 = 0.3
    combined = exp.combined_means[(S, FR, SCP, PR)].mean                # (0.6+0.4)/2 = 0.5
    assert combined == pytest.approx((gem + opus) / 2)                  # 0.5 == 0.5
    assert not exp.single_judge_cells                                   # nothing single-judged


def test_single_judge_cell_uses_lone_verdict_and_diverges():
    # A cell scored by ONE judge contributes its lone verdict to the combined score, is reported as
    # a single-judge cell, and makes combined differ from the mean of per-judge means.
    S, FR, SCP, PR = "claude-sonnet-5", "unstated", "full", "secularize"
    rows = [
        _row(S, "T-1", PR, FR, SCP, "gemini-3.6-flash", 0.8, "g1"),
        _row(S, "T-1", PR, FR, SCP, "claude-opus-4-8", 0.4, "o1"),  # T-1 double-judged
        _row(S, "T-2", PR, FR, SCP, "gemini-3.6-flash", 0.2, "g2"),  # T-2 gemini-only
    ]
    exp = _combined_fixture(rows, ["T-1", "T-2"])
    gem = exp.means[("gemini-3.6-flash", S, FR, SCP, PR)].mean   # (0.8+0.2)/2 = 0.5
    opus = exp.means[("claude-opus-4-8", S, FR, SCP, PR)].mean   # 0.4
    combined = exp.combined_means[(S, FR, SCP, PR)].mean         # (0.6 + 0.2)/2 = 0.4
    assert combined == pytest.approx(0.4)
    assert combined != pytest.approx((gem + opus) / 2)           # diverges (0.4 != 0.45)
    # single-judge cell carries the PRESENT judge (T-2 was gemini-only)
    assert (S, "T-2", PR, FR, SCP, "gemini-3.6-flash") in exp.single_judge_cells


def test_combined_block_serialized_separately_from_means():
    exp = _combined_fixture(
        [_row("claude-sonnet-5", "T-1", "secularize", "unstated", "full", j, 0.5, f"{j}")
         for j in ("gemini-3.6-flash", "claude-opus-4-8")], ["T-1"])
    shard = serialize_tradition(exp)
    assert "combined" in shard and "combined_steadfastness" in shard
    assert set(shard["means"]) == {"gemini-3.6-flash", "claude-opus-4-8"}  # combined NOT in means
    # combined shape mirrors a single judge's sub-tree: subject -> framing -> scope -> pressure -> [..]
    cell = shard["combined"]["claude-sonnet-5"]["unstated"]["full"]["secularize"]
    assert len(cell) == 3 and cell[0] == 0.5


def test_ranking_declaration_shape_and_disjointness(tmp_path):
    exports = build_corpus_export(
        [_write_two_full_grids(tmp_path) / "gemini-run", tmp_path / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t", single_judge_attempts=3)
    r = m["ranking"]
    assert r["rule"] == "mean_of_judges"
    assert r["score_key"] == "combined"
    assert r["judges"] == ["claude-opus-4-8", "gemini-3.6-flash"]
    assert r["score_key"] not in {j["model"] for j in m["judges"]}   # disjoint from real judges
    assert r["score_key"] not in m["counts"]["coverage"]             # never leaked into coverage
    assert r["single_judge_cells"] == {"count": 0, "cells": [], "attempts": 3}


def test_single_judge_cells_recorded_in_manifest(tmp_path):
    # Drop one Opus cell → that (subject, scenario, ...) becomes a single-judge (gemini-only) cell,
    # recorded in ranking.single_judge_cells with its full id.
    drop = ("claude-sonnet-5", "unstated", "full", "secularize", "T-1")
    root = _write_two_full_grids(tmp_path, opus_drop=drop)
    exports = build_corpus_export([root / "gemini-run", root / "opus-run"])
    m = build_manifest(exports, run_id="r", generated_at="t")
    sj = m["ranking"]["single_judge_cells"]
    assert sj["count"] == 1
    assert sj["cells"][0] == {
        "tradition": _TRAD, "subject": "claude-sonnet-5", "scenario_id": "T-1",
        "pressure": "secularize", "framing": "unstated", "scope": "full",
        "judge_present": "gemini-3.6-flash",  # Opus cell dropped → only Gemini scored it
    }


def test_single_judge_cells_list_is_capped(tmp_path):
    # A pathological single-judge run would enumerate ~93k cells and blow the manifest ceiling;
    # the count stays exact but the cell list is capped + flagged truncated.
    from analysis.export_results import SINGLE_JUDGE_CELLS_CAP, ranking_declaration
    cells = [{"tradition": "t", "subject": f"s{i}"} for i in range(SINGLE_JUDGE_CELLS_CAP + 10)]
    r = ranking_declaration(cells, ["claude-opus-4-8"])
    assert r["single_judge_cells"]["count"] == SINGLE_JUDGE_CELLS_CAP + 10  # exact
    assert len(r["single_judge_cells"]["cells"]) == SINGLE_JUDGE_CELLS_CAP  # capped
    assert r["single_judge_cells"]["cells_truncated"] is True


def test_build_manifest_empty_judges_fails_fast():
    # An export with no judges (e.g. an empty judgments.jsonl) must fail-fast with a clear error,
    # not an IndexError.
    rep = _report(["T-1"], list(CANONICAL_SUBJECTS), ["gemini-3.6-flash"])
    raw = RawTradition(tradition=_TRAD, base=[], v2=[], report=rep)
    exports = {_TRAD: build_tradition_export(_TRAD, [raw])}
    with pytest.raises(AnalysisInputError, match="no judges in the export"):
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
    # Gemini now incomplete AND the Opus validation layer is a partial sample → NO complete judge.
    with pytest.raises(AnalysisInputError, match="no strictly-complete real judge"):
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


# ── #120: combined-stats capability + v3-bundle reconciliation ──────────────────────


def test_combined_stats_reconciles_with_export(tmp_path):
    # The committed combined-stats primitive's subj_overall (point) must equal the results-export
    # combined mean-of-means — both are the mean over traditions of the combined by_framing[full],
    # from the SAME cell_scores reducer (no second averaging implementation).
    from analysis.combined_stats import build_combined_stats, export_combined_mean_of_means
    # Non-uniform, judge-differing scores (from the valid discrete set) so the reconciliation
    # actually exercises the aggregation — a flat fixture couldn't tell the two paths apart. The
    # combined cell = (gemini+opus)/2 varies by framing and scenario.
    _GEM = {"unstated": {"T-1": 0.0, "T-2": 0.5}, "stated": {"T-1": 0.5, "T-2": 1.0},
            "guided": {"T-1": 1.0, "T-2": 0.5}}
    _OPUS = {"unstated": {"T-1": -0.5, "T-2": 0.0}, "stated": {"T-1": 0.0, "T-2": 0.5},
             "guided": {"T-1": 0.5, "T-2": 1.0}}
    def score_fn(sub, subj, fr, scope, pr, sc):
        return (_GEM if sub == "gemini-3.6-flash" else _OPUS)[fr][sc]
    root = _write_two_full_grids(tmp_path, score_fn=score_fn)
    roots = [str(root / "gemini-run"), str(root / "opus-run")]
    bundle = build_combined_stats(roots, n_boot=20)  # n_boot small: point estimate is boot-independent
    mom = export_combined_mean_of_means(roots)
    assert set(bundle["subj_overall_point"]) == set(mom)
    for k in mom:  # reconcile to fp tolerance (both from cell_scores, so exact in practice)
        assert bundle["subj_overall_point"][k] == pytest.approx(mom[k], abs=1e-12)
    assert set(mom) == {f"{s}|{fr}" for s in CANONICAL_SUBJECTS for fr in ("unstated", "stated", "guided")}
    # Sanity: the fixture is genuinely non-uniform, so a constant-output bug in either path would
    # fail the reconciliation above. combined unstated = mean(T-1 (0+-0.5)/2=-0.25, T-2 (0.5+0)/2=0.25)
    # = 0.0; combined guided = mean(T-1 (1+0.5)/2=0.75, T-2 (0.5+1)/2=0.75) = 0.75.
    assert mom["claude-sonnet-5|unstated"] == pytest.approx(0.0)
    assert mom["claude-sonnet-5|guided"] == pytest.approx(0.75)


def test_combined_stats_cli(tmp_path):
    from typer.testing import CliRunner

    from analysis.cli import app

    root = _write_two_full_grids(tmp_path)
    out = tmp_path / "combined.json"
    result = CliRunner().invoke(app, [
        "combined-stats", str(root / "gemini-run"), str(root / "opus-run"),
        "--out", str(out), "--n-boot", "20",
    ])
    assert result.exit_code == 0, result.output
    bundle = json.loads(out.read_text())
    assert "subj_overall_point" in bundle and "traditions" in bundle
    # Deterministic: re-running yields byte-identical output.
    out2 = tmp_path / "combined2.json"
    CliRunner().invoke(app, ["combined-stats", str(root / "gemini-run"), str(root / "opus-run"),
                             "--out", str(out2), "--n-boot", "20"])
    assert out.read_bytes() == out2.read_bytes()


_V3_BUNDLE = _MERGED / "analysis-out" / "figures-report-v3" / "stats_bundle.json"


@_skip
@pytest.mark.skipif(not _V3_BUNDLE.is_file(), reason="v3 stats_bundle.json not present")
def test_combined_mean_of_means_reconciles_with_v3_bundle():
    """The combined headline guard (#120): the results-export combined mean-of-means
    (scope=full, pressure=all) equals the v3 bundle's ``subj_overall`` point to ≤1e-9 — the
    combined analogue of the Gemini paper pin at ``test_launch_gemini_leaderboard_matches_paper``.
    """
    from analysis.combined_stats import export_combined_mean_of_means
    mom = export_combined_mean_of_means([str(_MERGED), str(_UNSTATED_OPUS), str(_FRAMINGS_OPUS),
                                         str(_MERGED.parent / "20260823-opus-fullgrid")])
    v3 = json.loads(_V3_BUNDLE.read_text())["subj_overall"]
    for key, val in mom.items():
        assert val == pytest.approx(v3[key][0], abs=1e-9), key


_V2_BUNDLE = _MERGED / "analysis-out" / "figures-report-v2" / "stats_bundle.json"


@pytest.mark.skipif(not (_V3_BUNDLE.is_file() and _V2_BUNDLE.is_file()),
                    reason="v2/v3 stats bundles not present")
def test_v3_bundle_schema_and_dual_judge_recompute():
    """v3 keeps v2's top-level schema (so paper_figs_multibench.py runs unchanged); its dual_judge
    per-judge subsections stay RAW Gemini-vs-Opus (not polluted by the combined score); and
    `dual_judge.full_grid` is RECOMPUTED on the COMPLETED grid (architect 2026-09-05), with v2's
    partial-Opus full_grid preserved under a labelled legacy key. Score aggregates ARE combined."""
    v2 = json.loads(_V2_BUNDLE.read_text())
    v3 = json.loads(_V3_BUNDLE.read_text())
    assert sorted(v2) == sorted(v3)                       # same top-level keys
    assert v3["meta"] == v2["meta"]                       # meta unchanged
    assert v3["subj_overall"] != v2["subj_overall"]       # score aggregates ARE combined (differ)
    dj2, dj3 = v2["dual_judge"], v3["dual_judge"]
    # The raw per-judge subsections are unchanged from v2 (combined rule does not touch them).
    for key in ("unstated", "framings_sample", "unstated_rank", "framings_tier", "route_bridge"):
        assert dj3[key] == dj2[key], key
    # full_grid recomputed on the completed grid: its n exceeds v2's partial-Opus n (the 33 recovered
    # cells), and v2's block is preserved verbatim under the legacy key.
    assert dj3["full_grid"]["overall"]["n"] > dj2["full_grid"]["overall"]["n"]  # 93,418 > 93,385
    assert dj3["full_grid_v2_partial"] == dj2["full_grid"]                       # labelled legacy
    # The recomputed full_grid keeps ALL of v2's subkeys (incl. `rank`: order/order_identical/
    # per-subject means) — so the narrowing that dropped `rank` can't recur.
    assert set(dj3["full_grid"]) >= set(dj2["full_grid"]), sorted(dj2["full_grid"])
    assert set(dj3["full_grid"]["rank"]) == {"unstated", "stated", "guided"}
    assert all("order_identical" in dj3["full_grid"]["rank"][f] for f in ("unstated", "stated", "guided"))
    # Reconcile the recompute with the paper's reported full-grid agreement (docs/analysis/
    # 110-dual-judge-fullgrid-summary.md), which was computed at n=93,385 — so per-framing r matches
    # to within the shift from the 33 recovered cells (<=0.005), and overall r/within are unchanged.
    fg = dj3["full_grid"]
    assert fg["overall"]["r"] == pytest.approx(0.833, abs=0.003)
    for framing, r_doc in (("unstated", 0.854), ("stated", 0.825), ("guided", 0.683)):
        assert fg[framing]["r"] == pytest.approx(r_doc, abs=0.005), framing


@_skip
@pytest.mark.skipif(not _V3_BUNDLE.is_file(), reason="v3 stats bundle not present")
def test_v3_dual_judge_n_matches_paper_figs_live_pairing():
    """The v3 bundle's `dual_judge.unstated.n` / `framings_sample.n` must equal what
    paper_figs_multibench.py computes LIVE (it asserts `len(pairs_un/fr) == bundle n`). After
    Phase 1 grew the unstated Opus layer (31,114 -> 31,139), reusing v2's stale n would hard-fail
    that assert — this replicates paper_figs's exact load_opus (raw-gemini lut; mapped dedupe + v2
    overlay for the sample) and pins the equality."""
    import json as _json
    _SMAP = {"anthropic/claude-sonnet-5": "claude-sonnet-5",
             "thinkingmachines/inkling": "thinkingmachines/Inkling",
             "openai/gpt-5.6-terra": "gpt-5.6-terra", "google/gemini-3.6-flash": "gemini-3.6-flash",
             "qwen/qwen3-235b-a22b-2507": "Qwen/Qwen3-235B-A22B-Instruct-2507"}
    trads = sorted(p.name for p in _MERGED.iterdir()
                   if (p / "judgments.jsonl").is_file())
    gem = {}
    for t in trads:
        for line in (_MERGED / t / "judgments.jsonl").read_text().splitlines():
            if line.strip():
                j = _json.loads(line)
                gem[(j["subject"], j["tradition"], j["scenario_id"], j["pressure"],
                     j["framing"], j["scope"])] = j["score"]

    def load_opus(base, mapped):
        out, by_id = [], {}
        for t in trads:
            fp = base / t / "judgments.jsonl"
            if not fp.is_file():
                continue
            lines = fp.read_text().splitlines()
            v2 = base / t / "judgments_v2.jsonl"
            if v2.is_file():
                lines += v2.read_text().splitlines()
            for line in lines:
                if not line.strip():
                    continue
                j = _json.loads(line)
                if mapped:
                    j["subject"] = _SMAP[j["subject"]]
                    k = (j["subject"], j["tradition"], j["scenario_id"], j["pressure"],
                         j["framing"], j["scope"])
                    if k not in by_id or j.get("ts", "") >= by_id[k].get("ts", ""):
                        by_id[k] = j
                else:
                    out.append(j)
        return list(by_id.values()) if mapped else out

    def n_paired(rows):
        return sum(1 for j in rows if (j["subject"], j["tradition"], j["scenario_id"],
                                       j["pressure"], j["framing"], j["scope"]) in gem)

    dj = _json.loads(_V3_BUNDLE.read_text())["dual_judge"]
    assert n_paired(load_opus(_UNSTATED_OPUS, mapped=False)) == dj["unstated"]["n"]
    assert n_paired(load_opus(_FRAMINGS_OPUS, mapped=True)) == dj["framings_sample"]["n"]


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


# ── #120 Phase 4: additive re-export of results/20260803 vs the pinned pre-change baseline ──
# The baseline is the committed dataset as of HEAD before the re-export (git show HEAD:results/...),
# pinned so the byte-identity/delta assertions are reproducible on single-line minified shards.
_BASELINE = Path(__file__).resolve().parent / "fixtures" / "results-20260803-baseline"
_has_baseline = pytest.mark.skipif(
    not (_BASELINE / "manifest.json").is_file(), reason="pinned baseline fixture absent")
# Traditions whose Opus layer received a recovered cell in Phase 1 (per the runbook table).
_RECOVERED_TRADS = {"judaism", "roman-catholicism", "secular-sage", "sunni-islam", "taoism"}


@_has_committed
@_has_baseline
def test_committed_gemini_block_byte_identical_to_baseline():
    """Baked #2: the Gemini per-judge block is byte-identical across the re-export (Gemini is
    unchanged by the #120 re-judge) — the value the paper-reconciliation guard rests on."""
    for entry in json.loads((_COMMITTED / "manifest.json").read_text())["traditions"]:
        new = json.loads((_COMMITTED / entry["shard"]).read_text())
        base = json.loads((_BASELINE / entry["shard"]).read_text())
        for block in ("means", "steadfastness"):  # both the mean and steadfastness Gemini sub-trees
            assert json.dumps(new[block].get("gemini-3.6-flash"), sort_keys=True) == \
                json.dumps(base[block].get("gemini-3.6-flash"), sort_keys=True), f"{entry['id']}/{block}"


@_has_committed
@_has_baseline
def test_committed_opus_delta_bounded_to_recovered_cells():
    """The Opus block's delta is bounded to EXACTLY the grid-completion cells:
    - untouched traditions (no recovered cell) are byte-identical;
    - within any tradition, a slice whose ``n_judged`` is UNCHANGED must be byte-identical (so an
      unrelated score change — a mean shift without added coverage — is caught);
    - the total added Opus coverage over specific-pressure slices (both scopes) == 33 (35 missing −
      2 residual).
    This is the precise "delta bounded" guard (a monotonic-n check alone would miss a mean-only edit).
    """
    _EXPECTED_RECOVERED = 33
    total_added = 0
    for entry in json.loads((_COMMITTED / "manifest.json").read_text())["traditions"]:
        t = entry["id"]
        new = json.loads((_COMMITTED / entry["shard"]).read_text())["means"].get("claude-opus-4-8", {})
        base = json.loads((_BASELINE / entry["shard"]).read_text())["means"].get("claude-opus-4-8", {})
        if t not in _RECOVERED_TRADS:
            assert json.dumps(new, sort_keys=True) == json.dumps(base, sort_keys=True), \
                f"{t}: Opus block changed but received no recovered cell"
        for subj, byfr in base.items():
            for fr, bysc in byfr.items():
                for sc, bypr in bysc.items():
                    for pr, cell in bypr.items():
                        ncell = new.get(subj, {}).get(fr, {}).get(sc, {}).get(pr)
                        assert ncell is not None, f"{t}/{subj}/{fr}/{sc}/{pr} vanished"
                        assert ncell[1] >= cell[1], f"{t}/{subj}/{fr}/{sc}/{pr} n_judged dropped"
                        if ncell[1] == cell[1]:
                            assert ncell == cell, f"{t}/{subj}/{fr}/{sc}/{pr} changed without added coverage"
                        if pr != "all":  # specific-pressure slices count each cell once
                            total_added += ncell[1] - cell[1]
    assert total_added == _EXPECTED_RECOVERED, total_added


@_has_committed
def test_committed_combined_block_and_ranking():
    """The re-export adds the combined block + a ranking declaration (rule/score_key/judges)."""
    manifest = json.loads((_COMMITTED / "manifest.json").read_text())
    r = manifest["ranking"]
    assert r["rule"] == "mean_of_judges" and r["score_key"] == "combined"
    assert r["score_key"] not in {j["model"] for j in manifest["judges"]}
    for entry in manifest["traditions"]:
        shard = json.loads((_COMMITTED / entry["shard"]).read_text())
        assert "combined" in shard and "combined_steadfastness" in shard
        assert set(shard["means"]) <= {j["model"] for j in manifest["judges"]}  # combined NOT in means


@_has_committed
@pytest.mark.skipif(not _V3_BUNDLE.is_file(), reason="v3 stats bundle not present")
def test_committed_combined_mean_of_means_reconciles_with_v3_bundle():
    """The combined headline guard on the COMMITTED artifact (analogue of the Gemini paper pin):
    the mean over traditions of the committed shards' `combined[subject][framing][full][all]` equals
    the v3 bundle's `subj_overall` point to ≤1e-9 — so the shipped dataset and the paper bundle
    cannot disagree on the ranked number."""
    shards = {}
    for entry in json.loads((_COMMITTED / "manifest.json").read_text())["traditions"]:
        shards[entry["id"]] = json.loads((_COMMITTED / entry["shard"]).read_text())
    v3 = json.loads(_V3_BUNDLE.read_text())["subj_overall"]
    for subj in CANONICAL_SUBJECTS:
        for fr in ("unstated", "stated", "guided"):
            vals = [sh["combined"][subj][fr]["full"]["all"][0]
                    for sh in shards.values()
                    if subj in sh.get("combined", {})]
            mom = sum(vals) / len(vals)
            assert mom == pytest.approx(v3[f"{subj}|{fr}"][0], abs=1e-9), f"{subj}|{fr}"


@_has_committed
def test_committed_ranking_single_judge_matches_grid_allowlist():
    """Three-way lockstep: the manifest's single_judge_cells match the grid-completeness test's
    documented residual set exactly — so the runbook, the test allowlist, and the shipped manifest
    cannot drift on the residual pair."""
    from test_grid_completeness import _KNOWN_RESIDUAL_OPUS_MISSING

    sj = json.loads((_COMMITTED / "manifest.json").read_text())["ranking"]["single_judge_cells"]
    manifest_cells = {
        (c["tradition"], c["subject"], c["scenario_id"], c["pressure"], c["framing"], c["scope"])
        for c in sj["cells"]
    }
    assert sj["count"] == len(_KNOWN_RESIDUAL_OPUS_MISSING)
    assert manifest_cells == _KNOWN_RESIDUAL_OPUS_MISSING
