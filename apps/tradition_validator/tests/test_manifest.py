"""tradition.yaml manifest + taxonomy validation (spec §5.2/§5.3, §8.2 checks 2-3)."""

from pathlib import Path

import yaml
from conftest import find_finding

from tradition_validator.validator import validate_tradition


def _load_manifest(t: Path) -> dict:
    return yaml.safe_load((t / "tradition.yaml").read_text(encoding="utf-8"))


def _write_manifest(t: Path, m: dict) -> None:
    (t / "tradition.yaml").write_text(yaml.safe_dump(m, sort_keys=False), encoding="utf-8")


def _messages(report) -> str:
    return " | ".join(f.message for f in report.findings)


def test_valid_passes(valid_tradition: Path):
    report = validate_tradition(valid_tradition)
    assert report.ok(strict=True), _messages(report)


def test_id_must_equal_dirname(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    m["id"] = "different-id"
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    # Full located contract: error on tradition.yaml at `id`.
    f = find_finding(report, contains="directory name", severity="error")
    assert f is not None
    assert f.file.endswith("tradition.yaml")
    assert f.path == "id"


def test_unknown_key_rejected(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    m["maintainer"] = "typo-for-maintainers"  # unknown key
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("maintainer" in (f.path or "") or "extra" in f.message.lower() for f in report.errors)


def test_missing_required_field(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    del m["adherent_noun"]
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("adherent_noun" in (f.path or "") for f in report.errors)


def test_empty_manifest_null(valid_tradition: Path):
    (valid_tradition / "tradition.yaml").write_text("\n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("empty" in f.message.lower() for f in report.errors)


def test_string_field_not_coerced_from_bool(valid_tradition: Path):
    # YAML 1.1: a bare `no` parses to False; a strict str field must reject it.
    raw = (valid_tradition / "tradition.yaml").read_text(encoding="utf-8")
    raw = raw.replace("adherent_noun: Muslim", "adherent_noun: no")
    (valid_tradition / "tradition.yaml").write_text(raw, encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("adherent_noun" in (f.path or "") for f in report.errors)


def test_bad_scenario_id_pattern_regex(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    m["scenario_id_pattern"] = "JLS-(\\d{3}"  # unbalanced paren
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("regex" in f.message.lower() for f in report.errors)


def test_taxonomy_duplicate_value(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    m["taxonomies"]["pillars"]["values"] = ["justice", "justice", "courage"]
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("duplicate" in f.message.lower() for f in report.errors)


def test_taxonomy_bad_applies_to(valid_tradition: Path):
    m = _load_manifest(valid_tradition)
    m["taxonomies"]["pillars"]["applies_to"] = "sideways"
    _write_manifest(valid_tradition, m)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("applies_to" in (f.path or "") for f in report.errors)


def test_invalid_yaml_syntax(valid_tradition: Path):
    (valid_tradition / "tradition.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    assert any("Invalid YAML" in f.message for f in report.errors)
