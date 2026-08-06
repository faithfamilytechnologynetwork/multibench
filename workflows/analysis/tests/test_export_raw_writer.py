"""Tests for the raw-results deterministic writer + CLI (#51, Phase 2).

Covers byte-identical re-export, the size ceilings (per-shard + per-run, validate-before-
write), the multi-segment safe-path guards, `--limit` fixtures, stale-file pruning, the
cross-tier **fingerprint equality** (raw vs #49 score tier), and the `export-raw` CLI.
Reuses the complete-grid fixture helpers from ``test_export_raw``.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from analysis import export_raw
from analysis.export_raw import (
    MAX_SHARD_BYTES,
    MAX_TOTAL_BYTES,
    _require_safe_relpath,
    _require_safe_segment,
    write_dataset,
)
from analysis.export_results import CANONICAL_SUBJECTS, export_dataset
from analysis.loaders import AnalysisInputError
from tests.test_export_raw import _TRAD, _grid, _grid_root, _full_grid

runner = CliRunner()


def _read_manifest(run_dir: Path) -> dict:
    return json.loads((run_dir / "manifest.json").read_text())


# ── Writer: layout, determinism, gunzip ─────────────────────────────────────────────


def test_write_dataset_layout_and_gunzip(tmp_path):
    root = _grid_root(tmp_path)
    summary = write_dataset([root], tmp_path / "out", "run1")
    run_dir = tmp_path / "out" / "run1"
    assert (run_dir / "manifest.json").is_file()
    shard = run_dir / "buddhism" / "BUD-001.json.gz"
    assert shard.is_file()
    assert summary.scenarios == 1

    manifest = _read_manifest(run_dir)
    assert manifest["schema_version"] == 1
    assert manifest["fingerprint"].startswith("sha256:")
    assert manifest["items"] == [{
        "id": "BUD-001", "label": "BUD-001", "group": "buddhism",
        "shard": "buddhism/BUD-001.json.gz",
    }]
    # the gz shard decompresses to a valid, schema-versioned doc with cells
    doc = json.loads(gzip.decompress(shard.read_bytes()))
    assert doc["schema_version"] == 1
    assert len(doc["cells"]) == 1 * 3 * 6


def test_write_dataset_byte_identical_reexport(tmp_path):
    root = _grid_root(tmp_path, subjects=("gpt-5.6-terra", "claude-sonnet-5"))
    write_dataset([root], tmp_path / "a", "run1")
    write_dataset([root], tmp_path / "b", "run1")
    a_files = sorted(p.relative_to(tmp_path / "a").as_posix()
                     for p in (tmp_path / "a").rglob("*") if p.is_file())
    b_files = sorted(p.relative_to(tmp_path / "b").as_posix()
                     for p in (tmp_path / "b").rglob("*") if p.is_file())
    assert a_files == b_files
    for rel in a_files:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()


# ── Size ceilings (validate-before-write) ───────────────────────────────────────────


def test_per_shard_ceiling_aborts_before_write(tmp_path, monkeypatch):
    root = _grid_root(tmp_path)
    monkeypatch.setattr(export_raw, "MAX_SHARD_BYTES", 10)  # absurdly small
    with pytest.raises(AnalysisInputError, match="per-shard ceiling"):
        write_dataset([root], tmp_path / "out", "run1")
    assert not (tmp_path / "out" / "run1").exists()  # no partial tier


def test_per_run_ceiling_aborts_before_write(tmp_path, monkeypatch):
    root = _grid_root(tmp_path)
    monkeypatch.setattr(export_raw, "MAX_TOTAL_BYTES", 5)
    with pytest.raises(AnalysisInputError, match="ceiling"):
        write_dataset([root], tmp_path / "out", "run1")
    assert not (tmp_path / "out" / "run1").exists()


# ── Safe-path guards ────────────────────────────────────────────────────────────────


def test_safe_segment_and_relpath_guards():
    with pytest.raises(AnalysisInputError):
        _require_safe_segment("../evil", "run-id")
    with pytest.raises(AnalysisInputError):
        _require_safe_segment("a/b", "tradition")
    with pytest.raises(AnalysisInputError):
        _require_safe_relpath("../x/y.json.gz")
    with pytest.raises(AnalysisInputError):
        _require_safe_relpath("buddhism/BUD-001.json")  # wrong extension
    # EVERY component is validated — an intermediate traversal must be rejected
    with pytest.raises(AnalysisInputError):
        _require_safe_relpath("good/../../evil.json.gz")
    with pytest.raises(AnalysisInputError):
        _require_safe_relpath("a/../b/c.json.gz")
    _require_safe_relpath("buddhism/BUD-001.json.gz")  # ok


def test_empty_run_root_aborts(tmp_path):
    """An existing-but-empty run root fails loudly (a mis-mounted layer must not be skipped)."""
    fg = _grid_root(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AnalysisInputError, match="no tradition subdirs"):
        write_dataset([fg, empty], tmp_path / "out", "run1")


def test_summary_reports_uncompressed_and_ratio(tmp_path):
    summary = write_dataset([_grid_root(tmp_path)], tmp_path / "out", "run1")
    assert summary.shard_uncompressed_bytes > summary.shard_bytes  # gzip shrinks it
    assert summary.compression_ratio > 1.0


def test_unsafe_run_id_aborts(tmp_path):
    root = _grid_root(tmp_path)
    with pytest.raises(AnalysisInputError, match="unsafe run-id"):
        write_dataset([root], tmp_path / "out", "../escape")


# ── --limit + pruning ───────────────────────────────────────────────────────────────


def test_limit_writes_subset(tmp_path):
    base, sittings = [], []
    for sc in ("BUD-001", "BUD-002", "BUD-003"):
        b, s = _grid(["gpt-5.6-terra"], scenario=sc)
        base += b
        sittings += s
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
                      scenarios=("BUD-001", "BUD-002", "BUD-003"))
    summary = write_dataset([root], tmp_path / "out" / "lim", "run1", limit=2)
    assert summary.scenarios == 2
    items = _read_manifest(tmp_path / "out" / "lim" / "run1")["items"]
    assert [it["id"] for it in items] == ["BUD-001", "BUD-002"]

    # the limited fingerprint covers ONLY the written subset: it equals a full export of a
    # fixture containing just those two scenarios, and differs from the full 3-scenario export.
    b2, s2 = [], []
    for sc in ("BUD-001", "BUD-002"):
        b, s = _grid(["gpt-5.6-terra"], scenario=sc)
        b2 += b
        s2 += s
    subset_root = _full_grid(tmp_path / "subset", base=b2, sittings=s2,
                             subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
                             scenarios=("BUD-001", "BUD-002"))
    write_dataset([subset_root], tmp_path / "out" / "sub", "run1")
    write_dataset([root], tmp_path / "out" / "full", "run1")
    lim_fp = _read_manifest(tmp_path / "out" / "lim" / "run1")["fingerprint"]
    sub_fp = _read_manifest(tmp_path / "out" / "sub" / "run1")["fingerprint"]
    full_fp = _read_manifest(tmp_path / "out" / "full" / "run1")["fingerprint"]
    assert lim_fp == sub_fp != full_fp


def test_reexport_prunes_stale_shards(tmp_path):
    base, sittings = [], []
    for sc in ("BUD-001", "BUD-002"):
        b, s = _grid(["gpt-5.6-terra"], scenario=sc)
        base += b
        sittings += s
    root = _full_grid(tmp_path / "fg", base=base, sittings=sittings,
                      subjects=["gpt-5.6-terra"], judges=["gemini-3.6-flash"],
                      scenarios=("BUD-001", "BUD-002"))
    write_dataset([root], tmp_path / "out", "run1")  # both scenarios
    assert (tmp_path / "out" / "run1" / "buddhism" / "BUD-002.json.gz").is_file()
    write_dataset([root], tmp_path / "out", "run1", limit=1)  # now only BUD-001
    assert (tmp_path / "out" / "run1" / "buddhism" / "BUD-001.json.gz").is_file()
    assert not (tmp_path / "out" / "run1" / "buddhism" / "BUD-002.json.gz").is_file()


# ── Cross-tier fingerprint equality ─────────────────────────────────────────────────


def test_raw_and_score_manifests_share_fingerprint(tmp_path):
    """The raw tier and the #49 score tier stamp an equal fingerprint for the same run — the
    checkable form of 'cannot disagree'. Uses all canonical subjects so the score tier's
    full-grid assertion passes."""
    root = _grid_root(tmp_path, subjects=tuple(CANONICAL_SUBJECTS))
    write_dataset([root], tmp_path / "raw", "run1")
    export_dataset([root], str(tmp_path / "scores"), "run1", "2026-01-01T00:00:00Z")
    raw_fp = _read_manifest(tmp_path / "raw" / "run1")["fingerprint"]
    score_fp = _read_manifest(tmp_path / "scores" / "run1")["fingerprint"]
    assert raw_fp == score_fp and raw_fp.startswith("sha256:")


def test_raw_and_score_fingerprint_match_with_opus_layer(tmp_path):
    """Cross-tier fingerprint equality across DIFFERENT read paths + multiple roots: a full-grid
    run plus an Opus verdict layer. Both tiers resolve the same rows → equal fingerprints."""
    from tests.test_export_raw import _jrow, _write_run
    fg = _grid_root(tmp_path, subjects=tuple(CANONICAL_SUBJECTS))
    opus = _write_run(
        tmp_path / "opus",
        base=[_jrow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated", "turn1",
                    "anthropic/claude-opus-4.8", -0.5, "t9", direction="drifted"),
              _jrow("anthropic/claude-sonnet-5", "BUD-001", "secularize", "unstated", "full",
                    "anthropic/claude-opus-4.8", -1.0, "t9", direction="drifted more")],
    )
    write_dataset([fg, opus], tmp_path / "raw", "run1")
    export_dataset([fg, opus], str(tmp_path / "scores"), "run1", "2026-01-01T00:00:00Z")
    assert (_read_manifest(tmp_path / "raw" / "run1")["fingerprint"]
            == _read_manifest(tmp_path / "scores" / "run1")["fingerprint"])


def test_score_manifest_fingerprint_is_deterministic_no_wallclock_dependence(tmp_path):
    """The score-tier fingerprint depends only on the data, not on generated_at."""
    root = _grid_root(tmp_path, subjects=tuple(CANONICAL_SUBJECTS))
    export_dataset([root], str(tmp_path / "s1"), "run1", "2026-01-01T00:00:00Z")
    export_dataset([root], str(tmp_path / "s2"), "run1", "2027-12-31T23:59:59Z")
    assert (_read_manifest(tmp_path / "s1" / "run1")["fingerprint"]
            == _read_manifest(tmp_path / "s2" / "run1")["fingerprint"])


# ── CLI ─────────────────────────────────────────────────────────────────────────────


def test_export_raw_cli_help_lists_flags():
    from analysis.cli import app
    result = runner.invoke(app, ["export-raw", "--help"])
    assert result.exit_code == 0
    for flag in ("--run-id", "--out", "--limit"):
        assert flag in result.output


def test_export_raw_cli_runs(tmp_path):
    from analysis.cli import app
    root = _grid_root(tmp_path)
    result = runner.invoke(app, ["export-raw", str(root), "--run-id", "run1",
                                 "--out", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["run_id"] == "run1" and payload["scenarios"] == 1
    assert (tmp_path / "out" / "run1" / "manifest.json").is_file()
