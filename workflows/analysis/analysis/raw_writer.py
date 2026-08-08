"""Generic deterministic writer for a ``results-raw/<run_id>/`` tier (Spec 51 / #54).

Extracted from :mod:`analysis.export_raw` so a *second* catalog type (the AFB before/after
explorer, #54) can reuse the exact byte-stable writer without forking it. The primitive is
**catalog-agnostic**: it knows nothing about traditions/framings/pressures or the −1…+1 ramp —
it only serializes shards, validates the size ceilings, accumulates the ``content_fingerprint``
over the pre-gzip shard bytes, and writes ``manifest.json`` + gz shards, pruning stale files.

Shape (a **streaming finalizer**, because MultiBench builds its catalog only *after* the shard
loop): the caller streams each shard through :meth:`RawTierWriter.add_shard`, reads
:attr:`RawTierWriter.content_fingerprint` to stamp into its own ``catalog_doc`` (the caller owns
the judgment ``fingerprint`` and the whole manifest), then calls :meth:`RawTierWriter.write` to
validate-before-write and flush. No wall-clock anywhere → byte-identical re-exports.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path

from analysis.export_results import _require_safe_segment  # shared traversal guard (don't fork it)
from analysis.fingerprint import combine_fingerprint, content_fingerprint_line
from analysis.loaders import AnalysisInputError

# Guardrails calibrated ABOVE the real p99 (measured max shard 545,560 bytes ≈ 533 KB on
# roman-catholicism), not on it — they catch a pathological blowup, not normal data.
MAX_SHARD_BYTES = 1024 * 1024         # ≤ 1 MB per per-scenario gz shard
MAX_TOTAL_BYTES = 200 * 1024 * 1024   # ≤ 200 MB per run (above the ~110–150 MB observed)
_MANIFEST = "manifest.json"


def _require_safe_relpath(relpath: str) -> None:
    """Validate a multi-segment shard path (`<group>/<item>.json.gz`): EVERY component safe + ext.

    Each path component must be a safe single segment (so an intermediate ``..`` such as
    ``good/../../evil.json.gz`` is rejected, not just leading/trailing ones), and the leaf must
    carry the ``.json.gz`` extension.
    """
    parts = relpath.split("/")
    if not relpath.endswith(".json.gz") or len(parts) < 2:
        raise AnalysisInputError(f"unsafe shard path {relpath!r} — expected <group>/<item>.json.gz")
    for part in parts:
        _require_safe_segment(part, "shard path component")


def json_bytes(obj) -> bytes:
    """Deterministic JSON (sorted keys, compact separators) as UTF-8 bytes."""
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass(frozen=True)
class WriteSummary:
    """Sizes recorded by the writer (for the CLI's size measurement)."""

    shards: int                      # number of shards written (MB: scenarios; AFB: items)
    manifest_bytes: int
    shard_bytes: int                 # gzipped shard total
    shard_uncompressed_bytes: int    # pre-gzip shard total (for the ratio)
    max_shard_bytes: int
    total_bytes: int

    @property
    def compression_ratio(self) -> float:
        """Uncompressed ÷ compressed shard bytes (0.0 if nothing written)."""
        return self.shard_uncompressed_bytes / self.shard_bytes if self.shard_bytes else 0.0


class RawTierWriter:
    """Stream shards into a deterministic ``results-raw/<run_id>/`` tier, catalog-agnostic.

    ``prune`` removes stale files from a prior export of this run-id (a full export); pass
    ``prune=False`` for a purely-additive ``--limit`` fixture so a mistyped limit can never
    delete files from a real committed tier.
    """

    def __init__(self, out_root: str | Path, run_id: str, *, prune: bool) -> None:
        _require_safe_segment(run_id, "run-id")
        self._out_root = out_root
        self._run_id = run_id
        self._prune = prune
        self._docs: dict[str, bytes] = {}      # relpath → gz bytes (shards; manifest added at write)
        self._content_lines: list[str] = []    # per-shard (path + hash of canonical pre-gz bytes)
        self._n = 0
        self._shard_total = 0
        self._shard_uncompressed = 0
        self._max_shard = 0

    def add_shard(self, relpath: str, raw: bytes) -> None:
        """Buffer one shard: validate its path, gzip deterministically, accrue the content fp."""
        _require_safe_relpath(relpath)
        if relpath in self._docs:  # a second caller exists now — a collision must fail loudly
            raise AnalysisInputError(f"duplicate shard path {relpath!r}")
        payload = gzip.compress(raw, compresslevel=9, mtime=0)  # deterministic (mtime=0)
        self._docs[relpath] = payload
        self._content_lines.append(content_fingerprint_line(relpath, raw))  # over pre-gz bytes
        self._n += 1
        self._shard_total += len(payload)
        self._shard_uncompressed += len(raw)
        self._max_shard = max(self._max_shard, len(payload))

    def shard_bytes(self, relpath: str) -> bytes:
        """The deterministic gz bytes buffered for ``relpath`` (for byte-level guards)."""
        return self._docs[relpath]

    @property
    def content_fingerprint(self) -> str:
        """``sha256:<hex>`` over the buffered shard byte stream (sorted → order-independent)."""
        return combine_fingerprint(self._content_lines)

    def write(self, catalog_doc: dict, *, max_shard_bytes: int = MAX_SHARD_BYTES,
              max_total_bytes: int = MAX_TOTAL_BYTES) -> WriteSummary:
        """Validate all sizes BEFORE writing anything (no partial tier), then write + prune.

        The caller passes its fully-built ``catalog_doc`` (having already stamped
        :attr:`content_fingerprint` and its own judgment ``fingerprint``). Ceiling values are
        parameters so a caller can keep them monkeypatchable at its own module scope.
        """
        manifest_bytes = json_bytes(catalog_doc)
        docs = dict(self._docs)          # shard order preserved; manifest last
        docs[_MANIFEST] = manifest_bytes

        for name, payload in docs.items():
            if name != _MANIFEST and len(payload) > max_shard_bytes:
                raise AnalysisInputError(
                    f"{name} is {len(payload)} bytes (> {max_shard_bytes} per-shard ceiling)"
                )
        total = sum(len(p) for p in docs.values())
        if total > max_total_bytes:
            raise AnalysisInputError(f"dataset total {total} bytes (> {max_total_bytes} ceiling)")

        run_dir = Path(self._out_root) / self._run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if self._prune:
            existing = {p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file()}
            for rel in existing - set(docs):
                (run_dir / rel).unlink()
            # remove any now-empty group dirs (deepest first) so a dropped group leaves nothing
            for d in sorted((p for p in run_dir.rglob("*") if p.is_dir()),
                            key=lambda p: len(p.parts), reverse=True):
                if not any(d.iterdir()):
                    d.rmdir()
        for name, payload in docs.items():
            path = run_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        return WriteSummary(
            shards=self._n, manifest_bytes=len(manifest_bytes), shard_bytes=self._shard_total,
            shard_uncompressed_bytes=self._shard_uncompressed, max_shard_bytes=self._max_shard,
            total_bytes=total,
        )
