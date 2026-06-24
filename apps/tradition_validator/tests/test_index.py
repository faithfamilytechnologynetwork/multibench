"""scenarios/index.json validation + index⟺folders drift (spec §5.1, §8.2 check 4)."""

import json
import shutil
from pathlib import Path

from conftest import find_finding

from tradition_validator.validator import validate_tradition


def _write_index(t: Path, obj) -> None:
    (t / "scenarios" / "index.json").write_text(json.dumps(obj), encoding="utf-8")


def test_valid_index_passes(valid_tradition: Path):
    assert validate_tradition(valid_tradition).ok(strict=True)


def test_index_lists_missing_folder(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 1, "scenarios": ["JLS-001", "JLS-999"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    # Assert the FULL located contract: severity + file + path (spec §8.3).
    f = find_finding(report, contains="JLS-999", severity="error")
    assert f is not None and "drift" in f.message
    assert f.file.endswith("scenarios/index.json")
    assert f.path == "scenarios"


def test_folder_not_in_index(valid_tradition: Path):
    (valid_tradition / "scenarios" / "JLS-002").mkdir()
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    # This drift case is located on index.json at `scenarios`, like the inverse case.
    f = find_finding(report, contains="JLS-002", severity="error")
    assert f is not None and "drift" in f.message
    assert f.file.endswith("scenarios/index.json")
    assert f.path == "scenarios"


def test_index_unknown_key(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 1, "scenarios": ["JLS-001"], "extra": 1})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)


def test_index_duplicate_scenario(valid_tradition: Path):
    # Two folders, but index lists one twice -> dupe error (and drift-free otherwise).
    (valid_tradition / "scenarios" / "JLS-002").mkdir()
    _write_index(valid_tradition, {"schema_version": 1, "scenarios": ["JLS-001", "JLS-001", "JLS-002"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("duplicate" in f.message.lower() for f in report.errors)


def test_index_bad_schema_version(valid_tradition: Path):
    _write_index(valid_tradition, {"schema_version": 99, "scenarios": ["JLS-001"]})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("bank schema_version" in f.message for f in report.errors)


def test_index_invalid_json(valid_tradition: Path):
    (valid_tradition / "scenarios" / "index.json").write_text("{not json", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("Invalid JSON" in f.message for f in report.errors)


def test_no_scenario_folders(valid_tradition: Path):
    shutil.rmtree(valid_tradition / "scenarios" / "JLS-001")
    _write_index(valid_tradition, {"schema_version": 1, "scenarios": []})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("No scenario folders" in f.message for f in report.errors)


def test_index_missing_scenarios_key_is_located_error(valid_tradition: Path):
    # A `scenarios` key that is absent entirely must surface as a clear, located
    # "Field required" error on `scenarios` — NOT silently default to [] and then
    # mis-report the real JLS-001 folder as drift (the medium item from PR #2).
    _write_index(valid_tradition, {"schema_version": 1})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    f = find_finding(report, contains="scenarios", severity="error")
    assert f is not None
    assert f.file.endswith("scenarios/index.json")
    assert f.path == "scenarios"
    assert "required" in f.message.lower()
    # The misleading "drift" diagnosis must NOT be what the user sees.
    assert not any("drift" in f.message for f in report.errors)


def test_index_explicit_empty_scenarios_still_allowed(valid_tradition: Path):
    # The fix for the missing-key case must not reject an explicit empty list: with a
    # folder still present, an empty `scenarios` is a clean drift error, not a schema error.
    _write_index(valid_tradition, {"schema_version": 1, "scenarios": []})
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    # The diagnosis is drift (folder on disk, not listed) — not "Field required".
    assert any("drift" in f.message for f in report.errors)
    assert not any("required" in f.message.lower() and (f.path == "scenarios") for f in report.errors)
