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
import hashlib
import json
from pathlib import Path

import pytest

from analysis.export_raw import write_dataset
from analysis.fingerprint import combine_fingerprint, content_fingerprint_line
from analysis.loaders import AnalysisInputError
from analysis.raw_writer import RawTierWriter, json_bytes
from tests.test_export_raw import _grid_root

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
COMMITTED_TIER = REPO_ROOT / "results-raw" / "20260803"
GOLDEN = json.loads((HERE / "fixtures" / "raw_writer_golden.json").read_text())


def _shard(cells: list[dict]) -> bytes:
    return json_bytes({"schema_version": 1, "cells": cells})


def test_content_fingerprint_delegates_to_shard_bytes(tmp_path):
    """The primitive's content fingerprint == combine over content lines of the pre-gz bytes."""
    w = RawTierWriter(tmp_path, "run1", prune=True)
    shards = {
        "afb-150/AFB-001.json.gz": _shard([{"subject": "a"}]),
        "afb-150/AFB-002.json.gz": _shard([{"subject": "b"}]),
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
        w.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))
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


def test_full_export_matches_frozen_golden(tmp_path):
    """A full `write_dataset` export of the fixture matches committed golden hashes.

    The frozen regression gate (plan AC1): unlike the self-consistent byte-identical re-export
    test, this pins the WHOLE export — manifest (catalog fields, preset selection/order, item
    membership/order) + every shard — against hashes recorded from the reviewed implementation.
    Hashes are over the **pre-gz** shard bytes + raw manifest bytes, so they are independent of the
    zlib version (gz-byte stability is separately gated by the committed-tier test). Any change to
    catalog construction, presets, ordering, or file membership breaks this.

    Also exercises the extracted primitive end-to-end: a fresh ``RawTierWriter`` over the produced
    shards reproduces the manifest's ``content_fingerprint``.
    """
    root = _grid_root(tmp_path, subjects=("claude-sonnet-5", "gpt-5.6-terra"))  # 2 subjects → presets
    run_dir = tmp_path / "out" / "goldrun"
    write_dataset([root], tmp_path / "out", "goldrun")

    actual = {}
    for p in sorted(run_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(run_dir).as_posix()
        content = gzip.decompress(p.read_bytes()) if rel.endswith(".json.gz") else p.read_bytes()
        actual[rel] = hashlib.sha256(content).hexdigest()
    assert actual == GOLDEN  # full-output freeze: manifest + every shard

    # The primitive reproduces the exported manifest's content fingerprint over the same shards.
    manifest = json.loads((run_dir / "manifest.json").read_text())
    w = RawTierWriter(tmp_path / "verify", "goldrun", prune=False)
    for item in manifest["items"]:
        rel = item["shard"]
        w.add_shard(rel, gzip.decompress((run_dir / rel).read_bytes()))
    assert w.content_fingerprint == manifest["content_fingerprint"]


def test_per_shard_ceiling_param_aborts_before_write(tmp_path):
    """The ceiling is a write() parameter (kept patchable at caller scope) — breach → no tier."""
    w = RawTierWriter(tmp_path / "out", "run1", prune=True)
    w.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))
    with pytest.raises(AnalysisInputError):
        w.write({"schema_version": 1}, max_shard_bytes=10)
    assert not (tmp_path / "out" / "run1").exists()  # no partial tier


def test_per_run_total_ceiling_aborts_before_write(tmp_path):
    w = RawTierWriter(tmp_path / "out", "run1", prune=True)
    w.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))
    with pytest.raises(AnalysisInputError):
        w.write({"schema_version": 1}, max_total_bytes=5)
    assert not (tmp_path / "out" / "run1").exists()


def test_prune_true_removes_stale_false_keeps(tmp_path):
    """prune=True drops files absent from the new set; prune=False is purely additive."""
    for prune, expect_stale in [(True, False), (False, True)]:
        out = tmp_path / f"p{int(prune)}"
        first = RawTierWriter(out, "run1", prune=True)
        first.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))
        first.add_shard("afb-150/AFB-002.json.gz", _shard([{"subject": "b"}]))
        first.write({"schema_version": 1})
        second = RawTierWriter(out, "run1", prune=prune)
        second.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))  # drop AFB-002
        second.write({"schema_version": 1})
        stale = out / "run1" / "afb-150" / "AFB-002.json.gz"
        assert stale.exists() is expect_stale


def test_duplicate_shard_path_rejected(tmp_path):
    w = RawTierWriter(tmp_path, "run1", prune=True)
    w.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "a"}]))
    with pytest.raises(AnalysisInputError):
        w.add_shard("afb-150/AFB-001.json.gz", _shard([{"subject": "b"}]))  # collision


def test_unsafe_shard_path_rejected(tmp_path):
    w = RawTierWriter(tmp_path, "run1", prune=True)
    with pytest.raises(AnalysisInputError):
        w.add_shard("good/../../evil.json.gz", b"{}")
    with pytest.raises(AnalysisInputError):
        w.add_shard("buddhism/BUD-001.json", b"{}")  # wrong extension


@pytest.mark.skipif(not COMMITTED_TIER.is_dir(), reason="committed results-raw/20260803 tier absent")
def test_committed_20260803_reexport_bytes_and_fingerprint():
    """Route the committed shards through the extracted primitive → gz bytes + content fp match.

    The Phase-1 byte guard (the ``20260803`` source run-roots are NOT in the repo, so a literal
    re-export can't be performed):

    - **gz bytes** — feed a deterministic *sample* of committed shards (gunzipped to their pre-gz
      bytes) through :meth:`RawTierWriter.add_shard` (which re-gzips with ``compresslevel=9,
      mtime=0``) and assert the re-gzipped bytes equal the shipped gz. A compresslevel/mtime drift
      in the primitive is **global** (identical for every shard), so a sample catches it against
      real production bytes — while keeping the test ~1s instead of re-gzipping all 519 (~17s).
    - **content fingerprint** — recompute it over **every** committed shard (gunzip-only) via the
      same ``content_fingerprint_line``/``combine_fingerprint`` the primitive uses, and assert it
      equals the value stamped in the committed manifest.

    Supersedes the plan's separate golden-hash fixture (recorded in the builder thread), being a
    strictly stronger guard over real committed bytes.
    """
    manifest_text = (COMMITTED_TIER / "manifest.json").read_text()
    manifest = json.loads(manifest_text)
    # The committed manifest is itself in the writer's canonical form (pins json_bytes:
    # sort_keys/separators/trailing-newline — a drift would rewrite every shipped byte silently).
    assert json_bytes(manifest) == manifest_text.encode("utf-8")

    items = manifest["items"]
    step = max(1, len(items) // 24)  # ~two dozen shards spread across the manifest, deterministic
    w = RawTierWriter(COMMITTED_TIER.parent, "recompute", prune=False)
    lines = []
    sampled = 0
    for i, item in enumerate(items):
        rel = item["shard"]  # manifest-declared "<group>/<item>.json.gz"
        gz = (COMMITTED_TIER / rel).read_bytes()
        pre_gz = gzip.decompress(gz)
        lines.append(content_fingerprint_line(rel, pre_gz))  # full fp: every shard
        if i % step == 0:  # byte guard: a deterministic sample re-gzipped through the primitive
            assert json_bytes(json.loads(pre_gz)) == pre_gz  # shard also in canonical json_bytes form
            w.add_shard(rel, pre_gz)
            assert w.shard_bytes(rel) == gz  # gzip settings byte-stable vs the SHIPPED tier
            sampled += 1
    assert sampled >= 12  # a non-trivial sample actually exercised the primitive's re-gzip
    assert combine_fingerprint(lines) == manifest["content_fingerprint"]
