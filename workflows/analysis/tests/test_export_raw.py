"""Tests for the raw-results export core (#51, Phase 1) — the pure transform.

Deterministic unit/integration tests over tiny synthetic run roots in ``tmp_path`` (no
dependence on the git-ignored ``tmp/judging-runs/`` symlink). They cover the new sitting
reader (normalization, dedup, conflicting-prefix), the transcript↔verdict join (field
parity, orphan abort, out-of-universe abort, normalized-subject join, full-grid-only
transcript source), the per-shard contexts pool, the generic catalog, and the shared
source fingerprint (determinism + sensitivity + matching the resolved stream).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.aggregate import breakdown_mean, cell_scores
from analysis.export_raw import (
    SCHEMA_VERSION,
    build_catalog,
    build_raw_corpus,
    build_shard,
    read_full_grid_sittings,
    source_fingerprint,
)
from analysis.export_results import (
    JUDGE_UI,
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
          direction=None, rationale=None):
    row = {
        "subject": subject, "tradition": _TRAD, "scenario_id": scenario,
        "pressure": pressure, "framing": framing, "judge": judge,
        "scope": scope, "score": score, "ts": ts,
    }
    if direction is not None:
        row["direction"] = direction
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


def _full_grid(root: Path, *, base, sittings, subjects, judges, scenarios=("BUD-001",)):
    """A full-grid run root (report.json + sittings.jsonl + judgments.jsonl)."""
    return _write_run(root, base=base, sittings=sittings,
                      report=_report(list(scenarios), subjects, judges))


# ── Sitting reader ──────────────────────────────────────────────────────────────────


def test_sitting_reader_normalizes_subject_and_drops_harness_fields(tmp_path):
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[_srow("openai/gpt-5.6-terra", "BUD-001", "secularize", "unstated")],
        subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    sittings = read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)
    # keyed by the CANONICAL subject even though the source used the provider-prefixed id
    key = ("gpt-5.6-terra", "BUD-001", "secularize", "unstated")
    assert key in sittings
    s = sittings[key]
    assert s.turns == _TURNS
    assert s.context_prefix is None  # unstated → no prefix
    # only role/content survive on turns
    assert all(set(t) == {"role", "content"} for t in s.turns)


def test_sitting_reader_rejects_duplicate_identity(tmp_path):
    dup = _srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")
    root = _full_grid(
        tmp_path / "fg",
        base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[dup, dict(dup)],
        subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
    )
    with pytest.raises(AnalysisInputError, match="duplicate sitting identity"):
        read_full_grid_sittings(root / _TRAD / "sittings.jsonl", _TRAD)


def test_sitting_reader_rejects_conflicting_context_prefix(tmp_path):
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


# ── build_raw_corpus: join, parity, contexts, guards ────────────────────────────────


def _one_cell_corpus(tmp_path):
    """A minimal full-grid corpus: 1 scenario, 1 subject, unstated+stated, gemini, both scopes."""
    base = [
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
              "gemini-3.6-flash", 1.0, "t1", direction="held", rationale="stayed the course"),
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "full",
              "gemini-3.6-flash", 0.5, "t2", direction="wavered"),
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "stated", "turn1",
              "gemini-3.6-flash", 1.0, "t3"),
    ]
    sittings = [
        _srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated"),
        _srow("gpt-5.6-terra", "BUD-001", "secularize", "stated",
              context_prefix="[Context: talking with a practising Buddhist.]"),
    ]
    return _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])


def test_build_raw_corpus_cells_and_verdict_field_parity(tmp_path):
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    export = corpus.per_tradition[_TRAD]
    assert [s.scenario_id for s in export.scenarios] == ["BUD-001"]
    cells = {(c["subject"], c["conditions"]["framing"]): c for c in export.scenarios[0].cells}

    unstated = cells[("gpt-5.6-terra", "unstated")]
    assert unstated["transcript"] == _TURNS
    # two verdicts (turn1, full), sorted; fields match the resolved judgment (allowlisted)
    verdicts = {v["scope"]: v for v in unstated["verdicts"]}
    assert verdicts["turn1"] == {
        "judge": "gemini", "scope": "turn1", "score": 1.0,
        "summary": "held", "rationale": "stayed the course",
    }
    assert verdicts["full"] == {
        "judge": "gemini", "scope": "full", "score": 0.5, "summary": "wavered",
    }  # rationale omitted when absent


def test_contexts_pool_present_for_stated_absent_for_unstated(tmp_path):
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    scenario = corpus.per_tradition[_TRAD].scenarios[0]
    assert scenario.contexts == {"stated": "[Context: talking with a practising Buddhist.]"}
    shard = build_shard(scenario)
    assert shard["schema_version"] == SCHEMA_VERSION
    assert shard["contexts"]["stated"].startswith("[Context")
    assert "unstated" not in shard["contexts"]
    # the stated cell carries an explicit contextKey into the pool; the unstated cell doesn't
    by_framing = {c["conditions"]["framing"]: c for c in shard["cells"]}
    assert by_framing["stated"]["contextKey"] == "stated"
    assert "contextKey" not in by_framing["unstated"]


def test_conflicting_context_prefix_across_cells_aborts(tmp_path):
    # two subjects, same (scenario, stated framing), DIFFERENT prefix → pool is ambiguous
    base = [
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "stated", "turn1",
              "gemini-3.6-flash", 1.0, "t1"),
        _jrow("claude-sonnet-5", "BUD-001", "secularize", "stated", "turn1",
              "gemini-3.6-flash", 1.0, "t2"),
    ]
    sittings = [
        _srow("gpt-5.6-terra", "BUD-001", "secularize", "stated", context_prefix="[A]"),
        _srow("claude-sonnet-5", "BUD-001", "secularize", "stated", context_prefix="[B]"),
    ]
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra", "claude-sonnet-5"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="conflicting context_prefix for framing"):
        build_raw_corpus([root])


def test_report_scenario_without_sittings_aborts(tmp_path):
    # report lists BUD-001 and BUD-002 but only BUD-001 has sittings → partial full-grid run
    base = [_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                  "gemini-3.6-flash", 1.0, "t1")]
    sittings = [_srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")]
    root = _write_run(
        tmp_path / "fg", base=base, sittings=sittings,
        report=_report(["BUD-001", "BUD-002"], ["gpt-5.6-terra"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="have no full-grid sittings"):
        build_raw_corpus([root])


def test_orphan_verdict_without_transcript_aborts(tmp_path):
    # a judgment for a (guided) cell with no matching sitting
    base = [
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
              "gemini-3.6-flash", 1.0, "t1"),
        _jrow("gpt-5.6-terra", "BUD-001", "secularize", "guided", "turn1",
              "gemini-3.6-flash", 1.0, "t2"),
    ]
    sittings = [_srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")]
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="orphan"):
        build_raw_corpus([root])


def test_out_of_universe_sitting_aborts(tmp_path):
    base = [_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                  "gemini-3.6-flash", 1.0, "t1")]
    sittings = [
        _srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated"),
        _srow("gpt-5.6-terra", "BUD-999", "secularize", "unstated"),  # not in the report
    ]
    root = _write_run(tmp_path / "fg", base=base, sittings=sittings,
                      report=_report(["BUD-001"], ["gpt-5.6-terra"], ["gemini-3.6-flash"]))
    with pytest.raises(AnalysisInputError, match="outside the report universe"):
        build_raw_corpus([root])


def test_verdicts_join_across_roots_by_normalized_subject_and_full_grid_transcript(tmp_path):
    """An Opus layer (provider-prefixed spellings, its own sittings) contributes verdicts;
    transcripts still come from the full-grid run, joined by normalized subject."""
    fg = _full_grid(
        tmp_path / "fg",
        base=[_jrow("claude-sonnet-5", "BUD-001", "secularize", "unstated", "turn1",
                    "gemini-3.6-flash", 1.0, "t1")],
        sittings=[_srow("claude-sonnet-5", "BUD-001", "secularize", "unstated")],
        subjects=["claude-sonnet-5"], judges=["gemini-3.6-flash"],
    )
    # Opus root: provider-prefixed subject + Opus judge alias + a DIFFERENT sitting that must
    # be ignored (no report.json → not the full-grid source).
    opus = _write_run(
        tmp_path / "opus",
        base=[_jrow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated", "turn1",
                    "anthropic/claude-opus-4.8", -1.0, "t9", direction="drifted")],
        sittings=[_srow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated",
                        turns=[{"role": "user", "content": "WRONG"},
                               {"role": "assistant", "content": "WRONG"}])],
    )
    corpus = build_raw_corpus([fg, opus])
    cell = corpus.per_tradition[_TRAD].scenarios[0].cells[0]
    assert cell["subject"] == "claude-sonnet-5"
    assert cell["transcript"] == _TURNS  # from the full-grid run, NOT the opus sitting
    judges = {v["judge"] for v in cell["verdicts"]}
    assert judges == {"gemini", "opus"}  # both judges present, opus joined by normalized subject


def test_ambiguous_two_full_grid_roots_aborts(tmp_path):
    a = _full_grid(tmp_path / "a",
                   base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "turn1",
                               "gemini-3.6-flash", 1.0, "t1")],
                   sittings=[_srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")],
                   subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    b = _full_grid(tmp_path / "b",
                   base=[_jrow("gpt-5.6-terra", "BUD-001", "secularize", "unstated", "full",
                               "gemini-3.6-flash", 1.0, "t2")],
                   sittings=[_srow("gpt-5.6-terra", "BUD-001", "secularize", "unstated")],
                   subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"])
    with pytest.raises(AnalysisInputError, match="ambiguous transcript source"):
        build_raw_corpus([a, b])


# ── Catalog (generic) ───────────────────────────────────────────────────────────────


def test_catalog_is_generic_and_declares_scale_ramp_axes_items(tmp_path):
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    cat = build_catalog(corpus)
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
    # generic: no band labels on the ramp; scale is numeric
    assert all(isinstance(x, str) for x in cat["ramp"])


# ── Fingerprint ─────────────────────────────────────────────────────────────────────


# ── Agreement with the score tier + field allowlist ─────────────────────────────────


def test_raw_verdicts_reconcile_with_score_tier_aggregate(tmp_path):
    """Spec Test 2: a score-tier slice recomputed from the raw verdict stream equals the
    #49 export's slice — the raw and score tiers cannot disagree (same resolved stream)."""
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    raws = [read_run_root(root)[_TRAD]]
    te = build_tradition_export(_TRAD, raws)  # the #49 score-tier export

    # recompute the (gemini, gpt-5.6-terra, unstated, full, secularize) slice from raw verdicts
    cs = cell_scores([r for r in corpus.resolved if r["judge"] == "gemini-3.6-flash"])
    recomputed = breakdown_mean(cs, "gpt-5.6-terra", framing="unstated", scope="full",
                                pressure="secularize")
    slice_key = ("gemini-3.6-flash", "gpt-5.6-terra", "unstated", "full", "secularize")
    assert recomputed == te.means[slice_key].mean == 0.5


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
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    scenario = corpus.per_tradition[_TRAD].scenarios[0]
    shard = build_shard(scenario)
    catalog = build_catalog(corpus)
    disallowed = {"usage", "raw", "attempts", "ts", "sitting_key", "model", "context_prefix"}
    assert not (_all_keys(shard, set()) & disallowed)
    assert not (_all_keys(catalog, set()) & disallowed)
    # positive: cell + verdict keys are within the allowed sets
    for cell in shard["cells"]:
        assert set(cell) <= {"subject", "conditions", "transcript", "verdicts", "contextKey"}
        assert set(cell["conditions"]) == {"framing", "pressure"}
        for turn in cell["transcript"]:
            assert set(turn) == {"role", "content"}
        for v in cell["verdicts"]:
            assert set(v) <= {"judge", "scope", "score", "summary", "rationale"}


def test_fingerprint_deterministic_order_independent(tmp_path):
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    fp1 = source_fingerprint(corpus.resolved)
    fp2 = source_fingerprint(list(reversed(corpus.resolved)))
    assert fp1 == fp2 and fp1.startswith("sha256:")


def test_fingerprint_matches_resolved_stream_and_changes_on_edit(tmp_path):
    root = _one_cell_corpus(tmp_path)
    corpus = build_raw_corpus([root])
    # the corpus stream equals resolve_judgments over the same root (one tradition here)
    raws = [read_run_root(root)[_TRAD]]
    assert source_fingerprint(corpus.resolved) == source_fingerprint(resolve_judgments(raws))
    # mutating a score changes the fingerprint
    mutated = [dict(r) for r in corpus.resolved]
    mutated[0]["score"] = mutated[0]["score"] - 0.5
    assert source_fingerprint(mutated) != source_fingerprint(corpus.resolved)
