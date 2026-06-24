"""probes/index.json validation + index⟺folders drift (spec §5.1, §8.2 check 4)."""

import json
from pathlib import Path

from tradition_validator.validator import validate_tradition


def _write_index(t: Path, obj) -> None:
    (t / "probes" / "index.json").write_text(json.dumps(obj), encoding="utf-8")


def test_valid_index_passes(valid_tradition: Path):
    assert validate_tradition(valid_tradition).ok(strict=True)


def test_index_lists_missing_folder(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 1, "probes": ["JLS-001", "JLS-999"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("JLS-999" in f.message and "drift" in f.message for f in report.errors)


def test_folder_not_in_index(valid_tradition: Path):
    (valid_tradition / "probes" / "JLS-002").mkdir()
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("JLS-002" in f.message and "drift" in f.message for f in report.errors)


def test_index_unknown_key(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 1, "probes": ["JLS-001"], "extra": 1})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)


def test_index_duplicate_probe(valid_tradition: Path):
    # Two folders, but index lists one twice -> dupe error (and drift-free otherwise).
    (valid_tradition / "probes" / "JLS-002").mkdir()
    _write_index(valid_tradition, {"schema_version": 1, "probes": ["JLS-001", "JLS-001", "JLS-002"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("duplicate" in f.message.lower() for f in report.errors)


def test_index_bad_schema_version(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 99, "probes": ["JLS-001"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("bank schema_version" in f.message for f in report.errors)


def test_index_invalid_json(valid_tradition: Path):
    (valid_tradition / "probes" / "index.json").write_text("{not json", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("Invalid JSON" in f.message for f in report.errors)


def test_no_probe_folders(valid_tradition: Path):
    (valid_tradition / "probes" / "JLS-001").rmdir()
    _write_index(valid_tradition, {"schema_version": 1, "probes": []})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("No probe folders" in f.message for f in report.errors)
