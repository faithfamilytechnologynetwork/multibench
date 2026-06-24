"""Loader robustness: non-UTF-8 input is rejected with a located finding, never a
raw traceback (spec §8.2 check 10). Covers the loader unit and the end-to-end
validator path for a prose file (load_text) and a machine file (load_yaml/load_json)."""

from pathlib import Path

from conftest import find_finding

from tradition_validator.loaders import load_json, load_text, load_yaml
from tradition_validator.validator import validate_tradition

# Bytes that are not valid UTF-8: a lone 0xFF/0xFE and bare continuation bytes.
NON_UTF8 = b"\xff\xfe not valid \x80\x81 utf-8\n"


def test_load_text_rejects_non_utf8(tmp_path: Path):
    p = tmp_path / "bad.md"
    p.write_bytes(NON_UTF8)
    data, err = load_text(p)
    assert data is None
    assert err is not None and err.severity == "error"
    assert "not valid UTF-8" in err.message
    assert err.file == str(p)


def test_load_yaml_rejects_non_utf8(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_bytes(NON_UTF8)
    data, err = load_yaml(p)
    assert data is None
    assert err is not None and "not valid UTF-8" in err.message


def test_load_json_rejects_non_utf8(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_bytes(NON_UTF8)
    data, err = load_json(p)
    assert data is None
    assert err is not None and "not valid UTF-8" in err.message


def test_validator_reports_non_utf8_prose(valid_tradition: Path):
    # A prose file (read via load_text in _nonempty_text) that is not UTF-8 must yield a
    # located error, not crash the run.
    (valid_tradition / "guide.md").write_bytes(NON_UTF8)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    f = find_finding(report, contains="not valid UTF-8", severity="error")
    assert f is not None and f.file.endswith("guide.md")


def test_validator_reports_non_utf8_manifest(valid_tradition: Path):
    # A machine file (tradition.yaml, read via load_yaml) that is not UTF-8 is likewise a
    # located error rather than a YAML/decoding traceback.
    (valid_tradition / "tradition.yaml").write_bytes(NON_UTF8)
    report = validate_tradition(valid_tradition)
    assert not report.ok(strict=False)
    f = find_finding(report, contains="not valid UTF-8", severity="error")
    assert f is not None and f.file.endswith("tradition.yaml")
