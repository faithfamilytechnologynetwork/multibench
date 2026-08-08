"""Tests for the extracted generic raw-tier writer (`analysis.raw_writer`, #54 Phase 1).

The writer plumbing (gzip mtime=0, size ceilings validate-before-write, the content
fingerprint over pre-gz shard bytes, stale-file prune) was extracted from `export_raw` so the
AFB tier (#54) reuses it verbatim. These tests pin the primitive directly AND guard that the
extraction did not change the bytes of the real committed `results-raw/20260803` tier:

- `test_content_fingerprint_delegates_to_shard_bytes` — the primitive's `content_fingerprint`
  is exactly `combine_fingerprint` over `content_fingerprint_line(relpath, pre_gz_bytes)`.
- `test_committed_20260803_content_fingerprint_recompute` — recompute that fingerprint from the
  **committed** shards and assert it equals the value baked into the committed manifest. Because
  the primitive computes the content fingerprint via those same two functions, this is a
  byte-level regression guard against the real shipped tier (whose source run-roots are not in
  the repo, so a literal re-export cannot be performed).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from analysis.fingerprint import combine_fingerprint, content_fingerprint_line
from analysis.loaders import AnalysisInputError
from analysis.raw_writer import RawTierWriter, _json_bytes

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMITTED_TIER = REPO_ROOT / "results-raw" / "20260803"


def _shard(item_id: str, cells: list[dict]) -> bytes:
    return _json_bytes({"schema_version": 1, "cells": cells})


def test_content_fingerprint_delegates_to_shard_bytes(tmp_path):
    """The primitive's content fingerprint == combine over content lines of the pre-gz bytes."""
    w = RawTierWriter(tmp_path, "run1", prune=True)
    shards = {
        "afb-150/AFB-001.json.gz": _shard("AFB-001", [{"subject": "a"}]),
        "afb-150/AFB-002.json.gz": _shard("AFB-002", [{"subject": "b"}]),
    }
    for rel, raw in shards.items():
        w.add_shard(rel, raw)
    expected = combine_fingerprint([content_fingerprint_line(rel, raw) for rel, raw in shards.items()])
    assert w.content_fingerprint == expected
    assert w.content_fingerprint.startswith("sha256:")


def test_write_roundtrip_and_byte_identical(tmp_path):
    """write() lays out manifest + gz shards, round-trips, and re-writes byte-identically."""
    def build_and_write(dst: str) -> RawTierWriter:
        w = RawTierWriter(tmp_path / dst, "run1", prune=True)
        w.add_shard("afb-150/AFB-001.json.gz", _shard("AFB-001", [{"subject": "a"}]))
        catalog = {"schema_version": 1, "fingerprint": "sha256:x",
                   "content_fingerprint": w.content_fingerprint, "items": []}
        w.write(catalog)
        return w

    build_and_write("a")
    build_and_write("b")
    a_files = sorted(p.relative_to(tmp_path / "a").as_posix() for p in (tmp_path / "a").rglob("*") if p.is_file())
    assert a_files == ["run1/afb-150/AFB-001.json.gz", "run1/manifest.json"]
    for rel in a_files:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()
    doc = json.loads(gzip.decompress((tmp_path / "a" / "run1" / "afb-150" / "AFB-001.json.gz").read_bytes()))
    assert doc["cells"] == [{"subject": "a"}]


def test_per_shard_ceiling_param_aborts_before_write(tmp_path):
    """The ceiling is a write() parameter (kept patchable at caller scope) — breach → no tier."""
    w = RawTierWriter(tmp_path / "out", "run1", prune=True)
    w.add_shard("afb-150/AFB-001.json.gz", _shard("AFB-001", [{"subject": "a"}]))
    with pytest.raises(AnalysisInputError):
        w.write({"schema_version": 1}, max_shard_bytes=10)
    assert not (tmp_path / "out" / "run1").exists()  # no partial tier


def test_unsafe_shard_path_rejected(tmp_path):
    w = RawTierWriter(tmp_path, "run1", prune=True)
    with pytest.raises(AnalysisInputError):
        w.add_shard("good/../../evil.json.gz", b"{}")
    with pytest.raises(AnalysisInputError):
        w.add_shard("buddhism/BUD-001.json", b"{}")  # wrong extension


@pytest.mark.skipif(not COMMITTED_TIER.is_dir(), reason="committed results-raw/20260803 tier absent")
def test_committed_20260803_content_fingerprint_recompute():
    """Recompute the committed tier's content fingerprint from its shard bytes → must match.

    Real-data byte guard for the Phase-1 extraction: the primitive computes the content
    fingerprint as ``combine_fingerprint`` over ``content_fingerprint_line(shard, pre_gz_bytes)``
    (see :attr:`RawTierWriter.content_fingerprint`); recomputing that over the committed shards
    (gunzipped to their pre-gz bytes) reproduces the value stamped in the committed manifest.
    """
    manifest = json.loads((COMMITTED_TIER / "manifest.json").read_text())
    lines = []
    for item in manifest["items"]:
        rel = item["shard"]  # manifest-declared "<group>/<item>.json.gz"
        pre_gz = gzip.decompress((COMMITTED_TIER / rel).read_bytes())
        lines.append(content_fingerprint_line(rel, pre_gz))
    assert combine_fingerprint(lines) == manifest["content_fingerprint"]
