"""Smoke tests for the CLI and the Phase-1 structure-only check."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tradition_validator import core
from tradition_validator.cli import app

runner = CliRunner()


def _make_minimal_tradition(root: Path) -> Path:
    """Create a directory with the required top-level files + one probe folder.

    Content is not validated in Phase 1 — only structure (presence) is.
    """
    t = root / "sunni-islam"
    (t / "probes" / "JLS-001").mkdir(parents=True)
    for name in core.REQUIRED_TRADITION_FILES:
        (t / name).write_text("placeholder\n", encoding="utf-8")
    (t / "probes" / "index.json").write_text(
        json.dumps({"schema_version": 1, "probes": ["JLS-001"]}), encoding="utf-8"
    )
    return t


def test_help_runs():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output


def test_validate_empty_dir_fails_loudly(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(app, ["validate", str(empty)])
    assert result.exit_code == 1
    assert "tradition.yaml" in result.output
    assert "FAIL" in result.output


def test_validate_minimal_structure_passes(tmp_path: Path):
    t = _make_minimal_tradition(tmp_path)
    result = runner.invoke(app, ["validate", str(t)])
    assert result.exit_code == 0
    assert "PASS" in result.output


def test_validate_json_format_shape(tmp_path: Path):
    t = _make_minimal_tradition(tmp_path)
    result = runner.invoke(app, ["validate", str(t), "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["tradition"].endswith("sunni-islam")
    assert payload["findings"] == []


def test_validate_missing_probe_folder_fails(tmp_path: Path):
    t = tmp_path / "no-probes"
    (t / "probes").mkdir(parents=True)
    for name in core.REQUIRED_TRADITION_FILES:
        (t / name).write_text("x\n", encoding="utf-8")
    (t / "probes" / "index.json").write_text('{"schema_version": 1, "probes": []}', encoding="utf-8")
    result = runner.invoke(app, ["validate", str(t)])
    assert result.exit_code == 1
    assert "probe folders" in result.output.lower()


def test_bad_format_rejected(tmp_path: Path):
    result = runner.invoke(app, ["validate", str(tmp_path), "--format", "xml"])
    assert result.exit_code == 2


def test_validate_all_text(tmp_path: Path):
    # Two traditions: one minimal-valid, one missing files.
    _make_minimal_tradition(tmp_path)  # creates tmp_path/sunni-islam
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "tradition.yaml").write_text("x\n", encoding="utf-8")  # only a manifest
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 1  # one tradition fails -> overall fail
    assert "ALL PASS" not in result.output
    assert "SOME FAILED" in result.output


def test_validate_all_json_is_single_valid_document(tmp_path: Path):
    _make_minimal_tradition(tmp_path)
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "tradition.yaml").write_text("x\n", encoding="utf-8")
    result = runner.invoke(app, ["validate-all", str(tmp_path), "--format", "json"])
    # Must parse as ONE JSON document, not concatenated objects.
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert isinstance(payload["traditions"], list)
    assert len(payload["traditions"]) == 2
    by_ok = {t["tradition"].split("/")[-1]: t["ok"] for t in payload["traditions"]}
    assert by_ok["sunni-islam"] is True
    assert by_ok["broken"] is False


def test_validate_all_all_pass(tmp_path: Path):
    _make_minimal_tradition(tmp_path)
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 0
    assert "ALL PASS" in result.output


def test_validate_all_no_traditions(tmp_path: Path):
    result = runner.invoke(app, ["validate-all", str(tmp_path)])
    assert result.exit_code == 2
    assert "No traditions found" in result.output
