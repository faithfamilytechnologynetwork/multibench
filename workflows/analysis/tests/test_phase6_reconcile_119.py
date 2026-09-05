"""Phase 6 reconciliation (Spec 119) — the committed score tier ranks protestant-unified 5th.

Reads ONLY the committed ``results/20260905/`` shards (no ``tmp/`` run roots), so it is fast and
CI-safe; skips cleanly when the dataset is absent. It asserts two things about the #120/#121
two-judge ``mean_of_judges`` leaderboard:

1. Per tradition, the ranking mean-of-means computed from the shard's ``combined`` block equals an
   **independent recompute** from the per-judge ``means`` block — on every full-grid (symmetric-
   coverage) slice, ``combined = equal-weight mean of the two judges`` — validating that the ranked
   score really is the mean of Gemini + Opus, not a re-labelled single judge.
2. Ranking all 8 traditions by that score puts **protestant-unified at rank 5**.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from analysis.export_results import CANONICAL_SUBJECTS, FRAMINGS

_REPO = Path(__file__).resolve().parents[3]
_RESULTS = _REPO / "results" / "20260905"
_EXPERIMENT = _REPO / "experiments" / "119_protestant_unified"
_ANALYZE = _EXPERIMENT / "analyze.py"
_PAPER_NUMBERS = _EXPERIMENT / "data" / "output" / "paper_numbers.json"
_FULL = "full"
_ALL = "all"
_GEMINI = "gemini-3.6-flash"
_OPUS = "claude-opus-4-8"
_TOL = 1e-9


def _shards() -> dict[str, dict]:
    manifest = json.loads((_RESULTS / "manifest.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for t in manifest["traditions"]:
        out[t["id"]] = json.loads((_RESULTS / t["shard"]).read_text(encoding="utf-8"))
    return out


def _combined_full_all(shard: dict, subject: str, framing: str):
    return shard["combined"].get(subject, {}).get(framing, {}).get(_FULL, {}).get(_ALL)


def _judge_full_all(shard: dict, judge: str, subject: str, framing: str):
    return (
        shard["means"].get(judge, {}).get(subject, {}).get(framing, {}).get(_FULL, {}).get(_ALL)
    )


def _ranking_from_combined(shard: dict) -> float:
    vals = [
        cell[0]
        for s in CANONICAL_SUBJECTS
        for fr in FRAMINGS
        if (cell := _combined_full_all(shard, s, fr)) is not None
    ]
    assert vals, f"{shard['tradition']}: no combined full/all slices"
    return sum(vals) / len(vals)


pytestmark = pytest.mark.skipif(
    not (_RESULTS / "manifest.json").is_file(),
    reason=f"committed results dataset absent at {_RESULTS}",
)


def test_combined_is_mean_of_two_judges_on_symmetric_slices() -> None:
    """On every full-grid slice both judges cover equally, combined == mean(Gemini, Opus)."""
    checked = 0
    for tradition, shard in _shards().items():
        for s in CANONICAL_SUBJECTS:
            for fr in FRAMINGS:
                comb = _combined_full_all(shard, s, fr)
                gem = _judge_full_all(shard, _GEMINI, s, fr)
                opus = _judge_full_all(shard, _OPUS, s, fr)
                if comb is None or gem is None or opus is None:
                    continue
                # symmetric coverage: both judges scored the same cells as the combined block
                if not (gem[1] == opus[1] == comb[1]):
                    continue
                independent = 0.5 * (gem[0] + opus[0])
                assert abs(independent - comb[0]) <= _TOL, (
                    f"{tradition} {s}|{fr}: combined {comb[0]!r} != mean(Gemini,Opus) "
                    f"{independent!r}"
                )
                checked += 1
    assert checked > 0, "no symmetric slices were checked — dataset shape changed?"


def test_protestant_unified_ranks_fifth_of_eight() -> None:
    shards = _shards()
    assert "protestant-unified" in shards, "protestant-unified shard missing from the dataset"
    ranking = {t: _ranking_from_combined(sh) for t, sh in shards.items()}
    assert len(ranking) == 8, f"expected 8 traditions, got {sorted(ranking)}"

    ranked = sorted(ranking, key=lambda t: ranking[t], reverse=True)
    rank = ranked.index("protestant-unified") + 1
    assert rank == 5, (
        f"protestant-unified ranked {rank}, expected 5; order="
        + ", ".join(f"{t}={ranking[t]:+.4f}" for t in ranked)
    )


@pytest.mark.skipif(not _PAPER_NUMBERS.is_file(), reason="committed paper_numbers.json absent")
def test_committed_paper_numbers_matches_shards() -> None:
    """The committed ``paper_numbers.json`` (Phase 6 generated artifact) is not stale: its
    ``ranked_table`` points and rank order equal an independent recompute from the committed
    ``results/20260905/`` shards (≤1e-9). Guards against a hand-edited or out-of-date artifact
    passing CI while the dataset moved underneath it."""
    shards = _shards()
    recompute = {t: _ranking_from_combined(sh) for t, sh in shards.items()}
    expected = [t for t in sorted(recompute, key=lambda t: recompute[t], reverse=True)]

    paper = json.loads(_PAPER_NUMBERS.read_text(encoding="utf-8"))
    table = paper["ranked_table"]
    assert [row["tradition"] for row in table] == expected, (
        "paper_numbers.json ranked order != recompute from shards"
    )
    for i, row in enumerate(table, start=1):
        assert row["rank"] == i, f"rank field {row['rank']} != position {i} for {row['tradition']}"
        got = row["ranking_mean_of_means"]
        want = recompute[row["tradition"]]
        assert abs(got - want) <= _TOL, (
            f"{row['tradition']}: paper_numbers {got!r} != shard recompute {want!r}"
        )
        # each row also carries a CI bracketing the point
        assert row["ci_lo"] <= got <= row["ci_hi"], (
            f"{row['tradition']}: point {got!r} not within CI [{row['ci_lo']}, {row['ci_hi']}]"
        )


@pytest.mark.skipif(not _ANALYZE.is_file(), reason="analyze.py absent")
def test_analyze_smoke_imports_and_default_roots_are_repo_root_relative() -> None:
    """Smoke: `analyze.py` imports cleanly (no side effects at import) and its default roots resolve
    from ``__file__`` to the repo root — absolute paths under ``<repo>/tmp/judging-runs/`` — so a bare
    run reproduces from any CWD on the checkout it lives in (not tied to a worktree ``../../`` prefix
    or a repo-root CWD). Also checks the 5 expected run dirs, the results-dir default, the portable
    meta helper, and that the Typer CLI is constructed. Needs no ``tmp/`` roots."""
    spec = importlib.util.spec_from_file_location("pu_analyze_smoke", _ANALYZE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # executes module body; `if __name__ == "__main__"` guard = no run

    repo_root = mod._REPO_ROOT
    assert repo_root == _REPO, (repo_root, _REPO)  # parents[2] really is the repo root

    roots = mod.DEFAULT_ROOTS
    assert len(roots) == 5, roots
    for r in roots:
        rp = Path(r)
        assert rp.is_absolute(), r  # __file__-resolved, not CWD-relative
        assert rp.parent == repo_root / "tmp" / "judging-runs", r
    assert [Path(r).name for r in roots] == [
        "20260803-merged",
        "20260803-unstated-opus",
        "20260803-framings-opus-sample",
        "20260823-opus-fullgrid",
        "20260904-protestant-unified",
    ], roots
    assert Path(mod.DEFAULT_RESULTS_DIR) == repo_root / "results" / "20260905"
    # the committed-artifact path form is portable (repo-relative), whatever root was passed
    assert mod._portable_root("/anywhere/../../tmp/judging-runs/20260904-protestant-unified") == \
        "tmp/judging-runs/20260904-protestant-unified"

    import typer

    assert isinstance(mod.app, typer.Typer)
