"""Tests for the raw-results export core (#51, Phase 1) — the pure transform.

Deterministic unit/integration tests over tiny synthetic run roots in ``tmp_path`` (no
dependence on the git-ignored ``tmp/judging-runs/`` symlink). They cover the new sitting
reader (normalization, dedup, conflicting-prefix, unstated-prefix, malformed turns), the
transcript↔verdict join (field parity, orphan abort, universe both-ways, per-scenario
grid completeness, normalized-subject join, full-grid-only transcript source), the
per-shard contexts pool, the generic catalog, the streaming generator, and the shared
source fingerprint.

Corpus-level tests build a COMPLETE subject×framing×pressure grid (the exporter enforces
grid completeness), via ``_grid``; the focused reader tests stay minimal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.aggregate import breakdown_mean, cell_scores
from analysis.core_imports import FRAMINGS, PRESSURES
from analysis.export_raw import (
    SCHEMA_VERSION,
    build_catalog,
    build_raw_corpus,
    build_shard,
    iter_tradition_raw,
    read_full_grid_sittings,
    source_fingerprint,
)
from analysis.export_results import (
    build_tradition_export,
    read_run_root,
    resolve_judgments,
)
from analysis.loaders import AnalysisInputError

_TRAD = "buddhism"
_TURNS = [
    {"role": "user", "content": "I want to leave my faith."},
    {"role": "assistant", "content": "Tell me what's behind that."},
]


# ── Fixture builders ────────────────────────────────────────────────────────────────


def _jrow(subject, scenario, pressure, framing, scope, judge, score, ts,
          direction="held the line", rationale=None):
    row = {
        "subject": subject, "tradition": _TRAD, "scenario_id": scenario,
        "pressure": pressure, "framing": framing, "judge": judge,
        "scope": scope, "score": score, "ts": ts, "direction": direction,
    }
    if rationale is not None:
        row["rationale"] = rationale
    return row


def _srow(subject, scenario, pressure, framing, *, turns=None, context_prefix=None):
    # Includes harness-only fields (attempts/usage/ts/model) to prove the reader drops them.
    return {
        "subject": subject, "tradition": _TRAD, "scenario_id": scenario,
        "pressure": pressure, "framing": framing,
        "context_prefix": context_prefix, "model": subject,
        "ts": "2026-08-03T00:00:00Z", "attempts": [1], "usage": {"in": 1, "out": 1},
        "turns": turns if turns is not None else list(_TURNS),
    }


def _report(scenarios, subjects, judges):
    return {"tradition": _TRAD, "subjects": subjects, "judges": judges,
            "by_scenario": {s: {} for s in scenarios}}


def _write_run(root: Path, *, base, sittings=None, v2=None, report=None) -> Path:
    d = root / _TRAD
    d.mkdir(parents=True)
    (d / "judgments.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in base), encoding="utf-8")
    if sittings is not None:
        (d / "sittings.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in sittings), encoding="utf-8")
    if v2:
        (d / "judgments_v2.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in v2), encoding="utf-8")
    if report is not None:
        (d / "report.json").write_text(json.dumps(report), encoding="utf-8")
    return root


def _default_score(su, fr, pr, scope):
    return 1.0 if scope == "turn1" else 0.5


def _default_prefix(su, fr):
    return None if fr == "unstated" else f"[Context for {fr}.]"


def _grid(subjects, *, scenario="BUD-001", judge="gemini-3.6-flash",
          score_fn=_default_score, prefix_fn=_default_prefix, rationale=None):
    """A COMPLETE subject×framing×pressure grid (turn1+full judgments + one sitting/cell)."""
    base, sittings = [], []
    for su in subjects:
        for fr in FRAMINGS:
            for pr in PRESSURES:
                for scope in ("turn1", "full"):
                    base.append(_jrow(su, scenario, pr, fr, scope, judge,
                                      score_fn(su, fr, pr, scope), "t1", rationale=rationale))
                sittings.append(_srow(su, scenario, pr, fr, context_prefix=prefix_fn(su, fr)))
    return base, sittings


def _full_grid(root: Path, *, base, sittings, subjects, judges, scenarios=("BUD-001",)):
    """A full-grid run root (report.json + sittings.jsonl + judgments.jsonl)."""
    return _write_run(root, base=base, sittings=sittings,
                      report=_report(list(scenarios), subjects, judges))


def _grid_root(tmp_path, subjects=("gpt-5.6-terra",), **kw):
    base, sittings = _grid(list(subjects), **kw)
    return _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=list(subjects), judges=["gemini-3.6-flash"])


# ── Sitting reader (minimal, direct) ────────────────────────────────────────────────


def test_sitting_reader_normalizes_subject_and_drops_harness_fields(tmp_path):
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[_srow("openai/gpt-5.6-terra", "BUD-001", "secularize", "unstated")],
        subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    sittings = read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)
    key = ("gpt-5.6-terra", "BUD-001", "secularize", "unstated")  # CANONICAL subject
    assert key in sittings
    s = sittings[key]
    assert s.turns == _TURNS
    assert s.context_prefix is None
    assert all(set(t) == {"role", "content"} for t in s.turns)


def test_sitting_reader_rejects_duplicate_identity(tmp_path):
    dup = _srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[dup, dict(dup)], subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    with pytest.raises(AnalysisInputError, match="duplicate sitting identity"):
        read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)


def test_sitting_reader_rejects_conflicting_context_prefix_same_identity(tmp_path):
    a = _srow("gpt-5.6-terra", "BUD-001", "secularize", "stated", context_prefix="[A]")
    b = _srow("gpt-5.6-terra", "BUD-001", "secularize", "stated", context_prefix="[B]")
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "stated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[a, b], subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    with pytest.raises(AnalysisInputError, match="conflicting context_prefix"):
        read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)


def test_sitting_reader_rejects_unstated_with_prefix(tmp_path):
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[_srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated",
                        context_prefix="[should not be here]")],
        subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    with pytest.raises(AnalysisInputError, match="unstated cell carries a context_prefix"):
        read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)


def test_sitting_reader_rejects_malformed_turns(tmp_path):
    bad = _srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", turns="not a list")
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[bad], subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    with pytest.raises(AnalysisInputError, match="'turns' is not a list"):
        read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)


# ── build_raw_corpus: join, parity, contexts, guards (complete grids) ────────────────


def test_build_raw_corpus_cells_and_verdict_field_parity(tmp_path):
    root = _grid_root(tmp_path, rationale="stayed the course")
    corpus = build_raw_corpus([root])
    export = corpus.per_tradition[_TRAD]
    assert [s.scenario_id for s in export.scenarios] == ["BUD-001"]
    scenario = export.scenarios[0]
    assert len(scenario.cells) == 1 * len(FRAMINGS) * len(PRESSURES)  # complete grid

    unstated = next(c for c in scenario.cells
                    if c["conditions"] == {"framing": "unstated", "pressure": "secularize"})
    assert unstated["subject"] == "gpt-5.6-terra"
    assert unstated["transcript"] == _TURNS
    verdicts = {v["scope"]: v for v in unstated["verdicts"]}
    assert verdicts["turn1"] == {
        "judge": "gemini", "scope": "turn1", "score": 1.0,
        "summary": "held the line", "rationale": "stayed the course",
    }
    assert verdicts["full"] == {
        "judge": "gemini", "scope": "full", "score": 0.5, "summary": "held the line",
        "rationale": "stayed the course",
    }


def test_verdict_summary_always_present_even_without_rationale(tmp_path):
    root = _grid_root(tmp_path)  # no rationale
    corpus = build_raw_corpus([root])
    cell = corpus.per_tradition[_TRAD].scenarios[0].cells[0]
    for v in cell["verdicts"]:
        assert v["summary"] == "held the line"  # summary(=direction) always emitted
        assert "rationale" not in v


def test_verdict_missing_direction_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])
    base[0]["direction"] = ""  # blank direction on one verdict
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="no direction summary"):
        build_raw_corpus([root])


def test_contexts_pool_present_for_stated_absent_for_unstated(tmp_path):
    root = _grid_root(tmp_path)
    corpus = build_raw_corpus([root])
    scenario = corpus.per_tradition[_TRAD].scenarios[0]
    assert scenario.contexts == {"stated": "[Context for stated.]",
                                 "guided": "[Context for guided.]"}
    shard = build_shard(scenario)
    assert shard["schema_version"] == SCHEMA_VERSION
    assert "unstated" not in shard["contexts"]
    by_key = {(c["conditions"]["framing"], c["conditions"]["pressure"]): c for c in shard["cells"]}
    assert by_key[("stated", "secularize")]["contextKey"] == "stated"
    assert "contextKey" not in by_key[("unstated", "secularize")]


def test_incomplete_cell_grid_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])
    sittings = sittings[:-1]  # drop one cell → incomplete grid
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="incomplete cell grid"):
        build_raw_corpus([root])


def test_orphan_verdict_without_transcript_aborts(tmp_path):
    # complete grid for one subject, plus a stray verdict for a subject with no sitting
    base, sittings = _grid(["gpt-5.6-terra"])
    base.append(_jrow("claude-sonnet-5", "BUD-001", "secularize", "unstated", "turn1",
                      "gemini-3.6-flash", 1.0, "t9"))
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="orphan"):
        build_raw_corpus([root])


def test_out_of_universe_sitting_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])
    sittings.append(_srow("gpt-5.6-terra", "BUD-999", "secularize", "unstated"))  # not in report
    root = _write_run(tmp_path / "fg", base=base, sittings=sittings,
                      report=_report(["BUD-001"], ["gpt-5.6-terra"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="outside the report universe"):
        build_raw_corpus([root])


def test_report_scenario_without_sittings_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])  # only BUD-001
    root = _write_run(
        tmp_path / "fg", base=base, sittings=sittings,
        report=_report(["BUD-001", "BUD-002"], ["gpt-5.6-terra"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="have no full-grid sittings"):
        build_raw_corpus([root])


def test_conflicting_context_prefix_across_cells_aborts(tmp_path):
    # two subjects, same stated framing, DIFFERENT prefix → the framing-keyed pool is ambiguous
    def prefix_fn(su, fr):
        if fr == "unstated":
            return None
        if fr == "stated":
            return "[A]" if su == "gpt-5.6-terra" else "[B]"
        return f"[ctx {fr}]"
    base, sittings = _grid(["gpt-5.6-terra", "claude-sonnet-5"], prefix_fn=prefix_fn)
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra", "claude-sonnet-5"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="conflicting context_prefix for framing"):
        build_raw_corpus([root])


def test_verdicts_join_across_roots_by_normalized_subject_and_full_grid_transcript(tmp_path):
    """An Opus layer (provider-prefixed spellings, its own sittings) contributes verdicts;
    transcripts still come from the full-grid run, joined by normalized subject."""
    base, sittings = _grid(["claude-sonnet-5"])
    fg = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                    subjects=["claude-sonnet-5"], judges=["gemini-3.6-flash"])
    # Opus root: provider-prefixed subject + Opus judge alias, one cell; its own (ignored) sitting
    opus = _write_run(
        tmp_path / "opus",
        base=[_jrow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated", "turn1",
                    "anthropic/claude-opus-4.8", -1.0, "t9", direction="drifted")],
        sittings=[_srow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated",
                        turns=[{"role": "user", "content": "WRONG"},
                               {"role": "assistant", "content": "WRONG"}])],
    )
    corpus = build_raw_corpus([fg, opus])
    cell = next(c for c in corpus.per_tradition[_TRAD].scenarios[0].cells
                if c["conditions"] == {"framing": "unstated", "pressure": "secularize"})
    assert cell["subject"] == "claude-sonnet-5"
    assert cell["transcript"] == _TURNS  # from the full-grid run, NOT the opus sitting
    assert {v["judge"] for v in cell["verdicts"]} == {"gemini", "opus"}


def test_ambiguous_two_full_grid_roots_aborts(tmp_path):
    a = _grid_root(tmp_path / "wrap_a")
    # move to a distinct dir so both roots exist
    b_base, b_sit = _grid(["gpt-5.6-terra"])
    b = _full_grid(tmp_path / "b", base=b_base, sittings=b_sit,
                   subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="ambiguous transcript source"):
        build_raw_corpus([a, b])


# ── Streaming generator ─────────────────────────────────────────────────────────────


def test_iter_tradition_raw_yields_per_tradition(tmp_path):
    root = _grid_root(tmp_path)
    yielded = list(iter_tradition_raw([root]))
    assert [t for t, _e, _r in yielded] == [_TRAD]
    _t, export, resolved = yielded[0]
    assert export.scenarios[0].scenario_id == "BUD-001"
    assert resolved and all(r["judge"] == "gemini-3.6-flash" for r in resolved)


# ── Catalog (generic) ───────────────────────────────────────────────────────────────


def test_catalog_is_generic_and_declares_scale_ramp_axes_items(tmp_path):
    root = _grid_root(tmp_path)
    cat = build_catalog(build_raw_corpus([root]))
    assert cat["schema_version"] == SCHEMA_VERSION
    assert cat["dataset"]["license"] == "CC-BY-4.0"
    assert cat["scale"] == {"min": -1.0, "center": 0.0, "max": 1.0}
    assert cat["ramp"][0].startswith("#") and len(cat["ramp"]) == 7  # scoreColor stops, no labels
    assert cat["subjects"] == [{"id": "gpt-5.6-terra", "label": "gpt-5.6-terra"}]
    assert {a["key"] for a in cat["conditionAxes"]} == {"framing", "pressure"}
    assert cat["judges"] == [{"key": "gemini", "label": "gemini", "fullGrid": True}]
    assert cat["items"] == [{
        "id": "BUD-001", "label": "BUD-001", "group": "buddhism",
        "shard": "buddhism/BUD-001.json.gz",
    }]
    assert all(isinstance(x, str) for x in cat["ramp"])  # numeric scale, no band labels


# ── Agreement with the score tier + field allowlist ─────────────────────────────────


def _gemini_rows_from_shards(scenarios):
    """Reconstruct cell_scores-ready rows from the SHIPPED shard verdicts (not the input)."""
    rows = []
    for scenario in scenarios:
        shard = build_shard(scenario)
        for c in shard["cells"]:
            for v in c["verdicts"]:
                if v["judge"] == "gemini":
                    rows.append({
                        "subject": c["subject"], "scenario_id": scenario.scenario_id,
                        "pressure": c["conditions"]["pressure"],
                        "framing": c["conditions"]["framing"],
                        "scope": v["scope"], "score": v["score"],
                    })
    return rows


def test_raw_shard_verdicts_reconcile_with_score_tier_aggregate(tmp_path):
    """Spec Test 2: score-tier slices recomputed from the SHIPPED SHARD verdicts equal the #49
    export's slices — so a `_build_scenario` regression (dropped/altered verdict) is caught,
    not just the input stream. (Score varies by scope so the means are non-trivial.)"""
    root = _grid_root(tmp_path, score_fn=lambda su, fr, pr, scope: 1.0 if scope == "turn1" else 0.0)
    corpus = build_raw_corpus([root])
    te = build_tradition_export(_TRAD, [read_run_root(root)[_TRAD]])
    cs = cell_scores(_gemini_rows_from_shards(corpus.per_tradition[_TRAD].scenarios))

    for scope, expected in (("turn1", 1.0), ("full", 0.0)):
        per_pressure = breakdown_mean(cs, "gpt-5.6-terra", framing="unstated", scope=scope,
                                      pressure="secularize")
        pooled = breakdown_mean(cs, "gpt-5.6-terra", framing="unstated", scope=scope, pressure=None)
        assert per_pressure == te.means[
            ("gemini-3.6-flash", "gpt-5.6-terra", "unstated", scope, "secularize")].mean == expected
        assert pooled == te.means[
            ("gemini-3.6-flash", "gpt-5.6-terra", "unstated", scope, "all")].mean == expected


def _all_keys(obj, acc):
    if isinstance(obj, dict):
        acc.update(obj.keys())
        for v in obj.values():
            _all_keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _all_keys(v, acc)
    return acc


def test_field_allowlist_no_disallowed_keys_in_shards_or_catalog(tmp_path):
    """Spec Test 8: harness-only fields never leave the exporter."""
    corpus = build_raw_corpus([_grid_root(tmp_path)])
    scenario = corpus.per_tradition[_TRAD].scenarios[0]
    shard = build_shard(scenario)
    catalog = build_catalog(corpus)
    disallowed = {"usage", "raw", "attempts", "ts", "sitting_key", "model", "context_prefix"}
    assert not (_all_keys(shard, set()) & disallowed)
    assert not (_all_keys(catalog, set()) & disallowed)
    for cell in shard["cells"]:
        assert set(cell) <= {"subject", "conditions", "transcript", "verdicts", "contextKey"}
        assert set(cell["conditions"]) == {"framing", "pressure"}
        for turn in cell["transcript"]:
            assert set(turn) == {"role", "content"}
        for v in cell["verdicts"]:
            assert set(v) <= {"judge", "scope", "score", "summary", "rationale"}


# ── Additional guards + determinism ─────────────────────────────────────────────────


def test_no_report_bearing_root_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])
    root = _write_run(tmp_path / "noreport", base=base, sittings=sittings)  # no report.json
    with pytest.raises(AnalysisInputError, match="no run root provides report.json"):
        build_raw_corpus([root])


def test_missing_sittings_file_aborts(tmp_path):
    base, _sit = _grid(["gpt-5.6-terra"])
    root = _write_run(tmp_path / "nosit", base=base,
                      report=_report(["BUD-001"], ["gpt-5.6-terra"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="expected sittings file not found"):
        build_raw_corpus([root])


def test_unmapped_sitting_subject_aborts(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra"])
    sittings.append(_srow("acme/unknown-model", "BUD-001", "secularize", "unstated"))
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="unmapped subject id"):
        build_raw_corpus([root])


def test_export_deterministic_over_shuffled_input(tmp_path):
    base, sittings = _grid(["gpt-5.6-terra", "claude-sonnet-5"])
    subjects, judges = ["gpt-5.6-terra", "claude-sonnet-5"], ["gemini-3.6-flash"]
    a = _full_grid(tmp_path / "a", base=base, sittings=sittings, subjects=subjects, judges=judges)
    # same rows, reversed order → the canonical sort must make the output byte-identical
    b = _full_grid(tmp_path / "b", base=list(reversed(base)), sittings=list(reversed(sittings)),
                   subjects=subjects, judges=judges)
    ca, cb = build_raw_corpus([a]), build_raw_corpus([b])
    sa = [build_shard(s) for s in ca.per_tradition[_TRAD].scenarios]
    sb = [build_shard(s) for s in cb.per_tradition[_TRAD].scenarios]
    assert sa == sb
    assert build_catalog(ca) == build_catalog(cb)
    assert source_fingerprint(ca.resolved) == source_fingerprint(cb.resolved)


# ── Fingerprint ─────────────────────────────────────────────────────────────────────


def test_fingerprint_deterministic_order_independent(tmp_path):
    corpus = build_raw_corpus([_grid_root(tmp_path)])
    fp1 = source_fingerprint(corpus.resolved)
    fp2 = source_fingerprint(list(reversed(corpus.resolved)))
    assert fp1 == fp2 and fp1.startswith("sha256:")


def test_fingerprint_matches_resolved_stream_and_changes_on_edit(tmp_path):
    root = _grid_root(tmp_path)
    corpus = build_raw_corpus([root])
    raws = [read_run_root(root)[_TRAD]]
    assert source_fingerprint(corpus.resolved) == source_fingerprint(resolve_judgments(raws))
    mutated = [dict(r) for r in corpus.resolved]
    mutated[0]["score"] = mutated[0]["score"] - 0.5
    assert source_fingerprint(mutated) != source_fingerprint(corpus.resolved)
