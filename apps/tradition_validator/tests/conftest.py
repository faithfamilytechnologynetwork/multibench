"""Shared test fixtures: a factory that writes a canonical-format tradition on disk.

Tests build a valid tradition then mutate specific parts to exercise each check.
The baseline is Phase-2-valid (structure + manifest + index + probe folders that
match); per-probe-folder contents become meaningful in Phase 3.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

VALID_MANIFEST = {
    "id": "sunni-islam",
    "schema_version": 1,
    "display_name": "Sunni Islam",
    "construct": "al-jalis al-salih (the righteous companion)",
    "canonical_source": {
        "title": "Riyad al-Salihin",
        "author": "al-Nawawi",
        "locus_unit": "bab",
    },
    "adherent_noun": "Muslim",
    "maintainers": [{"name": "Test Maintainer", "contact": "t@example.com"}],
    "scholar_review": {"status": "none", "reviewers": []},
    "taxonomies": {
        "pillars": {
            "description": "Conduct pillars (Ibn al-Qayyim)",
            "applies_to": "scenario",
            "values": ["courage", "restraint", "justice", "patience", "cross_cutting"],
        },
        "hearts": {
            "description": "Heart states (al-Ghazali)",
            "applies_to": "response",
            "values": ["vigilance", "patience", "reliance_on_god", "intention_sincerity"],
        },
    },
    "probe_id_pattern": r"^JLS-\d{3}$",
}


def write_tradition(
    root: Path,
    name: str = "sunni-islam",
    *,
    probes: tuple[str, ...] = ("JLS-001",),
    manifest: dict | None = None,
    index: dict | None = None,
) -> Path:
    """Write a canonical-format tradition under ``root/name`` and return its path.

    ``manifest`` / ``index`` override the defaults wholesale when given. By default
    the manifest ``id`` is set to ``name`` so ``id == dirname`` holds.
    """
    t = root / name
    (t / "probes").mkdir(parents=True)

    if manifest is None:
        manifest = {**VALID_MANIFEST, "id": name}
    (t / "tradition.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    for fname in ("README.md", "source.md", "guide.md"):
        (t / fname).write_text(f"# {fname}\n\nplaceholder content\n", encoding="utf-8")

    if index is None:
        index = {"schema_version": 1, "probes": list(probes)}
    (t / "probes" / "index.json").write_text(
        json.dumps(index, ensure_ascii=False), encoding="utf-8"
    )

    for p in probes:
        (t / "probes" / p).mkdir(exist_ok=True)

    return t


@pytest.fixture
def make_tradition():
    """Factory fixture: ``make_tradition(root, ...)`` -> tradition Path."""
    return write_tradition


@pytest.fixture
def valid_tradition(tmp_path: Path) -> Path:
    """A Phase-2-valid tradition at ``tmp_path/sunni-islam``."""
    return write_tradition(tmp_path)
